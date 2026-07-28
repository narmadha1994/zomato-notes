import time
from typing import Callable, Awaitable
from fastapi import BackgroundTasks, Depends, FastAPI, File, Header, HTTPException, UploadFile

from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from . import crud
from .database import Base, engine, get_db
from .schemas import (
    NoteCreate,
    NoteResponse,
    NoteUpdate,
    UserCreate,
    UserResponse,
    
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Create the custom ASGI middleware
class ProcessTimeMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()

        async def send_with_process_time(message):
            if message["type"] == "http.response.start":
                process_time = time.perf_counter() - start_time

                headers = list(message.get("headers", []))
                headers.append(
                    (
                        b"x-process-time",
                        str(process_time).encode("utf-8")
                    )
                )

                message["headers"] = headers

            await send(message)

        await self.app(
            scope,
            receive,
            send_with_process_time
        )

app = FastAPI(
    title="Zomato Notes API",
    description="Internal notes and knowledge-base API",
    version="1.0.0",
)

def index_note(note_id: int):
    time.sleep(3)
    print(f"Background indexing completed for note {note_id}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ProcessTimeMiddleware)

def verify_token(x_token: str | None = Header(default=None)):
    if x_token != "zomato-secret-token":
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing x-token"
        )

    return x_token

@app.get("/")
def root():
    return {
        "message": "Zomato Notes API is running"
    }


@app.post(
    "/users",
    response_model=UserResponse,
    status_code=201
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = crud.get_user_by_email(
        db,
        user_data.email
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="A user with this email already exists"
        )

    return crud.create_user(
        db,
        user_data
    )


@app.post(
    "/notes",
    response_model=NoteResponse,
    status_code=201
)
def create_note(
    note_data: NoteCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    owner = crud.get_user_by_id(
        db,
        note_data.owner_id
    )

    if owner is None:
        raise HTTPException(
            status_code=404,
            detail="Owner user not found"
        )

    return crud.create_note(
        db,
        note_data
    )
    background_tasks.add_task(
        index_note,
        note.id
    )

    return note

@app.post(
    "/notes/import",
    status_code=201
)
def import_notes(
    owner_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Check owner BEFORE processing the file
    owner = crud.get_user_by_id(
        db,
        owner_id
    )

    if owner is None:
        raise HTTPException(
            status_code=404,
            detail="Owner user not found"
        )

    content = file.file.read().decode("utf-8")

    lines = [
        line.strip()
        for line in content.splitlines()
        if line.strip()
    ]

    created_notes = []

    for line in lines:
        note_data = NoteCreate(
            title=line[:120],
            content=line,
            tag="import",
            owner_id=owner_id
        )

        note = crud.create_note(
            db,
            note_data
        )

        created_notes.append(note)

    return {
        "message": "Notes imported successfully",
        "count": len(created_notes),
        "notes": created_notes
    }

@app.get(
    "/notes",
    response_model=list[NoteResponse]
)
def get_notes(
    tag: str | None = None,
    db: Session = Depends(get_db)
):
    return crud.get_notes(
        db,
        tag=tag
    )

@app.get(
    "/notes/{note_id}",
    response_model=NoteResponse
)
def get_note(
    note_id: int,
    db: Session = Depends(get_db)
):
    note = crud.get_note_by_id(
        db,
        note_id
    )

    if note is None:
        raise HTTPException(
            status_code=404,
            detail="Note not found"
        )

    return note

@app.put(
    "/notes/{note_id}",
    response_model=NoteResponse
)
def update_note(
    note_id: int,
    note_data: NoteUpdate,
    db: Session = Depends(get_db)
):
    note = crud.get_note_by_id(
        db,
        note_id
    )

    if note is None:
        raise HTTPException(
            status_code=404,
            detail="Note not found"
        )

    return crud.update_note(
        db,
        note,
        note_data
    )

@app.get("/reports/tag-summary")
def tag_summary(
    db: Session = Depends(get_db)
):
    query = text("""
        SELECT tag, COUNT(*) AS note_count
        FROM notes
        WHERE tag IS NOT NULL
        GROUP BY tag
        HAVING COUNT(*) > 1
        ORDER BY note_count DESC
    """)

    result = db.execute(query)

    return [
        {
            "tag": row.tag,
            "note_count": row.note_count
        }
        for row in result
    ]

@app.get("/reports/long-notes")
def long_notes(
    db: Session = Depends(get_db)
):
    query = text("""
        SELECT id, title, content, tag, owner_id, created_at
        FROM notes
        WHERE LENGTH(content) > (
            SELECT AVG(LENGTH(content))
            FROM notes
        )
        ORDER BY LENGTH(content) DESC
    """)

    result = db.execute(query)

    return [
        {
            "id": row.id,
            "title": row.title,
            "content": row.content,
            "tag": row.tag,
            "owner_id": row.owner_id,
            "created_at": row.created_at
        }
        for row in result
    ]

@app.get("/reports/user-notes")
def user_notes_report(
    db: Session = Depends(get_db)
):
    query = text("""
        SELECT
            u.id AS user_id,
            u.name,
            u.email,
            COUNT(n.id) AS note_count
        FROM users u
        LEFT JOIN notes n
            ON u.id = n.owner_id
        GROUP BY u.id, u.name, u.email
        ORDER BY note_count DESC
    """)

    result = db.execute(query)

    return [
        {
            "user_id": row.user_id,
            "name": row.name,
            "email": row.email,
            "note_count": row.note_count
        }
        for row in result
    ]

@app.delete(
    "/notes/{note_id}",
    status_code=204,
    dependencies=[Depends(verify_token)]
)
def delete_note(
    note_id: int,
    db: Session = Depends(get_db)
):
    note = crud.get_note_by_id(
        db,
        note_id
    )

    if note is None:
        raise HTTPException(
            status_code=404,
            detail="Note not found"
        )

    crud.delete_note(db, note)

    return None