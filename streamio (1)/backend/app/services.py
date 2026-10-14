from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def commit_or_conflict(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="This record conflicts with existing data. Check unique fields and related records.",
        ) from error


def flush_or_conflict(session: Session) -> None:
    try:
        session.flush()
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="This record conflicts with existing data. Check unique fields and related records.",
        ) from error


def require_record(record: object | None, label: str) -> object:
    if record is None:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    return record