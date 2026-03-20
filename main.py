from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json
import pymysql

app = FastAPI()

VANNA_API_KEY = "vn-071c62b7ef4e4fe38fa7ae09a631dbee"
VANNA_URL = "https://ask.vanna.ai/api/v0/chat_sse"

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "database": "_7fedefe90efce3c3",
    "user": "_7fedefe90efce3c3",
    "password": "tKPL3OWNsk0fmpNp"
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

def ask_vanna(question: str):
    headers = {
        "Content-Type": "application/json",
        "VANNA-API-KEY": VANNA_API_KEY
    }
    data = {
        "message": question,
        "user_email": "mina.wageh.it@gmail.com",
        "acceptable_responses": ["sql", "text"]
    }
    response = requests.post(
        VANNA_URL,
        headers=headers,
        data=json.dumps(data),
        stream=True
    )
    sql = None
    for line in response.iter_lines():
        if line:
            decoded = line.decode('utf-8')
            if decoded.startswith("data:"):
                try:
                    event = json.loads(decoded[5:].strip())
                    if event.get('type') == 'sql':
                        sql = event.get('query', '')
                except:
                    pass
    return sql

@app.get("/")
def root():
    return {"status": "Vanna API is running!"}

@app.post("/ask")
def ask(q: Question):
    try:
        sql = ask_vanna(q.question)
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