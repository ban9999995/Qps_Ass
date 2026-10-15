"""演示用内存仓储，保持与 MySQL 仓储相同的异步契约。"""

from copy import deepcopy
from uuid import uuid4

from app.domain.models import Competitor, CreativeStatus, DiagnosisStatus, Product, ReviewStatus, Workspace, now_utc


class InMemoryRepository:
    """用于本地演示和单元测试的仓储实现。"""

    def __init__(self) -> None:
        """初始化隔离的内存数据集合。"""
        self.products: dict[str, Product] = {}
        self.competitors: dict[str, list[Competitor]] = {}
        self.artifacts: dict[str, dict[str, dict]] = {}
        self.tasks: dict[str, dict] = {}
        self.assets: dict[str, dict] = {}
        self.strategies: dict[str, dict] = {}
        self.metrics: dict[str, list[dict]] = {}
        self.reviews: dict[str, dict] = {}

    async def create_product(self, product: Product) -> Product:
        """保存商品并返回副本。"""
        self.products[product.id] = deepcopy(product)
        return deepcopy(product)

    async def get_product(self, product_id: str) -> Product | None:
        """按编号读取商品。"""
        product = self.products.get(product_id)
        return deepcopy(product) if product else None

    async def list_products(self) -> list[Product]:
        """返回所有商品。"""
        return [deepcopy(item) for item in self.products.values()]

    async def save_product(self, product: Product) -> Product:
        """更新商品状态和更新时间。"""
        product.updated_at = now_utc()
        self.products[product.id] = deepcopy(product)
        return deepcopy(product)

    async def add_competitor(self, competitor: Competitor) -> Competitor:
        """追加竞品记录。"""
        self.competitors.setdefault(competitor.product_id, []).append(deepcopy(competitor))
        return deepcopy(competitor)

    async def list_competitors(self, product_id: str) -> list[Competitor]:
        """返回商品关联竞品。"""
        return deepcopy(self.competitors.get(product_id, []))

    async def get_workspace(self, product_id: str) -> dict:
        """组合商品工作台所需的结构化数据。"""
        product = await self.get_product(product_id)
        if product is None:
            raise KeyError(product_id)
        tasks = await self.list_tasks(product_id)
        assets = [deepcopy(item) for item in self.assets.values() if item.get("product_id") == product_id]
        return Workspace(
            product=product,
            competitors=await self.list_competitors(product_id),
            diagnosis=deepcopy(self.artifacts.get(product_id, {}).get("diagnosis")),
            creative=deepcopy(self.artifacts.get(product_id, {}).get("creative")),
            tasks=tasks,
            assets=assets,
            ad_strategy=deepcopy(self.strategies.get(product_id)),
            metrics=deepcopy(self.metrics.get(product_id, [])),
            review=deepcopy(self.reviews.get(product_id)),
            next_actions=_next_actions(product, tasks, assets),
        ).model_dump(mode="json")

    async def save_artifact(self, product_id: str, artifact_type: str, data: dict) -> str:
        """保存结构化产物并生成产物编号。"""
        artifact_id = f"{artifact_type[:4]}_{uuid4().hex[:8]}"
        self.artifacts.setdefault(product_id, {})[artifact_type] = {"id": artifact_id, **deepcopy(data)}
        return artifact_id

    async def list_tasks(self, product_id: str | None = None) -> list[dict]:
        """按商品筛选或返回全部任务。"""
        values = self.tasks.values() if product_id is None else (
            item for item in self.tasks.values() if item.get("product_id") == product_id
        )
        return [deepcopy(item) for item in values]

    async def get_task(self, task_id: str) -> dict | None:
        """读取异步任务。"""
        task = self.tasks.get(task_id)
        return deepcopy(task) if task else None

    async def save_task(self, task: dict) -> dict:
        """保存异步任务状态。"""
        self.tasks[task["id"]] = deepcopy(task)
        return deepcopy(task)

    async def save_asset(self, asset: dict) -> dict:
        """保存素材元数据。"""
        self.assets[asset["id"]] = deepcopy(asset)
        return deepcopy(asset)

    async def save_strategy(self, strategy: dict) -> dict:
        """保存投放策略。"""
        self.strategies[strategy["product_id"]] = deepcopy(strategy)
        return deepcopy(strategy)

    async def save_metrics(self, product_id: str, metrics: dict) -> dict:
        """按日期和来源幂等保存经营指标。"""
        rows = self.metrics.setdefault(product_id, [])
        key = (metrics.get("metric_date"), metrics.get("source"))
        rows[:] = [item for item in rows if (item.get("metric_date"), item.get("source")) != key]
        rows.append(deepcopy(metrics))
        return deepcopy(metrics)

    async def save_review(self, product_id: str, review: dict) -> dict:
        """保存复盘报告。"""
        self.reviews[product_id] = deepcopy(review)
        return deepcopy(review)


def _next_actions(product: Product, tasks: list[dict], assets: list[dict]) -> list[str]:
    """根据商品状态推导前端操作 Chip。"""
    if any(item.get("status") in {"pending", "running", "cancel_requested"} for item in tasks):
        return []
    pending_assets = [item for item in assets if item.get("review_status") == "pending"]
    if pending_assets:
        return ["review_asset"]
    approved_assets = [item for item in assets if item.get("review_status") == "approved"]
    if approved_assets and product.creative_status == CreativeStatus.CONFIRMED and product.ad_strategy_status == "draft":
        return ["generate_ad_strategy"]
    if product.diagnosis_status == DiagnosisStatus.NONE:
        return ["generate_diagnosis"]
    if product.diagnosis_status == DiagnosisStatus.GENERATED:
        return ["confirm_diagnosis", "generate_creative"]
    if product.creative_status == CreativeStatus.NONE:
        return ["generate_creative"]
    if product.creative_status == CreativeStatus.GENERATED:
        return ["confirm_creative"]
    if product.creative_status == CreativeStatus.CONFIRMED:
        return ["create_material_task"]
    if product.ad_strategy_status == "draft":
        return ["generate_ad_strategy"]
    if product.ad_strategy_status == "pending_approval":
        return ["approve_ad_strategy", "reject_ad_strategy"]
    if product.review_status == ReviewStatus.REVIEW_PENDING:
        return ["generate_review"]
    return ["start_next_diagnosis"]
