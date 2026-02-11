# Antigravity Engineering Rules

This skill enforces the Antigravity Engineering Rules for all projects. It covers technology profiles, naming conventions, directory structures, and best practices.

## Usage

This skill should be loaded when starting a new project or when ensuring compliance with Antigravity engineering standards.

## Rules

### 1. Language & Output
- **All explanations, comments, and documentation MUST be in Traditional Chinese (繁體中文).**
- Code identifiers (variables, functions, classes) MUST be in English.
- Pinyin naming is STRICTLY FORBIDDEN.
- Error messages, exceptions, logs, and print outputs MUST be in English.

### 2. Technology Profiles
**CRITICAL:** A project MUST follow EXACTLY ONE profile. No mixing.

#### Profile A: Backend/Frontend Separation (Default)
- **Use Case:** Enterprise systems, Microservices, Calculation-intensive tasks.
- **Frontend:** Vue 3 (Composition API) OR React 18 + TypeScript. Build tool: Vite.
- **Backend:** Python 3.11+, FastAPI (Default). REST/OpenAPI.
- **Database:** PostgreSQL / MySQL.
- **Structure:**
  - `backend/src/{api, core, domain, infra, utils}`
  - `frontend/src/{components, pages, services, stores}`
- **Constraints:**
  - Routers must not contain business logic.
  - Domain must not depend on Infra.
  - DB operations only in Repositories.

#### Profile B: Next.js Fullstack
- **Use Case:** SaaS, MVP, Prototype.
- **Stack:** Next.js 14 (App Router), TypeScript, TailwindCSS, Supabase.
- **Structure:** `app/`, `components/`, `lib/`, `supabase/`.
- **Constraints:**
  - App Router ONLY.
  - Server Components by default.
  - No direct Supabase Service Role Key usage in client.

#### Profile C: Static Web Page
- **Use Case:** Landing pages, Event pages, Demos.
- **Stack:** HTML5, TailwindCSS, Vanilla JS (ES2022+).
- **Constraints:** No frameworks (Vue/React). JS for interaction only.

#### Profile D: Odoo Customization
- **Use Case:** ERP Customization.
- **Stack:** Odoo 17.0 (Mandatory), Python 3.11+, PostgreSQL 15+.
- **Tools:** Docker, Odoo Studio.
- **Constraints:**
  - `snake_case` for modules.
  - Explicit `inherit_id` for views.
  - No hardcoded XML IDs in Python.
  - Author: 'Porter 規劃, Antigravity 執行'.

### 3. Naming Conventions
- **Variables/Functions:** `camelCase`
- **Classes/Components:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Files/Folders:** `kebab-case`

### 4. Windows Specifics
- Python scripts involving UI/Automation MUST handle Unicode encoding:
  ```python
  import sys, io
  if sys.platform == 'win32':
      sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
      sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
  ```

### 5. Project Declaration
- `README.md` MUST declare the profile:
  ```markdown
  ## Project Profile
  - Technology Profile: Profile A
  ```

## Instructions for AI
1. **Check Profile:** Determine which profile the current project belongs to. If unknown, ask the user or check `README.md`.
2. **Enforce Language:** Ensure all non-code text is in Traditional Chinese.
3. **Validate Structure:** specific file locations based on the profile.
4. **Code Review:** Check for naming conventions and Windows encoding fixes.
