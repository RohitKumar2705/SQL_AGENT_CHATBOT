# SQL Agent Chatbot User Manual

## 1. What This Application Does

SQL Agent Chatbot lets you ask questions about company checklists and delegated tasks using normal language. You do not need to write SQL.

The chatbot can answer questions about:

- Employees and departments
- Checklists
- Checklist tasks
- Pending and completed work
- Task priorities
- Delegations and delegation status
- Due dates and overdue work

## 2. Quick Start for Non-Developers

The easiest way to use the chatbot is through the hosted website. You do not
need Python, Git, SQLite, or coding knowledge.

1. Open the chatbot website URL shared by the project owner.
2. Wait for the chat screen to load.
3. Click the message box at the bottom of the page.
4. Type a question, such as `Show all pending checklist tasks`.
5. Click **Send** or press Enter.
6. Read the answer. Multiple results are displayed in a table.
7. Ask another question using the same message box.

Do not enter a Groq API key or any password in the chat box. The project owner
configures the API key on the server.

## 3. Open the Application

### Hosted version

Open the Render URL provided by the project owner in your browser.

### Local version

Start the application, then open:

```text
http://127.0.0.1:8000
```

The application displays a chat window with a message box and a **Send** button.

## 4. Ask a Question

1. Type your question in the message box.
2. Click **Send** or press Enter.
3. Wait while the chatbot checks the database.
4. Read the answer in the response area.

You can ask another question at any time.

## 5. Example Questions

Start with one of these questions:

- Show all pending checklist tasks.
- List overdue delegations.
- Which employee has the most delegated tasks?
- Show checklist completion by department.
- List all critical tasks that are not completed.
- Which tasks are assigned to Liam Chen?
- Show all tasks for the Operations department.
- How many checklist items are completed?
- Which delegations are still in progress?
- Show tasks due before 2026-09-30.
- List blocked checklist tasks.
- Show the employees who received delegated work.

## 6. How to Ask Better Questions

Include the information you want to filter or compare:

| Instead of asking | Ask this way |
| --- | --- |
| Show tasks | Show pending tasks assigned to the IT department |
| Delegations | List in-progress delegations with employee names |
| Show checklist | Show completed checklist items by department |
| Late work | List tasks overdue before 2026-09-30 |
| Employee work | Count delegated tasks for each employee |

Useful details include:

- Status: pending, completed, blocked, or in progress
- Priority: low, medium, high, or critical
- Department: Operations, Finance, Human Resources, IT, or Sales
- Employee name
- Date or date range
- Number of results

For example:

```text
Show the 10 highest-priority pending tasks assigned to the Operations department.
```

## 7. Understanding the Response

The chatbot may return:

- A short explanation for a count or summary
- A bullet list for a small set of results
- A table for multiple records
- A note explaining that no matching records were found

Tables can contain columns such as:

- Checklist ID
- Task
- Employee
- Department
- Due date
- Priority
- Status
- Delegation status

On smaller screens, wide tables can be scrolled horizontally.

## 8. Company Data Available

The default database contains these types of information:

### Employees

Employee name, department, role, and email address.

### Checklists

Checklist title, department, owner, due date, and overall status.

### Checklist items

Individual task, assigned employee, due date, status, priority, and completion date.

### Delegations

Who delegated a task, who received it, delegation date, current status, and notes.

## 9. Status Meanings

### Checklist status

- **Not started**: No work has started on the checklist.
- **In progress**: At least some checklist work is underway.
- **Completed**: The checklist has been completed.

### Task status

- **Pending**: Work has not been completed.
- **In progress**: Work is currently underway.
- **Completed**: Work is finished.
- **Blocked**: Work cannot continue until an issue is resolved.

### Delegation status

- **Assigned**: Work was delegated but not yet accepted.
- **Accepted**: The recipient accepted the delegated work.
- **In progress**: The recipient is working on it.
- **Completed**: The delegated work is finished.
- **Declined**: The recipient declined the work.

## 10. Common Workflows

### Find pending work

Ask:

```text
Show all pending checklist tasks with their assignees and due dates.
```

### Find overdue work

Ask:

```text
List all incomplete tasks whose due date has passed.
```

### Review one employee

Ask:

```text
Show all tasks and delegations assigned to Maya Patel.
```

### Review a department

Ask:

```text
Show the number of completed, pending, and blocked tasks for each department.
```

### Review delegation workload

Ask:

```text
Rank employees by the number of tasks delegated to them.
```

## 11. API Use

Developers can send a question directly to the chat API.

### Request

```http
POST /api/chat
Content-Type: application/json
```

```json
{
  "message": "List overdue delegations"
}
```

### Response

```json
{
  "reply": "The formatted chatbot answer appears here."
}
```

Health check:

```http
GET /api/health
```

A healthy application returns:

```json
{"status":"ok"}
```

## 12. If Something Goes Wrong

### The answer says `model_not_found`

The application owner must configure a Groq model that is available to the Groq project. This is not a user input problem.

### The chatbot shows an error after sending a question

Try the question again. If it continues:

1. Refresh the page.
2. Check that the application is online.
3. Tell the project owner the exact question and error message.

### The response is slow

The chatbot sends the question to the language model, loads the database schema, and runs a SQL query. A short wait is normal.

### No records are found

Try a broader question, check the spelling of an employee name, or ask for available statuses and departments.

### A table is cut off

Scroll horizontally inside the table. This is expected for tables with many columns on a small screen.

## 13. Safety and Data Rules

- The chatbot is designed for questions and reports.
- It does not allow normal users to insert, update, or delete database records through chat.
- Do not enter passwords, API keys, or other secrets into the chat box.
- Answers are based only on the data available in the connected database.

## 14. Quick Reference

| Action | What to do |
| --- | --- |
| Open the app | Visit the hosted URL or local address |
| Ask a question | Type it in the message box |
| Submit | Click **Send** or press Enter |
| See many results | Read the formatted table |
| Narrow results | Add a status, employee, department, priority, or date |
| Report an issue | Share the exact error with the project owner |
