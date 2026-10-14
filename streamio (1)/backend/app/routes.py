from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError
from sqlalchemy import Select, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Category,
    Content,
    Payment,
    Plan,
    Review,
    Subscription,
    User,
    WatchHistory,
    Watchlist,
)
from app.schemas import (
    CategoryWrite,
    ContentWrite,
    Page,
    PaymentWrite,
    PlanWrite,
    ReviewWrite,
    SubscriptionWrite,
    UserWrite,
    WatchHistoryWrite,
    WatchlistWrite,
)
from app.services import commit_or_conflict, flush_or_conflict, require_record


router = APIRouter(prefix="/api")
RESOURCE_CONFIG: dict[str, tuple[type, type, str]] = {
    "users": (User, UserWrite, "user_id"),
    "plans": (Plan, PlanWrite, "plan_id"),
    "categories": (Category, CategoryWrite, "category_id"),
    "content": (Content, ContentWrite, "content_id"),
    "subscriptions": (Subscription, SubscriptionWrite, "subscription_id"),
    "payments": (Payment, PaymentWrite, "payment_number"),
    "watchlist": (Watchlist, WatchlistWrite, "watchlist_id"),
    "watch-history": (WatchHistory, WatchHistoryWrite, "history_id"),
    "reviews": (Review, ReviewWrite, "review_id"),
}


def entity_values(entity: object, **extra: Any) -> dict[str, Any]:
    values = {
        column.key: getattr(entity, column.key)
        for column in entity.__mapper__.column_attrs
        if column.key != "password"
    }
    values.update(extra)
    return values


VALIDATION_MESSAGES = {
    "name": "Please enter a name.",
    "email": "Please enter a valid email address.",
    "user_id": "Please select a valid user.",
    "plan_id": "Please select a valid subscription plan.",
    "subscription_id": "Please select a valid subscription.",
    "content_id": "Please select valid content.",
    "category_id": "Please select a valid category.",
    "payment_amount": "Payment amount must be greater than or equal to zero.",
    "price": "Price must be greater than or equal to zero.",
    "rating": "Rating must be between zero and ten.",
    "start_date": "Please enter a valid start date.",
    "end_date": "End date cannot be earlier than start date.",
    "payment_date": "Please enter a valid payment date.",
    "watch_date": "Please enter a valid watch date.",
    "review_date": "Please enter a valid review date.",
}


def validate_payload(schema: type, payload: dict[str, Any]) -> Any:
    try:
        return schema.model_validate(payload)
    except ValidationError as error:
        details = []
        for issue in error.errors():
            field = str(issue["loc"][-1]) if issue["loc"] else "body"
            message = VALIDATION_MESSAGES.get(
                field,
                f"Please check the {field.replace('_', ' ')} value.",
            )
            details.append({"loc": ["body", field], "msg": message, "type": "value_error"})
        raise HTTPException(status_code=422, detail=details) from error


def require_related_record(record: object | None, message: str) -> object:
    if record is None:
        raise HTTPException(status_code=404, detail=message)
    return record


def validate_related_records(resource: str, payload: Any, db: Session) -> Plan | None:
    if resource == "users" and payload.plan_id is not None:
        return require_related_record(db.get(Plan, payload.plan_id), "Please select a valid subscription plan.")
    if resource == "subscriptions":
        require_related_record(db.get(User, payload.user_id), "Please select a valid user.")
        if payload.plan_id is None:
            return None
        return require_related_record(db.get(Plan, payload.plan_id), "Please select a valid subscription plan.")
    if resource == "payments":
        require_related_record(db.get(Subscription, payload.subscription_id), "Please select a valid subscription.")
    if resource in {"watchlist", "watch-history", "reviews"}:
        require_related_record(db.get(User, payload.user_id), "Please select a valid user.")
        require_related_record(db.get(Content, payload.content_id), "Please select valid content.")
    if resource == "content" and payload.category_id is not None:
        require_related_record(db.get(Category, payload.category_id), "Please select a valid category.")
    return None


def apply_search(query: Select, resource: str, term: str | None) -> Select:
    if not term:
        return query
    pattern = f"%{term.strip()}%"
    search_columns: dict[str, tuple] = {
        "users": (User.name, User.email, User.country),
        "plans": (Plan.plan_name,),
        "categories": (Category.category_name, Category.description),
        "content": (Content.title, Content.language, Category.category_name),
        "subscriptions": (User.name, User.email, Subscription.plan_name),
        "payments": (User.name, User.email, Subscription.plan_name, Payment.payment_method),
        "watchlist": (User.name, Content.title),
        "watch-history": (User.name, Content.title),
        "reviews": (User.name, Content.title, Review.comment),
    }
    return query.where(
        or_(*[column.ilike(pattern) for column in search_columns[resource]])
    )


