from fastapi import FastAPI
from pydantic import BaseModel
import pymysql
import anthropic
import os

app = FastAPI()

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

DB_CONFIG = {
    "host": "209.182.233.202",
    "port": 3306,
    "database": "_813e23c8a5386024",
    "user": "_813e23c8a5386024_remote",
    "password": "OTwspCMETxR442xV",
    "ssl_disabled": True
}

def get_relevant_tables(question: str):
    question_lower = question.lower()
    tables_to_fetch = set()

    # توزيع الـ 65 جدولاً بالكامل بدون حذف أي جدول
    keywords_mapping = {
        "fee": [
            'tabStudent', 'tabFees', 'tabFee Structure', 'tabFee Schedule',
            'tabFee Category', 'tabFee Component', 'tabFee Invoice',
            'tabFee Invoice Batch', 'tabFee Invoice Generator',
            'tabFee Invoice Batch Generated', 'tabFee Invoice Generator Generated',
            'tabFee Group', 'tabFee Head', 'tabFee Template'
        ],
        "invoice": [
            'tabStudent', 'tabFee Invoice', 'tabSales Invoice',
            'tabFee Invoice Batch', 'tabFee Invoice Generator'
        ],
        "wallet": [
            'tabStudent', 'tabCB Student Wallet',
            'tabCB Wallet Transaction', 'tabCB Cheque Bounce'
        ],
        "concession": [
            'tabCB Concession Type', 'tabCB Fee Payment Allocation',
            'tabCB Fee Refund Allocation'
        ],
        "attend": [
            'tabStudent', 'tabStudent Attendance',
            'tabAttendance', 'tabHoliday List', 'tabHoliday'
        ],
        "group": [
            'tabStudent', 'tabStudent Group', 'tabStudent Group Student',
            'tabStudent Group Instructor'
        ],
        "course": [
            'tabStudent', 'tabCourse', 'tabCourse Enrollment',
            'tabCourse Schedule', 'tabProgram', 'tabProgram Enrollment',
            'tabStudy Material'
        ],
        "assessment": [
            'tabStudent', 'tabAssessment Plan',
            'tabAssessment Result', 'tabGrading Scale'
        ],
        "class": [
            'tabStudent', 'tabClass', 'tabSection', 'tabRoom',
            'tabTimetable Periods', 'tabStudent Class Enrollment'
        ],
        "guardian": [
            'tabStudent', 'tabStudent Guardian', 'tabStudent Siblings'
        ],
        "employee": [
            'tabEmployee', 'tabDepartment', 'tabDesignation', 'tabInstructor'
        ],
        "leave": [
            'tabStudent', 'tabStudent Leave Application',
            'tabLeave Application', 'tabLeave Type'
        ],
        "admission": [
            'tabStudent Admission', 'tabStudent Applicant'
        ],
        "transport": [
            'tabStudent', 'tabStudent Transportation'
        ],
        "school": [
            'tabSchool Branch', 'tabSchool House',
            'tabAcademic Year', 'tabAcademic Term'
        ],
        # جداول إضافية لم يتم ذكرها بكلمات دلالية مباشرة، يتم تفعيلها بأسماء عامة
        "student": [
            'tabStudent', 'tabStudent Category', 'tabStudent Log',
            'tabStudent Certificate', 'tabStudent Gate Pass',
            'tabStudent Language', 'tabStudent Batch Name',
            'tabStudent LWI Log'
        ]
    }

    # جلب الجداول بناءً على الكلمات المفتاحية
    for key, tables in keywords_mapping.items():
        if key in question_lower:
            tables_to_fetch.update(tables)

    # إذا لم يجد أي كلمة مفتاحية، نمرر الجداول الأساسية (مثل الطلاب والرسوم والمجموعات)
    if not tables_to_fetch:
        tables_to_fetch.update([
            'tabStudent', 'tabStudent Group', 'tabFee Invoice',
            'tabFees', 'tabClass', 'tabAcademic Year'
        ])

    return list(tables_to_fetch)


def get_ddl_for_tables(tables_list):
    all_ddl = ""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        for table in tables_list:
            try:
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                row = cursor.fetchone()
                if row:
                    all_ddl += row[1] + ";\n\n"
            except:
                pass

        conn.close()
        return all_ddl
    except Exception as e:
        print(f"Database Connection Error: {e}")
        return ""


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
        relevant_tables = get_relevant_tables(q.question)
        DDL = get_ddl_for_tables(relevant_tables)

        system_training = f"""You are an expert in ERPNext (Frappe framework) databases.
Generate ONLY a MariaDB SQL query to answer the user's question.

CRITICAL RULES FOR ERPNEXT DATABASE:
1. Relationships are NOT defined by Foreign Keys.
2. Almost all tables have a primary key named `name` (which is a string, e.g., 'EDU-STU-2026-0001').
3. To link tables, use the specific Frappe 'Link' fields. For example:
   - In `tabFee Invoice`, the student is stored in the `student` column. To join with `tabStudent`, use: `FROM \`tabFee Invoice\` fi JOIN \`tabStudent\` s ON fi.student = s.name`
   - In `tabStudent Attendance`, use the `student` column to link with `tabStudent`.`name`.
4. Table names usually start with 'tab' (e.g., `tabStudent`, `tabFees`). Always wrap table names with backticks if they contain spaces.
5. ERPNext table and column names are case-sensitive.
6. When searching for classes or groups like "10 A", always use `LIKE '%10%'` because naming conventions in the database can vary.

Given these database tables:
{DDL}

Generate ONLY the SQL query, nothing else. No markdown, no explanation. Just the query."""

        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": system_training + f"\n\nQuestion: {q.question}"
            }]
        )

        sql = message.content[0].text.strip()
        sql = sql.replace("```sql", "").replace("```", "").strip()

        data = run_sql(sql)
        return {
            "question": q.question,
            "sql": sql,
            "data": data,
            "status": "ok",
            "tables_used": relevant_tables
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}

@app.get("/tables")
def tables():
    return {"message": "Use the /ask endpoint to dynamically load tables based on your query."}