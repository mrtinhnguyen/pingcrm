"""Backward-compatible re-export of all Celery tasks.

Tasks are now organized in app.services.task_jobs/ by domain.
This module re-exports them so existing imports and Celery task names
continue to work unchanged.
"""
from app.services.task_jobs.common import *  # noqa: F401,F403
from app.services.task_jobs.gmail import *  # noqa: F401,F403
from app.services.task_jobs.telegram import *  # noqa: F401,F403
from app.services.task_jobs.twitter import *  # noqa: F401,F403
from app.services.task_jobs.google import *  # noqa: F401,F403
from app.services.task_jobs.scoring import *  # noqa: F401,F403
from app.services.task_jobs.followups import *  # noqa: F401,F403
from app.services.task_jobs.maintenance import *  # noqa: F401,F403
from app.services.task_jobs.tagging import *  # noqa: F401,F403
