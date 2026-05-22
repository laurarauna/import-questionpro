import requests
import pandas as pd
import pyodbc
import time
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
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
SERVER = os.getenv("DB_SERVER", "default_server_name")
DATABASE = os.getenv("DB_NAME", "default_db_name")
TABLE_NAME = os.getenv("DB_TABLE", "default_table_name")

API_KEY = os.getenv("API_KEY")
SURVEY_ID = os.getenv("SURVEY_ID")
ENV = os.getenv("QP_ENV", "questionpro.com")


def connect_db(server, database, user, password, max_retries=5, base_delay=2):
    """Establishes database connection with exponential backoff."""
    for attempt in range(1, max_retries + 1):
        try:
            conn = pyodbc.connect(
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"UID={user};"
                f"PWD={password};"
                f"TrustServerCertificate=Yes;"
                f"MultiSubnetFailover=Yes;",
                timeout=30
            )
            logging.info("Database connection successful.")
            return conn
        except pyodbc.Error as e:
            logging.warning(f"DB Connection attempt {attempt} failed: {e}")
            if attempt == max_retries:
                logging.error("Max database retries reached.")
                raise
            time.sleep(base_delay * (2 ** (attempt - 1)))


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


def json_to_dataframe(responses):
    """Parses JSON responses into a structured DataFrame."""
    if not responses:
        return pd.DataFrame()

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

    # FIX: Clean and convert the timestamp column, not the responseID
    if "timestamp" in df.columns:
        df["timestamp"] = df["timestamp"].astype(str).str.replace(" ART", "", regex=False)
        df["timestamp"] = pd.to_datetime(df["timestamp"], format="%d %b, %Y %I:%M:%S %p", errors='coerce')

    df = df.dropna(subset=["responseID"])
    return df


def insert_db(df, conn, table_name):
    """Inserts new rows using bulk execution."""
    if df.empty:
        logging.info("DataFrame is empty. Nothing to insert.")
        return 0

    cursor = conn.cursor()
    # Enable bulk inserts for massive performance boost
    cursor.fast_executemany = True 

    # Determine which IDs already exist using a scalable approach
    # We query the DB only for the IDs present in our current DataFrame
    incoming_ids = tuple(df["responseID"].astype(str).tolist())
    
    # Handle single element tuple syntax for SQL
    if len(incoming_ids) == 1:
        query_ids = f"('{incoming_ids[0]}')"
    else:
        query_ids = str(incoming_ids)

    cursor.execute(f"SELECT responseID FROM {table_name} WHERE CAST(responseID AS VARCHAR) IN {query_ids}")
    existing_response_ids = {str(row[0]) for row in cursor.fetchall()}

    # Filter out existing rows
    new_rows = df[~df["responseID"].astype(str).isin(existing_response_ids)]

    if new_rows.empty:
        logging.info("No new responses to insert.")
        return 0

    # Dynamic SQL generation
    cols = ", ".join(f"[{col}]" for col in new_rows.columns)
    placeholders = ", ".join("?" for _ in new_rows.columns)
    insert_sql = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"
    
    # Prepare data for executemany (list of tuples)
    values = [tuple(row) for row in new_rows.to_numpy()]

    try:
        cursor.executemany(insert_sql, values)
        conn.commit()
        logging.info(f"Successfully inserted {len(new_rows)} new records.")
    except Exception as e:
        conn.rollback()
        logging.error(f"Failed to bulk insert data: {e}")
        return 0

    return len(new_rows)


def main():
    logging.info("Starting QuestionPro ETL Pipeline...")
    
    responses = get_responses(API_KEY, SURVEY_ID, ENV)
    df = json_to_dataframe(responses)
    
    if not df.empty:
        conn = connect_db(SERVER, DATABASE, USER, PASSWORD)
        if conn:
            insert_db(df, conn, TABLE_NAME)
            conn.close()
            logging.info("Pipeline executed successfully.")
    else:
        logging.warning("Pipeline finished without data.")

if __name__ == "__main__":
    main()
