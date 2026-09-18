from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

import jwt

from pwdlib import PasswordHash

from sqlalchemy import ScalarResult, select

from application.config import get_settings
from application.database import SessionDep
from application.models.user import User

import logging
logger = logging.getLogger(__name__)

# Settings import
settings = get_settings()


# Intialize OAuth for endpoint authentication using JWT Bearer tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
OAuthDependency = Annotated[str, Depends(oauth2_scheme)]                 


# Password hasher and utilities
hash = PasswordHash.recommended()
DUMMY_HASH: str = hash.hash("PreventTimingAttacks")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash.verify(plain_password, hashed_password)

def check_password(plain_password: str, hashed_password: str, user: User | None = None) -> bool:
    if user is None:
        return verify_password(plain_password, DUMMY_HASH)          # To help mitigate timing attacks, even if there is no user, still hash something to give no indication of time it takes to run hashing algo for authentication.
    else:
        return verify_password(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return hash.hash(password)

def create_access_token(data: dict, expires_delta: datetime.timedelta ) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.hashing_algo)
    return encoded_jwt

async def get_current_user(session: SessionDep, token: OAuthDependency) -> User:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.hashing_algo])
        user_id: int = int(payload.get("sub"))

        if user_id is None:
            raise Exception("No user ID supplied in auth token.")

        result: ScalarResult = await session.scalars(select(User).where(User.id == user_id))
        user: User = result.one()

        return user
    except Exception as e:
        logger.error(f"Failed to validate auth token. \n[Exception] {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
                            detail="Failed to authenticate",
                            headers={"WWW-Authenticate": "Bearer"}                          # This is an OAuth standard to return this header upon 401 to give what was expected to auth succcessfully
                            )    # Bubble up exception and return a 401 to the API requester


# Main auth dependnecy for the application
AuthDependency = Annotated[User, Depends(get_current_user)]             # Checks and sees if a request contains an authentication header of 'Bearer' 
                                                                        #   type with a valid JWT containing a user ID, then returns the user
