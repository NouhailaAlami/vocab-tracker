import bcrypt

from vocab_tracker import repository as repo


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def register(email: str, password: str) -> int:
    """Create a user and return their id."""
    return repo.create_user(email, hash_password(password))


def login(email: str, password: str) -> int | None:
    """Return the user id if the credentials are right, else None."""
    user = repo.get_user_by_email(email)
    if user and verify_password(password, user["password_hash"]):
        return user["id"]
    return None