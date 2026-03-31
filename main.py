from fastapi import FastAPI
from pydantic import BaseModel
import pymysql
import anthropic
import os
from contextlib import asynccontextmanager

# Global variable to hold the full schema in memory
FULL_SCHEMA_TEXT = ""

DB_CONFIG = {
    "host": "209.182.233.202",
    "port": 3306,
    "database": "_813e23c8a5386024",
    "user": "_813e23c8a5386024_remote",
    "password": "OTwspCMETxR442xV",
    "ssl_disabled": True
}

# Lifespan event to load the schema file once when the server starts
@asynccontextmanager
async def lifespan(app: FastAPI):
    global FULL_SCHEMA_TEXT
    print("⏳ Loading schema file into memory...")
    try:
        # Read the file from the root directory of your project
        with open("erpnext_schema.txt", "r", encoding="utf-8") as f:
            FULL_SCHEMA_TEXT = f.read()
        print("✅ Schema file loaded successfully!")
    except Exception as e:
        print(f"❌ Failed to read schema file: {e}")
    yield

app = FastAPI(lifespan=lifespan)
client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

class Question(BaseModel):
    question: str

def run_sql(sql: str):
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    return [dict(zip(columns, row)) for row in rows]

@app.post("/ask")
def ask(q: Question):
    try:
        # Claude will see all tables at once without filtering
        system_training = f"""You are an expert in ERPNext (Frappe framework) databases.
Generate ONLY a MariaDB SQL query to answer the user's question.

CRITICAL RULES FOR ERPNEXT DATABASE:
1. Relationships are NOT defined by Foreign Keys.
2. Almost all tables have a primary key named `name` (which is a string, e.g., 'EDU-STU-2026-0001').
3. To link tables, use the specific Frappe 'Link' fields.
4. Table names usually start with 'tab'. Always wrap table names with backticks if they contain spaces.
5. ERPNext table and column names are case-sensitive.
6. When searching for classes or groups like "10 A", always use `LIKE '%10%'`.

Given these database tables:
{FULL_SCHEMA_TEXT}

Generate ONLY the SQL query, nothing else. No markdown, no explanation."""

        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            messages=[{"role": "user", "content": system_training + f"\n\nQuestion: {q.question}"}]
        )

        sql = message.content[0].text.strip()
        sql = sql.replace("```sql", "").replace("```", "").strip()

        data = run_sql(sql)
        return {
            "question": q.question,
            "sql": sql,
            "data": data,
            "status": "ok"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}