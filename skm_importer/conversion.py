from collections import defaultdict
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from .rpt_schema import SECTION_FIELDS


def build_records(
    workbook_path: str | Path,
) -> tuple[dict[str, list[tuple[str, ...]]], tuple[str, ...]]:
    path = Path(workbook_path)
    if path.suffix.lower() not in {".xlsx", ".xlsm"}:
        raise ValueError("Generating SKM reports requires an .xlsx or .xlsm workbook.")
    if not path.is_file():
        raise FileNotFoundError(f"Workbook not found: {path}")

    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        if "FIELD CABLEOCP" not in workbook.sheetnames:
            raise ValueError("The workbook is missing the FIELD CABLEOCP sheet.")

        records: dict[str, list[tuple[str, ...]]] = defaultdict(list)
        warnings: list[str] = []
        transformer_sides = _transformers(workbook, records, warnings)
        buses: dict[str, dict[str, str]] = {}
        _bus_ducts(workbook, buses, warnings)
        utilities: dict[str, tuple[str, str]] = {}
        cable_names: set[str] = set()
        device_names: set[str] = set()
        sheet = workbook["FIELD CABLEOCP"]

        for row_number, values in enumerate(sheet.iter_rows(min_row=6, values_only=True), start=6):
            source_type, source_label = _text(_cell(values, 1)), _text(_cell(values, 2))
            load_type, load_label = _text(_cell(values, 3)), _text(_cell(values, 4))
            if not any((source_type, source_label, load_type, load_label)):
                continue
            if not all((source_type, source_label, load_type, load_label)):
                warnings.append(f"FIELD CABLEOCP row {row_number}: skipped because a source or load type/label is missing.")
                continue

            voltage = _text(_cell(values, 5))
            source_ref = _endpoint_ref(source_type, source_label, voltage, transformer_sides)
            load_ref = _endpoint_ref(load_type, load_label, voltage, transformer_sides)
            if source_ref is None or load_ref is None:
                warnings.append(f"FIELD CABLEOCP row {row_number}: skipped because a transformer endpoint is ambiguous or missing from XFMR.")
                continue

            for component_type, label in ((source_type, source_label), (load_type, load_label)):
                if component_type == "TRANS":
                    continue
                bus_name = _node_name(component_type, label)
                bus = buses.setdefault(bus_name, {"ComponentName": bus_name, "ComponentType": "10"})
                if voltage and not bus.get("SystemNominalVoltage"):
                    bus["SystemNominalVoltage"] = voltage
                elif voltage and bus.get("SystemNominalVoltage") != voltage:
                    warnings.append(
                        f"FIELD CABLEOCP row {row_number}: {bus_name} has conflicting nominal voltages; kept {bus['SystemNominalVoltage']}."
                    )
                if component_type == "UTILITY":
                    utilities[bus_name] = (f"UTILITY-{label}", voltage)

            cable_name = f"FEED {load_type} {load_label}"
            if cable_name in cable_names:
                warnings.append(f"FIELD CABLEOCP row {row_number}: duplicate feeder name {cable_name}; skipped.")
                continue
            cable_names.add(cable_name)

            has_protection = any(_text(_cell(values, column)) for column in (19, 20, 21, 22))
            device_name = _device_name(load_type, load_label, _text(_cell(values, 20)))
            if has_protection:
                if device_name in device_names:
                    device_name = f"{device_name} {row_number}"
                    warnings.append(f"FIELD CABLEOCP row {row_number}: duplicate protection name; generated {device_name}.")
                device_names.add(device_name)
                protection_code = _protection_code(device_name, _text(_cell(values, 20)))
                if not protection_code:
                    warnings.append(f"FIELD CABLEOCP row {row_number}: protective-device type is unknown; left its SKM type blank.")
                _append_record(
                    records,
                    "Protective Device",
                    {
                        "ComponentName": device_name,
                        "ComponentType": "112",
                        "ConnectedComponent1": f"{cable_name}:2",
                        "ConnectedComponent2": load_ref,
                        "SystemNominalVoltage": voltage,
                        "ProtectionType": protection_code,
                        "Manufacturer": _text(_cell(values, 19)),
                        "Type": _text(_cell(values, 20)),
                        "FrameVoltage": voltage,
                        "InterruptingRating": _text(_cell(values, 21)),
                        "Sensor/Trip": _text(_cell(values, 22)),
                        "Plug": _text(_cell(values, 22)),
                    },
                )

            _append_record(
                records,
                "Cable",
                {
                    "ComponentName": cable_name,
                    "ComponentType": "20",
                    "ConnectedComponent1": source_ref,
                    "ConnectedComponent2": f"{device_name}:1" if has_protection else load_ref,
                    "SystemNominalVoltage": voltage,
                    "CableSize": _text(_cell(values, 10)),
                    "Length": _text(_cell(values, 11)),
                    "ConductorType": _conductor_type(_cell(values, 12)),
                    "InsulationClass": _text(_cell(values, 13)),
                    "RacewayType": _text(_cell(values, 14)),
                    "Conductor Desc": _text(_cell(values, 15)),
                    "#/Conductors": _conductor_count(_cell(values, 9)),
                },
            )
            if not _text(_cell(values, 10)) or not _text(_cell(values, 11)):
                warnings.append(f"FIELD CABLEOCP row {row_number}: {cable_name} is missing cable size or length.")

        for bus in buses.values():
            _append_record(records, "Bus", bus)
        for bus_name, (utility_name, voltage) in utilities.items():
            _append_record(
                records,
                "Utility",
                {
                    "ComponentName": utility_name,
                    "ComponentType": "70",
                    "ConnectedComponent1": f"{bus_name}:1",
                    "SystemNominalVoltage": voltage,
                },
            )

        return dict(records), tuple(warnings)
    finally:
        workbook.close()


