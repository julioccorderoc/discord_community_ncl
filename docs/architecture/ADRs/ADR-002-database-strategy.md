# ADR-002: SUPABASE & SCHEMA-FIRST (NO ORM)

* **Date:** 2026-02-20
* **Status:** APPROVED

## 1. Context

The "Community OS" relies on relational data (Users -> Tickets -> Messages). Many Python projects default to ORMs (SQLAlchemy, Django). However, ORMs often introduce "lazy loading" performance hits (N+1 problem) and obscure the underlying data structure.

## 2. Decision

We will use the **Supabase Python Client (PostgREST)** wrapper combined with **Pydantic V2**.

* **Query Layer:** `supabase.table('users').select('*').eq('id', 1).execute()`
* **Validation:** `UserSchema.model_validate(response.data[0])`

## 3. Consequences (The "Why" for a Solo Dev)

### Positive

* **Velocity:** No writing raw SQL strings. The syntax is clean, Pythonic, and auto-completes in IDEs.
* **Safety:** The Supabase client handles parameterization automatically (Prevents SQL Injection).
* **Handover-Ready:** It is significantly easier for a new developer to read `table('users').select('*')` than to parse complex raw SQL strings inside Python code.

### Negative

* **Complex Queries:** Highly complex aggregations (Window functions) can be clunky in the client and may still require a Stored Procedure (Raw SQL) in Supabase.

## 4. Rule Extraction (The "How" for Agents)

* **Target File:** `docs/architecture/rules/db_rules.md`
* **Injected Constraint:**
    1. **Strict SQL Injection Protocol:** NEVER use f-strings to construct SQL queries. ALWAYS use parameterized queries (e.g., `await conn.execute("SELECT * FROM users WHERE id = $1", user_id)`).
    2. **Pydantic Validation:** Every database fetch must be wrapped in `Model.model_validate()` before passing to the business logic layer.
