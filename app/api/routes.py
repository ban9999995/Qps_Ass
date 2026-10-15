"""REST API 路由，负责校验、调用 Service 和返回统一结果。"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from app.api.dependencies import get_service
from app.api.schemas import AssetReviewRequest, CompetitorRequest, MaterialTaskRequest, MetricsRequest, RejectRequest, SettingsRequest, StrategyRequest
from app.domain.models import ProductCreate
from app.service.services import BusinessError, OperationsService

router = APIRouter()
settings_store: dict = {"llm": {"configured": False}, "vlm": {"configured": False}, "task": {"max_retries": 3}}


def handle_error(error: BusinessError) -> HTTPException:
    """将业务异常转换为 HTTP 异常。"""
    return HTTPException(status_code=error.status_code, detail=error.message)


@router.post("/products")
async def create_product(request: ProductCreate, service: OperationsService = Depends(get_service)):
    """创建商品档案。"""
    try:
        return await service.create_product(request)
    except BusinessError as error:
        raise handle_error(error) from error


@router.get("/products")
async def list_products(service: OperationsService = Depends(get_service)):
    """返回商品列表。"""
    return await service.repository.list_products()


@router.post("/products/{product_id}/competitors")
async def add_competitor(product_id: str, request: CompetitorRequest, service: OperationsService = Depends(get_service)):
    """录入商品竞品。"""
    try:
        return await service.add_competitor(product_id, request.model_dump())
    except BusinessError as error:
        raise handle_error(error) from error


@router.post("/products/{product_id}/diagnoses")
async def generate_diagnosis(product_id: str, service: OperationsService = Depends(get_service)):
    """生成商品诊断。"""
    try:
        return await service.generate_diagnosis(product_id)
    except BusinessError as error:
        raise handle_error(error) from error


@router.post("/products/{product_id}/creative-plans")
async def generate_creative(product_id: str, service: OperationsService = Depends(get_service)):
    """生成创意方案。"""
    try:
        return await service.generate_creative(product_id)
    except BusinessError as error:
        raise handle_error(error) from error


@router.post("/products/{product_id}/diagnoses/confirm")
async def confirm_diagnosis(product_id: str, service: OperationsService = Depends(get_service)):
    """确认商品诊断结果。"""
    try:
        return await service.confirm_diagnosis(product_id)
    except BusinessError as error:
        raise handle_error(error) from error


@router.post("/products/{product_id}/creative-plans/confirm")
async def confirm_creative(product_id: str, service: OperationsService = Depends(get_service)):
    """确认创意方案。"""
    try:
        return await service.confirm_creative(product_id)
    except BusinessError as error:
        raise handle_error(error) from error


@router.post("/material-tasks")
async def create_material_task(background_tasks: BackgroundTasks, product_id: str = Query(...), request: MaterialTaskRequest = MaterialTaskRequest(), service: OperationsService = Depends(get_service)):
    """创建异步素材任务。"""
    try:
        result = await service.create_material_task(product_id, request.model_dump())
        background_tasks.add_task(service.process_demo_material_task, result.artifact_id)
        return result
    except BusinessError as error:
        raise handle_error(error) from error


@router.get("/material-tasks/{task_id}")
async def get_material_task(task_id: str, service: OperationsService = Depends(get_service)):
    """查询素材任务状态。"""
    try:
        return await service.get_task(task_id)
    except BusinessError as error:
        raise handle_error(error) from error


@router.post("/material-tasks/{task_id}/retry")
async def retry_material_task(task_id: str, background_tasks: BackgroundTasks, service: OperationsService = Depends(get_service)):
    """重试失败素材任务。"""
    try:
        task = await service.get_task(task_id)
        result = await service.update_task(task_id, "pending", task.get("error"))
        background_tasks.add_task(service.process_demo_material_task, task_id)
        return result
    except BusinessError as error:
        raise handle_error(error) from error


@router.post("/material-tasks/{task_id}/cancel")
async def cancel_material_task(task_id: str, service: OperationsService = Depends(get_service)):
    """取消素材任务。"""
    try:
        return await service.update_task(task_id, "cancelled")
    except BusinessError as error:
        raise handle_error(error) from error


@router.patch("/assets/{asset_id}/review")
async def review_asset(asset_id: str, request: AssetReviewRequest, service: OperationsService = Depends(get_service)):
    """执行素材人工审核。"""
    for asset in service.repository.assets.values():
        if asset["id"] == asset_id:
            asset.update({"review_status": request.status, "remark": request.remark})
            return asset
    raise HTTPException(404, "素材不存在")


@router.post("/products/{product_id}/ad-strategies")
async def generate_strategy(product_id: str, request: StrategyRequest, service: OperationsService = Depends(get_service)):
    """生成投放建议。"""
    try:
        return await service.generate_ad_strategy(product_id, request.model_dump())
    except BusinessError as error:
        raise handle_error(error) from error


@router.post("/ad-strategies/{strategy_id}/approve")
async def approve_strategy(strategy_id: str, service: OperationsService = Depends(get_service)):
    """审批通过投放建议。"""
    try:
        return await service.approve_strategy(strategy_id)
    except BusinessError as error:
        raise handle_error(error) from error


@router.post("/ad-strategies/{strategy_id}/reject")
async def reject_strategy(strategy_id: str, request: RejectRequest, service: OperationsService = Depends(get_service)):
    """驳回投放建议。"""
    try:
        return await service.reject_strategy(strategy_id, request.reason)
    except BusinessError as error:
        raise handle_error(error) from error


@router.post("/products/{product_id}/metrics")
async def backfill_metrics(product_id: str, request: MetricsRequest, service: OperationsService = Depends(get_service)):
    """回填经营指标。"""
    try:
        return await service.backfill_metrics(product_id, request.model_dump())
    except BusinessError as error:
        raise handle_error(error) from error


@router.post("/products/{product_id}/reviews")
async def generate_review(product_id: str, service: OperationsService = Depends(get_service)):
    """生成经营复盘。"""
    try:
        return await service.generate_review(product_id)
    except BusinessError as error:
        raise handle_error(error) from error


@router.get("/products/{product_id}/workspace")
async def get_workspace(product_id: str, service: OperationsService = Depends(get_service)):
    """读取商品工作台聚合视图。"""
    try:
        return await service.workspace(product_id)
    except BusinessError as error:
        raise handle_error(error) from error


@router.get("/dashboard/overview")
async def dashboard_overview(service: OperationsService = Depends(get_service)):
    """返回运营大盘摘要。"""
    products = await service.repository.list_products()
    tasks = await service.repository.list_tasks()
    return {"store": {"name": "演示店铺", "product_count": len(products), "active_rate": 1 if products else 0}, "metrics": {"gmv": 0, "impressions": 0, "ctr": 0, "conversion_rate": 0, "roi": 0}, "inventory_alerts": [], "recent_tasks": tasks[-10:], "pending_assets": [asset for asset in service.repository.assets.values() if asset.get("review_status") == "pending"], "products": products}


@router.post("/imports/preview")
async def import_preview():
    """返回批量导入预览占位结果。"""
    return {"batch_id": "batch_demo", "status": "preview", "valid_rows": 0, "error_rows": []}


@router.post("/imports/commit")
async def import_commit():
    """提交批量导入占位结果。"""
    return {"batch_id": "batch_demo", "status": "completed", "imported_rows": 0, "failed_rows": 0}


@router.get("/imports/templates/{template_type}")
async def import_template(template_type: str):
    """返回导入模板元信息。"""
    return {"type": template_type, "columns": ["name", "category", "price", "description"]}


@router.get("/settings")
async def get_settings():
    """读取脱敏服务配置。"""
    return settings_store


@router.put("/settings")
async def update_settings(request: SettingsRequest):
    """更新脱敏服务配置。"""
    settings_store.update(request.values)
    return settings_store
