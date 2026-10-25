from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    String,
    UniqueConstraint,
    Float,
)
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)


class Edge(Base):
    __tablename__ = "edges"
    __table_args__ = (
        UniqueConstraint(
            "source_id", "destination_id", name="uq_edge_source_destination"
        ),
        CheckConstraint("latency > 0", name="ck_edge_positive_latency"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("nodes.id"))
    destination_id: Mapped[int] = mapped_column(ForeignKey("nodes.id"))
    latency: Mapped[float] = mapped_column(Float)


from datetime import datetime
from sqlalchemy import DateTime, JSON, func


class RouteHistory(Base):
    __tablename__ = "route_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("nodes.id"))
    destination_id: Mapped[int] = mapped_column(ForeignKey("nodes.id"))
    total_latency: Mapped[float] = mapped_column(Float)
    path: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
