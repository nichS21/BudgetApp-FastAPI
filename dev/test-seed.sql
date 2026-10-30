-- Note: Use for fresh DB only
-- User
INSERT INTO "user" (id, email, hashed_password, hashed_recovery_code)
VALUES (1, 'email@gmail.com', 'not_a_hash', 'recovery_code_1234');


-- Income
INSERT INTO income (annual_salary, income_tax, user_id)
VALUES (90000, 29.5, 1);

-- Expenses
INSERT INTO expense (frequency, name, description, cost, user_id, is_debt)
VALUES (0.25, 'Car insurance', 'Quarterly car insurance payment', 255.59, 1, FALSE), 
(1, 'Electric bill', 'Monthly electric bill payment - average', 330.97, 1, FALSE),
(1, 'Federal Student Loans', 'Monthly payment for federal student loans', 1097.10, 1, TRUE);

--Contributions 
INSERT INTO contribution (frequency, name, description, amount, user_id, type)
VALUES (2, 'Personal Roth IRA', 'Bi-weekly Roth IRA contribution', 150.50, 1, 'RETIREMENT'),
(1, 'Savings Account', 'Monthly savings account contribution', 300.97, 1, 'SAVINGS'),
(0.5, 'New PC Fund', 'Bi-monthly contribution for new PC', 250.66, 1, 'PERSONAL_GOAL');