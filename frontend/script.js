// === Resume & Job Description Analysis ===
async function analyze() {
  const resume = document.getElementById("resume").value;
  const jd = document.getElementById("jd").value;

  if (!resume || !jd) {
    alert("Please provide both resume and job description.");
    return;
  }

  try {
    const res = await fetch("http://localhost:8000/api/resume/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ resume_text: resume, job_description: jd })
    });

    const data = await res.json();

    document.getElementById("result").innerHTML = `
      <h3>Match Score: ${data.match_score}%</h3>
      <ul>${data.suggestions.map(s => `<li>${s}</li>`).join('')}</ul>
    `;
  } catch (err) {
    console.error("Analyze failed:", err);
    document.getElementById("result").innerText = "An error occurred during analysis.";
  }
}

// === Resume File Upload ===
async function uploadResume() {
  const fileInput = document.getElementById("resumeFile");
  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("http://localhost:8000/api/resume/upload", {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    document.getElementById("uploadResult").innerText = `Preview:\n${data.content_preview}`;
  } catch (err) {
    console.error("Upload failed:", err);
    document.getElementById("uploadResult").innerText = "Failed to upload resume.";
  }
}

// === Load Application Dashboard ===
async function loadDashboard() {
  try {
    const res = await fetch("http://localhost:8000/api/dashboard");
    const data = await res.json();

    const statuses = ["Applied", "Interview", "Rejected"];
    const grouped = {};
    statuses.forEach(status => grouped[status] = []);

    data.applications.forEach(app => {
      if (grouped[app.status]) {
        grouped[app.status].push(app);
      }
    });

    const container = document.getElementById("dashboard");
    container.innerHTML = statuses.map(status => `
      <div class="column"
           ondragover="event.preventDefault()"
           ondrop="handleDrop(event, '${status}')">
        <h3>${status}</h3>
        ${grouped[status].map(app => `
          <div class="app-card"
               draggable="true"
               ondragstart="handleDragStart(event, ${app.id})">
            <strong>${app.company}</strong><br />
            <span>${app.role}</span><br />
            <label>Status:</label>
            <select onchange="updateStatus(${app.id}, this.value)">
              ${statuses.map(s => `<option value="${s}" ${s === app.status ? "selected" : ""}>${s}</option>`).join('')}
            </select>
          </div>
        `).join('')}
      </div>
    `).join('');
  } catch (err) {
    console.error("Failed to load dashboard:", err);
    document.getElementById("dashboard").innerText = "Failed to load dashboard.";
  }
}

// === Update Application Status ===
async function updateStatus(id, newStatus) {
  try {
    await fetch("http://localhost:8000/api/dashboard/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id, status: newStatus })
    });

    loadDashboard(); // Refresh dashboard
  } catch (err) {
    console.error("Failed to update status:", err);
  }
}

// === Drag & Drop Support ===
let draggedAppId = null;

function handleDragStart(event, appId) {
  draggedAppId = appId;
  event.dataTransfer.effectAllowed = "move";
}

function handleDrop(event, newStatus) {
  event.preventDefault();
  if (draggedAppId !== null) {
    updateStatus(draggedAppId, newStatus);
    draggedAppId = null;
  }
}

// === Load dashboard on page load ===
window.onload = () => {
  loadDashboard();
};
