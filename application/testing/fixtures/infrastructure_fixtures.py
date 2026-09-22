import pytest_asyncio

from httpx import ASGITransport, AsyncClient

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from application.app import app
from application.database import get_session
from application.config import get_settings
from application.models import *          # Import models so Base.metadata gets filled with Table data for each model


# App settings from environment variables
settings = get_settings()

# Configure needed objects for test database sessions and app client
test_connection_str: str = settings.connection_str + "-test"        # Append '-test' to database name in connection string
test_engine = create_async_engine(test_connection_str, echo=True)
Base = ModelBase()                                                  # Get table metadata from the base class used by all models
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest_asyncio.fixture()
async def session():
    # For each test drop all tables if present, then recreate them as empty tables, for each test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Yield a session, until all code that calls this has executed, then end it
    async with TestingSessionLocal() as db:
        yield db


@pytest_asyncio.fixture()
async def test_api(session):

    # Dependency override so don't use normal database during testing
    async def override_get_session():
        try:
            yield session
        finally:
            await session.close()

    app.dependency_overrides[get_session] = override_get_session

    yield AsyncClient(transport=ASGITransport(app=app), base_url="http://budget-api")