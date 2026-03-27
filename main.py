from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pymysql
import os
import re
from vanna.remote import VannaDefault

app = FastAPI()

# Railway Variables
VANNA_MODEL = os.environ.get('VANNA_MODEL', 'virtu')
VANNA_API_KEY = os.environ.get('VANNA_API_KEY')

vn = VannaDefault(model=VANNA_MODEL, api_key=VANNA_API_KEY)

DB_CONFIG = {
    "host": "209.182.233.202",
    "port": 3306,
    "database": "_813e23c8a5386024",
    "user": "_813e23c8a5386024_remote",
    "password": "OTwspCMETxR442xV",
}

class Question(BaseModel):
    question: str

def is_safe_sql(sql: str) -> bool:
    sql_upper = sql.upper().strip()
    if not sql_upper.startswith("SELECT"):
        return False
    forbidden = ["DELETE", "DROP", "UPDATE", "INSERT", "TRUNCATE", "ALTER"]
    for word in forbidden:
        if re.search(rf'\b{word}\b', sql_upper):
            return False
    return True

def run_sql(sql: str):
    if not is_safe_sql(sql):
        raise HTTPException(status_code=403, detail="Unsafe SQL detected")
    conn = pymysql.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()

@app.get("/")
def root():
    return {"status": "API is running"}

@app.get("/train")
def train():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("SHOW TABLES LIKE 'tab%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        trained_list = []
        for table in tables:
            cursor.execute(f"SHOW CREATE TABLE `{table}`")
            res = cursor.fetchone()
            if res:
                ddl = res[1]
                vn.train(ddl=ddl)
                trained_list.append(table)
        
        conn.close()
        return {"status": "ok", "trained_on": trained_list}
    except Exception as e:
        return {"error": str(e), "status": "error"}

@app.post("/ask")
def ask(q: Question):
    try:
        sql = vn.generate_sql(q.question)
        sql = re.sub(r'```sql|```', '', sql).strip()
        data = run_sql(sql)
        return {
            "question": q.question,
            "sql": sql,
            "data": data,
            "status": "ok"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}