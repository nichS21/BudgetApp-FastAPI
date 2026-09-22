from decimal import Decimal

from httpx import AsyncClient

import pytest

from math import isclose

from fastapi import status

from sqlalchemy import ScalarResult, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from application.testing.fixtures.auth_utilities import register_test_user
from application.testing.fixtures.model_fixtures import *
from application.testing.fixtures.infrastructure_fixtures import test_api, session
from application.models.contribution import Contribution
from application.models.expense import Expense
from application.models.user import User


@pytest.mark.asyncio
async def test_overview_successful(user: User, expense: Expense, expense_two: Expense, 
                                   contribution: Contribution, contribution_two: Contribution, 
                                   income: Income, test_api: AsyncClient, session: AsyncSession) -> None:
    # Commit the user, their income, expenses, and contributions to the database
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    income.user_id = user_id
    expense.user_id = user_id
    expense_two.user_id = user_id
    contribution.user_id = user_id
    contribution_two.user_id = user_id
    session.add_all([income, expense, expense_two, contribution, contribution_two,])
    await session.commit()

    response = await test_api.get(
        f"/overview/{user_id}",
        headers={
            "Authorization": auth_header
        }
    )

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()

    # Verify response returns all relevant information for this user
    # Income
    api_income = response_json['income']
    result: ScalarResult = await session.scalars(select(Income).where(Income.user_id == user_id))
    db_income = result.one()

    assert api_income['annual_salary'] == db_income.annual_salary
    assert api_income['income_tax'] == db_income.income_tax
    assert api_income['user_id'] == db_income.user_id

    # Contributions - Endpoint returns ordered by ID desc
    api_contributions = response_json['contributions']
    result = await session.scalars(select(Contribution).where(Contribution.user_id == user_id).order_by(Contribution.id.desc()))
    db_contributions = result.all()

    end: int = len(db_contributions)
    db_monthly_total: Decimal = Decimal(0.0)
    for i in range(end):
        assert isclose(api_contributions[i]['frequency'], db_contributions[i].frequency)
        assert api_contributions[i]['name'] == db_contributions[i].name
        assert api_contributions[i]['description'] == db_contributions[i].description
        assert isclose(api_contributions[i]['amount'], db_contributions[i].amount)
        assert api_contributions[i]['user_id'] == db_contributions[i].user_id
        assert api_contributions[i]['type'] == db_contributions[i].type.name
        assert isclose(api_contributions[i]['monthly_cost'], db_contributions[i].monthly_cost)
        db_monthly_total += Decimal(db_contributions[i].monthly_cost)

    assert isclose(response_json['contributions_monthly_total'], db_monthly_total)

    # Expenses - Endpoint returns orderd by ID desc
    api_expenses = response_json['expenses']
    result = await session.scalars(select(Expense).where(Expense.user_id == user_id).order_by(Expense.id.desc()))
    db_expenses = result.all()

    end = len(db_expenses)
    db_monthly_total = Decimal(0.0)
    for i in range(end):
        assert isclose(api_expenses[i]['frequency'], db_expenses[i].frequency)
        assert api_expenses[i]['name'] == db_expenses[i].name
        assert api_expenses[i]['description'] == db_expenses[i].description
        assert isclose(api_expenses[i]['cost'], db_expenses[i].cost)
        assert api_expenses[i]['user_id'] == db_expenses[i].user_id
        assert api_expenses[i]['is_debt'] == db_expenses[i].is_debt
        assert isclose(api_expenses[i]['monthly_cost'], db_expenses[i].monthly_cost)
        db_monthly_total += Decimal(db_expenses[i].monthly_cost)

    assert isclose(response_json['expenses_monthly_total'], db_monthly_total)


