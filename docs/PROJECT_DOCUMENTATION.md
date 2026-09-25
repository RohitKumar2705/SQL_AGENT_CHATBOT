# SQL Agent Chatbot Documentation

## 1. Project Overview

SQL Agent Chatbot is a natural-language interface for querying a company task database. A user asks a question in the web chat, and the application:

1. Lists the available SQLite tables.
2. Loads the database schema and sample rows.
3. Generates a read-only SQL query with Groq.
4. Reviews the generated query.
5. Executes the query against SQLite.
6. Returns a formatted answer in the chat interface.

The seeded database models company checklists, checklist items, employees, and task delegations.

For non-technical users, see the [User Manual](USER_MANUAL.md) for instructions
on asking questions and understanding chatbot responses.

## 2. Main Features

- Natural-language SQL questions
- Company checklist and delegation data
- 200+ seeded checklist item and delegation records
- Read-only SQL execution
- Markdown-style headings and lists
- Pipe-formatted query results rendered as HTML tables
- FastAPI REST API
- Static HTML, CSS, and JavaScript frontend
- Local and Docker/Render deployment support

## 3. Technology Stack

| Layer | Technology |
| --- | --- |
| Backend API | FastAPI |
| Agent workflow | LangGraph |
| LLM provider | Groq through `langchain-groq` |
| SQL database | SQLite |
| Frontend | HTML, CSS, JavaScript |
| Package management | uv or pip |
| Deployment | Docker and Render |

## 4. Project Structure

```text
sql-agent-chatbot/
├── app/
│   ├── __init__.py
│   ├── agent.py              # SQL tools and LangGraph workflow
│   ├── database.py           # SQLite schema, seed data, and connections
│   ├── main.py               # FastAPI routes and static file serving
│   └── static/
│       ├── index.html        # Chat page
│       ├── script.js         # API calls and table rendering
│       └── style.css         # Chat UI styles
├── data/
│   └── CompanyTasks.db       # Created automatically at runtime
├── docs/
│   └── PROJECT_DOCUMENTATION.md
├── Dockerfile
├── pyproject.toml
├── requirements.txt
├── .env.example
└── README.md
```

## 5. Prerequisites

- Python 3.11 or newer
- A Groq API key
- `uv` or `pip`
- Docker, only if building the container locally

## 6. Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
# Optional custom SQLite path
# DB_PATH=./data/CompanyTasks.db
```

`GROQ_MODEL` must be a model that is enabled for the Groq project and supports tool calling. If Groq returns `model_not_found`, select an available model in the Groq console and update this variable.

Never commit `.env` or a real API key to GitHub.

## 7. Use the Project Directly

Anyone can download and run this project from GitHub:

```bash
git clone https://github.com/RohitKumar2705/SQL_AGENT_CHATBOT.git
cd SQL_AGENT_CHATBOT
```

Create a `.env` file from the example and add a Groq API key:

```bash
cp .env.example .env
```

On Windows PowerShell, use:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and replace `your_groq_api_key_here` with a real key from the Groq Console. Then install and start the application:

```bash
uv sync
uv run uvicorn app.main:app --reload
```

Open the application at:

```text
http://127.0.0.1:8000
```

The database is created automatically on first use. No separate database server or SQLite installation is required.

To use the hosted Render version, open the deployed Render URL in a browser. The hosted service still requires the owner to configure `GROQ_API_KEY` and `GROQ_MODEL` in Render; visitors do not need the source code for browser use.

## 8. Local Installation

### Using uv

```bash
uv sync
uv run uvicorn app.main:app --reload
```

### Using pip

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` in a browser.

The first application request creates `data/CompanyTasks.db` if it does not exist. The database seed contains these tables:

```text
employees
checklists
checklist_items
delegations
```

## 9. Database Schema

### `employees`

Stores people who own, receive, or complete work.

| Column | Description |
| --- | --- |
| `employee_id` | Primary key |
| `name` | Employee name |
| `department` | Department name |
| `role` | Job role |
| `email` | Unique email address |

### `checklists`

Stores high-level department checklists.

| Column | Description |
| --- | --- |
| `checklist_id` | Primary key |
| `title` | Checklist title |
| `department` | Responsible department |
| `owner_id` | Employee responsible for the checklist |
| `due_date` | Checklist due date in ISO format |
| `status` | `Not started`, `In progress`, or `Completed` |

### `checklist_items`

Stores individual tasks inside a checklist.

