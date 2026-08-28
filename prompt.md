# Prompt Log — Enrollments Update (mirror of PROMPT_LOG.md Prompt 6/7)

This file mirrors `PROMPT_LOG.md` for the `prompt.md` path requested.

## Prompt 6 — Implemented Enrollment domain (Challenge A + B)

**Tool/Model:** Muse Spark / Django 5.1 + DRF

**Prompt:**
> add the updates from enrollements folder to the readme and prompt.md update the architecture also

**What I used:**
- `enrollments/models.py:7` — `Enrollment` (`event` FK `events.Event`, `seeker` FK `User`, `status` enrolled/canceled, timestamps) with `UniqueConstraint(fields=['event','seeker'], condition=Q(status='enrolled'), name='unique_active_enrollment')`, `ordering=['-created_at']`
- `enrollments/serializers.py:5` — `EnrollmentSerializer` with nested `event_detail` (`EventSerializer`) + `seeker_email`
- `enrollments/views.py:13` — `EnrollView` (Seeker-only, past-event check, `transaction.atomic()` + `Event.objects.select_for_update().get()` at `enrollments/views.py:40`, `already_enrolled`/`event_full` handling, `canceled` reactivation at `enrollments/views.py:48`)
- `enrollments/views.py:68` — `CancelEnrollmentView` (soft-cancel `status='canceled'`, `already_canceled` guard, owner-scoped queryset)
- `enrollments/views.py:84` — `MyEnrollmentsView` (filters `status` and `time=upcoming/past` on `event__starts_at`, ordered by `event__starts_at`)
- `enrollments/urls.py:4` + `core/urls.py:10` — `api/enrollments/` (`''`, `'<int:pk>/cancel/'`, `'my-enrollments/'`)
- `enrollments/tests.py:1` — 11 tests including `test_concurrent_enrollments_dont_exceed_capacity` (Challenge A) and `test_cancel_then_reenroll` (Challenge B)
- `README.md:43` — API table + architecture (`enrollments/` domain) + key behaviors + limitations updated

**What I rejected:** permanent `unique(event,seeker)`, hard delete on cancel, lock-free `is_full()` check.

**How I verified it:** read enrollments files directly; `python manage.py check` + `python -m pytest enrollments/tests.py -v` (install `pytest`/`pytest-django` if missing).

## Prompt 7 — Challenge A Decision

**Tool/Model:** Muse Spark

**Prompt:**
> i completed my challenge A concurrency add that to my decision.md and why i choose that

**Choice:** `DECISIONS.md:48` Decision 4 — pessimistic row lock `select_for_update()` inside `transaction.atomic()`.

**Why:** serializes the read-check-write race per event so `is_full()` (`events/models.py:56`) sees post-commit state; DB unique constraint alone can't express `count < capacity`; optimistic locking/queues add complexity without benefit. Defense-in-depth via `unique_active_enrollment`. Trade-off: per-event serialization (short transactions, correctness over throughput).