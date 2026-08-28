# DECISIONS.md

## Non‑Trivial Engineering Decisions

This document outlines the key architectural and implementation decisions made during development of the Events Platform, focusing on the three core engineering challenges (A, B, C).

---

### Decision 1: Challenge A – Concurrency Protection Strategy

**Problem:**  
Event capacity must never be exceeded, even under high concurrency (e.g., 5 simultaneous enrollment attempts when only 1 spot remains). A naive check‑then‑act pattern would allow race conditions.

**Options Considered:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **Optimistic Locking** | Use a version field on `Event`; retry on conflict | No DB locks, works in all databases | Requires retry logic, complexity in tests |
| **Database Unique Constraint** | Pre‑fill enrollment records; enforce capacity via count | Simple, DB‑enforced | Cannot dynamically cap without pre‑allocating slots |
| **Application‑Level Mutex** | Use Python `threading.Lock` | Simple | Only works in single‑process; useless in production |
| **`select_for_update()` with Transaction** | Lock the event row during capacity check + creation | Atomic, reliable, PostgreSQL native | Locks the row; not supported by SQLite |

**Chosen Approach:**  
`select_for_update()` inside a `transaction.atomic()` block.

**Trade‑offs:**
- **Performance:** Row‑level locking serialises concurrent requests, reducing throughput under heavy load. For this system, the trade‑off is acceptable because enrollment is not expected to be a massive‑scale operation.
- **Database Dependency:** Works perfectly with PostgreSQL; with SQLite it is ignored. The assignment recommends PostgreSQL, and the application logic still prevents over‑enrollment in SQLite for most practical scenarios (though not guaranteed in extreme concurrency).
- **Simplicity:** No retry logic or complex error handling is required – the database handles queueing naturally.

---

### Decision 2: Challenge B – Re‑enrollment Lifecycle & Constraint Design

**Problem:**  
A seeker should be able to enroll, cancel, and later re‑enroll in the same event. A simple `UNIQUE(event, seeker)` constraint would prevent re‑enrollment because the canceled record would still exist, blocking a new insertion.

**Options Considered:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **Hard Delete on Cancel** | Delete the enrollment record entirely | Simpler constraint | Loses audit trail; cannot distinguish canceled from never enrolled |
| **Separate "Active" Table** | Move canceled records to a history table | Clean separation of active/historical data | Extra complexity, duplicate schema |
| **Soft Delete + UniqueConstraint with Condition** | Keep the record; enforce uniqueness only for `status='enrolled'` | Preserves history, simple querying | PostgreSQL‑specific (conditional indexes), but falls back to app logic in SQLite |
| **Application‑Only Check** | Check existence of any enrollment before allowing new one | DB agnostic | Race conditions possible without DB‑level enforcement |

**Chosen Approach:**  
`UniqueConstraint(fields=['event','seeker'], condition=Q(status='enrolled'))` in the `Enrollment` model.

**Trade‑offs:**
- **PostgreSQL Dependency:** Conditional unique constraints are fully supported only in PostgreSQL. For SQLite, Django creates a partial index only if supported; otherwise the constraint is ignored. We mitigated this with an application‑level check that prevents duplicate active enrollments even without the constraint.
- **Audit Trail:** The `status` field acts as a soft‑delete flag, preserving the full history of each seeker–event relationship.
- **Re‑enrollment Logic:** The view checks for an existing `canceled` record and reactivates it (updates `status` to `enrolled`) instead of creating a new one. This ensures that the unique constraint is never violated and no duplicate records are created.

---

### Decision 3: Challenge C – OTP Resend Policy

**Scenario:**  
OTP1 requested, 30s later OTP2 requested, user submits OTP1. Should OTP1 still be valid?

**Options Considered:**

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **OTP1 Remains Valid** | All generated OTPs are valid until expiry | Simple, user‑friendly | Increases attack surface; resend could be used to generate many valid OTPs |
| **OTP1 is Invalidated** | Resend marks all previous OTPs as used/expired | More secure, reduces abuse | User might be confused if they try the old one |
| **Multiple Valid OTPs with Short TTL** | Limit to 2 concurrent OTPs, both valid for 1 minute | Balances security and usability | More complex, still leaves a small window for abuse |

**Chosen Approach:**  
Resend invalidates all previous OTPs (sets `is_used=True` or expires them). The new OTP is the only valid one.

**Trade‑offs:**
- **Security:** This is the safest option – an attacker cannot use an intercepted old OTP after a resend.
- **User Experience:** If a user requests a resend and later tries the old OTP, they will get an error. This is acceptable because the resend was intentionally requested, and the user is informed via email that a new OTP has been sent.
- **Implementation:** Simple – just mark old OTPs as expired when a new one is generated.
- **Cooldown:** A 30‑second cooldown is enforced between resends to prevent abuse, returning `429 Too Many Requests` if violated.

---

### Additional Supporting Decisions

- **Email as Username:**  
  We use the `email` field as the username (via `USERNAME_FIELD` or by populating `username` with the email). This simplifies login and aligns with modern authentication patterns.

- **OTP Hash Storage:**  
  OTPs are hashed using Django’s `make_password` before storage. This ensures that even if the database is compromised, the OTPs cannot be recovered – an explicit requirement of Challenge C.

- **Error Response Shape:**  
  All custom views return errors in the format `{"detail": "...", "code": "..."}`. This provides a consistent, machine‑readable error structure for the frontend.

- **Pagination:**  
  DRF’s `PageNumberPagination` is used, returning `count`, `next`, `previous`, and `results` – as required by the brief.

---

### Summary

| Challenge | Decision | Rationale |
|-----------|----------|-----------|
| A – Concurrency | `select_for_update()` with transaction | Atomic, reliable, minimal code; PostgreSQL recommended |
| B – Re‑enrollment | Conditional unique constraint | Preserves history, enables soft‑delete + reactivation |
| C – OTP Resend | Resend invalidates old OTPs | Maximises security; user experience is acceptable given the context |