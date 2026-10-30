import json

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from sqlalchemy import ScalarResult, select, update

from application.auth_utilities import AuthDependency
from application.database import SessionDep
from application.models.income import Income, IncomeCreate, IncomeSchema, IncomeUpdate

import logging
logger = logging.getLogger(__name__)


income_router = APIRouter(
    prefix="/income",
    tags=["Annual Salary and Income Tax"]
)


@income_router.post(
        "/",
        summary="Create annual salary, and income tax rate",
        description="Create an annual salary with estimated income tax for this user."
        )
async def create_income_and_tax(data: IncomeCreate, session: SessionDep, user: AuthDependency) -> JSONResponse:
    try:
        user_income = Income(annual_salary=data.annual_salary, 
                             income_tax=data.income_tax,
                             user_id=data.user_id)
        session.add(user_income)
        await session.commit()
        logger.debug(f"Successfully created an income and tax for user, ID: {data.user_id}")
    except Exception as e:
        log: str = f"Failed to create an income and tax for user with ID: {data.user_id}." if data.user_id is not None else "No ID was given to create an income and tax."
        logger.error(f"{log} \n[Exception] {e}")        
        content = {"message": "Failed to create an income and tax for this user."}
        return JSONResponse(content=content, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) 

    content = {"message": "Created annual income and tax successfully"}
    return JSONResponse(content=content, status_code=status.HTTP_201_CREATED) 


@income_router.get(
        "/{user_id}",
        summary="Retrive annual salary and income tax rate",
        description="Retrieve the annual salary and income tax rate for this user"
        )
async def get_income_and_tax(user_id: int, session: SessionDep, user: AuthDependency):
    try:
        result: ScalarResult = await session.scalars(select(Income).where(Income.user_id == user_id))
        result = result.one()
        income_schema: IncomeSchema = IncomeSchema()
        income_json = income_schema.dump(result)
        logger.debug(f"Succesfully retrieved an income and tax for user with ID: {user_id}.")
    except Exception as e:
        log: str = f"Failed to retrieve an income and tax for user with ID: {user_id}." if user_id is not None else "No ID was given to retrieve an income and tax."
        logger.error(f"{log} \n[Exception] {e}")         
        content = {"message": "Failed retrieve annual income and tax for this user."}
        return JSONResponse(content=content, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    content = {
        "message": "Successfully retrieved date for this user", 
        "income": income_json
        }
    
    return JSONResponse(content=content, status_code=status.HTTP_200_OK)


@income_router.patch(
        "/{user_id}",
        summary="Update annual salary and income tax rate",
        description="Update the annual salary and income tax rate for this user."
        )
async def update_income_and_tax(user_id: int, data: IncomeUpdate, session: SessionDep, user: AuthDependency) -> JSONResponse:
    try:
        result = await session.execute(
           update(Income) 
           .where(Income.user_id == user_id)
           .values(annual_salary=data.annual_salary,
                   income_tax=data.income_tax)
        )
        await session.commit()

        # Check number of rows matched by where clause. If it is 0, then there are no rows that were updated by 
        #   this query. In SQL, this would be a normal query that runs but affects 0 rows. 
        if result.rowcount != 1: # type: ignore
            raise Exception("No income rows were matched with this ID, so none were updated")

        logger.debug(f"Successfully updated an income and tax for user with ID: {user_id}.")
    except Exception as e:
        log: str = f"Failed to update an income and tax for user with ID: {user_id}." if user_id is not None else "No ID was given to update an income and tax."
        logger.error(f"{log} \n[Exception] {e}")        
        content = {"message": "Failed to update income and tax for this user."}
        return JSONResponse(content=content, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    content = {"message": "Successfully updated income for this user."}
    return JSONResponse(content=content, status_code=status.HTTP_200_OK)