from app.model.user import User


def test_sign_up_success(client, database) -> None:
    database.create_database()

    payload = {
        "email": "john@example.com",
        "password": "12345678",
        "name": "John Doe",
        "avatarUrl": "https://example.com/avatar.png",
    }
    response = client.post("/api/v1/auth/sign-up", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["id"]
    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]
    assert data["avatarUrl"] == payload["avatarUrl"]
    assert "createdAt" in data


def test_sign_in_success_after_sign_up(client, database) -> None:
    database.create_database()

    sign_up_payload = {
        "email": "alice@example.com",
        "password": "12345678",
        "name": "Alice",
    }
    client.post("/api/v1/auth/sign-up", json=sign_up_payload)

    sign_in_payload = {
        "email__eq": sign_up_payload["email"],
        "password": sign_up_payload["password"],
    }
    response = client.post("/api/v1/auth/sign-in", json=sign_in_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["expiration"]
    assert data["user_info"]["email"] == sign_up_payload["email"]
    assert "hashed_password" not in data["user_info"]


def test_sign_up_duplicated_email(client, database) -> None:
    database.create_database()

    payload = {
        "email": "dup@example.com",
        "password": "12345678",
        "name": "Duplicate",
    }
    first_response = client.post("/api/v1/auth/sign-up", json=payload)
    second_response = client.post("/api/v1/auth/sign-up", json=payload)

    assert first_response.status_code == 200
    assert second_response.status_code == 400


def test_sign_in_wrong_password(client, database) -> None:
    database.create_database()

    email = "wrong-pass@example.com"
    password = "12345678"
    user = User(
        email=email,
        name="Wrong Pass",
        avatar_url=None,
        hashed_password="$argon2id$v=19$m=65536,t=3,p=4$8B42N1VrNE8wR0N1SE1LMQ$fe1bpVSa7WKfMRNcAIt0en2f6h9w8ebtLiIKlaSuAJA",
        user_token="wrongpass1",
        is_active=True,
        is_superuser=False,
    )
    with database.session() as session:
        session.add(user)
        session.commit()

    response = client.post("/api/v1/auth/sign-in", json={"email__eq": email, "password": password + "x"})

    assert response.status_code == 403
