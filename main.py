import os
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(title="To-Do List API", version="1.0.0")

_tasks: dict[int, dict] = {}
_next_id: int = 1


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=2000)
    completed: bool = False


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=2000)
    completed: bool | None = None


class Task(BaseModel):
    id: int
    title: str
    description: str | None
    completed: bool
    created_at: datetime
    updated_at: datetime


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate) -> Task:
    global _next_id
    now = _utc_now()
    task_id = _next_id
    _next_id += 1
    row = {
        "id": task_id,
        "title": payload.title,
        "description": payload.description,
        "completed": payload.completed,
        "created_at": now,
        "updated_at": now,
    }
    _tasks[task_id] = row
    return Task(**row)


@app.get("/tasks", response_model=list[Task])
def list_tasks() -> list[Task]:
    return [Task(**row) for row in sorted(_tasks.values(), key=lambda t: t["id"])]


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, payload: TaskUpdate) -> Task:
    if task_id not in _tasks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    row = _tasks[task_id]
    data = payload.model_dump(exclude_unset=True)
    if not data:
        return Task(**row)
    if "title" in data:
        row["title"] = data["title"]
    if "description" in data:
        row["description"] = data["description"]
    if "completed" in data:
        row["completed"] = data["completed"]
    row["updated_at"] = _utc_now()
    return Task(**row)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int) -> None:
    if task_id not in _tasks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    del _tasks[task_id]


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run("main:app", host="127.0.0.1", port=port, reload=True)
