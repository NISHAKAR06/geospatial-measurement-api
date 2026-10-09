from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MeasurementDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    status: str = "OK"


class FeatureMeasurementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    feature_id: int
    geometry_type: Optional[str] = None
    geometry: Optional[Dict[str, Any]] = None
    crs: Optional[str] = None
    measurement: Optional[MeasurementDetail] = None
    properties: Dict[str, Any] = Field(default_factory=dict)


class FileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    crs: Optional[str] = None
    original_crs: Optional[str] = None
    measurement_crs: Optional[str] = None
    feature_count: int
    status: Literal["PROCESSING", "COMPLETED", "FAILED"] = "COMPLETED"
    created_at: Optional[datetime] = None


class MeasurementListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    file_id: UUID
    original_crs: Optional[str] = None
    measurement_crs: Optional[str] = None
    measurements: List[FeatureMeasurementResponse]
