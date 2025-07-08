from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import database
from models import user_profiles
import os
import json
import re
import pdfplumber
from io import BytesIO
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Azure SDK imports
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Azure OpenAI config
AZURE_OPENAI_API_URL = os.getenv("AZURE_OPENAI_API_URL") + "/models"
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME")

client = ChatCompletionsClient(
    endpoint=AZURE_OPENAI_API_URL,
    credential=AzureKeyCredential(AZURE_OPENAI_API_KEY),
    api_version="2024-05-01-preview"
)

class ResumeRequest(BaseModel):
    resume_text: str
    job_description: str

class StatusUpdate(BaseModel):
    id: int
    status: str

class UserProfile(BaseModel):
    full_name: str
    email: str
    phone: str | None = None
    work_history: str | None = None
    education: str | None = None

applications = [
    {"id": 1, "company": "OpenAI", "role": "ML Engineer", "status": "Interview"},
    {"id": 2, "company": "Google", "role": "Frontend Dev", "status": "Applied"},
    {"id": 3, "company": "Amazon", "role": "Data Analyst", "status": "Rejected"},
    {"id": 4, "company": "Meta", "role": "UX Designer", "status": "Applied"},
    {"id": 5, "company": "Netflix", "role": "Data Engineer", "status": "Rejected"},
]

def extract_json(text: str):
    start = text.find('{')
    while start != -1:
        end = text.find('}', start)
        while end != -1:
            candidate = text[start:end+1]
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                end = text.find('}', end+1)
        start = text.find('{', start+1)
    return None

async def call_deepseek(prompt: str):
    import asyncio
    loop = asyncio.get_event_loop()

    def sync_call():
        response = client.complete(
            messages=[
                SystemMessage(content="You are a job application assistant."),
                UserMessage(content=prompt)
            ],
            max_tokens=1024,
            model=AZURE_DEPLOYMENT_NAME
        )
        return response.choices[0].message.content

    return await loop.run_in_executor(None, sync_call)

@app.get("/")
def root():
    return {"message": "Job Application Assistant API is running!"}

@app.post("/api/resume/analyze")
async def analyze_resume(data: ResumeRequest):
    prompt = f"""
Compare the following resume to the job description.
Give a match score out of 100 and suggest 3 improvements.

Resume:
{data.resume_text}

Job Description:
{data.job_description}

Return ONLY a JSON object EXACTLY like this (no other text or explanation):

{{
  "match_score": 87,
  "suggestions": ["Fix X", "Improve Y", "Add Z"]
}}
    """

    raw_output = await call_deepseek(prompt)
    json_text = extract_json(raw_output)
    if json_text:
        try:
            result = json.loads(json_text)
            return result
        except Exception as e:
            return {
                "match_score": 0,
                "suggestions": [
                    "Failed to parse extracted JSON.",
                    f"Error: {str(e)}",
                    "Raw output:",
                    raw_output
                ]
            }
    else:
        return {
            "match_score": 0,
            "suggestions": [
                "Failed to find JSON in the DeepSeek response.",
                "Raw output:",
                raw_output
            ]
        }

def split_sections(text: str):
    pattern = re.compile(r'(education|work experience|professional experience|skills|projects|certifications|contact information|summary)', re.I)
    splits = [(m.start(), m.group().lower()) for m in pattern.finditer(text)]
    sections = {}
    for i, (start, header) in enumerate(splits):
        end = splits[i+1][0] if i+1 < len(splits) else len(text)
        sections[header] = text[start:end].strip()
    return sections

def extract_contact_info(text: str):
    email = re.search(r'[\w\.-]+@[\w\.-]+', text)
    phone = re.search(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?){1,2}\d{4}', text)
    return {
        "email": email.group() if email else None,
        "phone": phone.group() if phone else None
    }

def extract_education(text: str):
    lines = text.split('\n')
    education_entries = [
        line.strip() for line in lines
        if re.search(r'(bachelor|master|ph\.d|degree|university|college)', line, re.I)
    ]
    return "\n".join(education_entries)

def extract_work_experience(text: str):
    lines = text.split('\n')
    jobs = [
        line.strip() for line in lines
        if re.search(r'(engineer|developer|manager|analyst|consultant|intern)', line, re.I)
    ]
    return "\n".join(jobs)

def parse_resume(text: str):
    sections = split_sections(text)
    contact_info = extract_contact_info(text)
    education = extract_education(sections.get('education', ''))
    work_history = extract_work_experience(
        sections.get('work experience', '') or sections.get('professional experience', '')
    )

    return {
        "full_name": None,
        "email": contact_info["email"],
        "phone": contact_info["phone"],
        "education": education,
        "work_history": work_history
    }

@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_bytes = await file.read()
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        text = "\n".join([page.extract_text() or "" for page in pdf.pages])

    parsed_data = parse_resume(text)

    # UPSERT logic to avoid duplicate emails
    insert_stmt = pg_insert(user_profiles).values(
        full_name=parsed_data["full_name"] or "Unknown",
        email=parsed_data["email"],
        phone=parsed_data["phone"],
        education=parsed_data["education"],
        work_history=parsed_data["work_history"]
    )
    update_stmt = insert_stmt.on_conflict_do_update(
        index_elements=["email"],
        set_={
            "full_name": insert_stmt.excluded.full_name,
            "phone": insert_stmt.excluded.phone,
            "education": insert_stmt.excluded.education,
            "work_history": insert_stmt.excluded.work_history,
        }
    )

    record_id = await database.execute(update_stmt)

    return {
        "id": record_id,
        "parsed_data": parsed_data,
        "content_preview": text[:300]
    }

@app.get("/api/dashboard")
def get_dashboard():
    return {"applications": applications}

@app.post("/api/dashboard/update")
def update_status(update: StatusUpdate):
    for app in applications:
        if app["id"] == update.id:
            app["status"] = update.status
            return {"success": True, "updated": app}
    raise HTTPException(status_code=404, detail="Application not found")

@app.post("/profile/")
async def create_profile(profile: UserProfile):
    query = user_profiles.insert().values(
        full_name=profile.full_name,
        email=profile.email,
        phone=profile.phone,
        work_history=profile.work_history,
        education=profile.education
    )
    last_record_id = await database.execute(query)
    return {**profile.model_dump(), "id": last_record_id}
