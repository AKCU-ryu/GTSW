# app/models.py
# -*- coding: utf-8 -*-
"""Database models for the group expense tracker."""
from __future__ import annotations

from datetime import datetime, date
from sqlalchemy import CheckConstraint, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import db

# 금액은 부동소수점 오차 방지를 위해 Numeric 사용
Money = db.Numeric(12, 2)

class Member(db.Model):
    """Represents a participant of the shared ledger."""
    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    nickname: Mapped[str | None]
    email: Mapped[str | None] = mapped_column(unique=True)
    is_admin: Mapped[bool] = mapped_column(server_default=db.text("0"))
    is_active: Mapped[bool] = mapped_column(server_default=db.text("1"))
    created_at: Mapped[datetime] = mapped_column(server_default=db.func.now())

    ledger_entries: Mapped[list["LedgerEntry"]] = relationship(back_populates="member")

    def display_name(self) -> str:
        return self.nickname or self.name


class LedgerEntry(db.Model):
    """Income or expense entry recorded in the ledger."""
    __tablename__ = "ledger_entries"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="amount_positive"),
        Index("ix_ledger_entries_date_type", "occurred_on", "entry_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    member_id: Mapped[int | None] = mapped_column(db.ForeignKey("members.id"))
    created_by_id: Mapped[int | None] = mapped_column(db.ForeignKey("members.id"))

    entry_type: Mapped[str] = mapped_column(
        Enum("income", "expense", name="entry_type"),
        nullable=False,
        server_default="expense",
    )

    category: Mapped[str] = mapped_column(server_default="기타")
    description: Mapped[str | None]
    amount: Mapped[float] = mapped_column(Money, nullable=False)

    occurred_on: Mapped[date] = mapped_column(server_default=db.text("(CURRENT_DATE)"))
    created_at: Mapped[datetime] = mapped_column(server_default=db.func.now())
    split_evenly: Mapped[bool] = mapped_column(server_default=db.text("0"))

    member: Mapped["Member | None"] = relationship(
        "Member", back_populates="ledger_entries", foreign_keys=[member_id]
    )
    created_by: Mapped["Member | None"] = relationship("Member", foreign_keys=[created_by_id])

    shares: Mapped[list["EntryShare"]] = relationship(
        back_populates="entry",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class EntryShare(db.Model):
    """Stores the 1/n split information for each ledger entry."""
    __tablename__ = "entry_shares"
    __table_args__ = (
        Index("ix_entry_shares_entry_member", "entry_id", "member_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    entry_id: Mapped[int] = mapped_column(
        db.ForeignKey("ledger_entries.id", ondelete="CASCADE"), index=True
    )
    member_id: Mapped[int] = mapped_column(
        db.ForeignKey("members.id"), index=True
    )
    amount: Mapped[float] = mapped_column(Money, nullable=False)

    entry: Mapped["LedgerEntry"] = relationship("LedgerEntry", back_populates="shares")
    member: Mapped["Member"] = relationship("Member")


class Holiday(db.Model):
    """Represents a holiday displayed on the calendar."""
    __tablename__ = "holidays"
    __table_args__ = (
        Index("ix_holidays_observed_on", "observed_on", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    observed_on: Mapped[date]
    source: Mapped[str | None] = mapped_column(server_default="manual")


class ReceiptExtractionLog(db.Model):
    """Stores logs for machine learning based receipt extraction attempts."""
    __tablename__ = "receipt_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    uploaded_filename: Mapped[str | None]
    detected_total: Mapped[float | None] = mapped_column(Money)
    detected_store: Mapped[str | None]
    detected_card: Mapped[str | None]
    processed_at: Mapped[datetime] = mapped_column(server_default=db.func.now())
    raw_payload: Mapped[str | None]
    status: Mapped[str] = mapped_column(server_default="pending")
