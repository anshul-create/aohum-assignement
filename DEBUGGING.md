# DEBUGGING

## Issue 1 — `NameError: name 'timezone' is not defined` on `POST /api/events/`

**Symptom:** Every `POST /api/events/` returned a 500. `server_err.log` showed the traceback ending at `events/serializers.py` inside `validate()`, at the line `if starts_at < timezone.now():`.

**Diagnosis:** `python -c "import events.serializers"` succeeded, so the usual "does the module import?" check passed and the bug survived every import-time validation. The error only reproduced when a request actually reached the serializer.

**Root cause:** `validate()` used `timezone.now()` but the file never imported `timezone`. Module import only executes top-level code — it never runs method bodies, so the missing name stayed invisible until the first real validation call.

**Fix:** Added `from django.utils import timezone` to `events/serializers.py`.

**Verification:** Ran a live `EventSerializer` validation with `ends_at` before `starts_at`: it returned the expected `invalid_time_range` error with no `NameError`. Full pytest suite green (`32 passed`).

---

## Issue 2 — Failed OTP attempts never persisted (lockout was unreachable)

**Symptom:** The new lockout test failed: after three wrong OTP codes, `otp_record.attempts` was still `0`, so the "Too many failed attempts" branch could never trigger.

**Diagnosis:** Stepped through `verify_otp()`: it incremented `attempts` and saved, then raised `ValueError` — but the whole function was decorated with `@transaction.atomic`. The exception unwound the transaction and rolled back the very increment that was supposed to persist.

**Root cause:** Mixing a persistence side-effect (failed-attempt counter) with exception-based control flow inside a single atomic block. Any `raise` inside `@transaction.atomic` discards *all* writes made in that block — including the ones made before the raise.

**Fix:** Restructured `verify_otp()`: the failure path (increment `attempts`, save, raise) now runs outside the atomic block; only the success path (mark profile verified + delete OTP record) is wrapped in its own `transaction.atomic()`.

**Verification:** New lockout test asserts `attempts` goes 1 → 2 → 3 across three wrong codes, then the *correct* code is rejected with "Too many failed attempts" and the profile stays unverified. Full suite green.

---

## Issue 3 — OTP debug output was easy to miss during POST-based manual testing

**Symptom:** A manual signup/resend POST was clearly generating and emailing an OTP, but the expected `print()` output was not obvious in the runserver console.

**Diagnosis:** The OTP send path was already deferred with `transaction.on_commit()`, and the first debug change used a tuple-returning `lambda` to do both `print()` and `send_mail()`. That callback executed in shell reproduction, but it was opaque and less reliable to reason about than an explicit function, especially when watching a live server process.

**Root cause:** The issue was not OTP generation itself; it was debug-output visibility. The callback shape made it harder to tell whether the OTP print was tied cleanly to the same post-commit path as the email send.

**Fix:** Replaced the inline `lambda` with a named `send_otp_email()` callback in `users/services.py`, and changed the debug print to `print(..., flush=True)` so OTP output is flushed immediately when the commit callback runs.

**Verification:** Reproduced `POST /api/users/signup/` locally and confirmed the console shows `OTP for <email>: <code>` immediately before the console email body for the same request.



## Issue 4 — Public Event Detail Endpoint Required Authentication

### Symptom

The `GET /api/events/{id}/` endpoint was unexpectedly returning an authentication error when accessed without a JWT token.

The endpoint was required to be **public**, so any client should be able to retrieve an event without authentication.

### Diagnosis

The issue was traced to the permission configuration in `EventDetailView`.

The view used:

```python
permission_classes = [
    permissions.IsAuthenticatedOrReadOnly,
    IsEventCreator,
]

Although IsAuthenticatedOrReadOnly allows unauthenticated GET requests, the additional IsEventCreator permission was also being evaluated.

Since IsEventCreator was intended for facilitator/owner authorization, it incorrectly affected the public read operation.

Root Cause

The permission classes combined public read access with an owner-specific permission at the view level.

As a result, the owner permission was being applied to the GET request as well as update/delete operations.

Fix

The permission handling was separated by operation.

Public GET requests are allowed without authentication, while ownership/facilitator checks are applied only to update and delete operations.
```