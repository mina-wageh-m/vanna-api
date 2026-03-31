from fastapi import FastAPI
from pydantic import BaseModel
import pymysql
import anthropic
import os
from contextlib import asynccontextmanager

app = FastAPI()

# قاموس هنخزن فيه الجداول في الميموري عشان نفلتر منهم
CACHED_SCHEMA = {}

DB_CONFIG = {
    "host": "209.182.233.202",
    "port": 3306,
    "database": "_813e23c8a5386024",
    "user": "_813e23c8a5386024_remote",
    "password": "OTwspCMETxR442xV",
    "ssl_disabled": True
}

# دالة الفلترة الذكية مبنية فقط على الجداول المعتمدة في كودك الأخير
def get_relevant_tables(question: str):
    question_lower = question.lower()
    tables_to_fetch = set()

    # خريطة الكلمات الدلالية لربطها بجداولك فقط لتفادي تخطي الـ Rate Limit
    keywords_mapping = {
        "student": [
            'tabStudent', 'tabStudent Attendance', 'tabStudent Group Student', 
            'tabStudent Guardian', 'tabStudent Category', 'tabStudent Leave Application', 
            'tabStudent Log', 'tabStudent Admission', 'tabStudent Applicant', 
            'tabStudent Certificate', 'tabStudent Gate Pass', 'tabStudent Siblings', 
            'tabStudent Transportation', 'tabStudent Language', 'tabStudent Batch Name', 
            'tabStudent Class Enrollment', 'tabStudent LWI Log'
        ],
        "fee": [
            'tabStudent', 'tabFees', 'tabFee Structure', 'tabFee Schedule', 
            'tabFee Category', 'tabFee Component', 'tabFee Invoice', 'tabFee Group', 
            'tabFee Head', 'tabFee Template', 'tabFee Invoice Batch', 'tabFee Invoice Generator', 
            'tabFee Invoice Batch Generated', 'tabFee Invoice Generator Generated', 
            'tabCB Concession Type', 'tabCB Fee Payment Allocation', 'tabCB Fee Refund Allocation'
        ],
        "invoice": ['tabStudent', 'tabFee Invoice', 'tabSales Invoice'],
        "wallet": ['tabStudent', 'tabCB Student Wallet', 'tabCB Wallet Transaction', 'tabCB Cheque Bounce'],
        "attend": ['tabStudent', 'tabStudent Attendance', 'tabAttendance', 'tabHoliday List', 'tabHoliday'],
        "group": ['tabStudent', 'tabStudent Group', 'tabStudent Group Student', 'tabStudent Group Instructor'],
        "course": ['tabStudent', 'tabCourse', 'tabCourse Enrollment', 'tabCourse Schedule', 'tabProgram', 'tabProgram Enrollment'],
        "assess": ['tabStudent', 'tabAssessment Plan', 'tabAssessment Result', 'tabGrading Scale'],
        "class": ['tabStudent', 'tabClass', 'tabSection', 'tabRoom', 'tabTimetable Periods', 'tabStudent Class Enrollment'],
        "employee": ['tabEmployee', 'tabDepartment', 'tabDesignation', 'tabInstructor'],
        "leave": ['tabStudent', 'tabStudent Leave Application', 'tabLeave Application', 'tabLeave Type'],
        "material": ['tabStudy Material'],
        "branch": ['tabSchool Branch', 'tabSchool House']
    }

    # البحث عن الكلمة المناسبة في سؤال المستخدم
    for key, tables in keywords_mapping.items():
        if key in question_lower:
            tables_to_fetch.update(tables)

    # لو السؤال عام أو ملوش كلمة مفتاحية واضحة، بنبعتله أهم الجداول كأمان
    if not tables_to_fetch:
        tables_to_fetch.update(['tabStudent', 'tabStudent Group', 'tabClass'])

    return list(tables_to_fetch)

# دالة لقراءة الـ DDL للجداول مرة واحدة عند تشغيل السيرفر وحفظها في الميموري
def get_all_ddl():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        important_tables = [
            'tabStudent', 'tabStudent Attendance', 'tabStudent Group', 'tabStudent Group Student',
            'tabStudent Guardian', 'tabStudent Category', 'tabStudent Leave Application', 'tabStudent Log',
            'tabStudent Class Enrollment', 'tabCourse', 'tabCourse Enrollment', 'tabCourse Schedule',
            'tabProgram', 'tabProgram Enrollment', 'tabAcademic Year', 'tabAcademic Term',
            'tabInstructor', 'tabStudent Group Instructor', 'tabAssessment Plan', 'tabAssessment Result',
            'tabFee Invoice Batch', 'tabFee Invoice Generator', 'tabFee Invoice Batch Generated',
            'tabFee Invoice Generator Generated', 'tabCB Cheque Bounce', 'tabCB Student Wallet',
            'tabCB Wallet Transaction', 'tabSales Invoice', 'tabFee Structure', 'tabFee Schedule',
            'tabFee Category', 'tabFee Component', 'tabCB Concession Type', 'tabCB Fee Payment Allocation',
            'tabCB Fee Refund Allocation', 'tabSection', 'tabClass', 'tabAttendance', 'tabLeave Application'
        ]
        
        # إزالة أي تكرار
        important_tables = list(dict.fromkeys(important_tables))

        schema_dict = {}
        for table in important_tables:
            try:
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                row = cursor.fetchone()
                if row:
                    schema_dict[table] = row[1] + ";\n\n"
            except:
                pass
                
        conn.close()
        return schema_dict
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return {}

# تحميل الجداول في الرام (الميموري) مرة واحدة فقط في البداية
CACHED_SCHEMA = get_all_ddl()

client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

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
    return {"status": "API is running!", "cached_tables_count": len(CACHED_SCHEMA)}

@app.post("/ask")
def ask(q: Question):
    try:
        # الفلترة الذكية حسب السؤال عشان نقلل حجم الرسالة ونمنع الـ Rate Limit
        relevant_tables = get_relevant_tables(q.question)
        
        # تجميع الـ DDL للجداول المختارة فقط من الميموري
        filtered_schema_text = ""
        for table in relevant_tables:
            if table in CACHED_SCHEMA:
                filtered_schema_text += CACHED_SCHEMA[table]

        # في حال لم يتم العثور على أي جدول في القاموس، استخدم الداتا الافتراضية كأمان
        if not filtered_schema_text:
            filtered_schema_text = CACHED_SCHEMA.get('tabStudent', '')

        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"""You are a school database expert.
Given these database tables:
{filtered_schema_text}

Generate ONLY a MariaDB SQL query to answer: {q.question}
Return ONLY the SQL query, nothing else. No markdown, no explanation."""
            }]
        )
        sql = message.content[0].text.strip()
        sql = sql.replace("```sql", "").replace("```", "").strip()

        data = run_sql(sql)
        return {
            "question": q.question,
            "sql": sql,
            "data": data,
            "status": "ok"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}

@app.get("/tables")
def tables():
    return {"tables_count": len(CACHED_SCHEMA), "tables_loaded": list(CACHED_SCHEMA.keys())}