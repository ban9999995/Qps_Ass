"""核心业务服务的确定性链路测试。"""

import pytest

from app.domain.models import ProductCreate
from app.repository.memory import InMemoryRepository
from app.service.services import BusinessError, OperationsService


@pytest.mark.asyncio
async def test_product_diagnosis_and_creative_chain() -> None:
    """验证商品创建、诊断和创意生成的编排顺序。"""
    service = OperationsService(InMemoryRepository())
    created = await service.create_product(ProductCreate(name="夏季防晒衣", price=199))
    diagnosis = await service.generate_diagnosis(created.artifact_id)
    creative = await service.generate_creative(created.artifact_id)
    assert diagnosis.status == "succeeded"
    assert len(creative.data["image_plans"]) == 3
    assert len(creative.data["video_scripts"]) == 3


@pytest.mark.asyncio
async def test_material_task_duplicate_is_rejected() -> None:
    """验证同一商品和素材类型不能同时存在多个活动任务。"""
    service = OperationsService(InMemoryRepository())
    created = await service.create_product(ProductCreate(name="演示商品"))
    await service.generate_diagnosis(created.artifact_id)
    await service.generate_creative(created.artifact_id)
    await service.create_material_task(created.artifact_id, {"asset_type": "image"})
    with pytest.raises(BusinessError):
        await service.create_material_task(created.artifact_id, {"asset_type": "image"})


@pytest.mark.asyncio
async def test_demo_material_task_reaches_review() -> None:
    """验证演示素材任务会完成并进入人工审核步骤。"""
    service = OperationsService(InMemoryRepository())
    created = await service.create_product(ProductCreate(name="演示商品"))
    await service.generate_diagnosis(created.artifact_id)
    await service.generate_creative(created.artifact_id)
    task = await service.create_material_task(created.artifact_id, {"asset_type": "image"})
    await service.process_demo_material_task(task.artifact_id)
    workspace = await service.workspace(created.artifact_id)
    assert workspace["tasks"][0]["status"] == "succeeded"
    assert workspace["assets"][0]["review_status"] == "pending"
    assert workspace["next_actions"] == ["review_asset"]


@pytest.mark.asyncio
async def test_metrics_are_idempotent() -> None:
    """验证相同日期和来源的指标回填会更新而不是重复追加。"""
    service = OperationsService(InMemoryRepository())
    created = await service.create_product(ProductCreate(name="演示商品"))
    metrics = {"metric_date": "2026-10-15", "source": "manual", "gmv": 100}
    await service.backfill_metrics(created.artifact_id, metrics)
    await service.backfill_metrics(created.artifact_id, {**metrics, "gmv": 200})
    workspace = await service.workspace(created.artifact_id)
    assert len(workspace["metrics"]) == 1
    assert workspace["metrics"][0]["gmv"] == 200
