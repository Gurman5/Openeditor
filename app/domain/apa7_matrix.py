MATRIX_ID_MAP = {
    "FP001": "APA-07",
    "SPE004": "APA-14",
    "TAB001": "APA-15",
    "STY003": "APA-01",
    "STY004": "APA-03",
    "APA001": "APA-00",
}

def get_matrix_id(legacy_id: str) -> str:
    """Resolve a legacy rule ID to its standard APA-7 matrix ID."""
    return MATRIX_ID_MAP.get(legacy_id, legacy_id)