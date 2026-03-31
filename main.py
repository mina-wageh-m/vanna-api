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

def get_all_ddl():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        important_tables = [
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
            'tabFee Invoice Batch Generated',
            'tabStudent',
            'tabStudent Attendance',
            'tabStudent Group',
            'tabStudent Group Student',
            'tabStudent Guardian',
            'tabStudent Category',
            'tabStudent Leave Application',
            'tabStudent Log',
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
            'tabFees',
            'tabFee Structure',
            'tabFee Schedule',
            'tabFee Category',
            'tabFee Component',
            'tabFee Invoice',
            'tabFee Invoice Batch',
            'tabFee Invoice Generator',
            'tabFee Invoice Batch Generated',
            'tabFee Invoice Generator Generated',
            'tabFee Group',
            'tabFee Head',
            'tabFee Template',
            'tabSales Invoice',
            'tabCB Cheque Bounce',
            'tabCB Student Wallet',
            'tabCB Wallet Transaction',
            'tabCB Concession Type',
            'tabCB Fee Payment Allocation',
            'tabCB Fee Refund Allocation',
            'tabCourse',
            'tabCourse Enrollment',
            'tabCourse Schedule',
            'tabProgram',
            'tabProgram Enrollment',
            'tabAcademic Year',
            'tabAcademic Term',
            'tabAssessment Plan',
            'tabAssessment Result',
            'tabGrading Scale',
            'tabStudy Material',
            'tabInstructor',
            'tabStudent Group Instructor',
            'tabTimetable Periods',
            'tabRoom',
            'tabSection',
            'tabClass',
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

        all_ddl = ""
        for table in important_tables:
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
        return ""

DDL = get_all_ddl()

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
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": f"""You are a school database expert.
Given these database tables:
{DDL}

Generate ONLY a MariaDB SQL query to answer: {q.question}
Return ONLY the SQL query, nothing else."""
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
    return {"tables_count": len(DDL.split("CREATE TABLE")), "ddl_length": len(DDL)}