"""HTTP 传输层请求模型。"""

from typing import Any

from pydantic import BaseModel, Field

from app.domain.models import ProductCreate


class CompetitorRequest(BaseModel):
    """竞品录入请求。"""

    name: str = Field(min_length=1)
    platform: str = ""
    url: str = ""
    price: float = Field(default=0, ge=0)
    parameters: dict[str, Any] = Field(default_factory=dict)


class MaterialTaskRequest(BaseModel):
    """素材任务创建请求。"""

    asset_type: str = Field(default="image", pattern="^(image|video)$")
    source_version: int = Field(default=1, ge=1)


class StrategyRequest(BaseModel):
    """投放策略生成请求。"""

    budget: float = Field(default=3000, ge=0)
    bid: float = Field(default=1.2, ge=0)
    period_days: int = Field(default=7, ge=1, le=90)


class RejectRequest(BaseModel):
    """投放策略驳回请求。"""

    reason: str = Field(min_length=1, max_length=1000)


class MetricsRequest(BaseModel):
    """经营指标回填请求。"""

    metric_date: str
    source: str = "manual"
    impressions: int = Field(default=0, ge=0)
    clicks: int = Field(default=0, ge=0)
    ctr: float = Field(default=0, ge=0)
    conversions: int = Field(default=0, ge=0)
    conversion_rate: float = Field(default=0, ge=0)
    gmv: float = Field(default=0, ge=0)
    roi: float = Field(default=0, ge=0)
    bounce_rate: float = Field(default=0, ge=0)
    remark: str = ""


class ReviewRequest(BaseModel):
    """复盘生成请求占位模型。"""

    confirm: bool = True


class AssetReviewRequest(BaseModel):
    """素材人工审核请求。"""

    status: str = Field(pattern="^(approved|rejected|archived)$")
    remark: str = ""


class SettingsRequest(BaseModel):
    """服务配置保存请求。"""

    values: dict[str, Any] = Field(default_factory=dict)
