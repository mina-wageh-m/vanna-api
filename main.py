from fastapi import FastAPI
from pydantic import BaseModel
import requests
import pymysql
import os

app = FastAPI()

# الإعدادات الخاصة بـ Vanna
# ملاحظة: الـ Model ID هو v00243-xk6 كما ظهر في صورك
VANNA_API_KEY = "vn-071c62b7ef4e4fe38fa7ae09a631dbee"
VANNA_MODEL = "v00243-xk6" 

# إعدادات قاعدة البيانات (MariaDB/MySQL)
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
    """وظيفة لتنفيذ الاستعلام المولد على قاعدة البيانات"""
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
            # إرجاع البيانات كـ List of Dictionaries لسهولة العرض في JSON
            return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()

@app.get("/")
def root():
    return {
        "status": "Vanna API is running!",
        "model_connected": VANNA_MODEL
    }

@app.post("/ask")
def ask(q: Question):
    try:
        # بناء الطلب بنظام JSON-RPC 2.0 المتوافق مع Vanna
        payload = {
            "method": "generate_sql",
            "params": [VANNA_MODEL, q.question],
            "jsonrpc": "2.0",
            "id": 1
        }

        response = requests.post(
            "https://ask.vanna.ai/rpc",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Vanna-Key": VANNA_API_KEY,
                "Vanna-Org": VANNA_MODEL
            }
        )
        
        result = response.json()
        
        # استخراج الـ SQL من رد Vanna
        # نظام الـ RPC بيرجع النتيجة في حقل اسمه 'result'
        sql = result.get("result", "")
        
        # التأكد من وجود خطأ في رد فاننا
        if "error" in result:
            return {
                "error": "Vanna RPC Error", 
                "details": result["error"], 
                "status": "error"
            }

        if not sql or "SELECT" not in sql.upper():
            return {
                "error": "No SQL generated", 
                "vanna_raw_response": result, 
                "status": "error"
            }

        # تنفيذ الـ SQL المولد وجلب البيانات الحقيقية
        data = run_sql(sql)
        
        return {
            "question": q.question,
            "sql": sql,
            "data": data,
            "status": "ok"
        }
        
    except Exception as e:
        return {"error": str(e), "status": "error"}