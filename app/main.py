from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from infra.db import get_db     # <-- 連線層
from app.services.search_service import search_teachers
from app.services.stat_service import compute_teacher_stats

app = FastAPI(title="NTUNHS Course API", version="1.0.0")

# ---------------------------------
# CORS for React / Node.js / etc.
# ---------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------
# Root
# ---------------------------------
@app.get("/")
def root():
    return {
        "message": "NTUNHS API Server Running!",
        "docs": "/docs",
        "mongo_connected": True
    }

# ---------------------------------
# Teacher Search API
# ---------------------------------
@app.get("/teachers/search")
def teacher_search(q: str):
    """
    Smart teacher name search across multiple semesters.
    """
    db = get_db()
    teachers = search_teachers(db, q)
    return {"query": q, "teachers": teachers}

# ---------------------------------
# Teacher Statistics API
# ---------------------------------
@app.get("/teachers/{teacher}/stats")
def teacher_stats(teacher: str, sem: str = "1142"):
    """
    Return teacher's cross-semester statistics 
    (courses per semester, departments, weekly hours, top3).
    """
    db = get_db()
    stats = compute_teacher_stats(db, teacher, sem)
    return stats




