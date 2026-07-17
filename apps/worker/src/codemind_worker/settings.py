from arq.connections import RedisSettings

from codemind_worker.deps import REDIS_URL, shutdown, startup
from codemind_worker.tasks import analyze_repository, index_repository


class WorkerSettings:
    functions = [index_repository, analyze_repository]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(REDIS_URL)
