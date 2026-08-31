"""Funnel guardrails, shared by the request schemas and the query builder.

They live here rather than next to either one because both need them and the
API must reject a bad definition before it can ever be persisted, while the
builder re-checks defensively for callers that bypass the schema (Celery jobs,
tests, a future internal report).
"""

from datetime import timedelta

# PostgreSQL's default ``join_collapse_limit`` is 8. Past it the planner stops
# reordering joins and plans get erratic; no real product funnel needs more.
MIN_FUNNEL_STEPS = 2
MAX_FUNNEL_STEPS = 8

MAX_STEP_NAME_LENGTH = 128

# An unbounded window turns each step lookup into "the rest of this user's
# history"; a sub-minute one cannot express any real journey.
MIN_WINDOW_SECONDS = 60
MAX_WINDOW_SECONDS = int(timedelta(days=30).total_seconds())

# Bounds the DISTINCT ON sort that finds funnel entrants, which is the half of
# the report cost that scales with the window rather than with funnel depth.
MAX_REPORT_RANGE = timedelta(days=92)
DEFAULT_REPORT_RANGE = timedelta(days=30)

# How many distinct event names the name-suggestion endpoint returns, and how
# far back it looks. Both are generous for a real bot's vocabulary and keep the
# grouped scan bounded on a noisy one.
MAX_EVENT_NAMES = 200
EVENT_NAMES_LOOKBACK = timedelta(days=90)

# One ingest batch, matching the log endpoint's limit.
MAX_EVENT_BATCH = 500

# Events are timestamped by the bot, so its clock can be ahead of ours. A small
# skew is normal; a large one would reorder a user's steps against events we
# recorded correctly.
MAX_EVENT_CLOCK_SKEW = timedelta(hours=1)
