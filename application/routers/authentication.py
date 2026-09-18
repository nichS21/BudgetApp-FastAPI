from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, status
from fastapi.params import Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm


from sqlalchemy import ScalarResult, select

from application.auth_utilities import check_password, create_access_token
from application.config import get_settings
from application.database import SessionDep
from application.models.user import User

import logging
logger = logging.getLogger(__name__)


# Settings import
settings = get_settings()


# Authentication Router
authentication_router = APIRouter(
    prefix="/auth",
    tags=["Router responsible for authentication with regards to JWT"]
)


@authentication_router.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep) -> JSONResponse:
    try:

        # Note 'OAuth2PasswordRequestForm' utility uses 'username' and 'password' for the login, but for this app a user's email is their username
        result: ScalarResult = await session.scalars(select(User).where(User.email == form_data.username))
        user: User = result.one()

        password_match: bool = check_password(form_data.password, user.hashed_password, user)
        if not password_match:
            logger.debug(f"Invalid password for user: {user.email}")
            raise Exception("Invalid password") 

        # 'sub' field is the optional subject field of the auth token (Per official JWT standards)
        access_token_expires: timedelta = timedelta(minutes=settings.access_token_expire_minutes)
        access_token: str  = create_access_token(data={"sub": str(user.id)}, expires_delta=access_token_expires)
        content =  {"access_token": access_token,
                    "token_type": "bearer",
                    "message": "Successfully logged in user"
                    }
        
        logger.debug("Successfully authenticated user.")
        return JSONResponse(content=content, status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Incorrect password or username. \n[Exception] {e}")
        content = {"message": "Incorrect password or username; unable to log in."}
        headers={"WWW-Authenticate": "Bearer"}                          # This is an OAuth standard to return this header upon 401 to give what was expected to auth succcessfully
        return JSONResponse(content=content, status_code=status.HTTP_400_BAD_REQUEST, headers=headers)


