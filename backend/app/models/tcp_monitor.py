from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class TcpMonitor(Base):
    __tablename__ = "tcp_monitors"

    __table_args__ = (
        CheckConstraint(
            "port BETWEEN 1 AND 65535",
            name="ck_tcp_monitors_port_range",
        ),
        CheckConstraint(
            "timeout_seconds > 0",
            name="ck_tcp_monitors_timeout_positive",
        ),
        UniqueConstraint(
            "host_id",
            "port",
            name="uq_tcp_monitors_host_port",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    host_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("hosts.id", ondelete="CASCADE"),
        nullable=False,
    )
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    timeout_seconds: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