def list_query(resource: str) -> tuple[Select, Any, dict[str, Any]]:
    if resource == "users":
        latest = (
            select(
                Subscription.user_id.label("user_id"),
                func.max(Subscription.subscription_id).label("subscription_id"),
            )
            .group_by(Subscription.user_id)
            .subquery()
        )
        query = (
            select(
                User,
                Subscription.plan_name.label("plan_name"),
                Subscription.status.label("subscription_status"),
                Plan.plan_id.label("plan_id"),
                Subscription.start_date.label("subscription_start_date"),
                Subscription.end_date.label("subscription_end_date"),
            )
            .outerjoin(latest, latest.c.user_id == User.user_id)
            .outerjoin(Subscription, Subscription.subscription_id == latest.c.subscription_id)
            .outerjoin(Plan, Plan.plan_name == Subscription.plan_name)
        )
        count_query = select(func.count()).select_from(query.subquery())
        sort_fields = {
            "user_id": User.user_id,
            "name": User.name,
            "email": User.email,
            "country": User.country,
        }
    elif resource == "content":
        review_count = (
            select(func.count(Review.review_id))
            .where(Review.content_id == Content.content_id)
            .correlate(Content)
            .scalar_subquery()
        )
        average_rating = (
            select(func.avg(Review.rating))
            .where(Review.content_id == Content.content_id)
            .correlate(Content)
            .scalar_subquery()
        )
        watch_count = (
            select(func.count(WatchHistory.history_id))
            .where(WatchHistory.content_id == Content.content_id)
            .correlate(Content)
            .scalar_subquery()
        )
        query = (
            select(
                Content,
                Category.category_name.label("category_name"),
                review_count.label("review_count"),
                average_rating.label("average_review_rating"),
                watch_count.label("watch_count"),
            )
            .outerjoin(Category, Category.category_id == Content.category_id)
        )
        count_query = select(func.count()).select_from(Content)
        sort_fields = {"content_id": Content.content_id, "title": Content.title, "release_year": Content.release_year, "rating": Content.rating}
    elif resource == "subscriptions":
        query = (
            select(
                Subscription,
                User.name.label("user_name"),
                User.email,
                Plan.plan_id.label("plan_id"),
            )
            .join(User, User.user_id == Subscription.user_id)
            .outerjoin(Plan, Plan.plan_name == Subscription.plan_name)
        )
        count_query = select(func.count()).select_from(Subscription)
        sort_fields = {"subscription_id": Subscription.subscription_id, "start_date": Subscription.start_date, "status": Subscription.status}
    elif resource == "payments":
        query = (
            select(
                Payment,
                User.name.label("user_name"),
                User.email,
                Subscription.plan_name.label("plan_name"),
                Subscription.price.label("plan_price"),
            )
            .join(Subscription, Subscription.subscription_id == Payment.subscription_id)
            .join(User, User.user_id == Subscription.user_id)
        )
        count_query = select(func.count()).select_from(Payment)
        sort_fields = {"payment_number": Payment.payment_number, "payment_date": Payment.payment_date, "payment_amount": Payment.payment_amount, "status": Payment.status}
    elif resource == "watchlist":
        query = (
            select(Watchlist, User.name.label("user_name"), Content.title.label("content_title"))
            .join(User, User.user_id == Watchlist.user_id)
            .join(Content, Content.content_id == Watchlist.content_id)
        )
        count_query = select(func.count()).select_from(Watchlist)
        sort_fields = {"watchlist_id": Watchlist.watchlist_id, "added_date": Watchlist.added_date}
    elif resource == "watch-history":
        query = (
            select(
                WatchHistory,
                User.name.label("user_name"),
                Content.title.label("content_title"),
                Content.duration.label("content_duration"),
                Category.category_name.label("category_name"),
                (Content.duration * WatchHistory.progress / 100).label("watched_minutes"),
            )
            .join(User, User.user_id == WatchHistory.user_id)
            .join(Content, Content.content_id == WatchHistory.content_id)
            .outerjoin(Category, Category.category_id == Content.category_id)
        )
        count_query = select(func.count()).select_from(WatchHistory)
        sort_fields = {"history_id": WatchHistory.history_id, "watch_date": WatchHistory.watch_date, "progress": WatchHistory.progress}
    elif resource == "reviews":
        query = (
            select(Review, User.name.label("user_name"), Content.title.label("content_title"))
            .join(User, User.user_id == Review.user_id)
            .join(Content, Content.content_id == Review.content_id)
        )
        count_query = select(func.count()).select_from(Review)
        sort_fields = {"review_id": Review.review_id, "review_date": Review.review_date, "rating": Review.rating}
    elif resource == "plans":
        query = select(Plan)
        count_query = select(func.count()).select_from(Plan)
        sort_fields = {"plan_id": Plan.plan_id, "plan_name": Plan.plan_name, "price": Plan.price}
    else:
        query = select(Category)
        count_query = select(func.count()).select_from(Category)
        sort_fields = {"category_id": Category.category_id, "category_name": Category.category_name}
    return query, count_query, sort_fields


