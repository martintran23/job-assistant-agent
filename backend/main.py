from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi import File, UploadFile
from fastapi import HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Allow frontend (if running on file:// or localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origin=["*"], # Use specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class ResumeRequest(BaseModel):
    resume_text: str
    job_description: str

@app.post("/api/resume/analyze")
def analyze_resume(data: ResumeRequest):
    #Placeholder scoring logic
    return {
        "match_score": 90,
        "suggestions": [
            "Add more keywords from the job description.",
            "Highlight your project management experience."
        ]
    }

@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    contents = await file.read()
    text = contents.decode("utf-8") # Assuming plain text or .txt for now

    # TODO: save or process the text
    return {
        "filename": file.filename,
        "content_preview": text[:300]
    }

applications = [
    {"id": 1, "company": "OpenAI", "role": "ML Engineer", "status": "Interview"},
    {"id": 2, "company": "Google", "role": "Frontend Dev", "status": "Applied"},
    {"id": 3, "company": "Amazon", "role": "Data Analyst", "status": "Rejected"},
    {"id": 4, "company": "Meta", "role": "UX Designer", "status": "Applied"},
    {"id": 5, "company": "Netflix", "role": "Data Engineer", "status": "Rejected"},
]

@app.get("/api/dashboard")
def get_dashboard():
    return {"applications": applications}

class StatusUpdate(BaseModel):
    id: int
    status: str

@app.post("/api/dashboard/update")
def update_status(update: StatusUpdate):
    for app in applications:
        if app["id"] == update.id:
            app["status"] = update.status
            return {"success": True, "updated": app}
    raise HTTPException(status_code=404, detail="Application not found")