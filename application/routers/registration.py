from datetime import timedelta

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from sqlalchemy import ScalarResult, func, select

from application.config import get_settings
from application.database import SessionDep
from application.models.user import User, UserCreate
from application.auth_utilities import create_access_token, get_password_hash

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

        # Create user
        hashed_password: str = get_password_hash(data.unhashed_password)
        user: User = User(
            email=data.email,
            hashed_password=hashed_password
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        logger.debug(f"Succesfully created user with email: {data.email}")

        # Make an access token
        access_token_expires: timedelta = timedelta(minutes=settings.access_token_expire_minutes)
        access_token: str  = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)
        content =  {"access_token": access_token,
                    "token_type": "bearer",
                    "message": "Successfully registered new user"
                    }
            
        logger.debug("Successfully authenticated user.")
        return JSONResponse(content=content, status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Failed to register user with email: {data.email} \n[Exception] {e}")
        content = {"message": "Failed to register new user"}
        return JSONResponse(content=content, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# TODO: forgot password endpoint


# TODO: reset password endpoint