def apply_filters(query: Select, resource: str, status: str | None, category_id: int | None, plan_id: int | None, user_id: int | None) -> Select:
    if status and resource == "users":
        if status == "unsubscribed":
            query = query.where(Subscription.subscription_id.is_(None))
        else:
            query = query.where(Subscription.status == status.lower())
    elif status and resource == "subscriptions":
        query = query.where(Subscription.status == status.lower())
    elif status and resource == "payments":
        query = query.where(Payment.status == status.lower())
    elif status and resource == "watch-history":
        if status == "completed":
            query = query.where(WatchHistory.completed.is_(True))
        elif status == "in-progress":
            query = query.where(WatchHistory.completed.is_(False))
    if category_id is not None and resource == "content":
        query = query.where(Content.category_id == category_id)
    if plan_id is not None:
        if resource == "subscriptions":
            query = query.where(Plan.plan_id == plan_id)
        elif resource == "users":
            query = query.where(Plan.plan_id == plan_id)
    if user_id is not None and resource in {"subscriptions", "watchlist", "watch-history", "reviews"}:
        model = {
            "subscriptions": Subscription,
            "watchlist": Watchlist,
            "watch-history": WatchHistory,
            "reviews": Review,
        }[resource]
        query = query.where(model.user_id == user_id)
    return query


