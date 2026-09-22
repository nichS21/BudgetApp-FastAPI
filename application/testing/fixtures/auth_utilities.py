from sqlalchemy import ScalarResult, select
from sqlalchemy.ext.asyncio import AsyncSession

from httpx import AsyncClient

from fastapi import status

from application.models.user import User


async def register_test_user(user: User, test_api: AsyncClient, session: AsyncSession) -> dict:
    # Register the test user
    response = await test_api.post(
        "/registration/sign-up",
        json={
            "email": user.email,
            "unhashed_password": user.hashed_password       # Password is unhashed from the fixture, since has not yet been registered officially
        }
    )

    assert response.status_code == status.HTTP_201_CREATED

    # Return user's auth token and user ID
    response_json = response.json()

    result: ScalarResult = await session.scalars(select(User).where(User.email == user.email))
    db_user: User = result.one()

    return {"user_id" : db_user.id, "access_token": response_json["access_token"]}

