from fastapi import FastAPI
from pydantic import BaseModel
import pymysql
import anthropic
import os
from contextlib import asynccontextmanager

# قاموس عالمي (Global Dictionary) هنخزن فيه الـ DDL لكل جدول في الميموري
CACHED_DDL = {}

# قائمة الـ 65 جدول بتوعك كاملين
ALL_TABLES = [
    'tabStudent', 'tabStudent Attendance', 'tabStudent Group', 'tabStudent Group Student',
    'tabStudent Guardian', 'tabStudent Category', 'tabStudent Leave Application', 'tabStudent Log',
    'tabFees', 'tabFee Structure', 'tabFee Schedule', 'tabFee Category', 'tabFee Component',
    'tabFee Invoice', 'tabCourse', 'tabCourse Enrollment', 'tabCourse Schedule', 'tabProgram',
    'tabProgram Enrollment', 'tabAcademic Year', 'tabAcademic Term', 'tabInstructor',
    'tabStudent Group Instructor', 'tabAssessment Plan', 'tabAssessment Result', 'tabGrading Scale',
    'tabTimetable Periods', 'tabRoom', 'tabSection', 'tabClass', 'tabFee Invoice Batch',
    'tabFee Invoice Generator', 'tabFee Invoice Batch Generated', 'tabFee Invoice Generator Generated',
    'tabCB Cheque Bounce', 'tabCB Student Wallet', 'tabCB Wallet Transaction', 'tabSales Invoice',
    'tabStudent Admission', 'tabStudent Applicant', 'tabStudent Certificate', 'tabStudent Gate Pass',
    'tabStudent Siblings', 'tabStudent Transportation', 'tabStudent Language', 'tabStudent Batch Name',
    'tabStudent Class Enrollment', 'tabStudent LWI Log', 'tabFee Group', 'tabFee Head',
    'tabFee Template', 'tabCB Concession Type', 'tabCB Fee Payment Allocation', 'tabCB Fee Refund Allocation',
    'tabStudy Material', 'tabSchool Branch', 'tabSchool House', 'tabAttendance', 'tabLeave Application',
    'tabLeave Type', 'tabHoliday List', 'tabHoliday', 'tabEmployee', 'tabDepartment', 'tabDesignation'
]

DB_CONFIG = {
    "host": "209.182.233.202",
    "port": 3306,
    "database": "_813e23c8a5386024",
    "user": "_813e23c8a5386024_remote",
    "password": "OTwspCMETxR442xV",
    "ssl_disabled": True
}

# دالة بتشتغل مرة واحدة بس لما السيرفر يفتح عشان "تحفظ" الجداول
def load_all_ddl_to_memory():
    print("⏳ جاري جلب هياكل الجداول وحفظها في الذاكرة المسبقة...")
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        for table in ALL_TABLES:
            try:
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                row = cursor.fetchone()
                if row:
                    # بنخزن الـ DDL في القاموس باسم الجدول
                    CACHED_DDL[table] = row[1] + ";\n\n"
            except:
                pass
        conn.close()
        print(f"✅ تم حفظ {len(CACHED_DDL)} جدول بنجاح في الذاكرة!")
    except Exception as e:
        print(f"❌ فشل الاتصال بقاعدة البيانات أثناء التشغيل: {e}")

# إدارة دورة حياة التطبيق (Lifespan) في FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # كود يشتغل عند بدء السيرفر
    load_all_ddl_to_memory()
    yield
    # كود يشتغل عند قفل السيرفر (لو محتاج تقفل اتصالات مثلاً)

app = FastAPI(lifespan=lifespan)
client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