def records_for(resource: str, rows: list[Any]) -> list[dict[str, Any]]:
    records = []
    for row in rows:
        if resource == "users":
            user, plan_name, subscription_status, plan_id, start_date, end_date = row
            record = entity_values(
                user,
                plan_name=plan_name,
                subscription_status=subscription_status,
                plan_id=plan_id,
                subscription_start_date=start_date,
                subscription_end_date=end_date,
            )
        elif resource == "content":
            content, category_name, review_count, average_rating, watch_count = row
            record = entity_values(content, category_name=category_name, review_count=review_count, average_review_rating=average_rating, watch_count=watch_count)
        elif resource in {"subscriptions", "payments", "watchlist", "watch-history", "reviews"}:
            entity = row[0]
            extras = dict(row._mapping)
            extras.pop(entity.__mapper__.class_.__name__.lower(), None)
            record = entity_values(entity)
            for key, value in extras.items():
                if not hasattr(value, "__mapper__"):
                    record[key] = value
        else:
            record = entity_values(row[0])
        records.append(record)
    return records


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)) -> dict[str, Any]:
    user_count = db.scalar(select(func.count()).select_from(User)) or 0
    content_count = db.scalar(select(func.count()).select_from(Content)) or 0
    active_subscriptions = db.scalar(
        select(func.count()).select_from(Subscription).where(Subscription.status == "active")
    ) or 0
    successful_revenue = db.scalar(
        select(func.coalesce(func.sum(Payment.payment_amount), 0)).where(Payment.status == "success")
    ) or 0
    payment_count = db.scalar(select(func.count()).select_from(Payment)) or 0
    watch_minutes = db.scalar(
        select(func.coalesce(func.sum(Content.duration * WatchHistory.progress / 100), 0))
        .join(WatchHistory, WatchHistory.content_id == Content.content_id)
    ) or 0
    review_average = db.scalar(select(func.avg(Review.rating))) or 0
    plan_rows = db.execute(
        select(Plan.plan_name, func.count(Subscription.subscription_id).label("members"))
        .outerjoin(
            Subscription,
            (Subscription.plan_name == Plan.plan_name) & (Subscription.status == "active"),
        )
        .group_by(Plan.plan_id, Plan.plan_name)
        .order_by(Plan.plan_id)
    ).all()
    category_rows = db.execute(
        select(Category.category_name, func.count(Content.content_id).label("titles"))
        .outerjoin(Content, Content.category_id == Category.category_id)
        .group_by(Category.category_id)
        .order_by(func.count(Content.content_id).desc(), Category.category_name)
    ).all()
    monthly_rows = db.execute(
        select(
            func.date_format(Payment.payment_date, "%Y-%m").label("month"),
            func.sum(Payment.payment_amount).label("revenue"),
            func.count(Payment.payment_number).label("payments"),
        )
        .where(Payment.status == "success")
        .group_by(func.date_format(Payment.payment_date, "%Y-%m"))
        .order_by(func.date_format(Payment.payment_date, "%Y-%m"))
    ).all()
    watch_count = (
        select(func.count(WatchHistory.history_id))
        .where(WatchHistory.content_id == Content.content_id)
        .correlate(Content)
        .scalar_subquery()
    )
    content_average = (
        select(func.avg(Review.rating))
        .where(Review.content_id == Content.content_id)
        .correlate(Content)
        .scalar_subquery()
    )
    top_content_rows = db.execute(
        select(Content, Category.category_name, watch_count, content_average)
        .outerjoin(Category, Category.category_id == Content.category_id)
        .order_by(watch_count.desc(), Content.title.asc())
        .limit(4)
    ).all()
    review_count = db.scalar(select(func.count()).select_from(Review)) or 0
    return {
        "members": user_count,
        "content": content_count,
        "active_subscriptions": active_subscriptions,
        "successful_revenue": successful_revenue,
        "payments": payment_count,
        "watch_minutes": round(float(watch_minutes), 1),
        "average_review_rating": round(float(review_average), 2),
        "review_count": review_count,
        "subscriptions_by_plan": [{"plan": row.plan_name, "members": row.members} for row in plan_rows],
        "titles_by_category": [{"category": row.category_name, "titles": row.titles} for row in category_rows],
        "monthly_revenue": [{"month": row.month, "revenue": row.revenue, "payments": row.payments} for row in monthly_rows],
        "top_content": [
            {
                "content_id": row[0].content_id,
                "title": row[0].title,
                "category_name": row[1],
                "watch_count": row[2],
                "average_rating": row[3],
            }
            for row in top_content_rows
        ],
    }


