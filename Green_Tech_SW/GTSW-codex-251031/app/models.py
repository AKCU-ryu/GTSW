"""Database models for the group expense tracker."""
from __future__ import annotations

from datetime import datetime, date

from sqlalchemy import CheckConstraint, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import db


class Member(db.Model):
    """Represents a participant of the shared ledger."""

    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    nickname: Mapped[str | None]
    email: Mapped[str | None]
    is_admin: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationship to ledger entries created for this member. ``lazy='dynamic'`` is not
    # required here because the dataset is expected to be reasonably small.
    ledger_entries: Mapped[list["LedgerEntry"]] = relationship(back_populates="member")

    def display_name(self) -> str:
        """Return nickname if available, otherwise the real name."""
        return self.nickname or self.name


class LedgerEntry(db.Model):
    """Income or expense entry recorded in the ledger."""

    __tablename__ = "ledger_entries"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="amount_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int | None] = mapped_column(db.ForeignKey("members.id"))
    created_by_id: Mapped[int | None] = mapped_column(db.ForeignKey("members.id"))
    entry_type: Mapped[str] = mapped_column(Enum("income", "expense", name="entry_type"))
    category: Mapped[str] = mapped_column(default="기타")
    description: Mapped[str | None]
    amount: Mapped[float] = mapped_column(nullable=False)
    occurred_on: Mapped[date] = mapped_column(default=date.today)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    split_evenly: Mapped[bool] = mapped_column(default=False)

    member: Mapped[Member | None] = relationship(
        "Member", back_populates="ledger_entries", foreign_keys=[member_id]
    )
    created_by: Mapped[Member | None] = relationship("Member", foreign_keys=[created_by_id])
    shares: Mapped[list["EntryShare"]] = relationship(back_populates="entry", cascade="all, delete-orphan")


class EntryShare(db.Model):
    """Stores the 1/n split information for each ledger entry."""

    __tablename__ = "entry_shares"

    id: Mapped[int] = mapped_column(primary_key=True)
    entry_id: Mapped[int] = mapped_column(db.ForeignKey("ledger_entries.id"))
    member_id: Mapped[int] = mapped_column(db.ForeignKey("members.id"))
    amount: Mapped[float] = mapped_column(nullable=False)

    entry: Mapped[LedgerEntry] = relationship("LedgerEntry", back_populates="shares")
    member: Mapped[Member] = relationship("Member")


class Holiday(db.Model):
    """Represents a holiday displayed on the calendar."""

    __tablename__ = "holidays"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    observed_on: Mapped[date] = mapped_column(unique=True)
    source: Mapped[str | None] = mapped_column(default="manual")


class ReceiptExtractionLog(db.Model):
    """Stores logs for machine learning based receipt extraction attempts."""

    __tablename__ = "receipt_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    uploaded_filename: Mapped[str | None]
    detected_total: Mapped[float | None]
    detected_store: Mapped[str | None]
    detected_card: Mapped[str | None]
    processed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    raw_payload: Mapped[str | None]
    status: Mapped[str] = mapped_column(default="pending")