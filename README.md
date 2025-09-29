# import-questionpro

Python script to extract survey responses from the QuestionPro API, process them into a structured tabular format, and export the results to an Excel file. Useful for automating feedback collection and analysis.

**Note:** This project is not affiliated with or endorsed by QuestionPro. It is an independent tool created to facilitate interaction with the QuestionPro API.

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

## Usage

- Generate your API key on QuestionPro by following their API key generation guide.
- Update the script's variables with your:
  - `api_key` — Your QuestionPro API key
  - `survey_id` — The survey ID to fetch responses from
  - `env` — Regional domain if different from the default (`questionpro.com`)

## Example Output

After running the script, the generated Excel file (`base_questionpro.xlsx`) will have a tabular structure similar to this:

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

## API Documentation

For more details on the QuestionPro API endpoints, authentication, and advanced usage, refer to the official documentation:

https://www.questionpro.com/pt-br/help/generate-api-key.html
