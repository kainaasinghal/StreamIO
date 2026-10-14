from datetime import date, time
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Time, text
from sqlalchemy.dialects.mysql import YEAR
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "user"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(15))
    country: Mapped[str | None] = mapped_column(String(50))
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="user", passive_deletes=True
    )


class Plan(Base):
    __tablename__ = "plan"

    plan_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    duration_months: Mapped[int] = mapped_column(Integer, nullable=False)
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="plan",
        primaryjoin=lambda: Plan.plan_name == foreign(Subscription.plan_name),
        viewonly=True,
    )


class Category(Base):
    __tablename__ = "category"

    category_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    contents: Mapped[list["Content"]] = relationship(back_populates="category")


class Content(Base):
    __tablename__ = "content"

    content_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    release_year: Mapped[int | None] = mapped_column(YEAR)
    duration: Mapped[int | None] = mapped_column(Integer)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    language: Mapped[str | None] = mapped_column(String(30))
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("category.category_id", ondelete="SET NULL")
    )
    category: Mapped[Category | None] = relationship(back_populates="contents")
    watchlist_entries: Mapped[list["Watchlist"]] = relationship(
        back_populates="content", passive_deletes=True
    )
    watch_history: Mapped[list["WatchHistory"]] = relationship(
        back_populates="content", passive_deletes=True
    )
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="content", passive_deletes=True
    )



class Subscription(Base):
    __tablename__ = "subscription"

    subscription_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    plan_name: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str | None] = mapped_column(
        String(20), nullable=True, server_default=text("'active'")
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False
    )
    user: Mapped[User] = relationship(back_populates="subscriptions")
    plan: Mapped[Plan | None] = relationship(
        back_populates="subscriptions",
        primaryjoin=lambda: foreign(Subscription.plan_name) == Plan.plan_name,
        viewonly=True,
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="subscription", passive_deletes=True
    )



class Payment(Base):
    __tablename__ = "payment"

    payment_number: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_amount: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    payment_method: Mapped[str | None] = mapped_column(String(30))
    status: Mapped[str | None] = mapped_column(String(20), nullable=True, server_default=text("'success'"))
    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("subscription.subscription_id", ondelete="CASCADE")
    )
    subscription: Mapped[Subscription] = relationship(back_populates="payments")


class Watchlist(Base):
    __tablename__ = "watchlist"

    watchlist_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    added_date: Mapped[date] = mapped_column(Date, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"))
    content_id: Mapped[int] = mapped_column(ForeignKey("content.content_id", ondelete="CASCADE"))
    user: Mapped[User] = relationship()
    content: Mapped[Content] = relationship(back_populates="watchlist_entries")


class WatchHistory(Base):
    __tablename__ = "watch_history"

    history_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    watch_date: Mapped[date] = mapped_column(Date, nullable=False)
    watch_time: Mapped[time | None] = mapped_column(Time)
    progress: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    completed: Mapped[bool | None] = mapped_column(Boolean, nullable=True, server_default=text("0"))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"))
    content_id: Mapped[int] = mapped_column(ForeignKey("content.content_id", ondelete="CASCADE"))
    user: Mapped[User] = relationship()
    content: Mapped[Content] = relationship(back_populates="watch_history")


class Review(Base):
    __tablename__ = "review"

    review_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rating: Mapped[Decimal] = mapped_column(Numeric(3, 1), nullable=False)
    comment: Mapped[str | None] = mapped_column(String(500))
    review_date: Mapped[date] = mapped_column(Date, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"))
    content_id: Mapped[int] = mapped_column(ForeignKey("content.content_id", ondelete="CASCADE"))
    user: Mapped[User] = relationship()
    content: Mapped[Content] = relationship(back_populates="reviews")