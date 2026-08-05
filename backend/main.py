from ai_sample_notes import AI_SAMPLE_NOTES
from semantic_search import (
    create_embeddings,
    semantic_search,
)

import json
import logging
from ai_service import get_ai_response
from prompt_template import AUTO_TAG_PROMPT

import time
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    Header,
    HTTPException,
    UploadFile,
)

from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

import crud
from algorithms import (
    insertion_sort_by_key,
    binary_search_iterative,
    binary_search_recursive,
    linear_search,
)
from database import Base, engine, get_db
from models import Note
from schemas import (
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

AI_EMBEDDINGS = create_embeddings(AI_SAMPLE_NOTES)

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


@app.post("/notes", response_model=None)
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

    note = crud.create_note(
        db,
        note_data
    )

    background_tasks.add_task(
        index_note,
        note.id
    )

    ai_suggestion = None

    try:
        ai_response = get_ai_response(
            user_message=note.content,
            system_prompt=AUTO_TAG_PROMPT
        )

        ai_suggestion = json.loads(ai_response)

    except Exception:
        logging.exception(
            "Failed to parse AI response"
        )

        ai_suggestion = None

    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "tag": note.tag,
        "owner_id": note.owner_id,
        "created_at": note.created_at,
        "ai_suggestion": ai_suggestion
    }
    
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

@app.get("/notes/search")
def search_notes(
    keyword: str | None = None,
    sort_by: str | None = None,
    db: Session = Depends(get_db)
):
    notes = crud.get_notes(db)

    # Date sorting mode
    if sort_by == "date":
        notes_data = []

        for note in notes:
            notes_data.append({
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "tag": note.tag,
                "owner_id": note.owner_id,
                "created_at": note.created_at,
                "created_at_epoch": note.created_at.timestamp()
            })

        return insertion_sort_by_key(
            notes_data,
            key="created_at_epoch"
        )

    # Relevance mode
    if keyword:
        keyword_lower = keyword.lower()
        notes_data = []

        for note in notes:
            content_lower = note.content.lower()

            score = content_lower.count(keyword_lower)

            notes_data.append({
                "id": note.id,
                "title": note.title,
                "content": note.content,
                "tag": note.tag,
                "owner_id": note.owner_id,
                "created_at": note.created_at,
                "score": score
            })

        ranked_notes = insertion_sort_by_key(
            notes_data,
            key="score"
        )

        return ranked_notes[:5]

    return []

@app.get("/notes/lookup")
def lookup_note(
    title: str,
    algo: str = "iterative",
    db: Session = Depends(get_db)
):
    # Get notes ordered by title (SQL ORDER BY)
    notes = crud.get_notes_sorted_by_title(db)

    # Create a sorted list of titles
    sorted_titles = []

    for note in notes:
        sorted_titles.append(note.title)

    # Choose algorithm
    if algo == "iterative":
        index = binary_search_iterative(
            sorted_titles,
            title
        )

    elif algo == "recursive":
        index = binary_search_recursive(
            sorted_titles,
            title,
            0,
            len(sorted_titles) - 1
        )

    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid algorithm. Use iterative or recursive."
        )

    # Not found
    if index == -1:
        return {
            "message": "Note not found"
        }

    # Return matching note
    note = notes[index]

    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "tag": note.tag,
        "owner_id": note.owner_id,
        "created_at": note.created_at
    }

@app.get("/notes/quick-find")
def quick_find(
    tag: str,
    db: Session = Depends(get_db)
):
    notes = db.query(Note).all()

    notes_data = []

    for note in notes:
        notes_data.append({
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "tag": note.tag,
            "owner_id": note.owner_id
        })

    result = linear_search(
        notes_data,
        key="tag",
        value=tag
    )

    if result is None:
        return {
            "message": "No note found",
            "tag": tag
        }

    return result

@app.get("/notes/smart-search")
def smart_search(q: str):

    results = semantic_search(
        q,
        AI_SAMPLE_NOTES,
        AI_EMBEDDINGS
    )

    return results

    
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

@app.get("/notes/quick-find")
def quick_find(
    tag: str,
    db: Session = Depends(get_db)
):
    notes = db.query(Note).all()
    notes_data = []

    for note in notes:
        notes_data.append({
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "tag": note.tags
        })

    result = linear_search(
        notes_data,
        key="tag",
        value=tag
    )

    if result is None:
        return {
            "message": "No note found",
            "tag": tag
        }
    return result

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

