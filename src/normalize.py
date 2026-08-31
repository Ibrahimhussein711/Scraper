from typing import Any


def normalize_price(price_text: str) -> float:
    """
    Convert a price like '£51.77' into 51.77.
    """

    cleaned = price_text.replace("£", "").strip()

    return float(cleaned)


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    """
    Add normalized fields while preserving the raw values.
    """

    normalized = record.copy()

    normalized["price_gbp"] = normalize_price(
        record["price_text"]
    )

    return normalized