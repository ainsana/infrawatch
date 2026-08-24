from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class NetworkCheck(Base):
    __tablename__ = "network_checks"

    __table_args__ = (
        CheckConstraint(
            "port BETWEEN 1 AND 65535",
            name="ck_network_checks_port_range",
        ),
        Index(
            "ix_network_checks_host_checked_at",
            "host_id",
            "checked_at",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    host_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("hosts.id", ondelete="CASCADE"),
        nullable=False,
    )
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    is_open: Mapped[bool] = mapped_column(Boolean, nullable=False)
    duration_ms: Mapped[float] = mapped_column(Float, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
