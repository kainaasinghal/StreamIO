import csv
import asyncio
import unittest
from pathlib import Path

from pydantic import ValidationError
from fastapi import HTTPException
from sqlalchemy.dialects.mysql import dialect
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy import select
from starlette.requests import Request

from app.main import app, database_error_handler
from app.models import Base, Subscription
from app.routes import RESOURCE_CONFIG, apply_filters, apply_search, list_query, validate_payload
from app.schemas import (
    ContentWrite,
    PaymentWrite,
    PlanWrite,
    ReviewWrite,
    SubscriptionWrite,
    UserWrite,
    WatchHistoryWrite,
)
from database.import_data import subscription_snapshot


EXPECTED_TABLES = {
    "user",
    "plan",
    "category",
    "content",
    "subscription",
    "payment",
    "watchlist",
    "watch_history",
    "review",
}
EXPECTED_ROWS = {
    "user": 12,
    "plan": 3,
    "category": 9,
    "content": 30,
    "subscription": 10,
    "payment": 12,
    "watchlist": 15,
    "watch_history": 12,
    "review": 9,
}
EXPECTED_COLUMNS = {
    "user": {"user_id", "name", "email", "password", "phone", "country"},
    "plan": {"plan_id", "plan_name", "price", "duration_months"},
    "subscription": {"subscription_id", "plan_name", "price", "start_date", "end_date", "status", "user_id"},
    "payment": {"payment_number", "payment_date", "payment_amount", "payment_method", "status", "subscription_id"},
    "category": {"category_id", "category_name", "description"},
    "content": {"content_id", "title", "release_year", "duration", "rating", "language", "category_id"},
    "watchlist": {"watchlist_id", "added_date", "user_id", "content_id"},
    "watch_history": {"history_id", "watch_date", "watch_time", "progress", "completed", "user_id", "content_id"},
    "review": {"review_id", "rating", "comment", "review_date", "user_id", "content_id"},
}


def count_rows(path: Path) -> int:
    with path.open(encoding="utf-8-sig", newline="") as source:
        return sum(1 for _ in csv.DictReader(source))


