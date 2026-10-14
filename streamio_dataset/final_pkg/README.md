# Streamio dataset

Files:
- `streaming_platform_final.sql` - MySQL 8 DDL + data (3NF, 9 tables)
- `csv/*.csv` - one file per table, column names match the SQL
- `streaming_platform_data.json` - all tables in one JSON file

Row counts: user=12, plan=3, category=9, content=30, subscription=10, payment=12, watchlist=15, watch_history=12, review=9

## Demo logins (passwords are stored as bcrypt hashes)

| Email | Password | Role |
|---|---|---|
| admin@streamio.com | Admin@12345 | ADMIN |
| editor@streamio.com | User@12345 | EDITOR |
| aarav@example.com | pass123 | USER |
| riya@example.com | pass456 | USER |
| john@example.com | pass789 | USER |
| emma@example.com | pass321 | USER |
| vikram@example.com | pass111 | USER |
| priya@example.com | pass222 | USER |
| liam@example.com | pass333 | USER |
| sofia@example.com | pass444 | USER |
| ali@example.com | pass555 | USER |
| ananya@example.com | pass666 | USER |
