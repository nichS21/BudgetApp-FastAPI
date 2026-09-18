from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from sqlalchemy import ScalarResult, delete, select, update

from application.auth_utilities import AuthDependency
from application.database import SessionDep
from application.models.expense import Expense, ExpenseCreate, ExpenseSchema, ExpenseUpdate

import logging
logger = logging.getLogger(__name__)


expense_router = APIRouter(
    prefix="/expense",
    tags=["User's periodic expenses"]
)


@expense_router.post(
    "/",
    summary="Create an expense",
    description="Create an expense for a specified user"
)
async def create_expense(data: ExpenseCreate, session: SessionDep, user: AuthDependency) -> JSONResponse:
    try: 
        expense = Expense(frequency=data.frequency, 
                          name=data.name,
                          description=data.description,
                          cost=data.cost,
                          user_id=data.user_id,
                          is_debt=data.is_debt)
        session.add(expense)
        await session.commit()

        logger.debug(f"Sucessfully created expense for User, ID: {data.user_id}.")
    except Exception as e:
        log: str = f"Failed to create an expense for user with ID: {data.user_id}." if data.user_id is not None else "No ID was given to create an expense."
        logger.error(f"{log} \n[Exception] {e}") 
        content = {"message": "Failed to create an expense for this user."}
        return JSONResponse(content=content, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    content = {"message": "Created expense successfully."}
    return JSONResponse(content=content, status_code=status.HTTP_201_CREATED)


@expense_router.get(
    "/{expense_id}",
    summary="Get an expense",
    description="Get an expense by its ID"
)
async def get_expense(expense_id: int, session: SessionDep, user: AuthDependency) -> JSONResponse:
    try:
        result: ScalarResult = await session.scalars(select(Expense).where(Expense.id == expense_id))
        result = result.one()
        expense_schema: ExpenseSchema = ExpenseSchema()
        expense_json = expense_schema.dump(result)

        logger.debug(f"Successfully retrieved expense, ID: {expense_id}.")
    except Exception as e:
        log: str = f"Failed to get an expense with ID: {expense_id}." if expense_id is not None else "No ID was given to retrieve an expense."
        logger.error(f"{log} \n[Exception] {e}")
        content = {"message": f"Failed to retrieve expense with ID: {expense_id}"}
        return JSONResponse(content=content, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    content = {
        "message": "Succesfully retrieved expense.",
        "expense": expense_json
    }

    return JSONResponse(content=content, status_code=status.HTTP_200_OK)


@expense_router.patch(
    "/{expense_id}",
    summary="Update an expense",
    description="Update an expense by its ID"
)
async def update_expense(expense_id: int, data: ExpenseUpdate, session: SessionDep, user: AuthDependency) -> JSONResponse:
    try:
        result = await session.execute(
            update(Expense)
            .where(Expense.id == expense_id)
            .values(frequency=data.frequency,
                    name=data.name,
                    description=data.description,
                    cost=data.cost,
                    is_debt=data.is_debt)
        )
        await session.commit()

        # Check number of rows matched by where clause. If it is 0, then there are no rows that were updated by 
        #   this query. In SQL, this would be a normal query that runs but affects 0 rows. 
        if result.rowcount != 1: # type: ignore
            raise Exception("No expense rows were found with this ID, so none were updated")

        logger.debug(f"Successfully updated expense, ID: {expense_id}.")
    except Exception as e:
        log: str = f"Failed to update an expense with ID: {expense_id}." if expense_id is not None else "No ID was given to update an expense."
        logger.error(f"{log} \n[Exception] {e}")
        content = {"message": "Failed to update expense."}
        return JSONResponse(content=content, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    content = {"message": "Successfully updated expense."}
    return JSONResponse(content=content, status_code=status.HTTP_200_OK)


@expense_router.delete(
    "/{expense_id}",
    summary="Delete an expense",
    description="Delete an expense by its ID"
)
async def delete_expense(expense_id: int, session: SessionDep, user: AuthDependency) -> JSONResponse:
    try:
        result = await session.execute(
            delete(Expense)
            .where(Expense.id == expense_id)
        )
        await session.commit()

        # Check number of rows matched by where clause. If it is 0, then there are no rows that were deleted by 
        #   this query. In SQL, this would be a normal query that runs but affects 0 rows. 
        if result.rowcount != 1: # type: ignore
            raise Exception("No expenses were found with this ID, so none were deleted")

        logger.debug(f"Succesfully deleted expense, ID: {expense_id}.")
    except Exception as e:
        log: str = f"Failed to delete an expense with ID: {expense_id}." if expense_id is not None else "No ID was given to delete an expense."
        logger.error(f"{log} \n[Exception] {e}")
        content = {"message": "Failed to delete given expense."}
        return JSONResponse(content=content, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    content = {"message": "Succesfully deleted specified expense."}
    return JSONResponse(content=content, status_code=status.HTTP_200_OK)


@expense_router.get(
    "/expense-list/{user_id}",
    summary="List expenses by user",
    description="Get all the expenses tied to the specified user"
)
async def list_expenses(user_id: int, session: SessionDep, user: AuthDependency) -> JSONResponse:
    try:
        result: ScalarResult = await session.scalars(select(Expense)
                                                     .where(Expense.user_id == user_id)
                                                     .order_by(Expense.id.desc()))
        results = result.all()
        expense_schema: ExpenseSchema = ExpenseSchema(many=True)
        expense_json = expense_schema.dump(results)

        logger.debug(f"Succesfully retrieved expense list for User, ID: {user_id}.")
    except Exception as e:
        log: str = f"Failed to get expense list for user with ID: {user_id}." if user_id is not None else "No ID was given to list expenses for a user."
        logger.error(f"{log} \n[Exception] {e}")
        content = {"message": "Failed to retrieve expenses for this user."}
        return JSONResponse(content=content, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    content = {
        "message": "Succesfully retrieved expenses for this user.",
        "expenses": expense_json
    }

    return JSONResponse(content=content, status_code=status.HTTP_200_OK)
