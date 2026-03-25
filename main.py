from fastapi import FastAPI
from pydantic import BaseModel
import requests
import pymysql

app = FastAPI()

# تأكد إن الـ API Key ده هو اللي شغال
VANNA_API_KEY = "vn-071c62b7ef4e4fe38fa7ae09a631dbee"
# التعديل هنا: استخدم الـ Model ID الحقيقي اللي ظهر في الصور عندك
VANNA_MODEL = "v00243-xk6" 

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
        password=DB_CONFIG["password"]
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()

@app.get("/")
def root():
    return {"status": "Vanna API is running!", "model": VANNA_MODEL}

@app.post("/ask")
def ask(q: Question):
    try:
        # تعديل الـ RPC Call لتكون مطابقة لبروتوكول Vanna
        response = requests.post(
            "https://ask.vanna.ai/rpc",
            json={
                "method": "generate_sql",
                "params": [VANNA_MODEL, q.question] # الـ Params هنا لازم تشمل اسم الموديل والسؤال
            },
            headers={
                "Content-Type": "application/json",
                "Vanna-Key": VANNA_API_KEY
            }
        )
        
        result = response.json()
        
        # التأكد من استخراج الـ SQL صح
        sql = result.get("result", "")
        
        if not sql or "SELECT" not in sql.upper():
            # لو فشل، بنشوف الـ error اللي راجع من فاننا
            return {"error": "No SQL generated", "vanna_response": result, "status": "error"}

        data = run_sql(sql)
        return {
            "question": q.question,
            "sql": sql,
            "data": data,
            "status": "ok"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}