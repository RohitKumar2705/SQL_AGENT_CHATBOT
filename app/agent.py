"""A small LangGraph SQL agent, backed by a Groq LLM.

Flow: list tables -> fetch schema -> generate SQL -> double-check SQL ->
run SQL -> (loop back to generate SQL, or finish with a natural-language
answer once the model stops calling tools).
"""

import os
from typing import Literal

from langchain.messages import AIMessage
from langchain.tools import tool
from langchain_groq import ChatGroq
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from .database import get_connection

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

_model = None


def get_model() -> ChatGroq:
    """Lazily build the Groq chat model so the app can still start (and
    /api/health can still respond) even if GROQ_API_KEY isn't set yet."""
    global _model
    if _model is None:
        _model = ChatGroq(model=GROQ_MODEL, temperature=0)
    return _model


# --------------------------------------------------------------------------
# Tools (minimal wrappers around sqlite3 - not hardened for production use;
# scope your DB permissions narrowly if you point this at a real database).
# --------------------------------------------------------------------------


@tool
def sql_db_list_tables() -> str:
    """Input is an empty string, output is a comma-separated list of tables in the database."""
    con = get_connection()
    try:
        cursor = con.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]
        return ", ".join(tables)
    finally:
        con.close()


@tool
def sql_db_schema(table_names: str) -> str:
    """Input is a comma-separated list of tables, output is the schema and sample rows.
    Be sure the tables actually exist by calling sql_db_list_tables first.
    Example Input: table1, table2"""
    con = get_connection()
    try:
        cursor = con.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        valid_tables = {row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")}
        results = []
        for table in table_names.split(","):
            table = table.strip()
            if table not in valid_tables:
                results.append(f"Error: table {table!r} not found in database")
                continue
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?;", (table,))
            schema_row = cursor.fetchone()
            if schema_row:
                results.append(schema_row[0])
                try:
                    quoted = '"' + table.replace('"', '""') + '"'
                    cursor.execute(f"SELECT * FROM {quoted} LIMIT 3;")
                    rows = cursor.fetchall()
                    if rows:
                        cols = [d[0] for d in cursor.description]
                        sample = "\t".join(cols) + "\n" + "\n".join(
                            "\t".join(str(x) for x in row) for row in rows
                        )
                        results.append(f"/*\n3 rows from {table} table:\n{sample}\n*/")
                except Exception as e:  # noqa: BLE001
                    results.append(f"Error fetching sample rows: {e}")
        return "\n\n".join(results)
    finally:
        con.close()


@tool
def sql_db_query(query: str) -> str:
    """Input is a syntactically correct SQL query, output is the query result.
    If an error is returned, rewrite the query and try again. Only SELECT
    statements are allowed."""
    stripped = query.strip().lower()
    if not stripped.startswith("select"):
        return "Error: only SELECT statements are permitted."
    con = get_connection()
    try:
        cursor = con.cursor()
        cursor.execute(query)
        return str(cursor.fetchall())
    except Exception as e:  # noqa: BLE001
        return f"Error: {e}"
    finally:
        con.close()


get_schema_node = ToolNode([sql_db_schema], name="get_schema")
run_query_node = ToolNode([sql_db_query], name="run_query")


# --------------------------------------------------------------------------
# Graph nodes
# --------------------------------------------------------------------------


def list_tables(state: MessagesState):
    tool_call = {"name": "sql_db_list_tables", "args": {}, "id": "list_tables_call", "type": "tool_call"}
    tool_call_message = AIMessage(content="", tool_calls=[tool_call])
    tool_message = sql_db_list_tables.invoke(tool_call)
    response = AIMessage(f"Available tables: {tool_message.content}")
    return {"messages": [tool_call_message, tool_message, response]}


def call_get_schema(state: MessagesState):
    llm_with_tools = get_model().bind_tools([sql_db_schema], tool_choice="any")
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


GENERATE_QUERY_PROMPT = """You are an agent designed to interact with a SQL database.
Given an input question, create a syntactically correct SQLite query to run,
then look at the results and return a clear natural-language answer. Unless
the user specifies a number of results, limit your query to at most 5 rows.

Never query all columns from a table, only the relevant ones.
Never perform DML statements (INSERT, UPDATE, DELETE, DROP, etc.).
Format the final answer in clear Markdown. Use a short heading when helpful,
bullet lists for multiple records, and Markdown tables for compact tabular data.
"""


def generate_query(state: MessagesState):
    system_message = {"role": "system", "content": GENERATE_QUERY_PROMPT}
    llm_with_tools = get_model().bind_tools([sql_db_query])
    response = llm_with_tools.invoke([system_message] + state["messages"])
    return {"messages": [response]}


CHECK_QUERY_PROMPT = """You are a SQL expert with a strong attention to detail.
Double check the SQLite query for common mistakes, including:
- Using NOT IN with NULL values
- Using UNION when UNION ALL should have been used
- Using BETWEEN for exclusive ranges
- Data type mismatch in predicates
- Properly quoting identifiers
- Using the correct number of arguments for functions
- Casting to the correct data type
- Using the proper columns for joins

If there are mistakes, rewrite the query. Otherwise reproduce it as-is.
You will call the query tool to execute it right after this check.
"""


def check_query(state: MessagesState):
    system_message = {"role": "system", "content": CHECK_QUERY_PROMPT}
    tool_call = state["messages"][-1].tool_calls[0]
    user_message = {"role": "user", "content": tool_call["args"]["query"]}
    llm_with_tools = get_model().bind_tools([sql_db_query], tool_choice="any")
    response = llm_with_tools.invoke([system_message, user_message])
    response.id = state["messages"][-1].id
    return {"messages": [response]}


def should_continue(state: MessagesState) -> Literal["check_query", "__end__"]:
    last_message = state["messages"][-1]
    return END if not last_message.tool_calls else "check_query"


def build_agent():
    builder = StateGraph(MessagesState)
    builder.add_node(list_tables)
    builder.add_node(call_get_schema)
    builder.add_node(get_schema_node, "get_schema")
    builder.add_node(generate_query)
    builder.add_node(check_query)
    builder.add_node(run_query_node, "run_query")

    builder.add_edge(START, "list_tables")
    builder.add_edge("list_tables", "call_get_schema")
    builder.add_edge("call_get_schema", "get_schema")
    builder.add_edge("get_schema", "generate_query")
    builder.add_conditional_edges("generate_query", should_continue)
    builder.add_edge("check_query", "run_query")
    builder.add_edge("run_query", "generate_query")
    return builder.compile()


_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent


def ask_agent(question: str) -> str:
    agent = get_agent()
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    final_message = result["messages"][-1]
    return final_message.content
