import pytest

from httpx import AsyncClient

from fastapi import status

from sqlalchemy import ScalarResult, func, select
from sqlalchemy.ext.asyncio import AsyncSession


from application.models.income import Income
from application.models.user import User
from application.testing.fixtures.infrastructure_fixtures import test_api, session
from application.testing.fixtures.model_fixtures import user, income
from application.testing.fixtures.auth_utilities import register_test_user


@pytest.mark.asyncio
async def test_income_create_successful(user: User, test_api: AsyncClient, session: AsyncSession) -> None: 
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]
    income_tax: float = 20.5
    annual_salary: int = 90000

    response = await test_api.post(
        "/income/",
        headers={
            "Authorization": auth_header
        },
        json={
            "annual_salary": annual_salary,
            "income_tax": income_tax,
            "user_id": user_id
        }
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"message": "Created annual income and tax successfully"}

    # Query DB to verify was created
    result: ScalarResult = await session.scalars(select(Income).where(Income.user_id == user_id))
    income: Income = result.one()

    assert income.annual_salary == annual_salary
    assert income.income_tax == income_tax
    assert income.user_id ==  user_id


@pytest.mark.asyncio
async def test_income_create_extra_fields(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]
    income_tax: float = 20.5
    annual_salary: int = 90000

    # Give extra fields in request body. Note that FastAPI ignores these fields since they don't map to the dataclass object at that route
    response = await test_api.post(
        "/income/",
        headers={
            "Authorization": auth_header
        },
        json={
            "annual_salary": annual_salary,
            "income_tax": income_tax,
            "user_id": user_id,
            "extra": "Never used",
            "More": "Still not used"
        }
    )

    # 
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"message": "Created annual income and tax successfully"}

    # Query DB to verify was created
    result: ScalarResult = await session.scalars(select(Income).where(Income.user_id == user_id))
    income: Income = result.one()

    assert income.annual_salary == annual_salary
    assert income.income_tax == income_tax
    assert income.user_id ==  user_id


