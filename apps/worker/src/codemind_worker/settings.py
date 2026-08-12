from arq.connections import RedisSettings

from codemind_worker.deps import REDIS_URL, shutdown, startup
from codemind_worker.tasks import analyze_repository, index_repository


class WorkerSettings:
    functions = [index_repository, analyze_repository]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(REDIS_URL)
    # arq's default (10) runs that many jobs concurrently in one process. Both
    # job types call the local sentence-transformers embedding provider, which
    # is CPU/memory-bound (no GPU, no batching across jobs) -- a burst of
    # concurrent indexing requests (e.g. several users connecting repos at
    # once) previously ran unbounded and caused severe CPU contention / worker
    # instability. Cap concurrency here; raise it once running on hardware
    # sized for the real embedding workload.
    max_jobs = 2
