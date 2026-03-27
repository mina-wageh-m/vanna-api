from fastapi import FastAPI
from pydantic import BaseModel
import pymysql
import anthropic
import os

app = FastAPI()

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

DB_CONFIG = {
    "host": "209.182.233.202",
    "port": 3306,
    "database": "_813e23c8a5386024",
    "user": "_813e23c8a5386024_remote",
    "password": "OTwspCMETxR442xV",
    "ssl_disabled": True
}

DDL = """
CREATE TABLE `tabStudent` (
  `name` varchar(140) NOT NULL,
  `first_name` varchar(140) DEFAULT NULL,
  `last_name` varchar(140) DEFAULT NULL,
  `student_name` varchar(140) DEFAULT NULL,
  `enabled` int(1) NOT NULL DEFAULT 1,
  `cb_student_status` varchar(140) DEFAULT 'Active',
  `current_class` varchar(140) DEFAULT NULL,
  `current_program` varchar(140) DEFAULT NULL,
  `admission_date` date DEFAULT NULL,
  `date_of_leaving` date DEFAULT NULL,
  PRIMARY KEY (`name`)
)
"""

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

@app.get("/")
def root():
    return {"status": "API is running!"}

@app.post("/ask")
def ask(q: Question):
    try:
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"""Given this database table:
{DDL}

Generate ONLY a SQL query to answer: {q.question}
Return ONLY the SQL query, nothing else."""
            }]
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
    
    @app.get("/train")
    def train():
        try:
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            
            all_ddl = ""
            for table in tables:
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                row = cursor.fetchone()
                if row:
                    all_ddl += row[1] + ";\n\n"
            
            conn.close()
            return {"tables": tables, "ddl": all_ddl, "status": "ok"}
        except Exception as e:
            return {"error": str(e), "status": "error"}