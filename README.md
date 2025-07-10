# 🧠 AI Job Application Assistant

An intelligent tool designed to streamline the job application process using automation, personalized content generation, and smart tracking.

## 🚀 Features

### 🔹 Autofill Agent
Securely stores a user's profile information — including name, contact details, work history, education, and more — and intelligently fills out job application forms across different websites.

### 🔹 Resume-to-JD Scoring Agent
Compares the user's uploaded resume with a specific job description to:
- Provide a **match score**
- Suggest actionable insights to improve resume alignment with the role

### 🔹 Tailored Answer Agent
Analyzes both the job description and the user’s profile to generate high-quality, personalized answers for common application questions such as:
- "Why are you a good fit for this role?"
- "What is your biggest strength?"

### 🔹 Application Tracker Dashboard
A centralized dashboard that helps users visualize and track the status of their job applications. Potential statuses include:
- Applied
- Interview
- Rejected

---

## 🛠️ Tech Stack

- **Frontend**: HTML, CSS, JavaScript (React)
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **AI & NLP**: Azure Deepseek-R1 API

---

## 📂 Folder Structure

project-root/
├── backend/
│ ├── scorer.py
│ ├── user.py
│ └── main.py
├── frontend/
│ ├── index.html
│ ├── script.js
│ └── styles.css
├── create_tables.py
├── database.py
├── models.py
└── README.md