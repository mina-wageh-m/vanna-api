from fastapi import FastAPI
from pydantic import BaseModel
from vanna import VannaDefault

app = FastAPI()

vn = VannaDefault(
    model='virtu',
    api_key='vn-071c62b7ef4e4fe38fa7ae09a631dbee'
)

class Question(BaseModel):
    question: str

@app.get("/")
def root():
    return {"status": "Vanna API is running!"}

@app.post("/ask")
def ask(q: Question):
    try:
        sql = vn.generate_sql(q.question)
        return {
            "question": q.question,
            "sql": sql,
            "status": "ok"
        }
    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }