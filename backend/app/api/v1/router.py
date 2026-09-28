from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.assessments import router as assessments_router
from app.api.v1.assistant import router as assistant_router
from app.api.v1.auth import router as auth_router
from app.api.v1.catalog import roles_router, skills_router
from app.api.v1.employees import router as employees_router
from app.api.v1.gap import router as gap_router
from app.api.v1.graph import router as graph_router
from app.api.v1.job_descriptions import router as job_descriptions_router
from app.api.v1.learning_paths import router as learning_paths_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.resources import (
    courses_router,
    mentors_router,
    projects_router,
)
from app.api.v1.resumes import router as resumes_router
from app.api.v1.twin import router as twin_router
from app.api.v1.whatif import router as whatif_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(employees_router)
api_router.include_router(resumes_router)
api_router.include_router(job_descriptions_router)
api_router.include_router(gap_router)
api_router.include_router(graph_router)
api_router.include_router(recommendations_router)
api_router.include_router(learning_paths_router)
api_router.include_router(assessments_router)
api_router.include_router(assistant_router)
api_router.include_router(whatif_router)
api_router.include_router(twin_router)
api_router.include_router(analytics_router)
api_router.include_router(roles_router)
api_router.include_router(skills_router)
api_router.include_router(courses_router)
api_router.include_router(projects_router)
api_router.include_router(mentors_router)
api_router.include_router(admin_router)
