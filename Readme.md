# Backend Developer Intern — Assignment Structure

**Deadline:** 24 hours from receipt
**Objective:** Compact Django REST backend for an Events Platform — auth, role-based access, event discovery, enrollments. Correctness/reasoning matter more than endpoint count.

---

## 1. Stack Requirements

- Django 4+ with Django REST Framework
- Default Django `User` model only — do not swap it
- JWT via SimpleJWT (or equivalent)
- PostgreSQL preferred
- Email: console/file backend is fine (no paid provider needed)

---

## 2. Core API

### 2.1 Authentication
- [ ] Signup: `email`, `password`, `role` (Seeker | Facilitator) — **no username in request**
- [ ] Creates unverified user + sends/stores 6-digit email OTP with TTL
- [ ] Verify email via `email + OTP`; unverified users blocked from login
- [ ] Login returns access + refresh JWT; refresh endpoint provided
- [ ] OTP: expiry, attempt limits, safe resend behavior

### 2.2 Roles & Domain Models
- [ ] Roles: **Seeker**, **Facilitator** — enforce role + ownership server-side
- [ ] `Event`: title, description, language, location, starts_at (UTC), ends_at (UTC), optional capacity, created_by, timestamps
- [ ] `Enrollment`: event, seeker, status (`enrolled`/`canceled`), timestamps
- [ ] Facilitator: CRUD own events; list own events with enrollment/available-seat counts
- [ ] Seeker: list/search events; enroll/cancel; list upcoming/past enrollments
- [ ] Search: `q` (title/description), `location`, `language`, `starts_after`, `starts_before` — paginated, upcoming-first ordering

---

## 3. Engineering Challenges (core evaluation focus)

### Challenge A — Enrollment Concurrency
- Scenario: capacity = 10, active enrollments = 9, 5 concurrent enroll attempts
- [ ] Guarantee active enrollments never exceed capacity (DB/backend-level protection — locking, `select_for_update`, or DB constraint)
- [ ] One automated/reproducible concurrency test
- [ ] Explain transaction/locking/constraint strategy in `DECISIONS.md`

### Challenge B — Cancellation & Re-enrollment
- Scenario: seeker enrolls → cancels → re-enrolls
- [ ] Define + implement intended lifecycle (a naive permanent `unique(event, seeker)` will break this)
- [ ] Document expected API behavior
- [ ] Document DB constraint / app-level rule used
- [ ] Test covering the full lifecycle

### Challenge C — OTP Resend
- Scenario: OTP1 requested → 30s later OTP2 requested → user submits OTP1
- [ ] Decide OTP1 validity and implement consistently
- [ ] OTP never returned in API responses
- [ ] No plaintext OTPs in normal logs
- [ ] Tests: expiry, failed-attempt limit, resend behavior

---

## 4. Response & Documentation Conventions

- [ ] DRF pagination shape: `count`, `next`, `previous`, `results`
- [ ] Consistent error shape: `{"detail": "message", "code": "error_code"}`
- [ ] Migrations included + indexes for common event queries
- [ ] Postman collection / API examples — nice to have, not mandatory
- [ ] Docker — bonus, not required

---

## 5. Mandatory Repository Evidence

| File | Must contain |
|---|---|
| `PROMPT_LOG.md` | Each material AI prompt: tool/model, prompt, what was used/changed/rejected, how verified. ≥2 "what AI got wrong / what I corrected" examples |
| `DECISIONS.md` | ≥3 non-trivial decisions: ambiguity, options considered, choice, trade-off (not decisions forced by the brief) |
| `DEBUGGING.md` | ≥2 real issues/failed assumptions: symptom, diagnosis, root cause, fix, verification |
| `README.md` | Setup/run instructions, architecture summary, known limitations, what you'd improve with more time |

**Commit history:** meaningful incremental commits — no single "assignment done" dump commit.

---

## 6. Submission Checklist

- [ ] GitHub repo with migrations + automated tests
- [ ] Seed/sample data or documented setup commands
- [ ] Concurrency test, re-enrollment lifecycle test, OTP edge-case tests
- [ ] `PROMPT_LOG.md`, `DECISIONS.md`, `DEBUGGING.md`, `README.md`
- [ ] Submitted within 24 hours

---

## 7. Evaluation Weighting

| Area | Weight |
|---|---|
| API/domain implementation | 35% |
| Correctness, security, constraints, automated tests | 30% |
| Engineering decisions & debugging | 15% |
| AI supervision & prompt log | 10% |
| Code quality & documentation | 10% |

**Reading the weights:** implementation + correctness/tests = 65% of the grade. Challenges A/B/C are where "correctness, security, constraints" is actually judged — prioritize these over extra endpoints.
