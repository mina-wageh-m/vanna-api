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

DDL = """
CREATE TABLE `tabStudent` ( `name` varchar(140) NOT NULL, `creation` datetime(6) DEFAULT NULL, `modified` datetime(6) DEFAULT NULL, `modified_by` varchar(140) DEFAULT NULL, `owner` varchar(140) DEFAULT NULL, `docstatus` int(1) NOT NULL DEFAULT 0, `idx` int(8) NOT NULL DEFAULT 0, `enabled` int(1) NOT NULL DEFAULT 1, `first_name` varchar(140) DEFAULT NULL, `middle_name` varchar(140) DEFAULT NULL, `last_name` varchar(140) DEFAULT NULL, `naming_series` varchar(140) DEFAULT NULL, `joining_date` date DEFAULT NULL, `user` varchar(140) DEFAULT NULL, `student_applicant` varchar(140) DEFAULT NULL, `image` text DEFAULT NULL, `student_email_id` varchar(140) DEFAULT NULL, `date_of_birth` date DEFAULT NULL, `blood_group` varchar(140) DEFAULT NULL, `student_mobile_number` varchar(140) DEFAULT NULL, `gender` varchar(140) DEFAULT NULL, `nationality` varchar(140) DEFAULT NULL, `address_line_1` varchar(140) DEFAULT NULL, `address_line_2` varchar(140) DEFAULT NULL, `pincode` varchar(140) DEFAULT NULL, `city` varchar(140) DEFAULT NULL, `state` varchar(140) DEFAULT NULL, `country` varchar(140) DEFAULT NULL, `customer` varchar(140) DEFAULT NULL, `customer_group` varchar(140) DEFAULT NULL, `date_of_leaving` date DEFAULT NULL, `leaving_certificate_number` varchar(140) DEFAULT NULL, `reason_for_leaving` text DEFAULT NULL, `student_name` varchar(140) DEFAULT NULL, `_user_tags` text DEFAULT NULL, `_comments` text DEFAULT NULL, `_assign` text DEFAULT NULL, `_liked_by` text DEFAULT NULL, `cb_student_status` varchar(140) DEFAULT 'Active', `is_graduated` int(1) NOT NULL DEFAULT 0, `left_without_info` int(1) NOT NULL DEFAULT 0, `has_siblings` int(1) NOT NULL DEFAULT 0, `admission_number` varchar(140) DEFAULT NULL, `admission_date` date DEFAULT NULL, `current_academic_year` varchar(140) DEFAULT NULL, `current_class` varchar(140) DEFAULT NULL, `current_academic_term` varchar(140) DEFAULT NULL, `current_program` varchar(140) DEFAULT NULL, `current_student_group` varchar(140) DEFAULT NULL, `current_section` varchar(140) DEFAULT NULL, `current_roll_number` int(11) NOT NULL DEFAULT 0, `birth_place` varchar(140) DEFAULT NULL, `fee_group` varchar(140) DEFAULT NULL, `lwi_start_date` date DEFAULT NULL, `lwi_end_date` date DEFAULT NULL, `has_lwi_history` int(1) NOT NULL DEFAULT 0, `custom_favourite_sport` varchar(140) DEFAULT NULL, `cb_total_bounces` int(11) NOT NULL DEFAULT 0, `cb_total_bounce_fines` decimal(21,9) NOT NULL DEFAULT 0.000000000, `cb_pending_bounce_fines` decimal(21,9) NOT NULL DEFAULT 0.000000000, `father_name` varchar(140) DEFAULT NULL, `father_mobile` varchar(140) DEFAULT NULL, `primary_guardian_name` varchar(140) DEFAULT NULL, `primary_guardian_phone` varchar(140) DEFAULT NULL, `student_category` varchar(140) DEFAULT NULL, `custom_religion` varchar(140) DEFAULT NULL, `custom_caste` varchar(140) DEFAULT NULL, `custom_emp_category` varchar(140) DEFAULT NULL, `custom_house` varchar(140) DEFAULT NULL, `custom_permanent_address_line_1` varchar(140) DEFAULT NULL, `custom_permanent_address_line_2` varchar(140) DEFAULT NULL, `custom_permanent_pincode` varchar(140) DEFAULT NULL, `custom_permanent_city` varchar(140) DEFAULT NULL, `custom_permanent_state` varchar(140) DEFAULT NULL, `custom_permanent_country` varchar(140) DEFAULT NULL, `cb_email_id` varchar(140) DEFAULT NULL, `cb_admission_registration` varchar(140) DEFAULT NULL, `mother_name` varchar(140) DEFAULT NULL, `mother_mobile` varchar(140) DEFAULT NULL, `cb_concession_type` varchar(140) DEFAULT NULL, PRIMARY KEY (`name`), UNIQUE KEY `student_email_id` (`student_email_id`), UNIQUE KEY `admission_number` (`admission_number`), KEY `modified` (`modified`) ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC

CREATE TABLE `tabStudent Attendance` ( `name` varchar(140) NOT NULL, `creation` datetime(6) DEFAULT NULL, `modified` datetime(6) DEFAULT NULL, `modified_by` varchar(140) DEFAULT NULL, `owner` varchar(140) DEFAULT NULL, `docstatus` int(1) NOT NULL DEFAULT 0, `idx` int(8) NOT NULL DEFAULT 0, `naming_series` varchar(140) DEFAULT NULL, `student` varchar(140) DEFAULT NULL, `student_name` varchar(140) DEFAULT NULL, `student_mobile_number` varchar(140) DEFAULT NULL, `course_schedule` varchar(140) DEFAULT NULL, `student_group` varchar(140) DEFAULT NULL, `date` date DEFAULT NULL, `status` varchar(140) DEFAULT 'Present', `leave_application` varchar(140) DEFAULT NULL, `amended_from` varchar(140) DEFAULT NULL, `link_nvfk` varchar(140) DEFAULT NULL, `_user_tags` text DEFAULT NULL, `_comments` text DEFAULT NULL, `_assign` text DEFAULT NULL, `_liked_by` text DEFAULT NULL, `teacher` varchar(140) DEFAULT NULL, PRIMARY KEY (`name`), KEY `student` (`student`), KEY `date` (`date`), KEY `modified` (`modified`) ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC

CREATE TABLE `tabFees` ( `name` varchar(140) NOT NULL, `creation` datetime(6) DEFAULT NULL, `modified` datetime(6) DEFAULT NULL, `modified_by` varchar(140) DEFAULT NULL, `owner` varchar(140) DEFAULT NULL, `docstatus` int(1) NOT NULL DEFAULT 0, `idx` int(8) NOT NULL DEFAULT 0, `naming_series` varchar(140) DEFAULT NULL, `student` varchar(140) DEFAULT NULL, `student_name` varchar(140) DEFAULT NULL, `include_payment` int(1) NOT NULL DEFAULT 0, `send_payment_request` int(1) NOT NULL DEFAULT 0, `company` varchar(140) DEFAULT NULL, `posting_date` date DEFAULT NULL, `posting_time` time(6) DEFAULT NULL, `due_date` date DEFAULT NULL, `set_posting_time` int(1) NOT NULL DEFAULT 0, `program_enrollment` varchar(140) DEFAULT NULL, `program` varchar(140) DEFAULT NULL, `academic_year` varchar(140) DEFAULT NULL, `academic_term` varchar(140) DEFAULT NULL, `fee_structure` varchar(140) DEFAULT NULL, `fee_schedule` varchar(140) DEFAULT NULL, `currency` varchar(140) DEFAULT NULL, `amended_from` varchar(140) DEFAULT NULL, `grand_total` decimal(21,9) NOT NULL DEFAULT 0.000000000, `grand_total_in_words` varchar(240) DEFAULT NULL, `outstanding_amount` decimal(21,9) NOT NULL DEFAULT 0.000000000, `contact_email` varchar(140) DEFAULT NULL, `student_category` varchar(140) DEFAULT NULL, `student_batch` varchar(140) DEFAULT NULL, `receivable_account` varchar(140) DEFAULT NULL, `income_account` varchar(140) DEFAULT NULL, `cost_center` varchar(140) DEFAULT NULL, `letter_head` varchar(140) DEFAULT NULL, `select_print_heading` varchar(140) DEFAULT NULL, `_user_tags` text DEFAULT NULL, `_comments` text DEFAULT NULL, `_assign` text DEFAULT NULL, `_liked_by` text DEFAULT NULL, PRIMARY KEY (`name`), KEY `posting_date` (`posting_date`), KEY `modified` (`modified`) ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC

CREATE TABLE `tabCourse` ( `name` varchar(140) NOT NULL, `creation` datetime(6) DEFAULT NULL, `modified` datetime(6) DEFAULT NULL, `modified_by` varchar(140) DEFAULT NULL, `owner` varchar(140) DEFAULT NULL, `docstatus` int(1) NOT NULL DEFAULT 0, `idx` int(8) NOT NULL DEFAULT 0, `course_name` varchar(140) DEFAULT NULL, `department` varchar(140) DEFAULT NULL, `hero_image` text DEFAULT NULL, `description` text DEFAULT NULL, `default_grading_scale` varchar(140) DEFAULT NULL, `_user_tags` text DEFAULT NULL, `_comments` text DEFAULT NULL, `_assign` text DEFAULT NULL, `_liked_by` text DEFAULT NULL, PRIMARY KEY (`name`), UNIQUE KEY `course_name` (`course_name`), KEY `modified` (`modified`) ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC

CREATE TABLE `tabStudent Group Instructor` ( `name` varchar(140) NOT NULL, `creation` datetime(6) DEFAULT NULL, `modified` datetime(6) DEFAULT NULL, `modified_by` varchar(140) DEFAULT NULL, `owner` varchar(140) DEFAULT NULL, `docstatus` int(1) NOT NULL DEFAULT 0, `idx` int(8) NOT NULL DEFAULT 0, `instructor` varchar(140) DEFAULT NULL, `instructor_name` varchar(140) DEFAULT NULL, `parent` varchar(140) DEFAULT NULL, `parentfield` varchar(140) DEFAULT NULL, `parenttype` varchar(140) DEFAULT NULL, PRIMARY KEY (`name`), KEY `parent` (`parent`) ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC

CREATE TABLE `tabStudent Group` ( `name` varchar(140) NOT NULL, `creation` datetime(6) DEFAULT NULL, `modified` datetime(6) DEFAULT NULL, `modified_by` varchar(140) DEFAULT NULL, `owner` varchar(140) DEFAULT NULL, `docstatus` int(1) NOT NULL DEFAULT 0, `idx` int(8) NOT NULL DEFAULT 0, `academic_year` varchar(140) DEFAULT NULL, `group_based_on` varchar(140) DEFAULT NULL, `student_group_name` varchar(140) DEFAULT NULL, `max_strength` int(11) NOT NULL DEFAULT 0, `academic_term` varchar(140) DEFAULT NULL, `program` varchar(140) DEFAULT NULL, `batch` varchar(140) DEFAULT NULL, `student_category` varchar(140) DEFAULT NULL, `course` varchar(140) DEFAULT NULL, `disabled` int(1) NOT NULL DEFAULT 0, `_user_tags` text DEFAULT NULL, `_comments` text DEFAULT NULL, `_assign` text DEFAULT NULL, `_liked_by` text DEFAULT NULL, PRIMARY KEY (`name`), UNIQUE KEY `student_group_name` (`student_group_name`), KEY `modified` (`modified`) ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC

CREATE TABLE `tabStudent Guardian` ( `name` varchar(140) NOT NULL, `creation` datetime(6) DEFAULT NULL, `modified` datetime(6) DEFAULT NULL, `modified_by` varchar(140) DEFAULT NULL, `owner` varchar(140) DEFAULT NULL, `docstatus` int(1) NOT NULL DEFAULT 0, `idx` int(8) NOT NULL DEFAULT 0, `guardian` varchar(140) DEFAULT NULL, `guardian_name` varchar(140) DEFAULT NULL, `relation` varchar(140) DEFAULT NULL, `parent` varchar(140) DEFAULT NULL, `parentfield` varchar(140) DEFAULT NULL, `parenttype` varchar(140) DEFAULT NULL, PRIMARY KEY (`name`), KEY `parent` (`parent`) ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC

CREATE TABLE `tabStudent Category` ( `name` varchar(140) NOT NULL, `creation` datetime(6) DEFAULT NULL, `modified` datetime(6) DEFAULT NULL, `modified_by` varchar(140) DEFAULT NULL, `owner` varchar(140) DEFAULT NULL, `docstatus` int(1) NOT NULL DEFAULT 0, `idx` int(8) NOT NULL DEFAULT 0, `category` varchar(140) DEFAULT NULL, `_user_tags` text DEFAULT NULL, `_comments` text DEFAULT NULL, `_assign` text DEFAULT NULL, `_liked_by` text DEFAULT NULL, PRIMARY KEY (`name`), UNIQUE KEY `category` (`category`), KEY `modified` (`modified`) ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC

CREATE TABLE `tabInstructor` ( `name` varchar(140) NOT NULL, `creation` datetime(6) DEFAULT NULL, `modified` datetime(6) DEFAULT NULL, `modified_by` varchar(140) DEFAULT NULL, `owner` varchar(140) DEFAULT NULL, `docstatus` int(1) NOT NULL DEFAULT 0, `idx` int(8) NOT NULL DEFAULT 0, `instructor_name` varchar(140) DEFAULT NULL, `employee` varchar(140) DEFAULT NULL, `gender` varchar(140) DEFAULT NULL, `status` varchar(140) DEFAULT 'Active', `naming_series` varchar(140) DEFAULT NULL, `department` varchar(140) DEFAULT NULL, `image` text DEFAULT NULL, `_user_tags` text DEFAULT NULL, `_comments` text DEFAULT NULL, `_assign` text DEFAULT NULL, `_liked_by` text DEFAULT NULL, PRIMARY KEY (`name`), KEY `modified` (`modified`) ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC
"""

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
                "content": f"""Given this database table:
{DDL}

Generate ONLY a SQL query to answer: {q.question}
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
    
    @app.get("/train")
    def train():
        try:
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            
            all_ddl = ""
            for table in tables:
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                row = cursor.fetchone()
                if row:
                    all_ddl += row[1] + ";\n\n"
            
            conn.close()
            return {"tables": tables, "ddl": all_ddl, "status": "ok"}
        except Exception as e:
            return {"error": str(e), "status": "error"}