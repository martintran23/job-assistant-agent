from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import httpx
import os
import json
from dotenv import load_dotenv
import pdfplumber
from io import BytesIO

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use specific origin in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResumeRequest(BaseModel):
    resume_text: str
    job_description: str

class StatusUpdate(BaseModel):
    id: int
    status: str

applications = [
    {"id": 1, "company": "OpenAI", "role": "ML Engineer", "status": "Interview"},
    {"id": 2, "company": "Google", "role": "Frontend Dev", "status": "Applied"},
    {"id": 3, "company": "Amazon", "role": "Data Analyst", "status": "Rejected"},
    {"id": 4, "company": "Meta", "role": "UX Designer", "status": "Applied"},
    {"id": 5, "company": "Netflix", "role": "Data Engineer", "status": "Rejected"},
]

AZURE_OPENAI_API_URL = os.getenv("AZURE_OPENAI_API_URL")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME")  # e.g., "gpt-4"

async def call_azure_openai(prompt: str):
    headers = {
        "Content-Type": "application/json",
        "api-key": AZURE_OPENAI_API_KEY,
    }
    payload = {
        "messages": [
            {"role": "system", "content": "You are a job application assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 512,
    }

    url = f"{AZURE_OPENAI_API_URL}/openai/deployments/{AZURE_DEPLOYMENT_NAME}/chat/completions?api-version=2024-05-01-preview"

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

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

Return only JSON in this format:
{{"match_score": 87, "suggestions": ["Fix X", "Improve Y", "Add Z"]}}
"""
    raw_output = await call_azure_openai(prompt)

    try:
        result = json.loads(raw_output)
        return result
    except Exception:
        return {
            "match_score": 0,
            "suggestions": [
                "Failed to parse response.",
                "Raw output:",
                raw_output
            ]
        }

@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    if file.filename.endswith(".pdf"):
        with pdfplumber.open(BytesIO(await file.read())) as pdf:
            text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
    else:
        contents = await file.read()
        try:
            text = contents.decode("utf-8")
        except Exception:
            return {"filename": file.filename, "content_preview": "<Could not decode file contents>"}

    return {
        "filename": file.filename,
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
