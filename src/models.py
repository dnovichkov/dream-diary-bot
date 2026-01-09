from datetime import date, datetime
from html import escape

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class User(Base):
    """Telegram user model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    dreams: Mapped[list["Dream"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, telegram_id={self.telegram_id})"


class Dream(Base):
    """Dream record model."""

    __tablename__ = "dreams"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[str] = mapped_column(String(500), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    dream_date: Mapped[date] = mapped_column(Date, default=date.today)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user: Mapped["User"] = relationship(back_populates="dreams")

    def __repr__(self) -> str:
        return f"Dream(id={self.id}, title={self.title!r})"

    def format_short(self) -> str:
        """Format dream for list view (HTML-escaped)."""
        title = escape(self.title)
        tags_str = f" [{escape(self.tags)}]" if self.tags else ""
        return f"{self.dream_date} | {title}{tags_str}"

    def format_full(self) -> str:
        """Format dream for detailed view (HTML-escaped)."""
        lines = [
            f"ID: {self.id}",
            f"Date: {self.dream_date}",
            f"Title: {escape(self.title)}",
            "",
            "Description:",
            escape(self.description) if self.description else "(empty)",
            "",
            f"Tags: {escape(self.tags) if self.tags else '(none)'}",
            "",
            "Notes:",
            escape(self.notes) if self.notes else "(empty)",
        ]
        return "\n".join(lines)