@pytest.mark.asyncio
async def test_overview_invalid_primary_key(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"

    response = await test_api.get(
        "/overview/not-a-pk",
        headers={
            "Authorization": auth_header
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
async def test_overview_no_user(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    response = await test_api.get(
        f"/overview/{user_id*2}",        # User that doesn't exist in the database, only the first user does
        headers={
            "Authorization": auth_header
        }
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_overview_no_expenses(user: User, income: Income, contribution: Contribution, 
                                    contribution_two: Contribution, test_api: AsyncClient, session: AsyncSession) -> None:
    # Commit needed objects to DB
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    income.user_id = user_id
    contribution.user_id = user_id
    contribution_two.user_id = user_id
    session.add_all([income, contribution, contribution_two,])
    await session.commit()

    response = await test_api.get(
        f"/overview/{user_id}",
        headers={
            "Authorization": auth_header
        }
    )

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()


    # Verify response returns all relevant information for this user
    # Income
    api_income = response_json['income']
    result: ScalarResult = await session.scalars(select(Income).where(Income.user_id == user_id))
    db_income = result.one()

    assert api_income['annual_salary'] == db_income.annual_salary
    assert api_income['income_tax'] == db_income.income_tax
    assert api_income['user_id'] == db_income.user_id

    # Contributions - Endpoint returns ordered by ID desc
    api_contributions = response_json['contributions']
    result = await session.scalars(select(Contribution).where(Contribution.user_id == user_id).order_by(Contribution.id.desc()))
    db_contributions = result.all()

    end: int = len(db_contributions)
    db_monthly_total: Decimal = Decimal(0.0)
    for i in range(end):
        assert isclose(api_contributions[i]['frequency'], db_contributions[i].frequency)
        assert api_contributions[i]['name'] == db_contributions[i].name
        assert api_contributions[i]['description'] == db_contributions[i].description
        assert isclose(api_contributions[i]['amount'], db_contributions[i].amount)
        assert api_contributions[i]['user_id'] == db_contributions[i].user_id
        assert api_contributions[i]['type'] == db_contributions[i].type.name
        assert isclose(api_contributions[i]['monthly_cost'], db_contributions[i].monthly_cost)
        db_monthly_total += Decimal(db_contributions[i].monthly_cost)

    assert isclose(response_json['contributions_monthly_total'], db_monthly_total)

    # Expenses - Endpoint returns orderd by ID desc
    # Note that this user doesn't have any, so we should have none to check
    assert 'expenses' in response_json
    assert len(response_json['expenses']) == 0
    assert 'expenses_monthly_total' in response_json
    assert response_json['expenses_monthly_total'] == 0.0


@pytest.mark.asyncio
async def test_overview_no_contributions(user: User, income: Income, expense: Expense,
                                         expense_two: Expense, test_api: AsyncClient, session: AsyncSession) -> None:
    # Commit needed objects to DB
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    income.user_id = user_id
    expense.user_id = user_id
    expense_two.user_id = user_id
    session.add_all([income, expense, expense_two])
    await session.commit()

    response = await test_api.get(
        f"/overview/{user_id}",
        headers={
            "Authorization": auth_header
        }
    )

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()

    # Verify response returns all relevant information for this user
    # Income
    api_income = response_json['income']
    result: ScalarResult = await session.scalars(select(Income).where(Income.user_id == user_id))
    db_income = result.one()

    assert api_income['annual_salary'] == db_income.annual_salary
    assert api_income['income_tax'] == db_income.income_tax
    assert api_income['user_id'] == db_income.user_id

    # Contributions - Endpoint returns ordered by ID desc
    # Note that this user has no contributions, so there should be nothing to check
    assert 'contributions' in response_json
    assert len(response_json['contributions']) == 0
    assert 'contributions_monthly_total' in response_json
    assert response_json['contributions_monthly_total'] == 0.0

    # Expenses - Endpoint returns orderd by ID desc
    api_expenses = response_json['expenses']
    result = await session.scalars(select(Expense).where(Expense.user_id == user_id).order_by(Expense.id.desc()))
    db_expenses = result.all()

    end: int = len(db_expenses)
    db_monthly_total: Decimal = Decimal(0.0)
    for i in range(end):
        assert isclose(api_expenses[i]['frequency'], db_expenses[i].frequency)
        assert api_expenses[i]['name'] == db_expenses[i].name
        assert api_expenses[i]['description'] == db_expenses[i].description
        assert isclose(api_expenses[i]['cost'], db_expenses[i].cost)
        assert api_expenses[i]['user_id'] == db_expenses[i].user_id
        assert api_expenses[i]['is_debt'] == db_expenses[i].is_debt
        assert isclose(api_expenses[i]['monthly_cost'], db_expenses[i].monthly_cost)
        db_monthly_total += Decimal(db_expenses[i].monthly_cost)

    assert isclose(response_json['expenses_monthly_total'], db_monthly_total)
   
    

@pytest.mark.asyncio
async def test_overview_no_expenses_or_contributions(user: User, income: Income, test_api: AsyncClient, session: AsyncSession) -> None:
    # Commit needed objects to DB
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    income.user_id = user_id
    session.add(income)
    await session.commit()

    response = await test_api.get(
        f"/overview/{user_id}",
        headers={
            "Authorization": auth_header
        }
    )

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()

    # Verify response returns all relevant information for this user
    # Income
    api_income = response_json['income']
    result: ScalarResult = await session.scalars(select(Income).where(Income.user_id == user_id))
    db_income = result.one()

    assert api_income['annual_salary'] == db_income.annual_salary
    assert api_income['income_tax'] == db_income.income_tax
    assert api_income['user_id'] == db_income.user_id

    # Contributions - Endpoint returns ordered by ID desc
    # Note that this user has no contributions, so there should be nothing to check
    assert 'contributions' in response_json
    assert len(response_json['contributions']) == 0
    assert 'contributions_monthly_total' in response_json
    assert response_json['contributions_monthly_total'] == 0.0

    # Expenses - Endpoint returns orderd by ID desc
    # Note that this user doesn't have any, so we should have none to check
    assert 'expenses' in response_json
    assert len(response_json['expenses']) == 0
    assert 'expenses_monthly_total' in response_json
    assert response_json['expenses_monthly_total'] == 0.0


@pytest.mark.asyncio
async def test_overview_no_auth(user: User, income: income, test_api: AsyncClient, session: AsyncSession) -> None:
    # Commit needed objects to DB
    registration_results: dict = await register_test_user(user, test_api, session)
    user_id: int = registration_results["user_id"]

    income.user_id = user_id
    session.add(income)
    await session.commit()
    
    response = await test_api.get(
        f"/overview/{user_id}",
        headers={
            "Authorization": "Bearer no-auth"
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