def _transformers(
    workbook: Any,
    records: dict[str, list[tuple[str, ...]]],
    warnings: list[str],
) -> dict[str, tuple[str, str, str, str]]:
    sides: dict[str, tuple[str, str, str, str]] = {}
    unmapped_construction_types = 0
    if "XFMR" not in workbook.sheetnames:
        return sides

    for row_number, values in enumerate(workbook["XFMR"].iter_rows(min_row=6, values_only=True), start=6):
        name = _text(_cell(values, 1))
        if not name:
            continue
        component_name = name if name.upper().startswith("TRANS ") else f"TRANS {name}"
        label = component_name[6:].strip()
        primary_bus, secondary_bus = f"{label} PRIM BUS", label
        primary_voltage, secondary_voltage = _text(_cell(values, 2)), _text(_cell(values, 3))
        if not primary_voltage or not secondary_voltage:
            warnings.append(f"XFMR row {row_number}: {component_name} is missing a primary or secondary voltage.")
        if _text(_cell(values, 6)):
            unmapped_construction_types += 1
        sides[component_name.casefold()] = (primary_bus, secondary_bus, primary_voltage, secondary_voltage)
        resistance, reactance = _impedance_components(_text(_cell(values, 5)), _text(_cell(values, 8)))
        primary_connection, secondary_connection = _connection_codes(_text(_cell(values, 7)))
        _append_record(
            records,
            "2-Winding Transformer",
            {
                "ComponentName": component_name,
                "ComponentType": "30",
                "ConnectedComponent1": f"{primary_bus}:1",
                "ConnectedComponent2": f"{secondary_bus}:1",
                "SystemNominalVoltage": primary_voltage,
                "SystemNominalVoltageSecondary": secondary_voltage,
                "Nominal kVA": _text(_cell(values, 4)),
                "Pri Connection": primary_connection,
                "Sec Connection": secondary_connection,
                "Rpos": resistance,
                "Xpos": reactance,
            },
        )
        _append_record(records, "Bus", {"ComponentName": primary_bus, "ComponentType": "10", "SystemNominalVoltage": primary_voltage})
        _append_record(records, "Bus", {"ComponentName": secondary_bus, "ComponentType": "10", "SystemNominalVoltage": secondary_voltage})
    if unmapped_construction_types:
        warnings.append(
            f"XFMR: survey construction type was not mapped for {unmapped_construction_types} records; SKM transformer type fields were left blank."
        )
    return sides


