from fastapi import FastAPI, HTTPException, File, UploadFile, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env file if present

app = FastAPI()

# Allow frontend requests (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Data models
class ResumeRequest(BaseModel):
    resume_text: str
    job_description: str

class StatusUpdate(BaseModel):
    id: int
    status: str

# In-memory applications storage (replace with DB in production)
applications = [
    {"id": 1, "company": "OpenAI", "role": "ML Engineer", "status": "Interview"},
    {"id": 2, "company": "Google", "role": "Frontend Dev", "status": "Applied"},
    {"id": 3, "company": "Amazon", "role": "Data Analyst", "status": "Rejected"},
    {"id": 4, "company": "Meta", "role": "UX Designer", "status": "Applied"},
    {"id": 5, "company": "Netflix", "role": "Data Engineer", "status": "Rejected"},
]

# DeepSeek API config from env
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

async def call_deepseek(prompt: str):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",  # Adjust model name if needed
        "messages": [
            {"role": "system", "content": "You are a job application assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 512
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(DEEPSEEK_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

# Resume analyze endpoint (using DeepSeek)
@app.post("/api/resume/analyze")
async def analyze_resume(data: ResumeRequest):
    prompt = f"""
Compare the following resume to the job description.
Give a match score out of 100 and suggest 3 improvements.

Resume:
{data.resume_text}

Job Description:
{data.job_description}

Return only JSON in this format:
{{"match_score": 87, "suggestions": ["Fix X", "Improve Y", "Add Z"]}}
    """
    raw_output = await call_deepseek(prompt)

    try:
        result = json.loads(raw_output)
        return result
    except Exception:
        return {
            "match_score": 0,
            "suggestions": [
                "Failed to parse DeepSeek response.",
                "Raw output:",
                raw_output
            ]
        }

# Resume upload endpoint
@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        text = contents.decode("utf-8")  # Assumes .txt files for now
    except UnicodeDecodeError:
        text = "<Could not decode file contents>"

    # TODO: Save/process the text if needed

    return {
        "filename": file.filename,
        "content_preview": text[:300]
    }

# Get all applications for dashboard
@app.get("/api/dashboard")
def get_dashboard():
    return {"applications": applications}

# Update status of one application
@app.post("/api/dashboard/update")
def update_status(update: StatusUpdate):
    for app in applications:
        if app["id"] == update.id:
            app["status"] = update.status
            return {"success": True, "updated": app}
    raise HTTPException(status_code=404, detail="Application not found")