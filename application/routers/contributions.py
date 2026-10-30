from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from sqlalchemy import ScalarResult, delete, select, update

from application.auth_utilities import AuthDependency
from application.database import SessionDep
from application.models.contribution import Contribution, ContributionCreate, ContributionUpdate, ContributionSchema

import logging
logger = logging.getLogger(__name__)


contribution_router = APIRouter(
    prefix="/contribution",
    tags=["User's periodic contributions"]
)


@contribution_router.post(
    "/",
    summary="Create a contribution",
    description="Create a contribution for a specified user"
)
async def create_contribution(data: ContributionCreate, session: SessionDep, user: AuthDependency) -> JSONResponse:
    try:
        contribution = Contribution(frequency=data.frequency,
                                    name=data.name,
                                    description=data.description,
                                    amount=data.amount,
                                    user_id=data.user_id,
                                    type=data.type
                                    )
        session.add(contribution)
        await session.commit()
        
        logger.debug(f"Contribution created successfully for User ID: {data.user_id}.")
    except Exception as e:
        log: str = f"Failed to create a contribution for User ID: {data.user_id}." if data.user_id is not None else "No user ID was given to create a contribution."
        logger.error(f"{log} \n[Exception] {e}")
        content = {"message": "Failed to create a contribution for this user."}
        return JSONResponse(content=content, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    content= {"message": "Created contribution successfully"}
    return JSONResponse(content=content, status_code=status.HTTP_201_CREATED)


@contribution_router.get(
    "/{contribution_id}",
    summary="Get a contribution",
    description="Get a contribution by its ID"
)
async def get_contribution(contribution_id: int, session: SessionDep, user: AuthDependency) -> JSONResponse:
    try:
        result: ScalarResult = await session.scalars(select(Contribution).where(Contribution.id == contribution_id))
        result = result.one()
        contribution_schema: ContributionSchema = ContributionSchema()
        contribution_json = contribution_schema.dump(result)
        
        logger.debug(f"Successfully retrieved Contribution, ID: {contribution_id}.")
    except Exception as e:
        log: str = f"Failed to get a contribution with ID: {contribution_id}." if contribution_id is not None else "No ID was given to retrieve a contribution."
        logger.error(f"{log} \n[Exception] {e}")
        content = {"message": f"Failed to retrieve contribution with ID: {contribution_id}"}
        return JSONResponse(content=content, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    content = {
        "message": "Succesfully retrieved contribution.",
        "contribution": contribution_json
    }

    return JSONResponse(content=content, status_code=status.HTTP_200_OK)


@contribution_router.patch(
    "/{contribution_id}",
    summary="Update a contribution",
    description="Update a contribution by its ID"
)
async def update_contribution(contribution_id: int, data: ContributionUpdate, session: SessionDep, user: AuthDependency) -> JSONResponse:
    try:
        result = await session.execute(
            update(Contribution)
            .where(Contribution.id == contribution_id)
            .values(frequency=data.frequency,
                    name=data.name,
                    description=data.description,
                    amount=data.amount,
                    type=data.type)
        )
        await session.commit()

        # Check number of rows matched by where clause. If it is 0, then there are no rows that were updated by 
        #   this query. In SQL, this would be a normal query that runs but affects 0 rows. 
        if result.rowcount != 1: # type: ignore
            raise Exception("No contributions were found with this ID, so none were updated")

        logger.debug(f"Successfully updated contribution, ID: {contribution_id}.")
    except Exception as e:
        log: str = f"Failed to update a contribution with ID: {contribution_id}." if contribution_id is not None else "No ID was given to update a contribution."
        logger.error(f"{log} \n[Exception] {e}")        
        content = {"message": "Failed to update contribution."}
        return JSONResponse(content=content, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    content = {"message": "Successfully updated contribution."}
    return JSONResponse(content=content, status_code=status.HTTP_200_OK)


@contribution_router.delete(
    "/{contribution_id}",
    summary="Delete a contribution",
    description="Delete a contribution by its ID"
)
async def delete_contribution(contribution_id: int, session: SessionDep, user: AuthDependency) -> JSONResponse:
    try:
        result = await session.execute(
            delete(Contribution)
            .where(Contribution.id == contribution_id)
        )
        await session.commit()

        # Check number of rows matched by where clause. If it is 0, then there are no rows that were deleted by 
        #   this query. In SQL, this would be a normal query that runs but affects 0 rows. 
        if result.rowcount != 1: # type: ignore
            raise Exception("No contributions were found with this ID, so none were deleted")

        logger.debug(f"Successfully deleted contribution with ID: {contribution_id}.")
    except Exception as e:
        log: str = f"Failed to delete a contribution with ID: {contribution_id}." if contribution_id is not None else "No ID was given to delete a contribution."
        logger.error(f"{log} \n[Exception] {e}")   
        content = {"message": "Failed to delete given contribution."}
        return JSONResponse(content=content, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    content = {"message": "Succesfully deleted specified contribution."}
    return JSONResponse(content=content, status_code=status.HTTP_200_OK)


@contribution_router.get(
    "/contribution-list/{user_id}",
    summary="List all contributions by user",
    description="Get all contributions tied to the specified user"
)
async def list_contributions(user_id: int, session: SessionDep, user: AuthDependency) -> JSONResponse:
    try:
        result: ScalarResult = await session.scalars(select(Contribution)
                                                    .where(Contribution.user_id == user_id)
                                                    .order_by(Contribution.id.desc()))
        results = result.all()
        contribution_schema: ContributionSchema = ContributionSchema(many=True)
        contribution_json = contribution_schema.dump(results)

        logger.debug(f"Successfully got contributions for User with ID: {user_id}.")
    except Exception as e:
        log: str = f"Failed to list contributions for user with ID: {user_id}." if user_id is not None else "No ID was given to list contributions for a user."
        logger.error(f"{log} \n[Exception] {e}")   
        content = {"message": "Failed to retrieve contributions for this user."}
        return JSONResponse(content=content, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    content = {
        "message": "Succesfully retrieved contributions for this user.",
        "contributions": contribution_json
    }

    return JSONResponse(content=content, status_code=status.HTTP_200_OK)
