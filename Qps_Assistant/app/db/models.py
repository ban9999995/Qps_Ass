"""核心 MySQL 表的 SQLAlchemy 模型骨架。"""

from datetime import datetime

from sqlalchemy import JSON, Date, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TimestampMixin:
    """提供公共时间字段。"""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Store(Base, TimestampMixin):
    """店铺表。"""

    __tablename__ = "stores"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    platform: Mapped[str] = mapped_column(String(100), default="")


class ProductRecord(Base, TimestampMixin):
    """商品主表。"""

    __tablename__ = "products"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    store_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(100), default="")
    brand: Mapped[str] = mapped_column(String(100), default="")
    price: Mapped[float] = mapped_column(Float, default=0)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="draft")
    diagnosis_status: Mapped[str] = mapped_column(String(32), default="none")
    creative_status: Mapped[str] = mapped_column(String(32), default="none")
    ad_strategy_status: Mapped[str] = mapped_column(String(32), default="draft")
    review_status: Mapped[str] = mapped_column(String(32), default="none")


class JsonRecord(Base, TimestampMixin):
    """用于版本化结构化产物的通用表。"""

    __abstract__ = True
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(64), index=True)
    version_no: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="generated")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)


class DiagnosisRecord(JsonRecord):
    """商品诊断版本表。"""

    __tablename__ = "diagnoses"


class CreativePlanRecord(JsonRecord):
    """创意方案版本表。"""

    __tablename__ = "creative_plans"


class CompetitorRecord(Base, TimestampMixin):
    """竞品表。"""

    __tablename__ = "competitors"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(200))
    platform: Mapped[str] = mapped_column(String(100), default="")
    url: Mapped[str] = mapped_column(String(500), default="")
    price: Mapped[float] = mapped_column(Float, default=0)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)


class MaterialTaskRecord(Base, TimestampMixin):
    """异步素材任务表。"""

    __tablename__ = "material_tasks"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(64), index=True)
    asset_type: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class AssetRecord(Base, TimestampMixin):
    """素材元数据和人工审核状态表。"""

    __tablename__ = "assets"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(64), index=True)
    task_id: Mapped[str] = mapped_column(String(64))
    asset_type: Mapped[str] = mapped_column(String(32))
    url: Mapped[str] = mapped_column(String(500), default="")
    review_status: Mapped[str] = mapped_column(String(32), default="pending")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class AdStrategyRecord(JsonRecord):
    """投放策略版本表。"""

    __tablename__ = "ad_strategies"


class ApprovalRecord(Base, TimestampMixin):
    """投放审批追加记录表。"""

    __tablename__ = "approval_records"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    strategy_id: Mapped[str] = mapped_column(String(64), index=True)
    action: Mapped[str] = mapped_column(String(32))
    reason: Mapped[str] = mapped_column(Text, default="")
    operator: Mapped[str] = mapped_column(String(100), default="demo_operator")


class OperationMetricRecord(Base, TimestampMixin):
    """经营指标表，日期和来源联合唯一。"""

    __tablename__ = "operation_metrics"
    __table_args__ = (UniqueConstraint("product_id", "metric_date", "source", name="uq_metric_product_date_source"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(64), index=True)
    metric_date: Mapped[datetime] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String(100))
    values: Mapped[dict] = mapped_column(JSON, default=dict)


class ReviewReportRecord(JsonRecord):
    """经营复盘报告表。"""

    __tablename__ = "review_reports"


class ImportBatchRecord(Base, TimestampMixin):
    """批量导入批次表。"""

    __tablename__ = "import_batches"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    import_type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), default="uploaded")
    summary: Mapped[dict] = mapped_column(JSON, default=dict)


class ImportRowErrorRecord(Base, TimestampMixin):
    """批量导入错误行表。"""

    __tablename__ = "import_row_errors"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    batch_id: Mapped[str] = mapped_column(String(64), index=True)
    row_number: Mapped[int] = mapped_column(Integer)
    raw_data: Mapped[dict] = mapped_column(JSON, default=dict)
    error_message: Mapped[str] = mapped_column(Text)


class ServiceConfigRecord(Base, TimestampMixin):
    """脱敏服务配置表。"""

    __tablename__ = "service_configs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    config_key: Mapped[str] = mapped_column(String(100), unique=True)
    config_value: Mapped[dict] = mapped_column(JSON, default=dict)


class AuditLogRecord(Base, TimestampMixin):
    """审计日志表。"""

    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    action: Mapped[str] = mapped_column(String(100))
    resource_type: Mapped[str] = mapped_column(String(100))
    resource_id: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
