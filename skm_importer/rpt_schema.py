SECTION_DEFAULTS = {
    "Bus": {
        "AF_Inst/ZSI Avail": "0",
        "AF_ElectrodeConfig": "1",
        "AF_EquipType": "1",
        "AF_UnLinkedBoxDimensions": "0",
        "AF_UnLinkedElectrodeConfig": "1",
        "AF_UnLinkedEquipType": "1",
    },
    "Cable": {
        "InService": "1",
        "Phase": "7",
        "Size/Do Not Size": "0",
        "KeyInLibrary": "1",
        "InsulationType": "PVC",
    },
    "2-Winding Transformer": {
        "InService": "1",
        "TransformerType": "0",
        "Phase": "7",
        "Size/Do Not Size": "0",
        "SizingCriteria": "0",
        "Pri Connection": "0",
        "Sec Connection": "2",
    },
    "Utility": {
        "InService": "1",
        "Phase": "7",
        "SC Contribution Unit": "2",
        "SC Contribution Type": "0",
    },
    "Protective Device": {
        "InService": "1",
        "Poles": "0",
        "INT/SC RatingBasis": "0",
        "ConnectionType": "2",
        "AF_ElectrodeConfig": "0",
        "AF_EquipType": "1",
        "AF_UnLinkedBoxDimensions": "0",
        "AF_UnLinkedElectrodeConfig": "0",
        "AF_UnLinkedEquipType": "0",
    },
}
SECTION_FIELDS = {
    "Bus": """ComponentName|ComponentType|Alternate UID|Alternate Name|Alternate Type|Alternate Desc 1|Alternate Desc 2|Alternate Cubicle Name|SystemNominalVoltage|EquipmentCategory|Manufacturer|Description|MaxVoltage (pu)|RatingDescription|ContinuousRating|Voltage Rating|TestXOverR|SeriesRating|ShortCircuitRating|AF_LabelNumber|AF_Inst/ZSI Protection|AF_Inst/ZSI Avail|AF_ElectrodeConfig|AF_EquipType|AF_BoxDepth|AF_BoxHeight|AF_BoxWidth|AF_UnLinkedBoxDimensions|AF_UnLinkedElectrodeConfig|AF_UnLinkedEquipType""".split("|"),
    "Cable": """ComponentName|ComponentType|Alternate UID|Alternate Name|Alternate Type|Alternate Desc 1|Alternate Desc 2|Alternate Cubicle Name|ConnectedComponent1|ConnectedComponent2|SystemNominalVoltage|InService|Phase|CableSize|NeutralSize|QtyPerPhase|Length|Size/Do Not Size|Manufacturer|ConductorType|#/Conductors|Description|DuctMaterial|InsulationType|InsulationClass|Conductor Desc|Installation|AmpacityDescription|VoltageRating|CircularMils|Rpos|Rzero|Xpos|Xzero|Temperature Ambient|Design Ampacity|DeratingFactor|RacewaySize|RacewayType|KeyInLibrary|B/2 pos|B/2 zero|G/2 pos|G/2 zero|Ampacity|Ampacity Sec|Ampacity (DamageCurve)|AdditionalDerating""".split("|"),
    "2-Winding Transformer": """ComponentName|ComponentType|Alternate UID|Alternate Name|Alternate Type|Alternate Desc 1|Alternate Desc 2|Alternate Cubicle Name|ConnectedComponent1|ConnectedComponent2|SystemNominalVoltage|SystemNominalVoltageSecondary|InService|TransformerType|Phase|Nominal kVA|FullLoad kVA|Size/Do Not Size|SizingCriteria|Pri Connection|Pri Tap|Pri RatedVoltage|Sec Connection|Sec Tap|Sec RatedVoltage|Manufacturer|Type|Rpos|Rzero|Xpos|Xzero|Pri NeutralR|Pri NeutralX|Sec NeutralR|Sec NeutralX|Ampacity|Ampacity Sec|KeyInLibrary""".split("|"),
    "Pi Equivalent": """ComponentName|ComponentType|Alternate UID|Alternate Name|Alternate Type|Alternate Desc 1|Alternate Desc 2|Alternate Cubicle Name|ConnectedComponent1|ConnectedComponent2|SystemNominalVoltage|InService|PiType|Phase|Ampacity|Ampacity Sec|Rpos|Xpos|Rzero|Xzero|G/2 pos|B/2 pos|G/2 zero|B/2 zero|Units|Base kVA|BaseVoltage""".split("|"),
    "Utility": """ComponentName|ComponentType|Alternate UID|Alternate Name|Alternate Type|Alternate Desc 1|Alternate Desc 2|Alternate Cubicle Name|ConnectedComponent1|SystemNominalVoltage|InService|Phase|Init Voltage|Init VoltageAngle|SC Contribution Unit|SC Contribution 3P|SC Contribution SLG|SC Contribution Type|X/R 3P|X/R SLG|Rated MVA|Rated Voltage|RPos PU|XPos PU|RZero PU|XZero PU""".split("|"),
    "Synchronous Generator": """ComponentName|ComponentType|Alternate UID|Alternate Name|Alternate Type|Alternate Desc 1|Alternate Desc 2|Alternate Cubicle Name|ConnectedComponent1|SystemNominalVoltage|InService|GeneratorType|Phase|ConnectionType|Description|RatedVoltage|RatedSize|RatedUnits|Rated PF|LeadorLag|Poles|SourceType|Init kW|Init kVAR|Init Voltage|Init VoltageAngle|Min kVAR|Max kVAR|VAR Participation|X\"Pos|X\"Neg|X\"Zero|X/R Pos|X/R Neg|X/R Zero|LinkWithContribution|X\"d|X\"q|X'd|Xd|R0|X0|Rg|Xdpp Saturated|Xdp Saturated|Xd Saturated|Ta|Tdp(TCC)|Tdpp(TCC)|If|Ifg|Tdpp|Tdp|Tdc|SteadyState|ExcitationLimit|Base linked with Rated|Base kVA|BaseVoltage|Pg (Power Station Unit)""".split("|"),
    "Induction Motor": """ComponentName|ComponentType|Alternate UID|Alternate Name|Alternate Type|Alternate Desc 1|Alternate Desc 2|Alternate Cubicle Name|ConnectedComponent1|SystemNominalVoltage|InService|Phase|ConnectionType|Description|NumMotors|RatedSize|RatedUnits|Load Factor|EnergyAuditLoadType|PF|LeadOrLag|Efficiency|Poles|Group|Priority|Link X/R w/ Starting PF|Link Xd\" (Z) w/ LRA/FLA|X\"d|X/R|R/X|Base linked with Rated|Base kVA|BaseVoltage|Rs/Rr|Tdpp|Tdc""".split("|"),
    "Protective Device": """ComponentName|ComponentType|Alternate UID|Alternate Name|Alternate Type|Alternate Desc 1|Alternate Desc 2|Alternate Cubicle Name|ConnectedComponent1|ConnectedComponent2|SystemNominalVoltage|InService|ProtectionType|Manufacturer|Type|Description|TCC No.|SelCoor Downstream Function|Frame/Model|Frame/Rating|FrameVoltage|InterruptingRating|Sensor/Trip|Plug|OverLoadFactor|DeviceVoltage|ShortTime|Override|Poles|ProtectiveDeviceLibName|VoltageRangeFactor K|Test X/R|INT/SC RatingBasis|Breaker/Switch Speed|Breaker/Switch PartingTime|Mom_Rating|Settings|FullLoadAmps|CT Primary|CT Ratio|CT ScalingFactor|CT Secondary|ConnectionType|AF_ElectrodeConfig|AF_EquipType|AF_BoxDepth|AF_BoxHeight|AF_BoxWidth|AF_UnLinkedBoxDimensions|AF_UnLinkedElectrodeConfig|AF_UnLinkedEquipType""".split("|"),
    "Auto-Transfer Switch": """ComponentName|ComponentType|Alternate UID|Alternate Name|Alternate Type|Alternate Desc 1|Alternate Desc 2|Alternate Cubicle Name|ConnectedComponent1|ConnectedComponent2|ConnectedComponent3|Switch Position|Description|ConnectedBus|ConnectedBus2|ConnectedBus3""".split("|"),
    "UPS": """ComponentName|ComponentType|Alternate UID|Alternate Name|Alternate Type|Alternate Desc 1|Alternate Desc 2|Alternate Cubicle Name|ConnectedComponent1|ConnectedComponent2|SystemNominalVoltage|SystemNominalVoltageLoad|InService|Description|Phase LineSide|RatedVoltageLine|Phase LoadSide|RatedVoltageLoad|UPS Rating|PF|X/R|SC Contribution 3P|SC Contribution SLG|BatteryCapacity|Bypass Switch|Bypass Zpos|Bypass X/Rpos|Bypass Zzero|Bypass X/Rzero|Init Voltage|Init VoltageAngle|Ampacity|I_K_Factor|CoorEval_Notes|OperatingMode""".split("|"),
}


def default_template() -> str:
    lines = [
        "// Export start : generated by SKM Importer",
        "// Datablock format : All Input Data",
        "// Query name : *ALL COMPONENTS",
        "",
    ]
    for section_name, fields in SECTION_FIELDS.items():
        lines.extend((f"// --- {section_name} ---", "//" + "\t".join(f"<{field}>" for field in fields)))
    return "\r\n".join(lines) + "\r\n"