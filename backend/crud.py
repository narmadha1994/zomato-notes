from sqlalchemy.orm import Session

from .models import Note, User
from .schemas import NoteCreate, NoteUpdate, UserCreate


# -------------------------
# USER CRUD
# -------------------------

def create_user(db: Session, user_data: UserCreate):
    user = User(
        name=user_data.name,
        email=user_data.email,
        password=user_data.password
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(
        User.email == email
    ).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(
        User.id == user_id
    ).first()


# -------------------------
# NOTE CRUD
# -------------------------

def create_note(db: Session, note_data: NoteCreate):
    note = Note(
        title=note_data.title,
        content=note_data.content,
        tag=note_data.tag,
        owner_id=note_data.owner_id
    )

    db.add(note)
    db.commit()
    db.refresh(note)

    return note


def get_notes(db: Session, tag: str | None = None):
    query = db.query(Note)

    if tag:
        query = query.filter(Note.tag == tag)

    return query.order_by(
        Note.created_at.desc()
    ).all()


def get_note_by_id(db: Session, note_id: int):
    return db.query(Note).filter(
        Note.id == note_id
    ).first()


def update_note(
    db: Session,
    note: Note,
    note_data: NoteUpdate
):
    note.title = note_data.title
    note.content = note_data.content
    note.tag = note_data.tag

    db.commit()
    db.refresh(note)

    return note


def delete_note(db: Session, note: Note):
    db.delete(note)
    db.commit()