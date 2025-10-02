# import-questionpro
A Python tool to extract survey responses from the QuestionPro API, with two output options:

- Export responses to an Excel file
- Persist responses directly into a SQL Server database

**Note:** This project is not affiliated with or endorsed by QuestionPro. It is an independent tool created to facilitate interaction with the QuestionPro API.

## Repository Structure
| File                        | Description |
|-----------------------------|-------------|
| `import_quentionpro.py` | Imports data from the API to Excel |
| `etl_questionpro.py`        | Extracts responses from the API and inserts new ones into a SQL Server database |
| `create_db_questionpro.ipynb` | Creates the SQL Server table from a base Excel file |
| `.env`                      | Environment variables file (should NOT be committed) |
| `README.md`                 | This documentation file |

## Features
- Connects to the QuestionPro API using your API key and survey ID.
- Fetches all survey responses with pagination support.
- Parses responses to create a clean table where each question code is a column.
- Handles multiple-choice and text answers.
- Exports the processed data to an Excel file (`.xlsx`).

## Prerequisites
- Python 3.7+
- `requests` library
- `pandas` library
- `pyodbc`
- `openpyxl`
- `python-dotenv`

## Configuration (.env)
Create a .env file in the project root with the following variables:

  API_KEY=your_api_key_here
  SURVEY_ID=your_survey_id_here
  DB_USER=your_db_user
  DB_PASSWORD=your_db_password

## Usage
**API:**
- Generate your API key on QuestionPro by following their API key generation guide.
- Update the script's variables with your:
  - `api_key` — Your QuestionPro API key
  - `survey_id` — The survey ID to fetch responses from
  - `env` — Regional domain if different from the default (`questionpro.com`)
 

**Recommended workflow:**
- 1. Generate the Excel base file with survey data
Run `import_questionpro.py` to fetch responses and export them to an Excel file (`quetsionpro_data.xlsx`).

- 2. Create the SQL Server table structure
Run `create_db_questionpro.ipynb` (or equivalent script) to create the database table based on the Excel file's structure.

- 3. Load survey responses into the database
Run `etl_questionpro.p`y to fetch survey responses and insert new entries into the SQL Server table.
This script can be scheduled (daily, weekly, etc.) to keep the database up to date with new responses.

## Example Output
After running the script, the generated Excel file (`quetsionpro_data.xlsx`) will have a tabular structure similar to this:

| responseID | timestamp                 | Q1        | Q2  | Q3                 | Q4           | Q5  |
|------------|---------------------------|-----------|-----|--------------------|--------------|-----|
| 100001     | 29 Sep, 2025 10:15:20 AM ART | Chocolate | Yes | Vanilla, Strawberry | Twice a week | No  |
| 100002     | 29 Sep, 2025 11:05:45 AM ART | Vanilla   | No  | Chocolate          | Once a month | Yes |

- Each `Q#` column corresponds to a question code from the survey.
- Multiple answers in one cell are separated by commas.
- The `timestamp` column shows when the response was submitted.
- `Yes`/`No` answers represent binary responses.
- Empty or missing cells indicate no response for that question.

## Notes
- The script handles pagination automatically, downloading all pages of responses.
- Responses are structured so that each survey question code becomes a column, with answers concatenated if multiple.
- Timestamps are preserved as strings but can be converted for further processing.
- The ETL script handles pagination automatically and avoids inserting duplicate responses based on the responseID.


## Integrating with Power BI
You can connect your SQL Server database to Power BI to monitor survey responses in near real-time. Schedule etl_questionpro.py to run periodically (e.g., daily) to keep your dataset updated.

## API Documentation
For more details on the QuestionPro API endpoints, authentication, and advanced usage, refer to the official documentation:

https://www.questionpro.com/pt-br/help/generate-api-key.html
