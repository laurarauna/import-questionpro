import requests
import pandas as pd
import json
import pyodbc
import time
from dotenv import load_dotenv
import os

# config gerais
server = os.getenv("DB_SERVER")
database = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
senha = os.getenv("DB_PASSWORD")
table_name = os.getenv("TABLE_NAME", "TB_RESPOSTA_QUESTIONPRO")  # valor padrão

# config api
api_key = os.getenv("API_KEY")
survey_id = os.getenv("SURVEY_ID")
env = "questionpro.com"  # ambiente padrão

# conecta banco
max_retries = 10
base_delay = 1
timeout = 60

def connect_db(
    server, database, user, senha,
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
                PWD={senha};
                """,
                timeout=timeout
            )
            print("Conexão bem-sucedida!")
            return conn
        except pyodbc.Error as e:
            print(f"Tentativa {attempt} falhou: {e}")
            if attempt == max_retries:
                raise
            sleep_time = base_delay * (2 ** (attempt - 1))
            time.sleep(sleep_time)


# extração questionpro
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
            print(f"Erro {response.status_code}: {response.text}")
            break

        data = response.json()
        responses = data.get("response", [])
        all_responses.extend(responses)

        print(f"Página {page} baixada com {len(responses)} respostas...")

        if page >= data["pagination"]["totalPages"]:
            break
        page += 1

    print(f"Total de respostas coletadas: {len(all_responses)}")
    return all_responses

# json em df
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

    if "timestamp" in df.columns:
        df["timestamp"] = df["timestamp"].str.replace(" ART", "", regex=False)
        df["timestamp"] = pd.to_datetime(df["timestamp"], format="%d %b, %Y %I:%M:%S %p", errors='coerce')

    df = df.dropna(subset=["timestamp"])
    return df

# insere respostas no db
def insert_db(df, conn, table_name):
    cursor = conn.cursor()

    # verifica observações do db
    cursor.execute(f"SELECT timestamp FROM {table_name}")
    existing_timestamps = {row[0] for row in cursor.fetchall()}

    # filtra novas
    new_rows = df[~df["timestamp"].isin(existing_timestamps)]

    if new_rows.empty:
        print("ℹ️ Nenhuma nova resposta a inserir.")
        return 0

    # verifica colunas da tabela
    existing_columns = [col.column_name for col in cursor.columns(table=table_name)]
    conn.commit()

    # Inserção linha a linha
    for _, row in new_rows.iterrows():
        cols = ", ".join(f"[{col}]" for col in row.index)
        placeholders = ", ".join("?" for _ in row)
        values = tuple(row.values)

        insert_sql = f"INSERT INTO {table_name} ({cols}) VALUES ({placeholders})"
        try:
            cursor.execute(insert_sql, values)
        except pyodbc.IntegrityError:
            continue  # ignora duplicatas silenciosamente
        except Exception as e:
            print(f"Erro ao inserir linha: {e}")
    conn.commit()

    return len(new_rows)

def main():
    conn = connect_db(server, database, user, senha)
    responses = get_responses(api_key, survey_id, env)
    df = json_to_dataframe(responses)
    total_inserted = insert_db(df, conn, table_name)
    conn.close()
    print(f"✅ Inserção concluída: {total_inserted} novas respostas adicionadas ao banco.")

if __name__ == "__main__":
    main()