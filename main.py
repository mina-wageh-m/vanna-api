from fastapi import FastAPI
from pydantic import BaseModel
import requests
import pymysql

app = FastAPI()

VANNA_API_KEY = "vn-071c62b7ef4e4fe38fa7ae09a631dbee"
VANNA_MODEL = "virtu"

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "database": "_7fedefe90efce3c3",
    "user": "_7fedefe90efce3c3",
    "password": "tKPL3OWNsk0fmpNp"
}

DDL = """
CREATE TABLE `tabStudent` (
  `name` varchar(140) NOT NULL,
  `first_name` varchar(140) DEFAULT NULL,
  `middle_name` varchar(140) DEFAULT NULL,
  `last_name` varchar(140) DEFAULT NULL,
  `student_name` varchar(140) DEFAULT NULL,
  `joining_date` date DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `date_of_leaving` date DEFAULT NULL,
  `gender` varchar(140) DEFAULT NULL,
  `nationality` varchar(140) DEFAULT NULL,
  `student_email_id` varchar(140) DEFAULT NULL,
  `student_mobile_number` varchar(140) DEFAULT NULL,
  `enabled` int(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`name`)
)
"""

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

def vanna_request(method: str, params: list):
    response = requests.post(
        "https://ask.vanna.ai/rpc",
        headers={
            "Content-Type": "application/json",
            "Vanna-Key": VANNA_API_KEY,
            "Vanna-Org": VANNA_MODEL,
            "Vanna-Email": "mina.wageh.it@gmail.com"
        },
        json={"method": method, "params": params}
    )
    return response.json()

@app.get("/")
def root():
    return {"status": "Vanna API is running!"}

@app.get("/train")
def train():
    result = vanna_request("train", [{"ddl": DDL}])
    return {"status": "trained", "result": result}

@app.post("/ask")
def ask(q: Question):
    try:
        result = vanna_request("generate_sql", [{"question": q.question}])
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