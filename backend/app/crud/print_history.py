from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from app.models.print_history import PrintHistory
from app.schemas.print_history import PrintHistoryCreate


def get_print_history(db: Session, history_id: str) -> Optional[PrintHistory]:
    """Retrieve a print history entry by ID"""
    return db.query(PrintHistory).filter(PrintHistory.id == history_id).first()


def get_print_history_by_asset(
    db: Session, asset_id: UUID, skip: int = 0, limit: int = 50
) -> List[PrintHistory]:
    """Retrieve the print history for a specific asset"""
    return (
        db.query(PrintHistory)
        .filter(PrintHistory.asset_id == asset_id)
        .order_by(desc(PrintHistory.generated_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_print_history_list(
    db: Session,
    asset_id: Optional[UUID] = None,
    template_id: Optional[int] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[PrintHistory]:
    """Retrieve the print history with filters"""
    query = db.query(PrintHistory)

    if asset_id:
        query = query.filter(PrintHistory.asset_id == asset_id)

    if template_id:
        query = query.filter(PrintHistory.template_id == template_id)

    if from_date:
        query = query.filter(PrintHistory.generated_at >= from_date)

    if to_date:
        query = query.filter(PrintHistory.generated_at <= to_date)

    return (
        query.order_by(desc(PrintHistory.generated_at)).offset(skip).limit(limit).all()
    )


def create_print_history(db: Session, history: PrintHistoryCreate) -> PrintHistory:
    """Create a new print history entry"""
    db_history = PrintHistory(**history.model_dump())
    db.add(db_history)
    db.commit()
    db.refresh(db_history)
    return db_history


def update_print_history_status(
    db: Session,
    history_id: str,
    status: str,
    file_path: Optional[str] = None,
    file_size: Optional[int] = None,
) -> Optional[PrintHistory]:
    """Update the status of a print"""
    db_history = get_print_history(db, history_id)
    if not db_history:
        return None

    db_history.status = status
    if file_path:
        db_history.file_path = file_path
    if file_size:
        db_history.file_size = file_size

    db.commit()
    db.refresh(db_history)
    return db_history


def delete_print_history(db: Session, history_id: str) -> bool:
    """Delete a print history entry"""
    db_history = get_print_history(db, history_id)
    if not db_history:
        return False

    db.delete(db_history)
    db.commit()
    return True
