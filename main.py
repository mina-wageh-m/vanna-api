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

TABLE_GROUPS = {
    "students": [
        'tabStudent',
        'tabStudent Guardian',
        'tabStudent Category',
        'tabStudent Log',
        'tabStudent Class Enrollment',
        'tabStudent Siblings',
        'tabStudent Applicant',
        'tabStudent Admission',
        'tabStudent Language',
        'tabStudent Batch Name',
        'tabStudent LWI Log',
        'tabStudent Certificate',
        'tabStudent Gate Pass',
        'tabStudent Transportation',
        'tabAdmission Registration',
        'tabAdmission Enquiry',
        'tabGuardian',
        'tabGuardian Student',
        'tabStudy Stream',
    ],
    "attendance": [
        'tabStudent Attendance',
        'tabAttendance',
        'tabAttendance Request',
        'tabStudent Leave Application',
        'tabLeave Application',
        'tabLeave Type',
        'tabHoliday',
        'tabHoliday List',
        'tabStudent',
        'tabStudent Group',
    ],
    "fees": [
        'tabSales Invoice Item',
        'tabSales Invoice',
        'tabCB Invoice Fine',
        'tabFee Invoice Batch Student',
        'tabFee Invoice Batch Generated',
        'tabFee Invoice Generator Student',
        'tabFee Invoice Generator Generated',
        'tabStudent Group Transfer Invoice',
        'tabFee Invoice Batch Component',
        'tabFee Invoice Batch Section',
        'tabFee Invoice Batch Group',
        'tabFee Invoice Batch Class',
        'tabFee Invoice Batch',
        'tabInvoice Title',
        'tabFee Invoice Generator Component',
        'tabFee Invoice Generator Section',
        'tabFee Invoice Generator',
        'tabInvoice Adjustment',
        'tabFee Invoice Batch Category',
        'tabFee Invoice Generator Class',
        'tabFee Invoice Generator Group',
        'tabCB Fee Payment Allocation',
        'tabFee Template Component',
        'tabFee Template Section',
        'tabFee Template',
        'tabFee Template Group',
        'tabFee Head',
        'tabFee Category',
        'tabFee Template Class',
        'tabTransport Fee Allocation',
        'tabFee Component',
        'tabFee Schedule',
        'tabFee Structure',
        'tabPayment Schedule',
        'tabPayment Ledger Entry',
        'tabPayment Entry Reference',
        'tabPayment Entry',
        'tabMode of Payment',
        'tabCB Student Wallet',
        'tabCB Wallet Transaction',
        'tabCB Wallet Payment Allocation',
        'tabGL Entry',
        'tabAccount',
        'tabSalary Component',
        'tabCost Center',
        'tabPrice List',
        'tabItem Price',
        'tabFee Group',
        'tabStudent',
    ],
    "groups": [
        'tabStudent Group',
        'tabStudent Group Student',
        'tabStudent Group Instructor',
        'tabStudent Group Fee Template',
        'tabStudent Group Subject',
        'tabStudent Group Transfer',
        'tabSection',
        'tabClass',
        'tabSchool Branch',
        'tabSchool House',
        'tabStudent',
        'tabInstructor',
    ],
    "courses": [
        'tabCourse',
        'tabCourse Enrollment',
        'tabCourse Schedule',
        'tabCourse Topic',
        'tabCourse Assessment Criteria',
        'tabProgram',
        'tabProgram Course',
        'tabProgram Enrollment',
        'tabProgram Enrollment Course',
        'tabProgram Enrollment Fee',
        'tabProgram Fee',
        'tabAcademic Year',
        'tabAcademic Term',
        'tabAssessment Plan',
        'tabAssessment Plan Criteria',
        'tabAssessment Result',
        'tabAssessment Result Detail',
        'tabAssessment Criteria',
        'tabAssessment Group',
        'tabGrading Scale',
        'tabStudy Material',
        'tabStudent',
    ],
    "instructors": [
        'tabInstructor',
        'tabInstructor Log',
        'tabStudent Group Instructor',
        'tabStudent Group',
        'tabCourse Schedule',
        'tabTimetable Periods',
        'tabTimetable Substitution',
        'tabRoom',
        'tabEmployee',
        'tabDepartment',
        'tabDesignation',
        'tabStudent',
    ],
    "announcements": [
        'tabAnnouncement',
        'tabAnnouncement Attachment',
        'tabAnnouncement Class',
        'tabAnnouncement Section',
        'tabAnnouncement Student',
        'tabAnnouncement Student Group',
        'tabStudent Group',
        'tabClass',
        'tabSection',
        'tabStudent',
    ],
    "assignments": [
        'tabAssignment',
        'tabAssignment Attachment',
        'tabAssignment Section',
        'tabAssignment Student',
        'tabAssignment Student Group',
        'tabStudent Group',
        'tabCourse',
        'tabStudent',
    ],
}

def get_ddl_for_tables(tables: list) -> str:
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        ddl = ""
        for table in list(dict.fromkeys(tables)):
            try:
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                row = cursor.fetchone()
                if row:
                    ddl += row[1] + ";\n\n"
            except:
                pass
        conn.close()
        return ddl
    except:
        return ""

def detect_category(question: str) -> str:
    q = question.lower()
    if any(w in q for w in ["fee", "payment", "invoice", "overdue", "paid", "outstanding", "bounce", "wallet", "concession", "refund", "financial"]):
        return "fees"
    if any(w in q for w in ["absent", "attendance", "present", "leave", "holiday"]):
        return "attendance"
    if any(w in q for w in ["instructor", "teacher"]):
        return "instructors"
    if any(w in q for w in ["group", "section", "class", "branch", "house"]):
        return "groups"
    if any(w in q for w in ["course", "program", "enrollment", "assessment", "grading", "topic"]):
        return "courses"
    if any(w in q for w in ["announcement", "notice"]):
        return "announcements"
    if any(w in q for w in ["assignment", "homework", "task"]):
        return "assignments"
    return "students"

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
        category = detect_category(q.question)
        tables = TABLE_GROUPS[category]
        ddl = get_ddl_for_tables(tables)

        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"""You are a school database expert using ERPNext/Frappe framework.
IMPORTANT RULES:
- Primary key for all tables is `name` (string).
- Relationships use Link fields, NOT foreign keys.
- Always use backticks around table names with spaces.
- Use LIKE '%value%' when searching for names or codes.

Given these database tables:
{ddl}

Generate ONLY a MariaDB SQL query to answer: {q.question}
Return ONLY the SQL query, nothing else."""
            }]
        )
        sql = message.content[0].text.strip()
        sql = sql.replace("```sql", "").replace("```", "").strip()

        data = run_sql(sql)
        return {
            "question": q.question,
            "category": category,
            "sql": sql,
            "data": data,
            "status": "ok"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}

@app.get("/tables")
def tables():
    return {
        "groups": {k: len(v) for k, v in TABLE_GROUPS.items()},
        "total_tables": sum(len(v) for v in TABLE_GROUPS.values())
    }