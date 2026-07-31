from .database import SessionLocal, Base, engine
from .models import User, Note
from .ranking_dataset import RANKING_DATASET

SEED_USERS = [
    {
        "id": 1,
        "name": "Alice",
        "email": "alice@example.com",
        "password": "alicepass123"
    },
    {
        "id": 2,
        "name": "Bob",
        "email": "bob@example.com",
        "password": "bobpass123"
    },
]


SEED_NOTES = [
    {
        "id": 1,
        "owner_id": 1,
        "title": "Standup Summary",
        "tag": "work",
        "content": "Discussed sprint progress, blockers on the payments API integration, and the plan for the demo on Friday."
    },
    {
        "id": 2,
        "owner_id": 1,
        "title": "Sprint Retro Notes",
        "tag": "work",
        "content": "Retro highlighted communication gaps between frontend and backend teams and agreed on daily syncs going forward."
    },
    {
        "id": 3,
        "owner_id": 2,
        "title": "One on One",
        "tag": "work",
        "content": "Quick check-in, no blockers, discussed career growth goals for next quarter."
    },
    {
        "id": 4,
        "owner_id": 1,
        "title": "Morning Run",
        "tag": "health",
        "content": "Ran 5km along the river trail before breakfast, felt great."
    },
    {
        "id": 5,
        "owner_id": 2,
        "title": "Doctor Visit",
        "tag": "health",
        "content": "Annual checkup went well, blood pressure normal, scheduled next visit in six months."
    },
    {
        "id": 6,
        "owner_id": 1,
        "title": "Pasta Recipe",
        "tag": "recipes",
        "content": "Boil pasta, saute garlic in olive oil, add tomatoes, basil, and a pinch of chili flakes."
    },
    {
        "id": 7,
        "owner_id": 2,
        "title": "Smoothie Recipe",
        "tag": "recipes",
        "content": "Blend banana, spinach, almond milk, and a spoon of peanut butter for breakfast."
    },
    {
        "id": 8,
        "owner_id": 1,
        "title": "Flight Booking",
        "tag": "travel",
        "content": "Booked a round trip flight for the December vacation, window seat confirmed."
    },
    {
        "id": 9,
        "owner_id": 2,
        "title": "Random Thought",
        "tag": "random",
        "content": "Maybe the library needs a better recommendation system based on reading history."
    },
    {
        "id": 10,
        "owner_id": 1,
        "title": "Quote To Remember",
        "tag": "random",
        "content": "Done is better than perfect, keep shipping."
    },
]


def seed_database():

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # Create users
        for user_data in SEED_USERS:
            existing_user = db.query(User).filter(
                User.id == user_data["id"]
            ).first()

            if existing_user is None:
                user = User(
                    id=user_data["id"],
                    name=user_data["name"],
                    email=user_data["email"],
                    password=user_data["password"]
                )

                db.add(user)

        db.commit()

        demo_notes = [

           {
               "title": "API Authentication Guide",
               "content": "JWT and token troubleshooting notes",
                "tags": "kb-demo"
            },

            {
                "title": "Database Backup Procedure",
                "content": "Steps for restoring production database",
                "tags": "kb-demo"
            },

           {
                "title": "Docker Deployment Checklist",
                "content": "Container deployment commands",
                "tags": "kb-demo"
            },

           {
                "title": "Kubernetes Health Check",
                "content": "Pod monitoring commands",
                "tags": "kb-demo"
            },

           {
               "title": "Logging Best Practices",
               "content": "Application logging guidelines",
               "tags": "kb-demo"
            }

        ]

        for item in demo_notes:

           note = Note(
              title=item["title"],
              content=item["content"],
              tags=item["tags"],
              owner_id=1
            )

           db.add(note)
           db.commit()
        # Create original Part 1 notes
        for note_data in SEED_NOTES:
            existing_note = db.query(Note).filter(
                Note.id == note_data["id"]
            ).first()

            if existing_note is None:
                note = Note(
                    id=note_data["id"],
                    owner_id=note_data["owner_id"],
                    title=note_data["title"],
                    tag=note_data["tag"],
                    content=note_data["content"]
                )

                db.add(note)

        db.commit()

        # Create ranking dataset notes
        for ranking_note in RANKING_DATASET:

            existing_note = db.query(Note).filter(
                Note.title == ranking_note["title"]
            ).first()

            if existing_note is None:
                note = Note(
                    owner_id=1,
                    title=ranking_note["title"],
                    content=ranking_note["content"],
                    tag="random"
                )

                db.add(note)

        db.commit()

        all_notes = db.query(Note).all()

        print("\nALL NOTES IN DATABASE:")
        for note in all_notes:
            print(note.id, note.title)

        print("Database seeded successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()