@pytest.mark.asyncio
async def test_income_create_bad_payload(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]
    income_tax: str = "bad data"
    annual_salary: str = "more bad data"

    # Request that is missing required data fields
    response = await test_api.post(
        "/income/",
        headers={
            "Authorization": auth_header
        },
        json={
            "user_id": user_id
        }
    )

    # API should get bad data and immediately throw away request because it is receiving unexpected data or data in the wrong format 
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Request with bad data types
    response = await test_api.post(
        "/income/",
        headers={
            "Authorization": auth_header
        },
        json={
            "annual_salary": annual_salary,
            "income_tax": income_tax,
            "user_id": user_id
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Query database to verify that was NOT created
    result: ScalarResult = await session.scalars(select(func.count()).select_from(Income).where(Income.user_id == user_id))
    income_count: int = result.one()
    assert income_count == 0


@pytest.mark.asyncio
async def test_income_create_no_user(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = 999           # ID to a user that doesn't exist
    income_tax: float = 20.5
    annual_salary: int = 90000

    response = await test_api.post(
        "/income/",
        headers={
            "Authorization": auth_header
        },
        json={
            "annual_salary": annual_salary,
            "income_tax": income_tax,
            "user_id": user_id
        }
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"message": "Failed to create an income and tax for this user."}

    # Query database to verify that was NOT created
    result: ScalarResult = await session.scalars(select(func.count()).select_from(Income).where(Income.user_id == user_id))
    income_count: int = result.one()
    assert income_count == 0


@pytest.mark.asyncio
async def test_income_create_income_already_exists(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]
    income_tax: float = 20.5
    annual_salary: int = 90000

    response = await test_api.post(
        "/income/",
        headers={
            "Authorization": auth_header
        },
        json={
            "annual_salary": annual_salary,
            "income_tax": income_tax,
            "user_id": user_id
        }
    )

    # Now that an income has been added for this user already, try it again
    response = await test_api.post(
        "/income/",
        headers={
            "Authorization": auth_header
        },
        json={
            "annual_salary": annual_salary,
            "income_tax": income_tax,
            "user_id": user_id
        }
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"message": "Failed to create an income and tax for this user."}

    # Query database to verify that there is only one income for this user
    result: ScalarResult = await session.scalars(select(func.count()).select_from(Income).where(Income.user_id == user_id))
    income_count: int = result.one()
    assert income_count == 1


@pytest.mark.asyncio
async def test_income_create_no_auth(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID.
    registration_results: dict = await register_test_user(user, test_api, session)
    user_id: int = registration_results["user_id"]
    income_tax: float = 20.5
    annual_salary: int = 90000

    response = await test_api.post(
        "/income/",
        headers={
            "Authorization": "Bearer no-auth"
        },
        json={
            "annual_salary": annual_salary,
            "income_tax": income_tax,
            "user_id": user_id
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Failed to authenticate"}

    # Query database to verify that was NOT created
    result: ScalarResult = await session.scalars(select(func.count()).select_from(Income).where(Income.user_id == user_id))
    income_count: int = result.one()
    assert income_count == 0
    

    
@pytest.mark.asyncio
async def test_get_income_successful(user: User, income: Income, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    income.user_id = user_id
    session.add(income)
    await session.commit()
    await session.refresh(income)

    response = await test_api.get(
        f"/income/{user_id}",
        headers={
            "Authorization": auth_header
        }
    )

    response_json = response.json()
    assert response.status_code == status.HTTP_200_OK
   
    assert response_json["income"]["annual_salary"] == income.annual_salary
    assert response_json["income"]["income_tax"] == income.income_tax
    assert response_json["income"]["user_id"] == income.user_id


@pytest.mark.asyncio
async def test_get_income_bad_primary_key(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"

    response = await test_api.get(
        f"/income/not-a-pk",
        headers={
            "Authorization": auth_header
        }
    )

    # API should recognize bad data getting sent in request and respond appropriately
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
async def test_get_income_nonexistant_primary_key(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"

    response = await test_api.get(
        f"/income/777",
        headers={
            "Authorization": auth_header
        }
    )

    # API shouldn't be able to find this in the database
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json() == {"message": "Failed retrieve annual income and tax for this user."}


@pytest.mark.asyncio
async def test_get_income_no_auth(user: User, income: Income, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID.
    registration_results: dict = await register_test_user(user, test_api, session)
    user_id: int = registration_results["user_id"]
    
    income.user_id = user_id
    session.add(income)
    await session.commit()
    await session.refresh(income)
    
    response = await test_api.get(
        f"/income/{income.id}",
        headers={
            "Authorization": "Bearer no-auth"
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED



@pytest.mark.asyncio
async def test_patch_income_successful(user: User, income: Income, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    income.user_id = user_id
    session.add(income)
    await session.commit()
    await session.refresh(income)

    new_salary: int = 95000
    new_tax: float = 35.0
    response = await test_api.patch(
        f"/income/{user_id}",
        headers={
            "Authorization": auth_header
        },
        json = {
            "annual_salary": new_salary,
            "income_tax": new_tax
        }
    )

    assert response.status_code == status.HTTP_200_OK

    # Verify is actually updated in the database
    result: ScalarResult = await session.scalars(select(Income).where(Income.user_id == user_id))
    updated_income: Income = result.one()

    assert updated_income.annual_salary == new_salary
    assert updated_income.income_tax == new_tax


@pytest.mark.asyncio
async def test_patch_income_bad_payload(user: User, income: Income, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    income.user_id = user_id
    session.add(income)
    await session.commit()
    await session.refresh(income)

    new_salary: str = "bad data"

    # Request missing 'income_tax' field, wrong types, and has unknown field
    response = await test_api.patch(
        f"/income/{user_id}",
        headers={
            "Authorization": auth_header
        },
        json = {
            "annual_salary": new_salary,
            "unknown field": "even more bad data"
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Verify has not been edited in the database
    result: ScalarResult = await session.scalars(select(Income).where(Income.user_id == user_id))
    updated_income: Income = result.one()

    assert updated_income.annual_salary == income.annual_salary
    assert updated_income.income_tax == income.income_tax



@pytest.mark.asyncio
async def test_patch_income_bad_primary_key(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    new_salary: int = 95000
    new_tax: float = 35.0

    response = await test_api.patch(
        "/income/not-a-pk",
        headers={
            "Authorization": auth_header
        },
        json = {
            "annual_salary": new_salary,
            "income_tax": new_tax
        }
    )

    # API should not be able to process this request since PK isn't even an int
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
async def test_patch_income_nonexistant_primary_key(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    new_salary: int = 95000
    new_tax: float = 35.0

    response = await test_api.patch(
        "/income/777",
        headers={
            "Authorization": auth_header
        },
        json = {
            "annual_salary": new_salary,
            "income_tax": new_tax
        }
    )

    # API should not find this primary key (currently nothing in the database when the test is ran)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_patch_income_no_auth(user: User, income: Income, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID.
    registration_results: dict = await register_test_user(user, test_api, session)
    user_id: int = registration_results["user_id"]
    
    income.user_id = user_id
    session.add(income)
    await session.commit()
    await session.refresh(income)

    new_salary: int = 95000
    new_tax: float = 35.0
    response = await test_api.patch(
        f"/income/{user_id}",
        headers={
            "Authorization": "Bearer no-auth"
        },
        json = {
            "annual_salary": new_salary,
            "income_tax": new_tax
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Verify has not been edited in the database
    result: ScalarResult = await session.scalars(select(Income).where(Income.user_id == user_id))
    updated_income: Income = result.one()

    assert updated_income.annual_salary == income.annual_salary
    assert updated_income.income_tax == income.income_tax
