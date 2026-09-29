import pytest

from httpx import AsyncClient

from fastapi import status

from sqlalchemy.ext.asyncio import AsyncSession

from application.models.user import User
from application.testing.fixtures.auth_utilities import register_test_user
from application.testing.fixtures.model_fixtures import user
from application.testing.fixtures.infrastructure_fixtures import test_api, session



@pytest.mark.asyncio
async def test_login_successful(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user with app so can login
    await register_test_user(user, test_api, session)

    response = await test_api.post(
        "/auth/login",
        data={
            "username": user.email,
            "password": user.hashed_password
        }
    )

    assert response.status_code == status.HTTP_200_OK

    response_json: dict = response.json()
    assert "access_token" in response_json
    assert len(response_json["access_token"]) > 0
    assert "token_type" in response_json
    assert response_json["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_incorrect_password(user: user, test_api: AsyncClient, session: AsyncSession) -> None:
    await register_test_user(user, test_api, session)

    response = await test_api.post(
        "/auth/login",
        data={
            "username": user.email,
            "password": "not-the-password"
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response_json: dict = response.json()
    assert "message" in response_json
    assert response_json["message"] == "Incorrect password or username; unable to log in."


@pytest.mark.asyncio
async def test_login_no_user(test_api: AsyncClient, session: AsyncSession) -> None:
    response = await test_api.post(
            "/auth/login",
            data={
                "username": "email@domain.com",
                "password": "AwfulPassword"
            }
        )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response_json: dict = response.json()
    assert "message" in response_json
    assert response_json["message"] == "Incorrect password or username; unable to log in."


@pytest.mark.asyncio
async def test_login_bad_payload(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    await register_test_user(user, test_api, session)

    # Missing fields
    response = await test_api.post(
        "/auth/login",
        data={
            "username": user.email,
            # "password": user.hashed_password
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Too many fields
    # Note that this one will succeed and the extra fields are just ignored
    response = await test_api.post(
        "/auth/login",
        data={
            "username": user.email,
            "password": user.hashed_password,
            "another field": "extra value",
            "unneeded": 0
        }
    )

    assert response.status_code == status.HTTP_200_OK

    response_json: dict = response.json()
    assert "access_token" in response_json
    assert len(response_json["access_token"]) > 0
    assert "token_type" in response_json
    assert response_json["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_incorrect_types(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    await register_test_user(user, test_api, session)

    response = await test_api.post(
        "/auth/login",
        data={
            "username": 47,
            "password": 91
        }
    )

    # FastAPI just casts the data once it reaches the server and then attempts to find a user 
    #  the with supplied data (of which there is not one)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
