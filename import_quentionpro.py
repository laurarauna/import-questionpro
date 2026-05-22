import requests
import json
import pandas as pd
import logging
import os
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- SETUP: Logging & Environment ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()

# Variables should strictly come from the environment
API_KEY = os.getenv("API_KEY")
SURVEY_ID = os.getenv("SURVEY_ID")
ENV = os.getenv("QP_ENV", "questionpro.com")

OUTPUT_PATH = "questionpro_data.xlsx"

def get_api_session():
    """Creates a robust HTTP session with automatic retry for API limits/failures."""
    session = requests.Session()
    retry_strategy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    return session

def get_responses(api_key, survey_id, env):
    """Fetches paginated responses from QuestionPro API."""
    if not api_key or not survey_id:
         logging.error("Missing API_KEY or SURVEY_ID environment variables.")
         raise ValueError("Missing API credentials.")

    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    
    session = get_api_session()
    page = 1
    per_page = 100
    all_responses = []

    while True:
        url = f"https://api.{env}/a/api/v2/surveys/{survey_id}/responses?page={page}&perPage={per_page}"
        try:
            response = session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"API Request failed on page {page}: {e}")
            break

        data = response.json()
        responses = data.get("response", [])
        all_responses.extend(responses)

        logging.info(f"Page {page} downloaded with {len(responses)} responses.")

        if page >= data.get("pagination", {}).get("totalPages", 1):
            break
        page += 1

    logging.info(f"Total responses downloaded: {len(all_responses)}")
    return all_responses

def json_to_excel(responses, output_path):
    """Parses JSON responses and exports directly to an Excel file."""
    if not responses:
         logging.warning("No data to process. Excel file will not be created.")
         return

    rows = []
    for entry in responses:
        row = {
            "responseID": entry.get("responseID"),
            "timestamp": entry.get("timestamp")
        }

        for question in entry.get("responseSet", []):
            qcode = question.get("questionCode")
            answers = question.get("answerValues", [])
            texts = [
                ans.get("answerText") or ans.get("value", {}).get("text", "")
                for ans in answers
            ]
            
            # Filter empty strings and join
            valid_texts = [str(t).strip() for t in texts if t]
            row[qcode] = ", ".join(valid_texts) if valid_texts else None

        rows.append(row)

    df = pd.DataFrame(rows)

    # Clean and convert the timestamp column
    if "timestamp" in df.columns:
        df["timestamp"] = df["timestamp"].astype(str).str.replace(" ART", "", regex=False)
        df["timestamp"] = pd.to_datetime(df["timestamp"], format="%d %b, %Y %I:%M:%S %p", errors='coerce')

    df = df.dropna(subset=["responseID"])
    
    try:
        df.to_excel(output_path, index=False)
        logging.info(f"Process completed successfully! File saved to: {output_path}")
    except Exception as e:
         logging.error(f"Failed to save Excel file: {e}")

def main():
    logging.info("Starting QuestionPro Data Export...")
    
    responses = get_responses(API_KEY, SURVEY_ID, ENV)
    json_to_excel(responses, OUTPUT_PATH)

if __name__ == "__main__":
    main()
