from fastapi import FastAPI
from pydantic import BaseModel
import requests
import pymysql

app = FastAPI()

VANNA_API_KEY = "vn-071c62b7ef4e4fe38fa7ae09a631dbee"
VANNA_MODEL = "virtu"

DB_CONFIG = {
    "host": "209.182.233.202",
    "port": 3306,
    "database": "_813e23c8a5386024",
    "user": "_813e23c8a5386024_remote",
    "password": "OTwspCMETxR442xV"
}

class Question(BaseModel):
    question: str

def run_sql(sql: str):
    conn = pymysql.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        ssl_disabled=True
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
            "https://ask.vanna.ai/api/v0/chat_sse",
            headers={
                "VANNA-API-KEY": VANNA_API_KEY
            },
            data={
                "message": q.question,
                "user_email": "mina.wageh.it@gmail.com",
                "acceptable_responses": '["sql"]'
            },
            stream=True
        )
        
        import json
        lines = []
        sql = None
        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                lines.append(decoded)
                if decoded.startswith("data:"):
                    try:
                        event = json.loads(decoded[5:].strip())
                        if event.get('type') == 'sql':
                            sql = event.get('query', '')
                    except:
                        pass
        
        if not sql:
            return {"error": "No SQL generated", "raw_response": lines, "status": "error"}
        
        data = run_sql(sql)
        return {
            "question": q.question,
            "sql": sql,
            "data": data,
            "status": "ok"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}