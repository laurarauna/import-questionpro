import requests
import pandas as pd
import json
import pyodbc
import time
from dotenv import load_dotenv
import os

# Environment variables
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")

server = 'server_name'
database = 'db_name'
table_name = 'table_name'

# API variables
api_key = os.getenv("API_KEY")
survey_id = os.getenv("SURVEY_ID")
env = 'questionpro.com'  # thasts the padron to USA asd Brazil, consult the env to your region in questionpro documentation

# db connection
max_retries = 10
base_delay = 1
timeout = 60

def connect_db(
    server, database, user, password,
    max_retries=10, base_delay=1, timeout=60
):
    for attempt in range(1, max_retries + 1):
        try:
            conn = pyodbc.connect(
                f"""
                DRIVER={{ODBC Driver 18 for SQL Server}};
                SERVER={server};
                DATABASE={database};
                TrustServerCertificate=Yes;
                MultiSubnetFailover=Yes;
                UID={user};
                PWD={password};
                """,
                timeout=timeout
            )
            print("Connection successful!")
            return conn
        except pyodbc.Error as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt == max_retries:
                raise
            sleep_time = base_delay * (2 ** (attempt - 1))
            time.sleep(sleep_time)


# extracting data from QuestionPro
def get_responses(api_key, survey_id, env):
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }

    page = 1
    per_page = 100
    all_responses = []

    while True:
        url = f"https://api.{env}/a/api/v2/surveys/{survey_id}/responses?page={page}&perPage={per_page}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")
            break

        data = response.json()
        responses = data.get("response", [])
        all_responses.extend(responses)

        print(f"Page {page} dowloalded with {len(responses)} responses...")

        if page >= data["pagination"]["totalPages"]:
            break
        page += 1

    print(f"Total of responses: {len(all_responses)}")
    return all_responses

# json -> df
def json_to_dataframe(responses):
    rows = []

    for entry in responses:
        row = {
            "responseID": entry.get("responseID"),
            "timestamp": entry.get("timestamp")
        }

        for question in entry.get("responseSet", []):
            qcode = question.get("questionCode")
            answers = question.get("answerValues", [])
            texts = []

            for ans in answers:
                text = ans.get("answerText") or ans.get("value", {}).get("text", "")
                if text:
                    texts.append(text.strip())

            row[qcode] = ", ".join(texts) if texts else ""

        rows.append(row)

    df = pd.DataFrame(rows)

    if "responseID" in df.columns:
        df["responseID"] = df["responseID"].str.replace(" ART", "", regex=False)
        df["responseID"] = pd.to_datetime(df["responseID"], format="%d %b, %Y %I:%M:%S %p", errors='coerce')

    df = df.dropna(subset=["responseID"])
    return df

# insert responses in db
def insert_db(df, conn, table_name):
    cursor = conn.cursor()

    # check for duplicate data
    cursor.execute(f"SELECT responseID FROM {table_name}")
    existing_responseID = {row[0] for row in cursor.fetchall()}
    new_rows = df[~df["responseID"].isin(existing_responseID)]

    if new_rows.empty:
        print("Any new response")
        return 0

    # verify columns
    existing_columns = [col.column_name for col in cursor.columns(table=table_name)]
    conn.commit()

    # insert new data
    for _, row in new_rows.iterrows():
        cols = ", ".join(f"[{col}]" for col in row.index)
        placeholders = ", ".join("?" for _ in row)
        values = tuple(row.values)

        insert_sql = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"
        try:
            cursor.execute(insert_sql, values)
        except pyodbc.IntegrityError:
            continue  # ignore duplicate data
        except Exception as e:
            print(f"Error in line: {e}")
    conn.commit()

    return len(new_rows)

def main():
    conn = connect_db(server, database, user, password)
    responses = get_responses(api_key, survey_id, env)
    df = json_to_dataframe(responses)
    total_inserted = insert_db(df, conn, table_name)
    conn.close()
    print(f"Conclude: {total_inserted} new responses.")

if __name__ == "__main__":
    main()