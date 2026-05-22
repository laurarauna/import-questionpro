# QuestionPro API to SQL Server Pipeline

A Python ETL tool designed to extract survey responses from the QuestionPro API, transform raw data into a structured relational format, and load it directly into a SQL Server database or an Excel file.

**Note:** This project is not affiliated with or endorsed by QuestionPro. It is an independent tool created to automate interactions with the QuestionPro API.

## Business Impact & Power BI Integration

This tool plays a critical role in our Customer Success tracking pipelines. By automating the extraction of survey data, it eliminates manual exports and enables near real-time monitoring of customer satisfaction and retention metrics.

The processed data feeds directly into a Power BI Dashboard requested by the Customer Success team to monitor the performance of customer retention call campaigns.

Challenges & Technical Solutions:
- Targeting & Cross-Referencing: The challenge was designing a survey targeted at customers with a poor relationship history and seamlessly integrating these subjective responses with hard financial data.
- The Solution: We solved this by extracting specific customer identifiers from the QuestionPro payloads and modeling relationship keys (e.g., Contract IDs) within Azure SQL Server. This allowed us to build a star schema joining the survey responses directly to internal financial and contract databases, providing a 360-degree view of the customer's health.

## Features

- Automated Data Extraction: Connects to the QuestionPro API and fetches all survey responses with built-in pagination support.
- Smart Parsing: Transforms complex JSON payloads into a clean tabular structure where each question code (Q1, Q2, etc.) becomes an independent column.
- Data Normalization: Handles multiple-choice and text answers, concatenating multiple selections into readable comma-separated strings.
- Dual Output: * Exports processed data to an Excel file (.xlsx).
- Persists responses directly into a SQL Server database, automatically avoiding duplicate inserts based on responseID.
- CI/CD Ready: Designed to be scheduled and run periodically (e.g., daily via GitHub Actions, Cron Jobs, or Windows Task Scheduler) to keep the Power BI dataset constantly updated.

## Repository Structure

| File / Folder | Description |
| :--- | :--- |
| `.github/workflows/` | Contains the GitHub Actions YAML file (`etl_pipeline.yml`) for CI/CD pipeline automation. |
| `import_questionpro.py` | Imports raw data from the API and exports it directly to an Excel file. |
| `etl_questionpro.py` | Full ETL script: Extracts API responses, transforms data, and inserts new records into the SQL Server database. |
| `create_db_questionpro.ipynb`| Jupyter Notebook detailing the creation of the SQL Server table schema and Primary Keys. |
| `requirements.txt` | Lists all project dependencies to ensure environment reproducibility. |
| `.gitignore` | Security and version control rules to prevent sensitive files (like `.env`) from being committed. |
| `.env` | Environment variables file containing API keys and DB credentials (⚠️ **Should NOT be committed**). |
| `README.md` | This documentation file. |


## Prerequisites
- **Python 3.10+**
- **Dependencies:** All required libraries (e.g., `pandas`, `pyodbc`, `requests`, `SQLAlchemy`) are mapped in the `requirements.txt` file. Run `pip install -r requirements.txt` to install them.
- **Database:** Access to a SQL Server / Azure SQL database (for the ETL workflow).
- **Automation:** A CI/CD or scheduling tool (e.g., GitHub Actions, Airflow, or Cron) if you wish to automate the pipeline.

## Configuration (.env)
Create a .env file in the project root with the following variables:

- API_KEY=your_api_key_here
- SURVEY_ID=your_survey_id_here
- DB_USER=your_db_user
- DB_PASSWORD=your_db_password

## Usage
**1. API Setup**
- Generate your API key on QuestionPro by following their API key generation guide. Update the script's variables with your specific api_key, survey_id, and env (regional domain, if different from the default).

**2. Recommended Workflow**
- 1. Generate the Base File: Run `import_questionpro.py` to fetch current responses and export them to an Excel file (`quetsionpro_data.xlsx`). This helps visualize the raw structure.
- 2. Create the SQL Schema: Run `create_db_questionpro.ipynb` (or execute your equivalent SQL DDL scripts) to create the database table based on the extracted structure.
- 3. Automate the Load: Run `etl_questionpro.py` to fetch responses and insert new entries into the SQL Server table. Schedule this script in your CI/CD pipeline to keep the database and Power BI dashboards up to date.


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


## Aplication and Integrating with Power BI

In this project, we create a summarized view of key customer retention and satisfaction metrics. This Power BI dashboard, requested by the Customer Success team, was designed to monitor the performance of customer retention call campaigns.

A Customer Success form was created, and survey data from question-pro was cross-referenced with internal financial and contract databases.

**Challenges: designing a survey to target customers with a poor relationship history and integrating financial data with customer success data.**

<img width="1920" height="1080" alt="Projetos" src="https://github.com/user-attachments/assets/a1fdca63-db4d-47bb-80ba-d4929910f11c" />
*Project pipeline*

<img width="1920" height="1080" alt="Projetos (2)" src="https://github.com/user-attachments/assets/8dc18aa9-f72b-45d4-b147-e8d2995d3a64" />
*Dashboard fed by periodic executions of etl_questionpro.py (e.g., daily) through the CI/CD pipeline*

## API Documentation
For more details on the QuestionPro API endpoints, authentication, and advanced usage, refer to the official documentation:

https://www.questionpro.com/pt-br/help/generate-api-key.html
