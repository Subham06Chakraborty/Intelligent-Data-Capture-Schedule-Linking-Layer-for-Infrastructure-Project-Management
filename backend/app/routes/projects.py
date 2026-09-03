"""Project CRUD API."""
from fastapi import APIRouter, status

from app.models.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services import project_service

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.get("", response_model=list[ProjectResponse])
def list_projects():
    return project_service.list_projects()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str):
    return project_service.get_project(project_id)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate):
    return project_service.create_project(payload)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, payload: ProjectUpdate):
    return project_service.update_project(project_id, payload)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str):
    project_service.delete_project(project_id)
