"""领域模型、状态枚举和跨层稳定的数据契约。"""

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def now_utc() -> datetime:
    """返回带时区的当前 UTC 时间。"""
    return datetime.now(timezone.utc)


class ProductStatus(StrEnum):
    """商品生命周期状态。"""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class DiagnosisStatus(StrEnum):
    """诊断结果状态。"""

    NONE = "none"
    GENERATING = "generating"
    GENERATED = "generated"
    CONFIRMED = "confirmed"
    ARCHIVED = "archived"


class CreativeStatus(StrEnum):
    """创意方案状态。"""

    NONE = "none"
    GENERATING = "generating"
    GENERATED = "generated"
    EDITING = "editing"
    CONFIRMED = "confirmed"
    ARCHIVED = "archived"


class TaskStatus(StrEnum):
    """异步素材任务状态。"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"


class AssetReviewStatus(StrEnum):
    """素材人工审核状态。"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class AdStrategyStatus(StrEnum):
    """投放策略审批状态。"""

    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class ReviewStatus(StrEnum):
    """经营复盘状态。"""

    NONE = "none"
    REVIEW_PENDING = "review_pending"
    GENERATING = "generating"
    GENERATED = "generated"
    CONFIRMED = "confirmed"
    ARCHIVED = "archived"


class Product(BaseModel):
    """商品领域对象。"""

    id: str = Field(default_factory=lambda: f"prd_{uuid4().hex[:10]}")
    name: str
    category: str = "服饰"
    brand: str = ""
    price: float = 0
    description: str = ""
    image_refs: list[str] = Field(default_factory=list)
    status: ProductStatus = ProductStatus.DRAFT
    diagnosis_status: DiagnosisStatus = DiagnosisStatus.NONE
    creative_status: CreativeStatus = CreativeStatus.NONE
    ad_strategy_status: AdStrategyStatus = AdStrategyStatus.DRAFT
    review_status: ReviewStatus = ReviewStatus.NONE
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class ProductCreate(BaseModel):
    """创建商品请求。"""

    name: str = Field(min_length=1, max_length=200)
    category: str = "服饰"
    brand: str = ""
    price: float = Field(default=0, ge=0)
    description: str = ""
    image_refs: list[str] = Field(default_factory=list)


class Competitor(BaseModel):
    """竞品领域对象。"""

    id: str = Field(default_factory=lambda: f"cmp_{uuid4().hex[:10]}")
    product_id: str
    name: str
    platform: str = ""
    url: str = ""
    price: float = 0
    parameters: dict[str, Any] = Field(default_factory=dict)


class ProcessResult(BaseModel):
    """统一返回给 API 的业务处理结果。"""

    reply: str
    artifact_type: str
    artifact_id: str
    status: str
    data: dict[str, Any] = Field(default_factory=dict)
    next_actions: list[str] = Field(default_factory=list)


class Workspace(BaseModel):
    """商品工作台聚合视图。"""

    product: Product
    competitors: list[Competitor] = Field(default_factory=list)
    diagnosis: dict[str, Any] | None = None
    creative: dict[str, Any] | None = None
    tasks: list[dict[str, Any]] = Field(default_factory=list)
    assets: list[dict[str, Any]] = Field(default_factory=list)
    ad_strategy: dict[str, Any] | None = None
    metrics: list[dict[str, Any]] = Field(default_factory=list)
    review: dict[str, Any] | None = None
    next_actions: list[str] = Field(default_factory=list)
