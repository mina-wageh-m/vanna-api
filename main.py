from fastapi import FastAPI
from pydantic import BaseModel
import requests
import pymysql

app = FastAPI()

VANNA_API_KEY = "vn-071c62b7ef4e4fe38fa7ae09a631dbee"
VANNA_MODEL = "virtu"

DB_CONFIG = {
    "host": "209.185.235.302",
    "port": 3306,
    "database": "_813eewc8a5386024",
    "user": "_813e23c8a53dfg86024@localhost",
    "password": "OTwspCMETxR442xVFG"
}

class Question(BaseModel):
    question: str

def run_sql(sql: str):
    conn = pymysql.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    return [dict(zip(columns, row)) for row in rows]

@app.get("/")
def root():
    return {"status": "Vanna API is running!"}

@app.post("/ask")
def ask(q: Question):
    try:
        response = requests.post(
            "https://ask.vanna.ai/rpc",
            headers={
                "Content-Type": "application/json",
                "Vanna-Key": VANNA_API_KEY,
                "Vanna-Org": VANNA_MODEL
            },
            json={
                "method": "generate_sql",
                "params": [{"question": q.question}]
            }
        )
        result = response.json()
        sql = result.get("result", {}).get("text", "")
        
        if not sql:
            return {"error": "No SQL generated", "status": "error"}
        
        data = run_sql(sql)
        return {
            "question": q.question,
            "sql": sql,
            "data": data,
            "status": "ok"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}