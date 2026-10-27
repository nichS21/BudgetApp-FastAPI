import pytest

from httpx import AsyncClient

from fastapi import status

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from application.models.user import User
from application.testing.fixtures.infrastructure_fixtures import test_api, session
from application.testing.fixtures.model_fixtures import user
from application.testing.fixtures.testing_auth_utilities import register_test_user



@pytest.mark.asyncio
async def test_sign_up_successful(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    response = await test_api.post(
        "/registration/sign-up",
        json={
            "email": user.email,
            "unhashed_password": user.hashed_password
        }
    )

    assert response.status_code == status.HTTP_201_CREATED

    response_json: dict = response.json()

    assert "access_token" in response_json
    assert len(response_json["access_token"]) > 0
    assert "token_type" in response_json
    assert response_json["token_type"] == "bearer"
    assert "recovery_code" in response_json
    assert len(response_json["recovery_code"]) > 0
    assert "message" in response_json
    assert response_json["message"] == "Successfully registered new user"

    # Verify user now exists in the database
    result = await session.scalars(select(User).where(User.email == user.email))
    new_user: User = result.one()
    assert new_user is not None


@pytest.mark.asyncio
async def test_sign_up_extra_info(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    response = await test_api.post(
        "/registration/sign-up",
         json={
            "email": user.email,
            "unhashed_password": user.hashed_password,
            "extra_field_1": "not used",
            "extra_field_2": "still should be ignored",
            "extra_field_3": 1234
        }
    )

    assert response.status_code == status.HTTP_201_CREATED

    response_json: dict = response.json()

    assert "access_token" in response_json
    assert len(response_json["access_token"]) > 0
    assert "token_type" in response_json
    assert response_json["token_type"] == "bearer"
    assert "recovery_code" in response_json
    assert len(response_json["recovery_code"]) > 0
    assert "message" in response_json
    assert response_json["message"] == "Successfully registered new user"

    # Verify user now exists in the database
    result = await session.scalars(select(User).where(User.email == user.email))
    new_user: User = result.one()
    assert new_user is not None


@pytest.mark.asyncio
async def test_sign_up_bad_payload(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    # Test missing needed fields
    response = await test_api.post(
        "/registration/sign-up",
         json={
            "email": user.email,
            # "unhashed_password": user.hashed_password
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    response_json: dict = response.json()

    assert "access_token" not in response_json
    assert "token_type" not in response_json
    assert "recovery_code" not in response_json

    # User shouldn't exist in the database
    result = await session.scalars(select(func.count()).select_from(User).where(User.email == user.email))
    user_count: int = result.one()
    assert user_count == 0

    # Test wrong data types for needed fields
    response = await test_api.post(
        "/registration/sign-up",
            json={
            "email": 123,
            "unhashed_password": 456
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    response_json: dict = response.json()

    assert "access_token" not in response_json
    assert "token_type" not in response_json
    assert "recovery_code" not in response_json

    # User shouldn't exist in the database
    result = await session.scalars(select(func.count()).select_from(User).where(User.email == user.email))
    user_count: int = result.one()
    assert user_count == 0


@pytest.mark.asyncio
async def test_sign_up_email_already_taken(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register a user, then attempt to register another using the same email
    await register_test_user(user, test_api, session)

    response = await test_api.post(
        "/registration/sign-up",
         json={
            "email": user.email,
            "unhashed_password": user.hashed_password
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response_json: dict = response.json()

    assert "access_token" not in response_json
    assert "token_type" not in response_json
    assert "recovery_code" not in response_json

    # User should exist in the database exactly once
    result = await session.scalars(select(func.count()).select_from(User).where(User.email == user.email))
    user_count: int = result.one()
    assert user_count == 1


@pytest.mark.asyncio
async def test_reset_password_successful(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    unhashed_original_password: str = user.hashed_password      # Not actually hashed from the fixture object
    unhashed_new_password: str = "New-password-given1"
    
    # Register user to reset password for
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"

    result = await session.scalars(select(User).where(User.email == user.email))
    user_from_db: User = result.one()
    hashed_original_password: str = user_from_db.hashed_password        # Now is hashed since we have officially registered this user

    response = await test_api.post(
        "/registration/reset-password",
        headers={
            "Authorization": auth_header
        },
        json={
            "old_password": unhashed_original_password,
            "new_password": unhashed_new_password
        }
    )

    assert response.status_code == status.HTTP_200_OK

    response_json: dict = response.json()

    assert "access_token" in response_json
    assert len(response_json["access_token"]) > 0
    assert "token_type" in response_json
    assert response_json["token_type"] == "bearer"
    assert "message" in response_json
    assert response_json["message"] == "Successfully reset password for this user"

    result = await session.scalars(select(User).where(User.email == user.email))
    user_from_db: User = result.one()

    assert hashed_original_password != user_from_db.hashed_password


    # Login with the new password
    response = await test_api.post(
        "/auth/login",
        data={
            "username": user.email,
            "password": unhashed_new_password
        }
    )

    assert response.status_code == status.HTTP_200_OK
    

@pytest.mark.asyncio
async def test_reset_password_extra_info(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    unhashed_original_password: str = user.hashed_password      # Not actually hashed from the fixture object
    unhashed_new_password: str = "New-password-given1"
    
    # Register user to reset password for
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"

    result = await session.scalars(select(User).where(User.email == user.email))
    user_from_db: User = result.one()
    hashed_original_password: str = user_from_db.hashed_password        # Now is hashed since we have officially registered this user

    # Extra fields given, but should still be successful regardless
    response = await test_api.post(
        "/registration/reset-password",
        headers={
            "Authorization": auth_header
        },
        json={
            "old_password": unhashed_original_password,
            "new_password": unhashed_new_password,
            "extra_field_1": "not used",
            "extra_field_2": 1234
        }
    )

    assert response.status_code == status.HTTP_200_OK

    response_json: dict = response.json()

    assert "access_token" in response_json
    assert len(response_json["access_token"]) > 0
    assert "token_type" in response_json
    assert response_json["token_type"] == "bearer"
    assert "message" in response_json
    assert response_json["message"] == "Successfully reset password for this user"

    result = await session.scalars(select(User).where(User.email == user.email))
    user_from_db: User = result.one()

    assert hashed_original_password != user_from_db.hashed_password


    # Login with the new password
    response = await test_api.post(
        "/auth/login",
        data={
            "username": user.email,
            "password": unhashed_new_password
        }
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_reset_password_bad_payload(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    unhashed_original_password: str = user.hashed_password      # Not actually hashed from the fixture object
    unhashed_new_password: str = "New-password-given1"
    
    # Register user to reset password for
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"

    result = await session.scalars(select(User).where(User.email == user.email))
    user_from_db: User = result.one()
    hashed_original_password: str = user_from_db.hashed_password        # Now is hashed since we have officially registered this user

    
    # Test missing fields
    response = await test_api.post(
        "/registration/reset-password",
        headers={
            "Authorization": auth_header
        },
        json={
            "old_password": unhashed_original_password,
            # "new_password": unhashed_new_password
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    response_json: dict = response.json()

    assert "access_token" not in response_json
    assert "token_type" not in response_json
   

    result = await session.scalars(select(User).where(User.email == user.email))
    user_from_db: User = result.one()

    assert hashed_original_password == user_from_db.hashed_password


    # Login with the new password
    response = await test_api.post(
        "/auth/login",
        data={
            "username": user.email,
            "password": unhashed_new_password
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


    # Test incorrect data types
    response = await test_api.post(
        "/registration/reset-password",
        headers={
            "Authorization": auth_header
        },
        json={
            "old_password": 12423,
            "new_password": 325
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    response_json: dict = response.json()

    assert "access_token" not in response_json
    assert "token_type" not in response_json
   

    result = await session.scalars(select(User).where(User.email == user.email))
    user_from_db: User = result.one()

    assert hashed_original_password == user_from_db.hashed_password


    # Login with the new password
    response = await test_api.post(
        "/auth/login",
        data={
            "username": user.email,
            "password": unhashed_new_password
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_reset_password_wrong_password(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    unhashed_new_password: str = "New-password-given1"
    
    # Register user to reset password for
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"

    result = await session.scalars(select(User).where(User.email == user.email))
    user_from_db: User = result.one()
    hashed_original_password: str = user_from_db.hashed_password        # Now is hashed since we have officially registered this user

    response = await test_api.post(
        "/registration/reset-password",
        headers={
            "Authorization": auth_header
        },
        json={
            "old_password": "not the old password",
            "new_password": unhashed_new_password
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response_json: dict = response.json()

    assert "access_token" not in response_json
    assert "token_type" not in response_json
    assert "message" in response_json
    assert response_json["message"] == "Invalid password"
 

    result = await session.scalars(select(User).where(User.email == user.email))
    user_from_db: User = result.one()

    assert hashed_original_password == user_from_db.hashed_password


    # Login with the new password
    response = await test_api.post(
        "/auth/login",
        data={
            "username": user.email,
            "password": unhashed_new_password
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    

@pytest.mark.asyncio
async def test_reset_password_no_auth(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    unhashed_original_password: str = user.hashed_password      # Not actually hashed from the fixture object
    unhashed_new_password: str = "New-password-given1"
    
    # Register user to reset password for
    await register_test_user(user, test_api, session)

    result = await session.scalars(select(User).where(User.email == user.email))
    user_from_db: User = result.one()
    hashed_original_password: str = user_from_db.hashed_password        # Now is hashed since we have officially registered this user

    response = await test_api.post(
        "/registration/reset-password",
        headers={
            "Authorization": "definitely not an auth header"
        },
        json={
            "old_password": unhashed_original_password,
            "new_password": unhashed_new_password
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response_json: dict = response.json()

    assert "access_token" not in response_json
    assert "token_type" not in response_json


    result = await session.scalars(select(User).where(User.email == user.email))
    user_from_db: User = result.one()

    assert hashed_original_password == user_from_db.hashed_password


    # Login with the new password
    response = await test_api.post(
        "/auth/login",
        data={
            "username": user.email,
            "password": unhashed_new_password
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_forgot_password_successful(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    user_email: str = user.email
    new_unhashed_password: str = "gullible-7super-reactant"
    
    # Register user to reset password for
    registration_results: dict = await register_test_user(user, test_api, session)
    recovery_code: str = registration_results["recovery_code"]

    result = await session.scalars(select(User).where(User.email == user_email))
    registered_user: User = result.one()
    old_hashed_password: str = registered_user.hashed_password

    response = await test_api.post(
        "/registration/forgot-password",
        json={
            "email": registered_user.email,
            "recovery_code": recovery_code,
            "new_password": new_unhashed_password
        }
    )

    response.status_code == status.HTTP_200_OK

    # Verify data sent back in response
    response_json: dict = response.json()
    assert "access_token" in  response_json
    assert len(response_json["access_token"]) > 0
    assert "token_type" in response_json
    assert response_json["token_type"] == "bearer"
    assert "message" in response_json
    assert response_json["message"] == "Successfully reset password for this user"

    # Verify password was changed in database
    result = await session.scalars(select(User).where(User.email == user_email))
    new_pass_user: User = result.one()

    assert new_pass_user.hashed_password != old_hashed_password

    # Verify login with new password works
    response = await test_api.post(
        "auth/login",
        data={
            "username": new_pass_user.email,
            "password": new_unhashed_password
        }
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_forgot_password_extra_info(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    user_email: str = user.email
    new_unhashed_password: str = "gullible-7super-reactant"
    
    # Register user to reset password for
    registration_results: dict = await register_test_user(user, test_api, session)
    recovery_code: str = registration_results["recovery_code"]
    
    result = await session.scalars(select(User).where(User.email == user_email))
    registered_user: User = result.one()
    old_hashed_password: str = registered_user.hashed_password

    response = await test_api.post(
        "/registration/forgot-password",
        json={
            "email": registered_user.email,
            "recovery_code": recovery_code,
            "new_password": new_unhashed_password,
            "extra_field_1": "not used",
            "extra_field_2": 124
        }
    )

    response.status_code == status.HTTP_200_OK

    # Verify data sent back in response
    response_json: dict = response.json()
    assert "access_token" in  response_json
    assert len(response_json["access_token"]) > 0
    assert "token_type" in response_json
    assert response_json["token_type"] == "bearer"
    assert "message" in response_json
    assert response_json["message"] == "Successfully reset password for this user"

    # Verify password was changed in database
    result = await session.scalars(select(User).where(User.email == user_email))
    new_pass_user: User = result.one()

    assert new_pass_user.hashed_password != old_hashed_password

    # Verify login with new password works
    response = await test_api.post(
        "auth/login",
        data={
            "username": new_pass_user.email,
            "password": new_unhashed_password
        }
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_forgot_password_bad_payload(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    user_email: str = user.email
    new_unhashed_password: str = "gullible-7super-reactant"
        
    # Register user to reset password for
    registration_results: dict = await register_test_user(user, test_api, session)
    recovery_code: str = registration_results["recovery_code"]
    
    result = await session.scalars(select(User).where(User.email == user_email))
    registered_user: User = result.one()
    old_hashed_password: str = registered_user.hashed_password

    # Missing needed fields #
    response = await test_api.post(
        "/registration/forgot-password",
        json={
            # "email": registered_user.email,
            "recovery_code": recovery_code,
            # "new_password": new_unhashed_password
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Verify data sent back in response
    response_json: dict = response.json()
    assert "access_token" not in  response_json
    assert "token_type" not in response_json

    # Verify password was not changed in database
    result = await session.scalars(select(User).where(User.email == user_email))
    new_pass_user: User = result.one()

    assert new_pass_user.hashed_password == old_hashed_password

    # Verify login with new password does not work
    response = await test_api.post(
        "auth/login",
        data={
            "username": new_pass_user.email,
            "password": new_unhashed_password
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    # Needed fields have wrong data types #
    response = await test_api.post(
        "/registration/forgot-password",
        json={
            "email": 1234,
            "recovery_code": recovery_code,
            "new_password": 7891
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Verify data sent back in response
    response_json: dict = response.json()
    assert "access_token" not in  response_json
    assert "token_type" not in response_json

    # Verify password was not changed in database
    result = await session.scalars(select(User).where(User.email == user_email))
    new_pass_user: User = result.one()

    assert new_pass_user.hashed_password == old_hashed_password

    # Verify login with new password does not work
    response = await test_api.post(
        "auth/login",
        data={
            "username": new_pass_user.email,
            "password": new_unhashed_password
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_forgot_password_no_user(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    user_email: str = user.email
    new_unhashed_password: str = "gullible-7super-reactant"
    
    # Register user to reset password for
    registration_results: dict = await register_test_user(user, test_api, session)
    recovery_code: str = registration_results["recovery_code"]
    
    result = await session.scalars(select(User).where(User.email == user_email))
    registered_user: User = result.one()
    old_hashed_password: str = registered_user.hashed_password

    response = await test_api.post(
        "/registration/forgot-password",
        json={
            "email": "nonexistant@unknown.com",         # email that doesn't belong to any user in the system
            "recovery_code": recovery_code,
            "new_password": new_unhashed_password
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Verify data sent back in response
    response_json: dict = response.json()
    assert "access_token" not in  response_json
    assert "token_type" not in response_json

    # Verify password was not changed in database
    result = await session.scalars(select(User).where(User.email == user_email))
    new_pass_user: User = result.one()

    assert new_pass_user.hashed_password == old_hashed_password

    # Verify login with new password does not work
    response = await test_api.post(
        "auth/login",
        data={
            "username": new_pass_user.email,
            "password": new_unhashed_password
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.asyncio
async def test_forgot_password_bad_recovery_code(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    user_email: str = user.email
    new_unhashed_password: str = "gullible-7super-reactant"
    
    # Register user to reset password for
    await register_test_user(user, test_api, session)
    
    result = await session.scalars(select(User).where(User.email == user_email))
    registered_user: User = result.one()
    old_hashed_password: str = registered_user.hashed_password

    response = await test_api.post(
        "/registration/forgot-password",
        json={
            "email": registered_user.email,         
            "recovery_code": "not the recovery code for this user",
            "new_password": new_unhashed_password
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Verify data sent back in response
    response_json: dict = response.json()
    assert "access_token" not in  response_json
    assert "token_type" not in response_json

    # Verify password was not changed in database
    result = await session.scalars(select(User).where(User.email == user_email))
    new_pass_user: User = result.one()

    assert new_pass_user.hashed_password == old_hashed_password

    # Verify login with new password does not work
    response = await test_api.post(
        "auth/login",
        data={
            "username": new_pass_user.email,
            "password": new_unhashed_password
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST

