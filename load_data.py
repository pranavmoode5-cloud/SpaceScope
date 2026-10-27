"""Import and normalize the Hugging Face launch log into MongoDB."""

import os
import re

import pandas as pd
from datasets import load_dataset
from pymongo import MongoClient, UpdateOne

DATASET_ID = "juliensimon/space-launch-log"
DATASET_CONFIG = "launches"
RECORD_ID_PREFIX = "space-launch-log-v1:"
MISSING_VALUES = {"", "-", "?", "none", "null", "nan", "n/a"}


def normalized_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def find_column(frame: pd.DataFrame, *names: str):
    columns = {normalized_name(str(column)): column for column in frame.columns}
    for name in names:
        if normalized_name(name) in columns:
            return columns[normalized_name(name)]
    return None


def text_column(frame: pd.DataFrame, column) -> pd.Series:
    if column is None:
        return pd.Series(None, index=frame.index, dtype="object")
    values = frame[column].astype("string").str.strip()
    missing = values.str.lower().isin(MISSING_VALUES)
    return values.mask(missing, pd.NA).astype("object")


def clean(frame: pd.DataFrame) -> pd.DataFrame:
    """Map source fields without interpreting undocumented codes as dates or outcomes."""
    frame = frame.copy()

    organization_col = find_column(frame, "agency", "company", "company name", "organization", "operator")
    vehicle_col = find_column(frame, "lv_type", "rocket", "vehicle", "launch vehicle")
    mission_col = find_column(frame, "mission", "mission name", "payload")
    flight_col = find_column(frame, "flight", "flight id")
    site_col = find_column(frame, "launch_site", "site", "location", "launch location")
    pad_col = find_column(frame, "launch_pad", "pad")
    category_col = find_column(frame, "category")
    launch_code_col = find_column(frame, "launch_code")
    fail_code_col = find_column(frame, "fail_code")
    source_label_col = find_column(frame, "launch_date")
    source_julian_day_col = find_column(frame, "launch_jd")
    payload_col = find_column(frame, "orbital_payload")
    destination_col = find_column(frame, "destination")
    apogee_col = find_column(frame, "apogee")
    if organization_col is None and vehicle_col is None and mission_col is None:
        raise ValueError(f"Dataset schema was not recognized. Found columns: {list(frame.columns)}")

    records = pd.DataFrame(index=frame.index)
    records["date"] = pd.Series(pd.NaT, index=frame.index, dtype="datetime64[ns]")
    records["year"] = pd.Series(pd.NA, index=frame.index, dtype="Int64")
    records["company"] = text_column(frame, organization_col)
    records["rocket"] = text_column(frame, vehicle_col)
    records["mission"] = text_column(frame, mission_col)
    records["flight"] = text_column(frame, flight_col)
    records["site"] = text_column(frame, site_col)
    records["pad"] = text_column(frame, pad_col)
    records["category"] = text_column(frame, category_col)
    records["launch_code"] = text_column(frame, launch_code_col)
    records["fail_code"] = text_column(frame, fail_code_col)
    records["source_launch_label"] = text_column(frame, source_label_col)
    records["source_julian_day"] = (
        pd.to_numeric(frame[source_julian_day_col], errors="coerce")
        if source_julian_day_col is not None
        else pd.Series(float("nan"), index=frame.index)
    )
    for output, source_column in (
        ("orbital_payload", payload_col),
        ("destination", destination_col),
        ("apogee", apogee_col),
    ):
        records[output] = (
            pd.to_numeric(frame[source_column], errors="coerce")
            if source_column is not None
            else pd.Series(float("nan"), index=frame.index)
        )
    records["outcome"] = pd.Series(None, index=frame.index, dtype="object")
    records["country"] = pd.Series(None, index=frame.index, dtype="object")
    return records.reset_index(drop=True)


def import_dataset(uri: str, database: str) -> int:
    print(f"Loading {DATASET_ID} ({DATASET_CONFIG})...")
    dataset = load_dataset(DATASET_ID, DATASET_CONFIG)
    source = dataset["train"] if "train" in dataset else next(iter(dataset.values()))
    cleaned = clean(source.to_pandas())
    collection_name = "launches"
    batch_size = 1000
    imported = 0

    with MongoClient(uri, serverSelectionTimeoutMS=5000) as client:
        client.admin.command("ping")
        collection = client[database][collection_name]
        for index in list(collection.list_indexes()):
            if index["name"] != "_id_":
                collection.drop_index(index["name"])

        for offset in range(0, len(cleaned), batch_size):
            batch = cleaned.iloc[offset : offset + batch_size]
            records = batch.astype(object).where(pd.notna(batch), None).to_dict("records")
            operations = [
                UpdateOne(
                    {"_id": f"{RECORD_ID_PREFIX}{offset + position}"},
                    {"$set": record},
                    upsert=True,
                )
                for position, record in enumerate(records)
            ]
            if operations:
                collection.bulk_write(operations, ordered=False)
                imported += len(operations)
                print(f"Imported {imported:,} / {len(cleaned):,} records", end="\r")

        collection.delete_many({"_id": {"$not": {"$regex": f"^{re.escape(RECORD_ID_PREFIX)}"}}})

    print(f"\nImported {imported:,} source records into MongoDB database '{database}'.")
    print("Dates and outcomes remain unavailable because the source does not provide reliable values.")
    return imported


def main() -> None:
    uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    database = os.environ.get("MONGO_DB", "spacescope")
    import_dataset(uri, database)


if __name__ == "__main__":
    main()
