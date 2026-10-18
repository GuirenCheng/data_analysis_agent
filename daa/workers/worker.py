"""ARQ Worker 配置 — 后台任务执行器。"""

import sys

# 修复 Windows 控制台 GBK 编码无法输出 emoji 的问题
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from arq.connections import RedisSettings

from daa.settings import get_settings
from daa.workers.tasks import run_analysis_task


async def startup(ctx: dict) -> None:
    """Worker 启动时的初始化。"""
    settings = get_settings()
    print(f"👷 ARQ Worker 已启动")
    print(f"   MySQL: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
    print(f"   Redis: {settings.REDIS_URL}")


async def shutdown(ctx: dict) -> None:
    """Worker 关闭时的清理。"""
    from daa.db.session import close_db
    from daa.db.redis import close_redis
    await close_redis()
    await close_db()
    print("👷 ARQ Worker 已关闭")


class WorkerSettings:
    """ARQ Worker 配置类。

    注意：arq 通过 ``settings_cls.__dict__``（类属性）读取配置，
    因此 ``functions`` / ``redis_settings`` 必须作为类属性定义，
    而不能在 ``__init__`` 中动态赋值（那样 arq 读取时会是空值）。
    """

    functions = [run_analysis_task]
    redis_settings = RedisSettings.from_dsn(get_settings().REDIS_URL)
    # 并发分析任务数。必须为 1：所有会话共享同一个 IPython 单例 shell
    # （InteractiveShell.instance()），>1 时并发任务的变量会互相串味。
    # 需要真并发时应改为多 worker 进程（每进程独立 shell），而不是调大此值。
    max_jobs: int = 1
    job_timeout: int = 3600  # 单任务最多 1 小时
    poll_delay: float = 0.5
    on_startup = startup
    on_shutdown = shutdown
