from fastapi import FastAPI
from pydantic import BaseModel
import pymysql
import anthropic
import os

app = FastAPI()

# الموديل الرسمي والمستقر حالياً من Anthropic
CLAUDE_MODEL = "claude-3-5-sonnet-20240620"

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

DB_CONFIG = {
    "host": "209.182.233.202",
    "port": 3306,
    "database": "_813e23c8a5386024",
    "user": "_813e23c8a5386024_remote",
    "password": "OTwspCMETxR442xV",
    "ssl_disabled": True
}

ALL_SYSTEM_TABLES = [
    'tabStudent', 'tabStudent Attendance', 'tabStudent Group',
    'tabStudent Group Student', 'tabStudent Guardian', 'tabStudent Category',
    'tabStudent Leave Application', 'tabStudent Log', 'tabFees',
    'tabFee Structure', 'tabFee Schedule', 'tabFee Category',
    'tabFee Component', 'tabFee Invoice', 'tabCourse',
    'tabCourse Enrollment', 'tabCourse Schedule', 'tabProgram',
    'tabProgram Enrollment', 'tabAcademic Year', 'tabAcademic Term',
    'tabInstructor', 'tabStudent Group Instructor', 'tabAssessment Plan',
    'tabAssessment Result', 'tabGrading Scale', 'tabTimetable Periods',
    'tabRoom', 'tabSection', 'tabClass', 'tabFee Invoice Batch',
    'tabFee Invoice Generator', 'tabFee Invoice Batch Generated',
    'tabFee Invoice Generator Generated', 'tabCB Cheque Bounce',
    'tabCB Student Wallet', 'tabCB Wallet Transaction', 'tabSales Invoice',
    'tabStudent Admission', 'tabStudent Applicant', 'tabStudent Certificate',
    'tabStudent Gate Pass', 'tabStudent Siblings', 'tabStudent Transportation',
    'tabStudent Language', 'tabStudent Batch Name', 'tabStudent Class Enrollment',
    'tabStudent LWI Log', 'tabFee Group', 'tabFee Head', 'tabFee Template',
    'tabCB Concession Type', 'tabCB Fee Payment Allocation',
    'tabCB Fee Refund Allocation', 'tabStudy Material', 'tabSchool Branch',
    'tabSchool House', 'tabAttendance', 'tabLeave Application',
    'tabLeave Type', 'tabHoliday List', 'tabHoliday', 'tabEmployee',
    'tabDepartment', 'tabDesignation',
]

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
        # --- الخطوة الأولى: اختيار الجداول ---
        tables_prompt = f"""You are a database router for an ERPNext school system.
Given this user question: "{q.question}"
And this list of available database tables in the system: {ALL_SYSTEM_TABLES}

Which tables from the list are needed to answer the question?
Return ONLY a comma-separated list of the table names, nothing else."""

        tables_response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": tables_prompt}]
        )

        selected_tables_text = tables_response.content[0].text.strip()
        selected_tables = [t.strip() for t in selected_tables_text.split(",") if t.strip() in ALL_SYSTEM_TABLES]

        if not selected_tables:
            selected_tables = ['tabStudent', 'tabStudent Group']

        # --- الخطوة الثانية: جلب الـ DDL ---
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        specific_ddl = ""
        for table in selected_tables:
            try:
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                row = cursor.fetchone()
                if row:
                    specific_ddl += row[1] + ";\n\n"
            except Exception:
                pass
        conn.close()

        # --- الخطوة الثالثة: إنشاء SQL ---
        sql_prompt = f"""You are a school database expert for an ERPNext system.
Given these specific database tables:
{specific_ddl}

Generate ONLY a MariaDB SQL query to answer the question: "{q.question}"

CRITICAL RULES:
1. Return ONLY the executable SQL query. Do not wrap it in ```sql and do not add any text before or after.
2. For text searching (like class names or student names), ALWAYS use `LIKE` with wildcards instead of exact matches `=`. For example: use `name LIKE '%SNS 11 A%'` instead of `name = 'SNS 11 A'`.
3. Keep the backticks around table names: `tabStudent Group`.
"""

        sql_response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": sql_prompt}]
        )

        sql = sql_response.content[0].text.strip()
        sql = sql.replace("```sql", "").replace("```", "").strip()

        data = run_sql(sql)

        return {
            "question": q.question,
            "selected_tables": selected_tables,
            "sql": sql,
            "data": data,
            "status": "ok"
        }

    except Exception as e:
        return {"error": str(e), "status": "error"}