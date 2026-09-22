import pytest

from application.models import User, Income
from application.models.contribution import Contribution, ContributionType
from application.models.expense import Expense

'''
Note: The modal fixtures here are not commited to the test database
    from here, because they would be deleted as soon as their respective 
    function finishes execution. The tests are configured to each run 
    with a clean database that is then torn down.

In other words, these fixtures have to be added to the database explicitly
in the tests they are required in.
'''

@pytest.fixture
def user() -> User:
    return User(
        email="test@email.com",
        hashed_password="Password!"     # This awful password doesn't actually get hashed until it is passed into the regitration utility used by the test suites
    )


@pytest.fixture
def income() -> Income:
    return Income(
        annual_salary=90000,
        income_tax=22.0
    )

@pytest.fixture
def contribution() -> Contribution:
    return Contribution(
        frequency = 1,   # i.e. contribution applied once a month
        name="Roth IRA",
        description="Monthly contribution to personal Roth IRA",
        amount=1000,
        type=ContributionType.RETIREMENT,
    )

@pytest.fixture
def contribution_two() -> Contribution:
    return Contribution(
        frequency = 4,
        name = "New PC Fund",
        description = "Fund for a new PC build",
        amount = 50.50,
        type = ContributionType.PERSONAL_GOAL,
    )

@pytest.fixture
def expense() -> Expense:
    return Expense(
        frequency=1/4,
        name='Car Insurance',
        description='Quarterly car insurance premium payment',
        cost=255.55,
        is_debt=False,
    )

@pytest.fixture
def expense_two() -> Expense:
    return Expense(
        frequency=4,
        name='Groceries',
        description='Monthly weekly grocery expense',
        cost=150.75,
        is_debt=False
    )