import pytest

from httpx import AsyncClient

from math import isclose

from fastapi import status

from sqlalchemy import ScalarResult, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from application.models.contribution import Contribution, ContributionType
from application.models.user import User
from application.testing.fixtures.infrastructure_fixtures import test_api, session
from application.testing.fixtures.model_fixtures import user, contribution, contribution_two
from application.testing.fixtures.auth_utilities import register_test_user


@pytest.mark.asyncio
async def test_create_contribution_successful(user: User, contribution: Contribution, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    contribution.user_id = user_id 
    
    response = await test_api.post(
        "/contribution/",
        headers={
            "Authorization": auth_header
        },
        json={
            "frequency": contribution.frequency,
            "name": contribution.name,
            "description": contribution.description,
            "amount": contribution.amount,
            "user_id": contribution.user_id,
            "type": contribution.type.value
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"message": "Created contribution successfully"}

    # Verify contribution is now in DB (there should only be one contribution for this user)
    result: ScalarResult = await session.scalars(select(Contribution).where(Contribution.user_id == user_id))
    db_contribution: Contribution = result.one()

    assert db_contribution.frequency == contribution.frequency
    assert db_contribution.name == contribution.name
    assert db_contribution.description == contribution.description
    assert db_contribution.amount == contribution.amount
    assert db_contribution.user_id == contribution.user_id
    assert db_contribution.type == contribution.type


@pytest.mark.asyncio
async def test_create_contribution_extra_fields(user: User, contribution: Contribution, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    contribution.user_id = user_id 
    
    # Give extra fields in request body. Note that FastAPI ignores these fields since they don't map to the dataclass object at that route
    response = await test_api.post(
        "/contribution/",
        headers={
                "Authorization": auth_header
        },
        json={
            "frequency": contribution.frequency,
            "name": contribution.name,
            "description": contribution.description,
            "amount": contribution.amount,
            "user_id": contribution.user_id,
            "type": contribution.type.value,
            "extra": "I'm not used at all!",
            "even more": "There's no point to this data"
        }
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"message": "Created contribution successfully"}

    # Verify contribution is now in DB (there should only be one contribution for this user)
    result: ScalarResult = await session.scalars(select(Contribution).where(Contribution.user_id == user_id))
    db_contribution: Contribution = result.one()

    assert db_contribution.frequency == contribution.frequency
    assert db_contribution.name == contribution.name
    assert db_contribution.description == contribution.description
    assert db_contribution.amount == contribution.amount
    assert db_contribution.user_id == contribution.user_id
    assert db_contribution.type == contribution.type


@pytest.mark.asyncio
async def test_create_contribution_bad_payload(user: User, contribution: Contribution, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]
    
    contribution.user_id = user_id 
    
    # Request with missing required fields
    response = await test_api.post(
        "/contribution/",
        headers={
            "Authorization": auth_header
        },
        json={
            "frequency": contribution.frequency,
            "name": contribution.name,
            "description": contribution.description,
            "amount": contribution.amount,
            # "user_id": contribution.user_id,
            # "type": contribution.type.value
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Request with wrong data types
    response = await test_api.post(
        "/contribution/",
        headers={
            "Authorization": auth_header
        },
        json={
            "frequency": "1/3",
            "name": 27,
            "description": 38,
            "amount": "March",
            "user_id": contribution.user_id,
            "type": contribution.type.value
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Query database to verify contribution was never created
    result: ScalarResult = await session.scalars(select(func.count()).select_from(Contribution).where(Contribution.user_id == user_id))
    contribution_count: int = result.one()
    assert contribution_count == 0


@pytest.mark.asyncio
async def test_create_contribution_no_user(user: User, contribution: Contribution, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"

    # Request has what could have been a valid user ID, but there is no such user in the database, per this test's scope
    user_id: int = 999
    response = await test_api.post(
        "/contribution/",
        headers={
            "Authorization": auth_header
        },
        json={
            "frequency": contribution.frequency,
            "name": contribution.name,
            "description": contribution.description,
            "amount": contribution.amount,
            "user_id": user_id,
            "type": contribution.type.value
        }
    )
     
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    # Query database to verify contribution was never created
    result: ScalarResult = await session.scalars(select(func.count()).select_from(Contribution).where(Contribution.user_id == user_id))
    contribution_count: int = result.one()
    assert contribution_count == 0


@pytest.mark.asyncio
async def test_create_contribution_no_auth(contribution: Contribution, test_api: AsyncClient, session: AsyncSession) -> None:
    user_id: int = 999
    response = await test_api.post(
        "/contribution/",
        headers={
            "Authorization": "Bearer bad-token"
        },
        json={
            "frequency": contribution.frequency,
            "name": contribution.name,
            "description": contribution.description,
            "amount": contribution.amount,
            "user_id": user_id,
            "type": contribution.type.value
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Query database to verify contribution was never created
    result: ScalarResult = await session.scalars(select(func.count()).select_from(Contribution).where(Contribution.user_id == user_id))
    contribution_count: int = result.one()
    assert contribution_count == 0


@pytest.mark.asyncio
async def test_get_contribution_successful(user: User, contribution: Contribution, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    contribution.user_id = user_id 
    session.add(contribution)
    await session.commit()
    await session.refresh(contribution)
    contribution_id: int = contribution.id

    response = await test_api.get(
        f"/contribution/{contribution_id}",
        headers={
            "Authorization": auth_header
        },
    )

    response_json = response.json()
    assert response.status_code == status.HTTP_200_OK

    assert response_json["contribution"]["frequency"] == contribution.frequency
    assert response_json["contribution"]["name"] == contribution.name
    assert response_json["contribution"]["description"] == contribution.description
    assert response_json["contribution"]["amount"] == contribution.amount
    assert response_json["contribution"]["user_id"] == contribution.user_id
    assert response_json["contribution"]["type"] == contribution.type.name
    assert response_json["contribution"]["monthly_cost"] == contribution.monthly_cost    


@pytest.mark.asyncio
async def test_get_contribution_invalid_primary_key(user: User, contribution: Contribution, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    contribution.user_id = user_id 
    session.add(contribution)
    await session.commit()
    await session.refresh(contribution)

    response = await test_api.get(
        "/contribution/not-a-pk",
        headers={
            "Authorization": auth_header
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
async def test_get_contribution_no_contribution(user: User, contribution: Contribution, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    contribution.user_id = user_id 
    session.add(contribution)
    await session.commit()
    await session.refresh(contribution)
    contribution_id: int = contribution.id

    response = await test_api.get(
        f"/contribution/{contribution_id*2}",
        headers={
            "Authorization": auth_header
        }
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.asyncio
async def test_get_contribution_no_auth(user: User, contribution: Contribution, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID.
    registration_results: dict = await register_test_user(user, test_api, session)
    user_id: int = registration_results["user_id"]
    
    contribution.user_id = user_id 
    session.add(contribution)
    await session.commit()
    await session.refresh(contribution)
    contribution_id: int = contribution.id

    response = await test_api.get(
        f"/contribution/{contribution_id}",
        headers={
            "Authorization": "Bearer no-auth"
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_patch_contribution_successful(user: User, contribution: Contribution, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    contribution.user_id = user_id
    session.add(contribution)
    await session.commit()
    await session.refresh(contribution)
    contribution_id = contribution.id

    updated_frequency: float = 1/3
    updated_name: str = "HYSA" 
    updated_desc: str = "High Yield Savings Account"
    updated_amount: float = 350.57
    updated_type: str = ContributionType.SAVINGS.value

    response = await test_api.patch(
        f"/contribution/{contribution_id}",
        headers={
            "Authorization": auth_header
        },
        json={
          "frequency": updated_frequency,
          "name": updated_name,
          "description": updated_desc,
          "amount": updated_amount,
          "type": updated_type   
        }
    )

    assert response.status_code == status.HTTP_200_OK

    # Verify has been updated in the database
    result: ScalarResult = await session.scalars(select(Contribution).where(Contribution.id == contribution_id))
    updated_contrib: Contribution = result.one()

    # Note, Postgres returns Decimal Python types, when we originally used Python Floats. Due to decimal point 
    #   precision differences, Math.isclose() is used to verify results, minus very minor rounding differences. 
    assert isclose(updated_contrib.frequency, updated_frequency)
    assert updated_contrib.name == updated_name
    assert updated_contrib.description == updated_desc
    assert isclose(updated_contrib.amount, updated_amount)
    assert updated_contrib.type == ContributionType.SAVINGS


@pytest.mark.asyncio
async def test_patch_contribution_extra_fields(user: User, contribution: Contribution, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    contribution.user_id = user_id
    session.add(contribution)
    await session.commit()
    await session.refresh(contribution)
    contribution_id = contribution.id

    updated_frequency: float = 1/3
    updated_name: str = "HYSA" 
    updated_desc: str = "High Yield Savings Account"
    updated_amount: float = 350.57
    updated_type: str = ContributionType.SAVINGS.value

    # Response with extra fields - which should be ignored
    response = await test_api.patch(
        f"/contribution/{contribution_id}",
        headers={
            "Authorization": auth_header
        },
        json={
          "frequency": updated_frequency,
          "name": updated_name,
          "description": updated_desc,
          "amount": updated_amount,
          "type": updated_type,
          "extra_field": "I shouldn't get used!",
          "extra_field_again": 9999
        }
    )

    assert response.status_code == status.HTTP_200_OK

    # Verify has been updated in the database
    result: ScalarResult = await session.scalars(select(Contribution).where(Contribution.id == contribution_id))
    updated_contrib: Contribution = result.one()

    # Note, Postgres returns Decimal Python types, when we originally used Python Floats. Due to decimal point 
    #   precision differences, Math.isclose() is used to verify results, minus very minor rounding differences. 
    assert isclose(updated_contrib.frequency, updated_frequency)
    assert updated_contrib.name == updated_name
    assert updated_contrib.description == updated_desc
    assert isclose(updated_contrib.amount, updated_amount)
    assert updated_contrib.type == ContributionType.SAVINGS


@pytest.mark.asyncio
async def test_patch_contribution_invalid_primary_key(user: User, contribution: Contribution, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    contribution.user_id = user_id
    session.add(contribution)
    await session.commit()
    await session.refresh(contribution)
    contribution_id = contribution.id

    updated_frequency: float = 1/3
    updated_name: str = "HYSA" 
    updated_desc: str = "High Yield Savings Account"
    updated_amount: float = 350.57
    updated_type: str = ContributionType.SAVINGS.value

    response = await test_api.patch(
        f"/contribution/not-a-primary-key",
        headers={
            "Authorization": auth_header
        },
        json={
          "frequency": updated_frequency,
          "name": updated_name,
          "description": updated_desc,
          "amount": updated_amount,
          "type": updated_type
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Verify has not been updated in the database
    result: ScalarResult = await session.scalars(select(Contribution).where(Contribution.id == contribution_id))
    updated_contrib: Contribution = result.one()

    assert not isclose(updated_contrib.frequency, updated_frequency)
    assert updated_contrib.name != updated_name
    assert updated_contrib.description != updated_desc
    assert not isclose(updated_contrib.amount, updated_amount)
    assert updated_contrib.type != ContributionType.SAVINGS


@pytest.mark.asyncio
async def test_patch_contribution_no_contribution(user: User, contribution: Contribution, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    contribution.user_id = user_id
    session.add(contribution)
    await session.commit()
    await session.refresh(contribution)
    contribution_id = contribution.id

    updated_frequency: float = 1/3
    updated_name: str = "HYSA" 
    updated_desc: str = "High Yield Savings Account"
    updated_amount: float = 350.57
    updated_type: str = ContributionType.SAVINGS.value

    response = await test_api.patch(
        f"/contribution/{contribution.id*2}",     # Contribution ID that doesn't exist 
        headers={
            "Authorization": auth_header
        },
        json={
          "frequency": updated_frequency,
          "name": updated_name,
          "description": updated_desc,
          "amount": updated_amount,
          "type": updated_type
        }
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    # Verify has not been updated in the database
    result: ScalarResult = await session.scalars(select(Contribution).where(Contribution.id == contribution_id))
    updated_contrib: Contribution = result.one()

    assert not isclose(updated_contrib.frequency, updated_frequency)
    assert updated_contrib.name != updated_name
    assert updated_contrib.description != updated_desc
    assert not isclose(updated_contrib.amount, updated_amount)
    assert updated_contrib.type != ContributionType.SAVINGS


@pytest.mark.asyncio
async def test_patch_contribution_bad_payload(user: User, contribution: Contribution, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    contribution.user_id = user_id
    session.add(contribution)
    await session.commit()
    await session.refresh(contribution)
    contribution_id = contribution.id

    updated_frequency: float = 1/3
    updated_name: str = "HYSA" 
    updated_desc: str = "High Yield Savings Account"
    updated_amount: float = 350.57

    # Bad payload that is missing fields and giving the wrong types of information for required data. 
    response = await test_api.patch(
        f"/contribution/{contribution.id*2}",     # Contribution ID that doesn't exist 
        headers={
            "Authorization": auth_header
        },
        json={
          "frequency": "Tuesday",
          "description": updated_desc,
          "amount": "Retirement Account",
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Verify has not been updated in the database
    result: ScalarResult = await session.scalars(select(Contribution).where(Contribution.id == contribution_id))
    updated_contrib: Contribution = result.one()

    assert not isclose(updated_contrib.frequency, updated_frequency)
    assert updated_contrib.name != updated_name
    assert updated_contrib.description != updated_desc
    assert not isclose(updated_contrib.amount, updated_amount)
    assert updated_contrib.type != ContributionType.SAVINGS


@pytest.mark.asyncio
async def test_patch_contribution_no_auth(user: User, contribution: Contribution, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    user_id: int = registration_results["user_id"]

    contribution.user_id = user_id
    session.add(contribution)
    await session.commit()
    await session.refresh(contribution)
    contribution_id = contribution.id

    updated_frequency: float = 1/3
    updated_name: str = "HYSA" 
    updated_desc: str = "High Yield Savings Account"
    updated_amount: float = 350.57
    updated_type: str = ContributionType.SAVINGS.value

    response = await test_api.patch(
        f"/contribution/{contribution.id}",     
        headers={
            "Authorization": "Bearer no-auth"
        },
        json={
            "frequency": updated_frequency,
            "name": updated_name,
            "description": updated_desc,
            "amount": updated_amount,
            "type": updated_type
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Verify has not been updated in the database
    result: ScalarResult = await session.scalars(select(Contribution).where(Contribution.id == contribution_id))
    updated_contrib: Contribution = result.one()

    assert not isclose(updated_contrib.frequency, updated_frequency)
    assert updated_contrib.name != updated_name
    assert updated_contrib.description != updated_desc
    assert not isclose(updated_contrib.amount, updated_amount)
    assert updated_contrib.type != ContributionType.SAVINGS


@pytest.mark.asyncio
async def test_delete_contribution_successful(user: User, contribution: Contribution, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    contribution.user_id = user_id
    session.add(contribution)
    await session.commit()
    await session.refresh(contribution)
    contribution_id = contribution.id

    response = await test_api.delete(
        f"/contribution/{contribution_id}",
        headers={
            "Authorization": auth_header
        },  
    )
        
    assert response.status_code == status.HTTP_200_OK

    # Verify that the contribution has been deleted
    result: ScalarResult = await session.scalars(select(func.count()).select_from(Contribution).where(Contribution.id == contribution_id))
    contribution_count: int = result.one()
    assert contribution_count == 0


@pytest.mark.asyncio
async def test_delete_contribution_invalid_primary_key(user: User, contribution: Contribution, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    contribution.user_id = user_id
    session.add(contribution)
    await session.commit()
    await session.refresh(contribution)
    contribution_id = contribution.id

    response = await test_api.delete(
        f"/contribution/not-a-primary-key",
        headers={
            "Authorization": auth_header
        }, 
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    # Verify that the contribution has NOT been deleted
    result: ScalarResult = await session.scalars(select(func.count()).select_from(Contribution).where(Contribution.id == contribution_id))
    contribution_count: int = result.one()
    assert contribution_count == 1


@pytest.mark.asyncio
async def test_delete_contribution_no_contribution(user: User, contribution: Contribution, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    contribution.user_id = user_id
    session.add(contribution)
    await session.commit()
    await session.refresh(contribution)
    contribution_id = contribution.id

    response = await test_api.delete(
        f"/contribution/{contribution_id*2}",      # No contribution exists at this ID
        headers={
            "Authorization": auth_header
        }, 
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    # Verify that the contribution has NOT been deleted
    result: ScalarResult = await session.scalars(select(func.count()).select_from(Contribution).where(Contribution.id == contribution_id))
    contribution_count: int = result.one()
    assert contribution_count == 1


@pytest.mark.asyncio
async def test_delete_contribution_no_auth(user: User, contribution: Contribution, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID.
    registration_results: dict = await register_test_user(user, test_api, session)
    user_id: int = registration_results["user_id"]

    contribution.user_id = user_id
    session.add(contribution)
    await session.commit()
    await session.refresh(contribution)
    contribution_id = contribution.id

    response = await test_api.delete(
        f"/contribution/{contribution_id}",    
        headers={
            "Authorization": "Bearer no-auth"
        }, 
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Verify that the contribution has NOT been deleted
    result: ScalarResult = await session.scalars(select(func.count()).select_from(Contribution).where(Contribution.id == contribution_id))
    contribution_count: int = result.one()
    assert contribution_count == 1


@pytest.mark.asyncio
async def test_contribution_list_successful(user: User, contribution: Contribution, contribution_two: Contribution, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    # Add contributions to retrieve
    contribution.user_id = user_id
    contribution_two.user_id = user_id
    session.add_all([contribution, contribution_two])
    await session.commit()

    # Get contributions in descending order for this user - this is what the end point will be verified against
    result: ScalarResult = await session.scalars(select(Contribution)
                                                .where(Contribution.user_id == user_id)
                                                .order_by(Contribution.id.desc()))
    contributions = result.all()
    response = await test_api.get(
        f"contribution/contribution-list/{user_id}",
        headers={
            "Authorization": auth_header
        }, 
    )
    
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    response_json = response_json['contributions']

    length: int = len(contributions)
    for i in range(length):
        assert contributions[i].frequency == response_json[i]['frequency']
        assert contributions[i].name == response_json[i]['name']
        assert contributions[i].description == response_json[i]['description']
        assert contributions[i].amount == response_json[i]['amount']
        assert contributions[i].user_id == response_json[i]['user_id']
        assert contributions[i].type.name == response_json[i]['type']
        assert contributions[i].monthly_cost == response_json[i]['monthly_cost']


@pytest.mark.asyncio
async def test_contribution_list_successful_no_contributions(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    response = await test_api.get(
        f"contribution/contribution-list/{user_id}",
        headers={
            "Authorization": auth_header
        }, 
    )

    # This user has no contributions to list, and that's OK
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    contributions = response_json['contributions']
    assert len(contributions) == 0

@pytest.mark.asyncio
async def test_contribution_list_invalid_primary_key(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    
    response = await test_api.get(
        "contribution/contribution-list/not-a-primary-key",
        headers={
            "Authorization": auth_header
        }, 
    )
        
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
async def test_contribution_list_no_user(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    nonexistent_user_id: int = 999

    response = await test_api.get(
        f"contribution/contribution-list/{nonexistent_user_id}",
        headers={
            "Authorization": auth_header
        }, 
    )

    # A given user may have zero contributions, so there's nothing to list which is acceptable.
    # A user that doesn't exist will never have any contributions
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert 'contributions' in response_json
    assert len(response_json['contributions']) == 0


@pytest.mark.asyncio
async def test_contribution_list_no_auth(user: User, test_api: AsyncClient, session: AsyncSession) -> None:
    # Register user for an ID and an auth token.
    registration_results: dict = await register_test_user(user, test_api, session)
    auth_header: str = f"Bearer {registration_results["access_token"]}"
    user_id: int = registration_results["user_id"]

    response = await test_api.get(
        f"contribution/contribution-list/{user_id}",
        headers={
            "Authorization": "Bearer no-auth"
        }, 
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED