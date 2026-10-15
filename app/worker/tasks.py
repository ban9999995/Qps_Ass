"""Celery 异步素材任务入口。"""

from celery import Celery

from app.shared.config import get_settings

celery_app = Celery("qps_assistant", broker=get_settings().celery_broker_url, backend=get_settings().celery_result_backend)


@celery_app.task(name="qps_assistant.generate_material")
def generate_material(task_id: str) -> dict[str, str]:
    """素材生成 Worker 占位任务，生产环境接入真实 Provider。"""
    return {"task_id": task_id, "status": "queued"}
