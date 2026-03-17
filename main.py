from fastapi import FastAPI
from pydantic import BaseModel
import requests

app = FastAPI()

VANNA_API_KEY = "vn-071c62b7ef4e4fe38fa7ae09a631dbee"
VANNA_MODEL = "virtu"

class Question(BaseModel):
    question: str

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
        return {
            "question": q.question,
            "sql": result.get("result", {}).get("text", ""),
            "status": "ok"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}