# نفس الدالة الذكية لفلترة الجداول حسب السؤال (عشان نوفر Tokens)
def get_relevant_tables(question: str):
    question_lower = question.lower()
    tables_to_fetch = set()

    keywords_mapping = {
        "fee": ['tabStudent', 'tabFees', 'tabFee Structure', 'tabFee Schedule', 'tabFee Category', 'tabFee Component', 'tabFee Invoice', 'tabFee Invoice Batch', 'tabFee Invoice Generator', 'tabFee Invoice Batch Generated', 'tabFee Invoice Generator Generated', 'tabFee Group', 'tabFee Head', 'tabFee Template'],
        "invoice": ['tabStudent', 'tabFee Invoice', 'tabSales Invoice', 'tabFee Invoice Batch', 'tabFee Invoice Generator'],
        "wallet": ['tabStudent', 'tabCB Student Wallet', 'tabCB Wallet Transaction', 'tabCB Cheque Bounce'],
        "concession": ['tabCB Concession Type', 'tabCB Fee Payment Allocation', 'tabCB Fee Refund Allocation'],
        "attend": ['tabStudent', 'tabStudent Attendance', 'tabAttendance', 'tabHoliday List', 'tabHoliday'],
        "group": ['tabStudent', 'tabStudent Group', 'tabStudent Group Student', 'tabStudent Group Instructor'],
        "course": ['tabStudent', 'tabCourse', 'tabCourse Enrollment', 'tabCourse Schedule', 'tabProgram', 'tabProgram Enrollment', 'tabStudy Material'],
        "assessment": ['tabStudent', 'tabAssessment Plan', 'tabAssessment Result', 'tabGrading Scale'],
        "class": ['tabStudent', 'tabClass', 'tabSection', 'tabRoom', 'tabTimetable Periods', 'tabStudent Class Enrollment'],
        "guardian": ['tabStudent', 'tabStudent Guardian', 'tabStudent Siblings'],
        "employee": ['tabEmployee', 'tabDepartment', 'tabDesignation', 'tabInstructor'],
        "leave": ['tabStudent', 'tabStudent Leave Application', 'tabLeave Application', 'tabLeave Type'],
        "admission": ['tabStudent Admission', 'tabStudent Applicant'],
        "transport": ['tabStudent', 'tabStudent Transportation'],
        "school": ['tabSchool Branch', 'tabSchool House', 'tabAcademic Year', 'tabAcademic Term'],
        "student": ['tabStudent', 'tabStudent Category', 'tabStudent Log', 'tabStudent Certificate', 'tabStudent Gate Pass', 'tabStudent Language', 'tabStudent Batch Name', 'tabStudent LWI Log']
    }

    for key, tables in keywords_mapping.items():
        if key in question_lower:
            tables_to_fetch.update(tables)

    if not tables_to_fetch:
        tables_to_fetch.update(['tabStudent', 'tabStudent Group', 'tabFee Invoice', 'tabFees', 'tabClass', 'tabAcademic Year'])

    return list(tables_to_fetch)

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

@app.post("/ask")
def ask(q: Question):
    try:
        relevant_tables = get_relevant_tables(q.question)

        # 🔥 هنا السحر! مش بنروح لقاعدة البيانات.. بنجيب الـ DDL من الـ Memory فوراً
        DDL = ""
        for table in relevant_tables:
            if table in CACHED_DDL:
                DDL += CACHED_DDL[table]

        system_training = f"""You are an expert in ERPNext (Frappe framework) databases.
Generate ONLY a MariaDB SQL query to answer the user's question.

CRITICAL RULES FOR ERPNEXT DATABASE:
1. Relationships are NOT defined by Foreign Keys.
2. Almost all tables have a primary key named `name` (which is a string, e.g., 'EDU-STU-2026-0001').
3. To link tables, use the specific Frappe 'Link' fields.
4. Table names usually start with 'tab'. Always wrap table names with backticks if they contain spaces.
5. ERPNext table and column names are case-sensitive.
6. When searching for classes or groups like "10 A", always use `LIKE '%10%'`.

Given these database tables:
{DDL}

Generate ONLY the SQL query, nothing else. No markdown, no explanation."""

        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            messages=[{"role": "user", "content": system_training + f"\n\nQuestion: {q.question}"}]
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