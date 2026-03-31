from fastapi import FastAPI
from pydantic import BaseModel
import pymysql
import anthropic
import os

app = FastAPI()

# يفضل دائمًا تخزين المفتاح في البيئة الافتراضية
client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

DB_CONFIG = {
    "host": "209.182.233.202",
    "port": 3306,
    "database": "_813e23c8a5386024",
    "user": "_813e23c8a5386024_remote",
    "password": "OTwspCMETxR442xV",
    "ssl_disabled": True
}

# 1. دي لستة بكل أسماء الجداول اللي عندك (بدون تكرار)
# تقدر تضيف هنا الـ 1000 جدول بتوع السيستم كلهم براحتك، مش هيحصل بطء لأننا بنبعت الأسماء بس مش الـ DDL كله!
ALL_SYSTEM_TABLES = [
    'tabStudent',
    'tabStudent Attendance',
    'tabStudent Group',
    'tabStudent Group Student',
    'tabStudent Guardian',
    'tabStudent Category',
    'tabStudent Leave Application',
    'tabStudent Log',
    'tabFees',
    'tabFee Structure',
    'tabFee Schedule',
    'tabFee Category',
    'tabFee Component',
    'tabFee Invoice',
    'tabCourse',
    'tabCourse Enrollment',
    'tabCourse Schedule',
    'tabProgram',
    'tabProgram Enrollment',
    'tabAcademic Year',
    'tabAcademic Term',
    'tabInstructor',
    'tabStudent Group Instructor',
    'tabAssessment Plan',
    'tabAssessment Result',
    'tabGrading Scale',
    'tabTimetable Periods',
    'tabRoom',
    'tabSection',
    'tabClass',
    'tabFee Invoice Batch',
    'tabFee Invoice Generator',
    'tabFee Invoice Batch Generated',
    'tabFee Invoice Generator Generated',
    'tabCB Cheque Bounce',
    'tabCB Student Wallet',
    'tabCB Wallet Transaction',
    'tabSales Invoice',
    'tabStudent Admission',
    'tabStudent Applicant',
    'tabStudent Certificate',
    'tabStudent Gate Pass',
    'tabStudent Siblings',
    'tabStudent Transportation',
    'tabStudent Language',
    'tabStudent Batch Name',
    'tabStudent Class Enrollment',
    'tabStudent LWI Log',
    'tabFee Group',
    'tabFee Head',
    'tabFee Template',
    'tabCB Concession Type',
    'tabCB Fee Payment Allocation',
    'tabCB Fee Refund Allocation',
    'tabStudy Material',
    'tabSchool Branch',
    'tabSchool House',
    'tabAttendance',
    'tabLeave Application',
    'tabLeave Type',
    'tabHoliday List',
    'tabHoliday',
    'tabEmployee',
    'tabDepartment',
    'tabDesignation',
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
        # --- الخطوة الأولى: نسأل الـ AI يختار الجداول المناسبة فقط ---
        tables_prompt = f"""You are a database router for an ERPNext school system.
Given this user question: "{q.question}"
And this list of available database tables in the system: {ALL_SYSTEM_TABLES}

Which tables from the list are needed to answer the question?
Return ONLY a comma-separated list of the table names, nothing else.
Example: tabStudent,tabStudent Group"""

        tables_response = client.messages.create(
            model="claude-3-5-sonnet-latest", # موديل ممتاز جداً في الـ SQL
            max_tokens=200,
            messages=[{"role": "user", "content": tables_prompt}]
        )

        selected_tables_text = tables_response.content[0].text.strip()
        # تنظيف الداتا والتأكد إن الجداول اللي اختارها موجودة فعلاً في اللستة بتاعتنا
        selected_tables = [t.strip() for t in selected_tables_text.split(",") if t.strip() in ALL_SYSTEM_TABLES]

        # لو الموديل فشل في اختيار جداول صح، بنخليه يبص على الجداول الأساسية كـ Default
        if not selected_tables:
            selected_tables = ['tabStudent', 'tabStudent Group']

        # --- الخطوة الثانية: جلب الـ DDL للجداول المختارة فقط من قاعدة البيانات ---
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

        # --- الخطوة الثالثة: توجيه الـ AI لإنشاء كود SQL دقيق ---
        sql_prompt = f"""You are a school database expert for an ERPNext system.
Given these specific database tables:
{specific_ddl}

Generate ONLY a MariaDB SQL query to answer the question: "{q.question}"

CRITICAL RULES:
1. Return ONLY the executable SQL query. Do not wrap it in ```sql and do not add any text before or after.
2. For text searching (like class names or student names), ALWAYS use `LIKE` with wildcards instead of exact matches `=`. For example: use `name LIKE '%SNS 11 A%'` instead of `name = 'SNS 11 A'`. This ensures we don't miss data due to minor spacing or naming differences.
3. In ERPNext, spaces in table names are represented with spaces, like `tabStudent Group`. Keep the backticks around table names: `tabStudent Group`.
"""

        sql_response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": sql_prompt}]
        )

        sql = sql_response.content[0].text.strip()

        # تنظيف الكود في حالة لو خالف التعليمات وحط Markdown
        sql = sql.replace("```sql", "").replace("```", "").strip()

        # تنفيذ كود الـ SQL الناتج
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

@app.get("/tables")
def tables():
    return {"tables_count": len(ALL_SYSTEM_TABLES)}