# 电商运营助手后端

后端采用 FastAPI 分层架构。默认使用确定性演示引擎和内存仓储，配置 MySQL 后可切换持久化仓储。

```powershell
uv sync
uv run uvicorn app.main:app --reload
```

启动后访问 `http://localhost:8000/docs`。