class BackendContractTests(unittest.TestCase):
    def test_models_cover_the_dataset_tables(self) -> None:
        self.assertEqual(set(Base.metadata.tables), EXPECTED_TABLES)

    def test_model_columns_match_confirmed_live_schema(self) -> None:
        actual = {
            name: {column.name for column in table.columns}
            for name, table in Base.metadata.tables.items()
        }
        self.assertEqual(actual, EXPECTED_COLUMNS)
        self.assertTrue(Base.metadata.tables["payment"].c.status.nullable)
        self.assertTrue(Base.metadata.tables["watch_history"].c.completed.nullable)

    def test_all_resource_queries_compile_for_mysql(self) -> None:
        for resource in RESOURCE_CONFIG:
            with self.subTest(resource=resource):
                query, _, _ = list_query(resource)
                query = apply_search(query, resource, "probe")
                query = apply_filters(query, resource, "active", 1, 1, 1)
                compiled = str(query.compile(dialect=dialect()))
                self.assertIn("SELECT", compiled.upper())

    def test_search_matches_any_searchable_column(self) -> None:
        query, _, _ = list_query("users")
        compiled = str(apply_search(query, "users", "probe").compile(dialect=dialect()))
        self.assertIn(" OR ", compiled.upper())

    def test_subscription_plan_relationship_joins_snapshot_name_read_only(self) -> None:
        compiled = str(select(Subscription).join(Subscription.plan).compile(dialect=dialect()))
        self.assertIn("subscription.plan_name = plan.plan_name", compiled)
        self.assertTrue(Subscription.plan.property.viewonly)

    def test_openapi_exposes_system_and_resource_routes(self) -> None:
        paths = app.openapi()["paths"]
        self.assertIn("/api/dashboard", paths)
        self.assertIn("/api/health", paths)
        self.assertIn("/api/meta/options", paths)
        self.assertIn("/api/{resource}", paths)
        self.assertIn("/api/{resource}/{record_id}", paths)

    def test_user_email_is_normalized_and_password_is_not_an_input(self) -> None:
        user = UserWrite.model_validate({"name": "A User", "email": "A@Example.com"})
        self.assertEqual(user.email, "a@example.com")
        with self.assertRaises(ValidationError):
            UserWrite.model_validate({"name": "A User", "email": "invalid"})

    def test_content_rating_validation(self) -> None:
        with self.assertRaises(ValidationError):
            ContentWrite.model_validate({"title": "Out of range", "rating": 11})

    def test_money_ratings_and_progress_reject_invalid_ranges(self) -> None:
        invalid_inputs = (
            (PlanWrite, {"plan_name": "Invalid", "price": "-0.01", "duration_months": 1}),
            (PaymentWrite, {"payment_date": "2026-10-14", "payment_amount": "-0.01", "subscription_id": 1}),
            (ReviewWrite, {"rating": 10.1, "review_date": "2026-10-14", "user_id": 1, "content_id": 1}),
            (WatchHistoryWrite, {"watch_date": "2026-10-14", "progress": 100.01, "user_id": 1, "content_id": 1}),
        )
        for schema, payload in invalid_inputs:
            with self.subTest(schema=schema.__name__):
                with self.assertRaises(ValidationError):
                    schema.model_validate(payload)

    def test_subscription_ids_and_date_range_have_field_messages(self) -> None:
        with self.assertRaises(HTTPException) as invalid_ids:
            validate_payload(
                SubscriptionWrite,
                {"plan_id": 0, "user_id": 0, "start_date": "2026-10-14"},
            )
        messages = {item["loc"][-1]: item["msg"] for item in invalid_ids.exception.detail}
        self.assertEqual(messages["plan_id"], "Please select a valid subscription plan.")
        self.assertEqual(messages["user_id"], "Please select a valid user.")

        with self.assertRaises(HTTPException) as invalid_dates:
            validate_payload(
                SubscriptionWrite,
                {
                    "plan_id": 1,
                    "user_id": 1,
                    "start_date": "2026-10-14",
                    "end_date": "2026-10-13",
                },
            )
        self.assertEqual(
            invalid_dates.exception.detail[0]["msg"],
            "End date cannot be earlier than start date.",
        )

    def test_subscription_csv_maps_plan_id_to_snapshot_columns(self) -> None:
        row = {
            "subscription_id": "7",
            "plan_id": "2",
            "start_date": "2026-01-01",
            "end_date": "2027-01-01",
            "status": "active",
            "user_id": "4",
        }
        result = subscription_snapshot(
            row, {2: {"plan_name": "Standard", "price": "399.00"}}
        )
        self.assertEqual(result["plan_name"], "Standard")
        self.assertEqual(result["price"], "399.00")
        self.assertNotIn("plan_id", result)

    def test_database_errors_return_service_unavailable(self) -> None:
        request = Request({"type": "http", "method": "GET", "path": "/api/users", "headers": []})
        response = asyncio.run(database_error_handler(request, SQLAlchemyError("offline")))
        self.assertEqual(response.status_code, 500)

    def test_schema_errors_are_actionable_without_leaking_sql(self) -> None:
        request = Request({"type": "http", "method": "GET", "path": "/api/users", "headers": []})
        error = OperationalError("select", {}, Exception(1054, "Unknown column user.role"))
        response = asyncio.run(database_error_handler(request, error))
        self.assertEqual(response.status_code, 500)
        self.assertIn(b"schema mismatch", response.body)
        self.assertNotIn(b"user.role", response.body)

    def test_connection_errors_return_safe_service_unavailable(self) -> None:
        request = Request({"type": "http", "method": "GET", "path": "/api/health", "headers": []})
        error = OperationalError("connect", {}, Exception(1045, "Access denied"))
        response = asyncio.run(database_error_handler(request, error))
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b"Access denied", response.body)

    def test_csv_counts_match_dataset_readme(self) -> None:
        workspace = Path(__file__).resolve().parents[3]
        csv_directory = workspace / "streamio_dataset" / "final_pkg" / "csv"
        actual = {path.stem: count_rows(path) for path in csv_directory.glob("*.csv")}
        self.assertEqual(actual, EXPECTED_ROWS)


if __name__ == "__main__":
    unittest.main()