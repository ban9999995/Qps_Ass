"""创建运营助手核心业务表。"""

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """由 SQLAlchemy 元数据创建所有表。"""
    from app.db.base import Base
    from app.db import models  # noqa: F401
    from sqlalchemy import create_engine
    from app.shared.config import get_settings

    engine = create_engine(get_settings().database_url.replace("+asyncmy", ""))
    Base.metadata.create_all(engine)


def downgrade() -> None:
    """回滚时删除所有应用表。"""
    from app.db.base import Base
    from app.db import models  # noqa: F401
    from sqlalchemy import create_engine
    from app.shared.config import get_settings

    engine = create_engine(get_settings().database_url.replace("+asyncmy", ""))
    Base.metadata.drop_all(engine)
