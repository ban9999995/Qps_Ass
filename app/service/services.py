"""应用服务层：编排状态校验、Agent、仓储和异步任务。"""

import asyncio
from datetime import date
from uuid import uuid4

from app.domain.models import AdStrategyStatus, Competitor, CreativeStatus, DiagnosisStatus, Product, ProductCreate, ProcessResult, ProductStatus, ReviewStatus, TaskStatus, now_utc
from app.engine.agents import AdStrategyAgent, CreativeAgent, DiagnosisAgent, ReviewAgent


class BusinessError(Exception):
    """可安全返回给调用方的业务异常。"""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class OperationsService:
    """电商运营用例编排服务。"""

    def __init__(self, repository, diagnosis_agent=None, creative_agent=None, ad_agent=None, review_agent=None) -> None:
        """注入仓储和可替换 Agent。"""
        self.repository = repository
        self.diagnosis_agent = diagnosis_agent or DiagnosisAgent()
        self.creative_agent = creative_agent or CreativeAgent()
        self.ad_agent = ad_agent or AdStrategyAgent()
        self.review_agent = review_agent or ReviewAgent()

    async def create_product(self, request: ProductCreate) -> ProcessResult:
        """创建商品档案并返回首个操作建议。"""
        product = await self.repository.create_product(Product(**request.model_dump(), status=ProductStatus.ACTIVE))
        return ProcessResult(reply="商品档案创建成功", artifact_type="product", artifact_id=product.id, status=product.status, next_actions=["generate_diagnosis"], data=product.model_dump(mode="json"))

    async def add_competitor(self, product_id: str, request: dict) -> ProcessResult:
        """录入商品竞品。"""
        await self.require_product(product_id)
        competitor = await self.repository.add_competitor(Competitor(product_id=product_id, **request))
        return ProcessResult(reply="竞品录入成功", artifact_type="competitor", artifact_id=competitor.id, status="succeeded", next_actions=["generate_diagnosis"], data=competitor.model_dump(mode="json"))

    async def generate_diagnosis(self, product_id: str) -> ProcessResult:
        """调用诊断 Agent 并保存诊断版本。"""
        product = await self.require_product(product_id)
        result = await self.diagnosis_agent.generate({"product": product.model_dump(), "competitors": [item.model_dump() for item in await self.repository.list_competitors(product_id)]})
        artifact_id = await self.repository.save_artifact(product_id, "diagnosis", result)
        product.diagnosis_status = DiagnosisStatus.GENERATED
        await self.repository.save_product(product)
        return ProcessResult(reply="商品诊断已完成，发现透气性表达可继续优化。", artifact_type="diagnosis", artifact_id=artifact_id, status="succeeded", data=result, next_actions=["confirm_diagnosis", "generate_creative"])

    async def generate_creative(self, product_id: str) -> ProcessResult:
        """基于诊断结果生成创意方案。"""
        product = await self.require_product(product_id)
        if product.diagnosis_status not in {"generated", "confirmed"}:
            raise BusinessError("请先生成商品诊断")
        workspace = await self.repository.get_workspace(product_id)
        result = await self.creative_agent.generate(workspace)
        artifact_id = await self.repository.save_artifact(product_id, "creative", result)
        product.creative_status = CreativeStatus.GENERATED
        await self.repository.save_product(product)
        return ProcessResult(reply="创意方案已生成，包含 3 组主图和 3 套脚本。", artifact_type="creative", artifact_id=artifact_id, status="succeeded", data=result, next_actions=["confirm_creative", "create_material_task"])

    async def confirm_diagnosis(self, product_id: str) -> ProcessResult:
        """确认当前诊断版本，允许后续创意流程使用。"""
        product = await self.require_product(product_id)
        if product.diagnosis_status != "generated":
            raise BusinessError("当前没有待确认的诊断结果")
        product.diagnosis_status = "confirmed"
        await self.repository.save_product(product)
        return ProcessResult(reply="诊断结果已确认", artifact_type="diagnosis", artifact_id=product_id, status="confirmed", data=await self.repository.get_workspace(product_id), next_actions=["generate_creative"])

    async def confirm_creative(self, product_id: str) -> ProcessResult:
        """确认当前创意版本，允许创建素材任务。"""
        product = await self.require_product(product_id)
        if product.creative_status != "generated":
            raise BusinessError("当前没有待确认的创意方案")
        product.creative_status = "confirmed"
        await self.repository.save_product(product)
        return ProcessResult(reply="创意方案已确认，可以创建素材任务", artifact_type="creative", artifact_id=product_id, status="confirmed", data=await self.repository.get_workspace(product_id), next_actions=["create_material_task"])

    async def create_material_task(self, product_id: str, request: dict) -> ProcessResult:
        """创建图片或视频素材异步任务。"""
        product = await self.require_product(product_id)
        if product.creative_status not in {"generated", "confirmed"}:
            raise BusinessError("请先生成并确认创意方案")
        active = [item for item in await self.repository.list_tasks(product_id) if item["status"] in {"pending", "running", "cancel_requested"} and item["asset_type"] == request.get("asset_type")]
        if active:
            raise BusinessError("同一商品和素材类型已有活动任务")
        task = {"id": f"task_{uuid4().hex[:10]}", "product_id": product_id, "asset_type": request.get("asset_type", "image"), "source_version": request.get("source_version", 1), "status": TaskStatus.PENDING, "attempts": 0, "error": None, "created_at": now_utc().isoformat(), "updated_at": now_utc().isoformat()}
        await self.repository.save_task(task)
        return ProcessResult(reply="素材生成任务已创建", artifact_type="material_task", artifact_id=task["id"], status=task["status"], data=task, next_actions=["get_material_task", "cancel_material_task"])

    async def get_task(self, task_id: str) -> dict:
        """读取素材任务状态。"""
        task = await self.repository.get_task(task_id)
        if task is None:
            raise BusinessError("素材任务不存在", 404)
        return task

    async def update_task(self, task_id: str, status: str, error: str | None = None) -> ProcessResult:
        """更新任务状态并在成功时创建素材元数据。"""
        task = await self.get_task(task_id)
        task["status"] = status
        task["attempts"] += 1 if status in {"running", "failed"} else 0
        task["error"] = error
        task["updated_at"] = now_utc().isoformat()
        await self.repository.save_task(task)
        if status == TaskStatus.SUCCEEDED:
            await self.repository.save_asset({"id": f"asset_{uuid4().hex[:8]}", "product_id": task["product_id"], "task_id": task_id, "asset_type": task["asset_type"], "review_status": "pending", "url": f"/files/{task_id}"})
        return ProcessResult(reply=f"素材���务状态已更新为 {status}", artifact_type="material_task", artifact_id=task_id, status=status, data=task, next_actions=["review_asset"] if status == "succeeded" else [])

    async def process_demo_material_task(self, task_id: str) -> None:
        """在本地演示模式推进任务状态并生成演示素材记录。"""
        task = await self.get_task(task_id)
        if task["status"] != TaskStatus.PENDING:
            return
        await self.update_task(task_id, TaskStatus.RUNNING)
        await asyncio.sleep(1)
        current = await self.get_task(task_id)
        if current["status"] == TaskStatus.RUNNING:
            await self.update_task(task_id, TaskStatus.SUCCEEDED)

    async def generate_ad_strategy(self, product_id: str, request: dict) -> ProcessResult:
        """生成投放建议，但不自动审批或执行投放。"""
        product = await self.require_product(product_id)
        if product.creative_status not in {"generated", "confirmed"}:
            raise BusinessError("请先准备创意方案")
        strategy = await self.ad_agent.generate(request)
        strategy.update({"id": f"ads_{uuid4().hex[:8]}", "product_id": product_id, "status": "pending_approval", "created_at": now_utc().isoformat()})
        await self.repository.save_strategy(strategy)
        product.ad_strategy_status = AdStrategyStatus.PENDING_APPROVAL
        await self.repository.save_product(product)
        return ProcessResult(reply="投放建议已生成，等待人工审批", artifact_type="ad_strategy", artifact_id=strategy["id"], status="pending_approval", data=strategy, next_actions=["approve_ad_strategy", "reject_ad_strategy"])

    async def approve_strategy(self, strategy_id: str) -> ProcessResult:
        """确认采纳投放建议。"""
        strategy = await self.find_strategy(strategy_id)
        strategy["status"] = "approved"
        await self.repository.save_strategy(strategy)
        product = await self.require_product(strategy["product_id"])
        product.ad_strategy_status = AdStrategyStatus.APPROVED
        await self.repository.save_product(product)
        return ProcessResult(reply="投放建议已确认采纳", artifact_type="ad_strategy", artifact_id=strategy_id, status="approved", data=strategy, next_actions=["backfill_metrics"])

    async def reject_strategy(self, strategy_id: str, reason: str) -> ProcessResult:
        """驳回投放建议并保留驳回原因。"""
        if not reason.strip():
            raise BusinessError("驳回原因不能为空")
        strategy = await self.find_strategy(strategy_id)
        strategy["status"] = "rejected"
        strategy["reject_reason"] = reason
        await self.repository.save_strategy(strategy)
        return ProcessResult(reply="投放建议已驳回，请调整后生成新版本", artifact_type="ad_strategy", artifact_id=strategy_id, status="rejected", data=strategy, next_actions=["generate_ad_strategy"])

    async def backfill_metrics(self, product_id: str, metrics: dict) -> ProcessResult:
        """幂等保存经营数据并标记可生成复盘。"""
        await self.require_product(product_id)
        saved = await self.repository.save_metrics(product_id, metrics)
        product = await self.require_product(product_id)
        product.review_status = ReviewStatus.REVIEW_PENDING
        await self.repository.save_product(product)
        return ProcessResult(reply="经营数据已回填，可以生成复盘", artifact_type="operation_metrics", artifact_id=f"metric_{metrics.get('metric_date', date.today().isoformat())}", status="succeeded", data=saved, next_actions=["generate_review"])

    async def generate_review(self, product_id: str) -> ProcessResult:
        """调用复盘 Agent 并保存报告。"""
        product = await self.require_product(product_id)
        review = await self.review_agent.generate({"metrics": (await self.repository.get_workspace(product_id))["metrics"]})
        review["id"] = await self.repository.save_artifact(product_id, "review", review)
        await self.repository.save_review(product_id, review)
        product.review_status = ReviewStatus.GENERATED
        await self.repository.save_product(product)
        return ProcessResult(reply="经营复盘已生成", artifact_type="review", artifact_id=review["id"], status="succeeded", data=review, next_actions=["start_next_diagnosis"])

    async def workspace(self, product_id: str) -> dict:
        """返回商品工作台聚合数据。"""
        await self.require_product(product_id)
        return await self.repository.get_workspace(product_id)

    async def require_product(self, product_id: str) -> Product:
        """读取商品，不存在时抛出统一业务异常。"""
        product = await self.repository.get_product(product_id)
        if product is None:
            raise BusinessError("商品不存在", 404)
        return product

    async def find_strategy(self, strategy_id: str) -> dict:
        """按策略编号查找策略。"""
        products = await self.repository.list_products()
        for product in products:
            workspace = await self.repository.get_workspace(product.id)
            strategy = workspace.get("ad_strategy")
            if strategy and strategy.get("id") == strategy_id:
                return strategy
        raise BusinessError("投放策略不存在", 404)
