# Fake auth para MVP
FAKE_USERS = {
    "martha": "TAC2026",
    "claudia": "TAC2026"
}

def authenticate(username: str, password: str) -> bool:
    return FAKE_USERS.get(username) == password