@router.get("/{resource}", response_model=Page)
def list_records(
    resource: str,
    q: str | None = Query(default=None, max_length=100),
    status: str | None = Query(default=None, max_length=20),
    category_id: int | None = Query(default=None, ge=1),
    plan_id: int | None = Query(default=None, ge=1),
    user_id: int | None = Query(default=None, ge=1),
    sort_by: str | None = None,
    descending: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> Page:
    if resource not in RESOURCE_CONFIG:
        raise HTTPException(status_code=404, detail="Resource not found")
    query, count_query, sort_fields = list_query(resource)
    query = apply_search(query, resource, q)
    query = apply_filters(query, resource, status, category_id, plan_id, user_id)
    count_query = select(func.count()).select_from(query.order_by(None).subquery())
    sort_column = sort_fields.get(sort_by or "")
    if sort_column is not None:
        query = query.order_by(sort_column.desc() if descending else sort_column.asc())
    else:
        model, _, key = RESOURCE_CONFIG[resource]
        query = query.order_by(getattr(model, key).asc())
    total = db.scalar(count_query) or 0
    rows = db.execute(query.offset((page - 1) * page_size).limit(page_size)).all()
    return Page(items=records_for(resource, rows), page=page, page_size=page_size, total=total)


@router.get("/{resource}/{record_id:int}")
def get_record(resource: str, record_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    if resource not in RESOURCE_CONFIG:
        raise HTTPException(status_code=404, detail="Resource not found")
    model, _, key = RESOURCE_CONFIG[resource]
    record = db.get(model, record_id)
    record = require_record(record, resource[:-1] if resource.endswith("s") else resource)
    return entity_values(record)


@router.post("/{resource}", status_code=201)
def create_record(resource: str, payload: dict[str, Any], db: Session = Depends(get_db)) -> dict[str, Any]:
    if resource not in RESOURCE_CONFIG:
        raise HTTPException(status_code=404, detail="Resource not found")
    model, schema, _ = RESOURCE_CONFIG[resource]
    validated = validate_payload(schema, payload)
    selected_plan = validate_related_records(resource, validated, db)
    if resource == "subscriptions" and selected_plan is None:
        raise HTTPException(
            status_code=422,
            detail=[{"loc": ["body", "plan_id"], "msg": "Please select a valid subscription plan.", "type": "value_error"}],
        )
    values = validated.model_dump(
        exclude={"plan_id"} if resource in {"users", "subscriptions"} else set()
    )
    if resource == "subscriptions" and selected_plan is not None:
        values.update(plan_name=selected_plan.plan_name, price=selected_plan.price)
    plan_id = getattr(validated, "plan_id", None)
    record = model(**values)
    db.add(record)
    if resource == "users" and plan_id is not None:
        flush_or_conflict(db)
        db.add(
            Subscription(
                start_date=date.today(),
                status="active",
                user_id=record.user_id,
                plan_name=selected_plan.plan_name,
                price=selected_plan.price,
            )
        )
    commit_or_conflict(db)
    db.refresh(record)
    return entity_values(record)


@router.put("/{resource}/{record_id:int}")
def update_record(resource: str, record_id: int, payload: dict[str, Any], db: Session = Depends(get_db)) -> dict[str, Any]:
    if resource not in RESOURCE_CONFIG:
        raise HTTPException(status_code=404, detail="Resource not found")
    model, schema, _ = RESOURCE_CONFIG[resource]
    record = require_record(db.get(model, record_id), resource[:-1] if resource.endswith("s") else resource)
    validated = validate_payload(schema, payload)
    selected_plan = validate_related_records(resource, validated, db)
    values = validated.model_dump(
        exclude={"plan_id"} if resource in {"users", "subscriptions"} else set()
    )
    if resource == "subscriptions" and selected_plan is not None:
        values.update(plan_name=selected_plan.plan_name, price=selected_plan.price)
    plan_id = getattr(validated, "plan_id", None)
    for key, value in values.items():
        setattr(record, key, value)
    if resource == "users" and plan_id is not None:
        current_plan_id = db.scalar(
            select(Plan.plan_id)
            .join(Subscription, Subscription.plan_name == Plan.plan_name)
            .where(Subscription.user_id == record.user_id)
            .order_by(Subscription.subscription_id.desc())
            .limit(1)
        )
        if plan_id != current_plan_id:
            db.add(
                Subscription(
                    start_date=date.today(),
                    status="active",
                    user_id=record.user_id,
                    plan_name=selected_plan.plan_name,
                    price=selected_plan.price,
                )
            )
    commit_or_conflict(db)
    db.refresh(record)
    return entity_values(record)


@router.delete("/{resource}/{record_id}", status_code=204)
def delete_record(resource: str, record_id: int, db: Session = Depends(get_db)) -> None:
    if resource not in RESOURCE_CONFIG:
        raise HTTPException(status_code=404, detail="Resource not found")
    model, _, key = RESOURCE_CONFIG[resource]
    record = require_record(db.get(model, record_id), resource[:-1] if resource.endswith("s") else resource)
    db.delete(record)
    commit_or_conflict(db)


@router.get("/meta/options")
def options(db: Session = Depends(get_db)) -> dict[str, list[dict[str, Any]]]:
    plans = db.scalars(select(Plan).order_by(Plan.plan_id)).all()
    categories = db.scalars(select(Category).order_by(Category.category_name)).all()
    users = db.scalars(select(User).order_by(User.name)).all()
    content = db.execute(select(Content.content_id, Content.title).order_by(Content.title)).all()
    subscriptions = db.execute(
        select(Subscription.subscription_id, User.name, Subscription.plan_name, Subscription.status)
        .join(User, User.user_id == Subscription.user_id)
        .order_by(Subscription.subscription_id)
    ).all()
    return {
        "plans": [entity_values(plan) for plan in plans],
        "categories": [entity_values(category) for category in categories],
        "users": [entity_values(user) for user in users],
        "content": [{"content_id": item.content_id, "title": item.title} for item in content],
        "subscriptions": [
            {
                "subscription_id": item.subscription_id,
                "label": f"#{item.subscription_id} · {item.name} · {item.plan_name} ({item.status})",
            }
            for item in subscriptions
        ],
    }