def _bus_ducts(workbook: Any, buses: dict[str, dict[str, str]], warnings: list[str]) -> None:
    if "BUS DUCT" not in workbook.sheetnames:
        return
    for row_number, values in enumerate(workbook["BUS DUCT"].iter_rows(min_row=6, values_only=True), start=6):
        name = _text(_cell(values, 1))
        if not name:
            continue
        component_name = name if name.upper().startswith("BUS RISER ") else f"BUS RISER {name}"
        bus = buses.setdefault(component_name, {"ComponentName": component_name, "ComponentType": "10"})
        bus.update(
            {
                "ContinuousRating": _text(_cell(values, 3)),
                "Manufacturer": _text(_cell(values, 5)),
                "Description": _text(_cell(values, 2)),
            }
        )
        if not bus["ContinuousRating"]:
            warnings.append(f"BUS DUCT row {row_number}: {component_name} is missing ampacity.")


def _endpoint_ref(
    component_type: str,
    label: str,
    voltage: str,
    transformer_sides: dict[str, tuple[str, str, str, str]],
) -> str | None:
    if component_type != "TRANS":
        return f"{_node_name(component_type, label)}:1"
    sides = transformer_sides.get(f"TRANS {label}".casefold())
    if sides is None:
        return None
    primary_bus, secondary_bus, primary_voltage, secondary_voltage = sides
    if voltage and voltage == primary_voltage:
        return f"{primary_bus}:1"
    if voltage and voltage == secondary_voltage:
        return f"{secondary_bus}:1"
    return None


def _node_name(component_type: str, label: str) -> str:
    return f"UTILITY {label}" if component_type == "UTILITY" else f"{component_type} {label}"


def _device_name(load_type: str, load_label: str, model: str) -> str:
    model_name = model.upper()
    fuse_models = {
        "A4BY", "A4J", "A6D", "AJT", "CLF", "ECSR", "FLSRID", "FRN-R", "FRS-R",
        "JKS", "LPJ_SP", "LPN-RK", "LPS-RK", "TR", "TRS",
    }
    words = load_type.strip().split(maxsplit=1)
    declared_prefix = words[0].upper() if words else ""
    category = words[1] if declared_prefix in {"CB", "FUSE"} and len(words) > 1 else load_type
    prefix = "FUSE" if declared_prefix == "FUSE" or model_name in fuse_models else "CB"
    parts = [prefix]
    if category:
        parts.append(category)
    if load_label:
        parts.append(load_label)
    return " ".join(parts)


def _protection_code(device_name: str, model: str) -> str:
    if device_name.startswith("FUSE "):
        return "11041"
    if model.upper() in {"TP", "THP", "SKPB"}:
        return "11001"
    if model.upper() in {"EHB", "LA", "NF", "QB", "QP", "TED", "TEY", "THQB", "TQD"}:
        return "11003"
    return ""


def _append_record(
    records: dict[str, list[tuple[str, ...]]],
    section: str,
    values: dict[str, str],
) -> None:
    record = {field: "" for field in SECTION_FIELDS[section]}
    for field, value in values.items():
        if field not in record:
            raise ValueError(f"Unknown {section} field: {field}")
        record[field] = value
    records.setdefault(section, []).append(tuple(record[field] for field in SECTION_FIELDS[section]))


def _cell(values: tuple[object, ...], index: int) -> object:
    return values[index] if index < len(values) else None


def _text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _conductor_type(value: object) -> str:
    return {"CU": "Copper", "AL": "Aluminum"}.get(_text(value).upper(), _text(value))


def _conductor_count(value: object) -> str:
    try:
        count = int(float(_text(value)))
    except ValueError:
        return ""
    return str(count - 1) if 1 <= count <= 6 else ""


def _connection_codes(connection: str) -> tuple[str, str]:
    codes = {"DELTA": "0", "WYE": "1", "WYE GND": "2", "WYE-GND": "2"}
    sides = [side.strip() for side in connection.upper().split("-")]
    if len(sides) != 2:
        return "", ""
    return codes.get(sides[0], ""), codes.get(sides[1], "")


def _impedance_components(impedance: str, x_over_r: str) -> tuple[str, str]:
    try:
        magnitude, ratio = float(impedance), float(x_over_r)
    except ValueError:
        return "", ""
    resistance = magnitude / (1 + ratio * ratio) ** 0.5
    reactance = resistance * ratio
    return f"{resistance:.4f}", f"{reactance:.4f}"