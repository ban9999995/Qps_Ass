"""可替换的模型 Provider 协议与 HTTP 适配器。"""

from typing import Any, Protocol

import httpx


class LLMClient(Protocol):
    """大语言模型客户端协议。"""

    async def generate_structured(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]: ...


class VLMClient(Protocol):
    """视觉语言模型客户端协议。"""

    async def analyze_image(self, image_ref: str, prompt: str) -> dict[str, Any]: ...
    async def analyze_video(self, video_ref: str, prompt: str) -> dict[str, Any]: ...


class HttpJsonClient:
    """通用 JSON HTTP Provider，实际接口格式由项目配置和供应商适配。"""

    def __init__(self, base_url: str, api_key: str, timeout: float = 60) -> None:
        """初始化基础地址、密钥和超时。"""
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    async def post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """向 Provider 发送 JSON 请求并返回对象。"""
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.post(path, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
