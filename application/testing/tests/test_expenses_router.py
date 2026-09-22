import pytest

from math import isclose

from httpx import AsyncClient

from fastapi import status

from sqlalchemy import ScalarResult, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from application.models.expense import Expense
from application.models.user import User
from application.testing.fixtures.infrastructure_fixtures import test_api, session
from application.testing.fixtures.model_fixtures import user, expense, expense_two
from application.testing.fixtures.auth_utilities import register_test_user


@pytest.mark.asyncio
async def test_create_expense_successful(user: User, expense: Expense, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    expense.user_id = user_id

    response = await test_api.post(
        "/expense/",
        headers={
            "Authorization": auth_header
        },
        json={
            "frequency": expense.frequency,
            "name": expense.name,
            "description": expense.description,
            "cost": expense.cost,
            "user_id": expense.user_id,
            "is_debt": expense.is_debt,
        }
    )

    assert response.status_code == status.HTTP_201_CREATED

    # Verify expense is in DB and then compare versus what we POST'd
    result: ScalarResult = await session.scalars(select(Expense).where(Expense.user_id == user_id))
    db_expense: Expense = result.one()

    assert db_expense.frequency == expense.frequency
    assert db_expense.name == expense.name
    assert db_expense.description == expense.description
    assert isclose(db_expense.cost, expense.cost)
    assert db_expense.user_id == expense.user_id
    assert db_expense.is_debt == expense.is_debt
    assert isclose(db_expense.monthly_cost, (expense.frequency * expense.cost))


@pytest.mark.asyncio
async def test_create_expense_extra_fields(user: User, expense: Expense, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    expense.user_id = user_id

    # Give extra fields in the response body that FastAPI should ignore
    response = await test_api.post(
        "/expense/",
        headers={
            "Authorization": auth_header
        },  
        json={
            "frequency": expense.frequency,
            "name": expense.name,
            "description": expense.description,
            "cost": expense.cost,
            "user_id": expense.user_id,
            "is_debt": expense.is_debt,
            "extra": "I won't be used!",
            "even more": 109
        }
    )

    assert response.status_code == status.HTTP_201_CREATED

    # Expense still should have been created as normal, and as specified
    result: ScalarResult = await session.scalars(select(Expense).where(Expense.user_id == expense.user_id))
    db_expense: Expense = result.one()

    assert db_expense.frequency == expense.frequency
    assert db_expense.name == expense.name
    assert db_expense.description == expense.description
    assert isclose(db_expense.cost, expense.cost)
    assert db_expense.user_id == expense.user_id
    assert db_expense.is_debt == expense.is_debt
    assert isclose(db_expense.monthly_cost, (expense.frequency * expense.cost))
    

@pytest.mark.asyncio
async def test_create_expense_bad_payload(user: User, expense: Expense, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    expense.user_id = user_id

    # Give a request with missing data fields
    response = await test_api.post(
        "/expense/",
        headers={
            "Authorization": auth_header
        }, 
        json={
            "frequency": expense.frequency,
            "description": expense.description,
            "cost": expense.cost,
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    result: ScalarResult = await session.scalars(select(func.count()).select_from(Expense).where(Expense.user_id == expense.user_id))
    expense_count: int = result.one()

    assert expense_count == 0

    # Give a request with data fields containing the wrong type
    response = await test_api.post(
        "/expense/",
        headers={
            "Authorization": auth_header
        }, 
        json={
            "frequency": expense.frequency,
            "name": 10,
            "description": expense.description,
            "cost": "Wednesday",
            "user_id": expense.user_id,
            "is_debt": 1009
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    result: ScalarResult = await session.scalars(select(func.count()).select_from(Expense).where(Expense.user_id == expense.user_id))
    expense_count: int = result.one()

    assert expense_count == 0


@pytest.mark.asyncio
async def test_create_expense_no_user(user: User, expense: Expense, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    expense.user_id = user_id*2     # Non-existant user id
    response = await test_api.post(
        "/expense/",
        headers={
            "Authorization": auth_header
        }, 
        json={
            "frequency": expense.frequency,
            "name": expense.name,
            "description": expense.description,
            "cost": expense.cost,
            "user_id": expense.user_id,                    
            "is_debt": expense.is_debt,
        }
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    # Check in DB that nothing was created
    result: ScalarResult = await session.scalars(select(func.count()).select_from(Expense).where(Expense.user_id == expense.user_id))
    expense_count: int = result.one()

    assert expense_count == 0


@pytest.mark.asyncio
async def test_create_expense_no_auth(user: User, expense: Expense, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    expense.user_id = user_id
    response = await test_api.post(
        "/expense/",
        headers={
            "Authorization": "Bearer no-auth"
        }, 
        json={
            "frequency": expense.frequency,
            "name": expense.name,
            "description": expense.description,
            "cost": expense.cost,
            "user_id": expense.user_id,                    
            "is_debt": expense.is_debt,
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Check in DB that nothing was created
    result: ScalarResult = await session.scalars(select(func.count()).select_from(Expense).where(Expense.user_id == expense.user_id))
    expense_count: int = result.one()

    assert expense_count == 0



@pytest.mark.asyncio
async def test_get_expense_successful(user: User, expense: Expense, test_api: AsyncClient, session: AsyncSession) -> None:
   # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    expense.user_id = user_id
    session.add(expense)
    await session.commit()
    await session.refresh(expense)
    expense_id: int = expense.id

    response = await test_api.get(
        f"/expense/{expense_id}",
        headers={
            "Authorization": auth_header
        }, 
    )

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    response_json = response_json["expense"]

    assert response_json['frequency'] == expense.frequency
    assert response_json['name'] == expense.name
    assert response_json['description'] == expense.description
    assert isclose(response_json['cost'], expense.cost)
    assert response_json['user_id'] == expense.user_id
    assert response_json['is_debt'] == expense.is_debt
    assert isclose(response_json['monthly_cost'], (expense.cost * expense.frequency))


@pytest.mark.asyncio
async def test_get_expense_invalid_primary_key(user: User, expense: Expense, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    expense.user_id = user_id
    session.add(expense)
    await session.commit()

    # Use a completely invalid query parameter for the PK
    response = await test_api.get(
        "/expense/not-a-valid-pk",
        headers={
            "Authorization": auth_header
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
async def test_get_expense_no_user(user: User, expense: Expense, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]
    
    expense.user_id = user_id
    session.add(expense)
    await session.commit()
    await session.refresh(expense)
    expense_id: int = expense.id
    

    # Use an ID that could be legit, but doesn't match with the only user and expense in the DB
    response = await test_api.get(
        f"/expense/{expense_id*2}",
        headers={
            "Authorization": auth_header
        },
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_get_expense_no_auth(user: User, expense: Expense, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]
    
    expense.user_id = user_id
    session.add(expense)
    await session.commit()
    await session.refresh(expense)
    expense_id: int = expense.id
    
    response = await test_api.get(
        f"/expense/{expense_id}",
        headers={
            "Authorization": "Bearer no-auth"
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_patch_expense_successful(user: User, expense: Expense, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]
    
    expense.user_id = user_id
    session.add(expense)
    await session.commit()
    await session.refresh(expense)
    expense_id: int = expense.id

    updated_frequency: float = 1
    updated_name: str = "Student Loan"
    updated_description: str = "Monthly student loan payment"
    updated_cost: float = 300.25
    updated_is_debt: bool = True

    response = await test_api.patch(
        f"/expense/{expense_id}",
        headers={
            "Authorization": auth_header
        },
        json = {
            "frequency": updated_frequency,
            "name": updated_name,
            "description": updated_description,
            "cost": updated_cost,
            "user_id": user_id,
            "is_debt": updated_is_debt
        }
    )

    assert response.status_code == status.HTTP_200_OK

    result: ScalarResult = await session.scalars(select(Expense).where(Expense.id == expense_id))
    db_expense = result.one()

    assert isclose(db_expense.frequency, updated_frequency)
    assert db_expense.name == updated_name
    assert db_expense.description == updated_description
    assert isclose(db_expense.cost, updated_cost)
    assert db_expense.is_debt == updated_is_debt


@pytest.mark.asyncio
async def test_patch_expense_bad_payload(user: User, expense: Expense, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]
    
    expense.user_id = user_id
    session.add(expense)
    await session.commit()
    await session.refresh(expense)
    expense_id: int = expense.id

    updated_frequency: float = 1
    updated_name: str = "Student Loan"
    updated_description: str = "Monthly student loan payment"
    updated_cost: float = 300.25
    updated_is_debt: bool = True
    
    # Payload that is missing fields
    response = await test_api.patch(
        f"/expense/{expense_id}",
        headers={
            "Authorization": auth_header
        },
        json = {
            "frequency": updated_frequency,
            "user_id": user_id,
            "is_debt": updated_is_debt
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Make sure expense was not updated in the database
    result: ScalarResult = await session.scalars(select(Expense).where(Expense.id == expense_id))
    db_expense = result.one()

    assert db_expense.frequency != updated_frequency
    assert db_expense.name != updated_name
    assert db_expense.description != updated_description
    assert db_expense.cost != updated_cost
    assert db_expense.is_debt != updated_is_debt


     # Payload that has the wrong data types
    response = await test_api.patch(
        f"/expense/{expense_id}",
        headers={
            "Authorization": auth_header
        },
        json = {
            "frequency": "Tuesday",
            "name": 1,
            "description": updated_description,
            "cost": "One",
            "user_id": user_id,
            "is_debt": -37,
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Make sure expense was not updated in the database
    result: ScalarResult = await session.scalars(select(Expense).where(Expense.id == expense_id))
    db_expense = result.one()

    assert db_expense.frequency != updated_frequency
    assert db_expense.name != updated_name
    assert db_expense.description != updated_description
    assert db_expense.cost != updated_cost
    assert db_expense.is_debt != updated_is_debt


@pytest.mark.asyncio
async def test_patch_expense_invalid_primary_key(user: User, expense: Expense, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]
    
    expense.user_id = user_id
    session.add(expense)
    await session.commit()
    await session.refresh(expense)
    expense_id: int = expense.id

    updated_frequency: float = 1
    updated_name: str = "Student Loan"
    updated_description: str = "Monthly student loan payment"
    updated_cost: float = 300.25
    updated_is_debt: bool = True
    
    # Request with a completely invalid primary key
    response = await test_api.patch(
        f"/expense/not-a-primary-key",
        headers={
            "Authorization": auth_header
        },
        json = {
            "frequency": updated_frequency,
            "name": updated_name,
            "description": updated_description,
            "cost": updated_cost,
            "user_id": user_id,
            "is_debt": updated_is_debt
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Make sure expense was not updated in the database
    result: ScalarResult = await session.scalars(select(Expense).where(Expense.id == expense_id))
    db_expense = result.one()

    assert db_expense.frequency != updated_frequency
    assert db_expense.name != updated_name
    assert db_expense.description != updated_description
    assert db_expense.cost != updated_cost
    assert db_expense.is_debt != updated_is_debt


@pytest.mark.asyncio
async def test_patch_expense_no_expense(user: User, expense: Expense, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]
    
    expense.user_id = user_id
    session.add(expense)
    await session.commit()
    await session.refresh(expense)
    expense_id: int = expense.id

    updated_frequency: float = 1
    updated_name: str = "Student Loan"
    updated_description: str = "Monthly student loan payment"
    updated_cost: float = 300.25
    updated_is_debt: bool = True
    
    # Request that doesn't match against any expense in the DB
    response = await test_api.patch(
        f"/expense/{expense_id*2}",
        headers={
            "Authorization": auth_header
        },
        json = {
            "frequency": updated_frequency,
            "name": updated_name,
            "description": updated_description,
            "cost": updated_cost,
            "user_id": user_id,
            "is_debt": updated_is_debt
        }
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    # Make sure expense was not updated in the database
    result: ScalarResult = await session.scalars(select(Expense).where(Expense.id == expense_id))
    db_expense = result.one()

    assert db_expense.frequency != updated_frequency
    assert db_expense.name != updated_name
    assert db_expense.description != updated_description
    assert db_expense.cost != updated_cost
    assert db_expense.is_debt != updated_is_debt


@pytest.mark.asyncio
async def test_patch_expense_extra_fields(user: User, expense: Expense, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]
    
    expense.user_id = user_id
    session.add(expense)
    await session.commit()
    await session.refresh(expense)
    expense_id: int = expense.id

    updated_frequency: float = 1
    updated_name: str = "Student Loan"
    updated_description: str = "Monthly student loan payment"
    updated_cost: float = 300.25
    updated_is_debt: bool = True
    
    # Request that doesn't match against any expense in the DB
    response = await test_api.patch(
        f"/expense/{expense_id}",
        headers={
            "Authorization": auth_header
        },
        json = {
            "frequency": updated_frequency,
            "name": updated_name,
            "description": updated_description,
            "cost": updated_cost,
            "user_id": user_id,
            "is_debt": updated_is_debt,
            "extra_one": "Extra field",
            "extra_two": 2
        }
    )

    assert response.status_code == status.HTTP_200_OK

    result: ScalarResult = await session.scalars(select(Expense).where(Expense.id == expense_id))
    db_expense = result.one()

    assert isclose(db_expense.frequency, updated_frequency)
    assert db_expense.name == updated_name
    assert db_expense.description == updated_description
    assert isclose(db_expense.cost, updated_cost)
    assert db_expense.is_debt == updated_is_debt


@pytest.mark.asyncio
async def test_patch_expense_no_auth(user: User, expense: Expense, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    expense.user_id = user_id
    session.add(expense)
    await session.commit()
    await session.refresh(expense)
    expense_id: int = expense.id

    updated_frequency: float = 1
    updated_name: str = "Student Loan"
    updated_description: str = "Monthly student loan payment"
    updated_cost: float = 300.25
    updated_is_debt: bool = True
    
    response = await test_api.patch(
        f"/expense/{expense_id}",
        headers={
            "Authorization": "Bearer no-auth"
        },
        json = {
            "frequency": updated_frequency,
            "name": updated_name,
            "description": updated_description,
            "cost": updated_cost,
            "user_id": user_id,
            "is_debt": updated_is_debt
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Make sure expense was not updated in the database
    result: ScalarResult = await session.scalars(select(Expense).where(Expense.id == expense_id))
    db_expense = result.one()

    assert db_expense.frequency != updated_frequency
    assert db_expense.name != updated_name
    assert db_expense.description != updated_description
    assert db_expense.cost != updated_cost
    assert db_expense.is_debt != updated_is_debt

@pytest.mark.asyncio
async def test_delete_expense_succesful(user: User, expense: Expense, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]
    
    expense.user_id = user_id
    session.add(expense)
    await session.commit()
    await session.refresh(expense)
    expense_id: int = expense.id

    response = await test_api.delete(
        f"/expense/{expense_id}",
        headers={
            "Authorization": auth_header
        }
    )

    assert response.status_code == status.HTTP_200_OK

    # Validate with database that expense no longer exists
    result: ScalarResult = await session.scalars(select(func.count()).select_from(Expense).where(Expense.id == expense_id))
    expense_count: int = result.one()
    assert expense_count == 0


@pytest.mark.asyncio
async def test_delete_invalid_primary_key(user: User, expense: Expense, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]
    
    expense.user_id = user_id
    session.add(expense)
    await session.commit()
    await session.refresh(expense)
    expense_id: int = expense.id

    response = await test_api.delete(
        "/expense/not-a-pk",
        headers={
            "Authorization": auth_header
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Verify that expense was not deleted
    result: ScalarResult = await session.scalars(select(func.count()).select_from(Expense).where(Expense.id == expense_id))
    expense_count: int = result.one()
    assert expense_count == 1


@pytest.mark.asyncio
async def test_delete_no_expense(user: User, expense: Expense, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]
    
    expense.user_id = user_id
    session.add(expense)
    await session.commit()
    await session.refresh(expense)
    expense_id: int = expense.id

    response = await test_api.delete(
        f"/expense/{expense_id*2}",         # No expense at this ID to be deleted
        headers={
            "Authorization": auth_header
        }
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    # Verify expense was not deleted in DB
    result: ScalarResult = await session.scalars(select(func.count()).select_from(Expense).where(Expense.id == expense_id))
    expense_count: int = result.one()
    assert expense_count == 1


@pytest.mark.asyncio
async def test_delete_no_auth(user: User, expense: Expense, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    expense.user_id = user_id
    session.add(expense)
    await session.commit()
    await session.refresh(expense)
    expense_id: int = expense.id

    response = await test_api.delete(
        f"/expense/{expense_id}",         
        headers={
            "Authorization": "Bearer no-auth"
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Verify expense was not deleted in DB
    result: ScalarResult = await session.scalars(select(func.count()).select_from(Expense).where(Expense.id == expense_id))
    expense_count: int = result.one()
    assert expense_count == 1

@pytest.mark.asyncio
async def test_expense_list_successful(user: User, expense: Expense, expense_two: Expense, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    # Add expenses to the DB
    expense.user_id = user_id
    expense_two.user_id = user_id
    session.add_all([expense, expense_two])
    await session.commit()

    # Get expenses in descending order, as this is what the list endpoint will return
    result = await session.scalars(select(Expense).where(Expense.user_id == user_id).order_by(Expense.id.desc()))
    expenses = result.all()  

    response = await test_api.get(
        f"/expense/expense-list/{user_id}",
        headers={
            "Authorization": auth_header
        }
    )

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    response_json = response_json['expenses']

    length: int = len(expenses)
    for i in range(length):
        assert expenses[i].frequency == response_json[i]['frequency']
        assert expenses[i].name == response_json[i]['name']
        assert expenses[i].description == response_json[i]['description']
        assert isclose(expenses[i].cost, response_json[i]['cost'])
        assert expenses[i].user_id == response_json[i]['user_id']
        assert expenses[i].is_debt == response_json[i]['is_debt']
        assert isclose(expenses[i].monthly_cost, response_json[i]['monthly_cost'])


@pytest.mark.asyncio
async def test_expense_list_invalid_primary_key(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"

    # Note, there will be no expenses in the DB when this test is ran
    response = await test_api.get(
        "/expense/expense-list/not-a-pk",
        headers={
            "Authorization": auth_header
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
async def test_expense_list_no_user(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"

    # Note, there are no expenses in the DB when this test is ran
    nonexistent_user_id: int = 999
    response = await test_api.get(
        f"/expense/expense-list/{nonexistent_user_id}",
         headers={
            "Authorization": auth_header
        }
    )

    # A given user may have zero expenses, so there's nothing to list which is acceptable.
    # A user that doesn't exist will never have any expenses
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert 'expenses' in response_json
    assert len(response_json['expenses']) == 0


@pytest.mark.asyncio
async def test_expense_list_no_expenses(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    # Add user to DB and get its assigned ID
    session.add(user)
    await session.commit()
    await session.refresh(user)
    user_id: int = user.id

    response = await test_api.get(
        f"/expense/expense-list/{user_id}",
        headers={
            "Authorization": auth_header
        }
    )

    # This user has no expenses to list, and that's OK
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert 'expenses' in response_json
    assert len(response_json['expenses']) == 0


@pytest.mark.asyncio
async def test_expense_list_no_auth(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID.
    registration_results: dict = await register_test_user(user, test_api, session)
    user_id: int = registration_results["user_id"]

    response = await test_api.get(
        f"/expense/expense-list/{user_id}",
        headers={
            "Authorization": "Bearer no_auth"
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
