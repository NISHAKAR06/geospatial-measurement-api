import uuid
from typing import TYPE_CHECKING, Any, Dict
from sqlalchemy import Float, ForeignKey, Index, Integer, LargeBinary, String, UniqueConstraint, Uuid, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.file import File


class Feature(Base):
    __tablename__ = "features"
    __table_args__ = (
        UniqueConstraint("file_id", "feature_index", name="uq_features_file_id_feature_index"),
        Index("idx_features_geometry", "geometry", postgresql_using="gist"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feature_index: Mapped[int] = mapped_column(Integer, nullable=False)
    geometry_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    properties: Mapped[Dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )
    measurement_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    measurement_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    measurement_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # PostGIS geometry column storing spatial representation in WGS84 (EPSG:4326),
    # with LargeBinary variant for cross-dialect / in-memory testing.
    geometry = mapped_column(
        Geometry(
            geometry_type="GEOMETRY",
            srid=4326,
            nullable=True,
            spatial_index=False,
        ).with_variant(LargeBinary, "sqlite"),
        nullable=True,
    )

    file: Mapped["File"] = relationship("File", back_populates="features")