| Column | Description |
| --- | --- |
| `item_id` | Primary key |
| `checklist_id` | Parent checklist |
| `task` | Task description |
| `assigned_to` | Assigned employee |
| `due_date` | Task due date |
| `status` | `Pending`, `In progress`, `Completed`, or `Blocked` |
| `priority` | `Low`, `Medium`, `High`, or `Critical` |
| `completed_at` | Completion date, when complete |

### `delegations`

Stores task delegation history.

| Column | Description |
| --- | --- |
| `delegation_id` | Primary key |
| `item_id` | Delegated checklist item |
| `delegated_by` | Employee who assigned the work |
| `delegated_to` | Employee receiving the work |
| `delegated_on` | Delegation date |
| `status` | `Assigned`, `Accepted`, `In progress`, `Completed`, or `Declined` |
| `notes` | Additional delegation details |

## 10. Example Questions

The following questions work with the seeded company database:

- Show all pending checklist tasks.
- Which employee has the most delegated tasks?
- List overdue delegations.
- Show checklist completion by department.
- List all critical tasks that are not completed.
- Which tasks are assigned to the IT department?
- Show the delegation status for each employee.
- Count completed checklist items by priority.

The agent should generate `SELECT` statements only. Data-changing SQL such as `INSERT`, `UPDATE`, `DELETE`, and `DROP` is rejected by the query tool.

## 11. API Reference

### Health check

```http
GET /api/health
```

Response:

```json
{"status":"ok"}
```

### Chat

```http
POST /api/chat
Content-Type: application/json
```

Request:

```json
{"message":"Show all pending checklist tasks"}
```

Response:

```json
{"reply":"...formatted answer from the agent..."}
```

Example with PowerShell:

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/api/chat `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"message":"List overdue delegations"}'
```

## 12. Agent Workflow

The workflow in `app/agent.py` is:

```text
User question
    |
    v
List SQLite tables
    |
    v
Load schema and sample rows
    |
    v
Generate SELECT query with Groq
    |
    v
Review query
    |
    v
Execute query
    |
    v
Generate final formatted answer
```

The application uses a direct SQLite schema-loading step before query generation. This avoids depending on the LLM to correctly call the schema tool when a model has strict tool-call validation.

## 13. Docker

Build and run locally:

```bash
docker build -t sql-agent-chatbot .
docker run --rm -p 8000:8000 `
  -e GROQ_API_KEY=your_groq_api_key_here `
  -e GROQ_MODEL=openai/gpt-oss-20b `
  sql-agent-chatbot
```

Then open `http://localhost:8000`.

The container listens on the `PORT` environment variable. Render supplies this variable automatically.

## 14. Render Deployment

1. Push the project to GitHub.
2. Create a Render Web Service connected to the repository.
3. Select Docker deployment.
4. Add these environment variables:

```text
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

5. Deploy the service.
6. Open the Render URL.
7. Check `https://your-render-url.onrender.com/api/health`.

After code changes:

```bash
git add .
git commit -m "Describe the change"
git push origin main
```

Then select **Manual Deploy** in Render if automatic deployment is disabled.

### SQLite persistence on Render

The default SQLite file is stored inside the running container. Without a persistent disk, data can be lost after a restart or redeploy. For persistent SQLite data, attach a Render Persistent Disk mounted at `/app/data` and use:

```env
DB_PATH=/app/data/CompanyTasks.db
```

For production multi-instance workloads, use a managed database instead of SQLite.

## 15. Troubleshooting

### `model_not_found`

The configured model is not available to the Groq project. Check the Models page in Groq Console, choose an enabled tool-calling model, and update `GROQ_MODEL` in Render.

### `Tool call validation failed`

Deploy the latest commit. The application loads the database schema directly before asking the model to generate SQL. Also verify that Render is using the expected branch and commit.

### `Unexpected token '<'` or HTML instead of JSON

The frontend received an HTML error page instead of the `/api/chat` JSON response. Check the Render service logs, confirm the service is running the latest commit, and hard-refresh the browser with `Ctrl+Shift+R`.

### `500 Internal Server Error`

Check:

- `GROQ_API_KEY` exists in Render
- `GROQ_MODEL` is enabled for the key's project
- The Render deployment completed successfully
- The Render logs for the original Python exception

### No database rows

Confirm that `DB_PATH` points to the intended SQLite file. If the path does not exist, the application creates and seeds a new company task database.

## 16. Security Notes

- Keep `GROQ_API_KEY` in environment variables, never in source code.
- The query tool permits only statements beginning with `SELECT`.
- Do not connect this demo directly to a production database without stronger authorization, auditing, query validation, and database permissions.
- Limit database credentials to read-only access when connecting to external data.
