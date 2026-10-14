from datetime import date, time
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class InputModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)


class UserWrite(InputModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=100)
    phone: str | None = Field(default=None, max_length=15)
    country: str | None = Field(default=None, max_length=50)
    plan_id: int | None = Field(default=None, ge=1)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("Enter a valid email address")
        return value.lower()


class CategoryWrite(InputModel):
    category_name: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=255)


class ContentWrite(InputModel):
    title: str = Field(min_length=1, max_length=150)
    release_year: int | None = Field(default=None, ge=1901, le=2155)
    duration: int | None = Field(default=None, ge=1)
    rating: Decimal | None = Field(default=None, ge=0, le=10)
    language: str | None = Field(default=None, max_length=30)
    category_id: int | None = Field(default=None, ge=1)


class PlanWrite(InputModel):
    plan_name: str = Field(min_length=1, max_length=50)
    price: Decimal = Field(ge=0, max_digits=8, decimal_places=2)
    duration_months: int = Field(ge=1)


class SubscriptionWrite(InputModel):
    plan_id: int | None = Field(default=None, ge=1)
    start_date: date
    end_date: date | None = None
    status: Literal["active", "expired", "cancelled"] = "active"
    user_id: int = Field(ge=1)

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, value: date | None, info: ValidationInfo) -> date | None:
        start_date = info.data.get("start_date")
        if value is not None and start_date is not None and value < start_date:
            raise ValueError("End date cannot be earlier than start date.")
        return value


class PaymentWrite(InputModel):
    payment_date: date
    payment_amount: Decimal = Field(ge=0, max_digits=8, decimal_places=2)
    payment_method: str | None = Field(default=None, max_length=30)
    status: Literal["success", "failed", "refunded"] | None = "success"
    subscription_id: int = Field(ge=1)


class WatchlistWrite(InputModel):
    added_date: date
    user_id: int = Field(ge=1)
    content_id: int = Field(ge=1)


class WatchHistoryWrite(InputModel):
    watch_date: date
    watch_time: time | None = None
    progress: Decimal | None = Field(default=None, ge=0, le=100, max_digits=5, decimal_places=2)
    completed: bool | None = False
    user_id: int = Field(ge=1)
    content_id: int = Field(ge=1)


class ReviewWrite(InputModel):
    rating: Decimal = Field(ge=0, le=10, max_digits=3, decimal_places=1)
    comment: str | None = Field(default=None, max_length=500)
    review_date: date
    user_id: int = Field(ge=1)
    content_id: int = Field(ge=1)


class Page(BaseModel):
    items: list[dict]
    page: int
    page_size: int
    total: int