from random import randint
from faker import Faker

from app import app
from models import db, User, Note


fake = Faker()


def clear_data():
    """
    Remove existing rows.
    This does NOT drop tables or touch migrations; it just clears rows.
    """
    print("Clearing existing data...")
    # Order matters because of foreign key constraints: child rows first.
    Note.query.delete()
    User.query.delete()
    db.session.commit()


def create_users():
    """
    Create a few demo users with known passwords for easy testing.
    Returns the list of created User objects.
    """
    print("Creating users...")

    users_data = [
        # username, password
        ("alice", "password123"),
        ("bob", "password123"),
        ("charlie", "password123"),
    ]

    users = []

    for username, password in users_data:
        user = User(username=username)
        user.password = password  # triggers hashing in models.User.password setter
        db.session.add(user)
        users.append(user)

    db.session.commit()

    print(f"Created {len(users)} users.")
    return users


def create_notes(users):
    """
    Create some demo notes for each user.
    """
    print("Creating notes...")

    total_notes = 0

    for user in users:
        # 3–6 notes per user
        for _ in range(randint(3, 6)):
            note = Note(
                title=fake.sentence(nb_words=4),
                content=fake.paragraph(nb_sentences=3),
                user_id=user.id,
            )
            db.session.add(note)
            total_notes += 1

    db.session.commit()

    print(f"Created {total_notes} notes.")


def run_seed():
    """
    Main entrypoint. Wrap everything in app.app_context() so
    SQLAlchemy knows which app / DB to use.
    """
    with app.app_context():
        clear_data()
        users = create_users()
        create_notes(users)
        print("Seeding complete.")


if __name__ == "__main__":
    run_seed()
