from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Any
 
 
class AssetInput(BaseModel):
    hostname: str = Field(..., min_length=1, max_length=255)
    ip_address: str = Field(..., min_length=7, max_length=45)
    os_type: str = Field(..., min_length=1, max_length=100)
 
    # BUG-1 FIX: Was 'str' (required). Network scanner returns None when
    # OS detection fails. This caused 422 errors on all auto-scanned devices.
    os_version: Optional[str] = Field(default="Unknown", max_length=100)
 
    services: List[str] = Field(default_factory=list)
 
    # BUG-2 FIX: No validation meant -5 or 999 could be sent, breaking
    # the risk formula. ge=1, le=10 enforces the valid range.
    asset_criticality: int = Field(..., ge=1, le=10)
 
    firmware_version: Optional[str] = None
 
    @field_validator("os_version", mode="before")
    @classmethod
    def default_os_version(cls, v):
        # IMP-2: None becomes "Unknown" automatically
        return v if v else "Unknown"
 
    @field_validator("services", mode="before")
    @classmethod
    def clean_services(cls, v):
        # IMP-1: Strip whitespace, remove empty strings
        if not v:
            return []
        return [str(s).strip() for s in v if s and str(s).strip()]
 
 
class RiskReport(BaseModel):
    risk_score: float
    risk_level: str
    gap_analysis: List[str]
    remediation_steps: List[str]
    matched_cves: List[str]
    cvss_base_score: float
 
 
# BUG-3 FIX: This wrapper model was MISSING. Without it, the
# /generate-report endpoint always failed with 422 because FastAPI
# cannot parse two separate Body() params from one JSON object.
# The frontend sends: { "asset": {...}, "analysis": {...} }
# This model matches that structure exactly.
class ReportRequest(BaseModel):
    asset: AssetInput
    analysis: RiskReport
 
 
class KnowledgeBaseEntry(BaseModel):
    cve_id: str
    description: str
    base_score: float
    affected_versions: List[str]