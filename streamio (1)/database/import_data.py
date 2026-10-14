import csv
import os
from pathlib import Path

import pymysql
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / "backend" / ".env")

CSV_DIR = Path(
    os.getenv(
        "STREAMIO_CSV_DIR",
        PROJECT_ROOT.parent / "streamio_dataset" / "final_pkg" / "csv",
    )
)
IMPORT_ORDER = (
    "user",
    "plan",
    "category",
    "content",
    "subscription",
    "payment",
    "watchlist",
    "watch_history",
    "review",
)
PRIMARY_KEYS = {
    "user": "user_id",
    "plan": "plan_id",
    "category": "category_id",
    "content": "content_id",
    "subscription": "subscription_id",
    "payment": "payment_number",
    "watchlist": "watchlist_id",
    "watch_history": "history_id",
    "review": "review_id",
}


def normalize_value(column: str, value: str | None) -> object:
    if value is None or value.strip() == "":
        return None
    if column == "completed":
        return value.strip().lower() in {"1", "true", "yes"}
    return value.strip()


def subscription_snapshot(
    row: dict[str, str], plan_catalog: dict[int, dict[str, str]]
) -> dict[str, str]:
    try:
        plan = plan_catalog[int(row["plan_id"])]
    except (KeyError, ValueError) as error:
        raise ValueError(
            f"Subscription {row.get('subscription_id', '?')} references a missing plan."
        ) from error
    return {
        "subscription_id": row["subscription_id"],
        "plan_name": plan["plan_name"],
        "price": plan["price"],
        "start_date": row["start_date"],
        "end_date": row["end_date"],
        "status": row["status"],
        "user_id": row["user_id"],
    }


def read_plan_catalog() -> dict[int, dict[str, str]]:
    path = CSV_DIR / "plan.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Required dataset file is missing: {path}")
    with path.open(encoding="utf-8-sig", newline="") as source:
        return {
            int(row["plan_id"]): {"plan_name": row["plan_name"], "price": row["price"]}
            for row in csv.DictReader(source)
        }


def import_table(connection: pymysql.Connection, table: str) -> int:
    path = CSV_DIR / f"{table}.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Required dataset file is missing: {path}")

    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        columns = reader.fieldnames
        if not columns:
            raise ValueError(f"Dataset file has no header: {path}")
        source_rows = list(reader)
        if table == "subscription":
            columns = [
                "subscription_id",
                "plan_name",
                "price",
                "start_date",
                "end_date",
                "status",
                "user_id",
            ]
            plan_catalog = read_plan_catalog()
            source_rows = [
                subscription_snapshot(row, plan_catalog) for row in source_rows
            ]

        names = ", ".join(f"`{column}`" for column in columns)
        placeholders = ", ".join(["%s"] * len(columns))
        primary_key = PRIMARY_KEYS[table]
        statement = (
            f"INSERT INTO `{table}` ({names}) VALUES ({placeholders}) "
            f"ON DUPLICATE KEY UPDATE `{primary_key}` = `{primary_key}`"
        )
        rows = [
            tuple(normalize_value(column, row[column]) for column in columns)
            for row in source_rows
        ]
        if rows:
            with connection.cursor() as cursor:
                cursor.executemany(statement, rows)
        return len(rows)


def main() -> None:
    required = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER")
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise SystemExit(
            f"Set {', '.join(missing)} in backend/.env before importing the dataset."
        )

    connection = pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.getenv("DB_PASSWORD", ""),
        database=os.environ["DB_NAME"],
        charset="utf8mb4",
        autocommit=False,
    )
    try:
        imported = {
            table: import_table(connection, table) for table in IMPORT_ORDER
        }
        connection.commit()
        with connection.cursor() as cursor:
            counts = {}
            for table in IMPORT_ORDER:
                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                counts[table] = cursor.fetchone()[0]
        print(f"CSV rows processed: {imported}")
        print(f"Rows currently in database: {counts}")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()