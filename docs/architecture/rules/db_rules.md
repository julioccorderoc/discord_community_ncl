# DATABASE RULES

Extracted from **ADR-002** (Supabase & Schema-First, No ORM). These are hard constraints for all agents working on data access.

---

## 1. Core DB Conventions

**Decision:** We use the **Supabase Python client (PostgREST)** as the query layer. No ORM.

- **No ORM:** Never import `sqlalchemy`, `tortoise`, `django.db`, or any ORM library. The Supabase client is the only allowed query interface.
- **Client Singleton:** The Supabase client is initialized **once** in `src/database/client.py` and imported wherever needed. Never instantiate a new client inside a service function.
- **Supabase client syntax:**

    ```python
    # ✅ CORRECT: Use the PostgREST client
    response = supabase.table("discord_users").select("*").eq("discord_id", user_id).execute()

    # ❌ WRONG: Raw SQL strings in Python code
    response = supabase.rpc("SELECT * FROM discord_users WHERE discord_id = ...")
    ```

- **Complex aggregations** that cannot be expressed cleanly in the client (e.g., window functions for Churn Radar, weekly score comparisons) must be implemented as **Supabase Stored Procedures (RPC)**, then called via `supabase.rpc("function_name", params)`.

---

## 2. SQL Injection Protocol

**Rule:** User-controlled data must NEVER be concatenated into a query string.

- **Forbidden:** f-strings, `.format()`, or `%` interpolation to build queries.
- **Required:** Use the Supabase client's built-in filter methods, which parameterize automatically.

    ```python
    # ❌ NEVER DO THIS — SQL Injection risk
    supabase.table("tickets").select("*").filter(f"author_id = {user_id}").execute()

    # ✅ ALWAYS DO THIS — Parameterized via client API
    supabase.table("tickets").select("*").eq("author_id", user_id).execute()
    ```

- For **raw SQL via Supabase RPC**, pass parameters as a dictionary argument — never interpolate:

    ```python
    # ✅ CORRECT: Parameters passed separately
    supabase.rpc("get_user_score", {"p_user_id": user_id, "p_days": 7}).execute()
    ```

---

## 3. The "Service Layer" Pattern (Critical for Streamlit)

**Context:** Streamlit scripts re-run from top to bottom on every interaction. Embedding database logic directly in the UI code (`dashboard.py`) makes the app unmaintainable and hard to test.

**Rule:**

1. **Zero UI-DB Coupling:** NEVER write `supabase.table(...)` calls inside `src/dashboard/`.
2. **The Service Boundary:** All data fetching must happen in `src/services/` (e.g., `data_service.py` or `user_service.py`).
3. **Pydantic Return Types:** Service functions must return Pydantic Models or typed Lists, never raw API dictionaries.

**Example:**

- ❌ **BAD (Inside `dashboard.py`):**

    ```python
    # Violates Separation of Concerns
    data = supabase.table("users").select("*").execute()
    st.dataframe(data.data)
    ```

- ✅ **GOOD:**
  - *Inside `src/services/user_service.py`:*

    ```python
    def get_active_users() -> List[User]:
        response = supabase.table("users").select("*").execute()
        return [User(**item) for item in response.data]
    ```

  - *Inside `dashboard.py`:*

    ```python
    users = get_active_users()
    st.dataframe(users)
    ```

---

## 4. Pydantic Validation at the Boundary

Every row returned from a database call must be validated through a Pydantic model before it enters business logic. This catches schema drift early.

```python
# ✅ CORRECT: Validate at the DB boundary
response = supabase.table("discord_users").select("*").eq("discord_id", user_id).single().execute()
user = DiscordUser.model_validate(response.data)

# ❌ WRONG: Passing raw dict into business logic
user = response.data  # This is an untyped dict — do not pass downstream
```

For list responses:

```python
# ✅ CORRECT
users = [DiscordUser.model_validate(row) for row in response.data]
```
