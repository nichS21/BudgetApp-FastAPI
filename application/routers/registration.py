from uuid import uuid4

from datetime import timedelta

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from sqlalchemy import ScalarResult, func, select, update
from sqlalchemy.exc import NoResultFound, MultipleResultsFound

from application.config import get_settings
from application.database import SessionDep
from application.models.user import ForgotPassword, PasswordReset, User, UserCreate
from application.auth_utilities import AuthDependency, check_password, create_access_token, get_password_hash

import logging
logger = logging.getLogger(__name__)

# Settings import
settings = get_settings()

registration_router = APIRouter(
    prefix="/registration",
    tags=["Router responsible for registration of new users"]
)


@registration_router.post("/sign-up")
async def sign_up(data: UserCreate, session: SessionDep) -> JSONResponse:
    try:
        # Assert that this email has not already registered previously
        result: ScalarResult = await session.scalars(select(func.count()).select_from(User).where(User.email == data.email))
        count: int = result.one()
        if count > 0:
           logger.warning(f"Failed to create an account for user with email: {data.email}. This email address is already taken.")
           return JSONResponse(content={"message": "This email has already been taken."},
                               status_code=status.HTTP_400_BAD_REQUEST) 

        recovery_code: str = str(uuid4())
        hashed_recovery_code: str = get_password_hash(recovery_code)
        hashed_password: str = get_password_hash(data.unhashed_password)
        user: User = User(
            email=data.email,
            hashed_password=hashed_password,
            hashed_recovery_code=hashed_recovery_code
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        logger.debug(f"Succesfully created user with email: {data.email}")

        access_token_expires: timedelta = timedelta(minutes=settings.access_token_expire_minutes)
        access_token: str  = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)
        content =  {"access_token": access_token,
                    "token_type": "bearer",
                    "recovery_code": recovery_code,
                    "message": "Successfully registered new user"
                    }
            
        logger.debug("Successfully authenticated user.")
        return JSONResponse(content=content, status_code=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Failed to register user with email: {data.email} \n[Exception] {e}")
        content = {"message": "Failed to register new user"}
        return JSONResponse(content=content, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@registration_router.post("/reset-password")
async def reset_password(data: PasswordReset, session: SessionDep, user: AuthDependency) -> JSONResponse:
    try:
        password_match: bool = check_password(data.old_password, user.hashed_password, user)
        if not password_match:
            logger.debug(f"Invalid password for user: {user.email}")
            return JSONResponse(
                content={
                    "message": "Invalid password"
                },
                status_code=status.HTTP_400_BAD_REQUEST
            )

        new_password: str = get_password_hash(data.new_password)

        result = await session.execute(
            update(User)
            .where(User.id == user.id)
            .values(hashed_password=new_password)
        )
        await session.commit()

        # Verify number of rows updated in the database, matching this 'WHERE' clause
        if result.rowcount != 1:
            raise Exception("No users were found with this ID, so no password was reset.")

        logger.debug(f"Successfully reset password for user with ID: {user.id}")

        # Create new access token for frontend to replace old one with
        access_token_expires: timedelta = timedelta(minutes=settings.access_token_expire_minutes)
        access_token: str  = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)

        logger.debug(f"Successfully created a new access token for user {user.id} after a password reset.")

        return JSONResponse(
            content={
                "access_token": access_token,
                "token_type": "bearer",
                "message": "Successfully reset password for this user"
            },
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Failed to reset password for user with ID: {user.id} \n[Exception] {e}")
        return JSONResponse(
            content={
                "message": "Failed to reset password for this user"
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    
@registration_router.post("/forgot-password")
async def forgot_password(data: ForgotPassword, session: SessionDep) -> JSONResponse:
    try:
        result = await session.scalars(select(User).where(User.email == data.email))
        user: User = result.one()

        valid_recovery_code: bool = check_password(data.recovery_code, user.hashed_recovery_code, user)
        if not valid_recovery_code:
            logger.debug(f"Invalid recovery code for user with ID: {user.id}. Cannot reset password")
            return JSONResponse(
                content={
                    "message": "Incorrect recovery code."
                },
                status_code=status.HTTP_400_BAD_REQUEST
            )

        new_password: str = get_password_hash(data.new_password)
        
        result = await session.execute(
            update(User)
            .where(User.id == user.id)
            .values(hashed_password=new_password)
        )
        await session.commit()

        # Verify number of rows updated in the database, matching this 'WHERE' clause
        if result.rowcount != 1:
            raise Exception("No users were found with this ID, so no password was reset.")

        logger.debug(f"Successfully reset password for user with ID: {user.id}")

        # Create new access token for frontend to replace old one with
        access_token_expires: timedelta = timedelta(minutes=settings.access_token_expire_minutes)
        access_token: str  = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)

        logger.debug(f"Successfully created a new access token for user {user.id} after a password reset.")

        return JSONResponse(
            content={
                "access_token": access_token,
                "token_type": "bearer",
                "message": "Successfully reset password for this user"
            },
            status_code=status.HTTP_200_OK
        )
    except NoResultFound as e:
        logger.warning(f"Unable to find user with email '{data.email}.' \n[Exception] {e}")
        return JSONResponse(
            content={
                "message": "No user found with given email."
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except MultipleResultsFound as e:
        # This should not be able to happen; email addresses are enforced to be unique at registration
        logger.error(f"Multiple user found with email '{data.email}.' \n[Exception] {e}")
        return JSONResponse(
            content={
                "message": "Multiple user accounts associated with this email"
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Unable to reset forgotten password. \n[Exception] {e}")
        return JSONResponse(
            content={
                "message": "Unable to reset forgotten password"
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


