from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import re
from dotenv import load_dotenv
import pdfplumber
from io import BytesIO

# Azure SDK imports
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

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

# Azure OpenAI/DeepSeek config from env
AZURE_OPENAI_API_URL = os.getenv("AZURE_OPENAI_API_URL") + "/models"
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME")

# Create Azure client (reuse this for all calls)
client = ChatCompletionsClient(
    endpoint=AZURE_OPENAI_API_URL,
    credential=AzureKeyCredential(AZURE_OPENAI_API_KEY),
    api_version="2024-05-01-preview"
)

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

# Resume analyze endpoint (using Azure DeepSeek)
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

    # Try extracting JSON from raw output
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

# Resume upload endpoint
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
