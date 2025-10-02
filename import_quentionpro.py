import requests
import json
import pandas as pd

# general config: input/output
input_path = "respostas_quetsionpro.json"
output_path = "questionpro_data.xlsx"

# API config
api_key = "xxxxxx-xxxxxx-xxxxxx-xx"  # generated on the QuestionPro documentation page
survey_id = "xxxxxxxxx"  # survey ID
env = "questionpro.com"  # default region
page = 1
per_page = 100
all_responses = []

# extraction
headers = {
    "Content-Type": "application/json",
    "api-key": api_key
}

while True:
    url = f"https://api.{env}/a/api/v2/surveys/{survey_id}/responses?page={page}&perPage={per_page}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        break

    data = response.json()
    responses = data.get("response", [])
    all_responses.extend(responses)

    print(f"Page {page} downloaded with {len(responses)} responses...")

    if page >= data["pagination"]["totalPages"]:
        break
    page += 1

# save as JSON
with open(input_path, "w", encoding="utf-8") as f:
    json.dump(all_responses, f, ensure_ascii=False, indent=4)

print("Extraction completed")

# process to Excel
with open(input_path, "r", encoding="utf-8") as file:
    json_data = json.load(file)

excel_data = []

# build table
for entry in json_data:
    row = {
        "responseID": entry.get("responseID"),
        "timestamp": entry.get("timestamp")
    }

    for question in entry.get("responseSet", []):
        qcode = question.get("questionCode")
        answers = question.get("answerValues", [])

        # extract answers
        texts = []
        for ans in answers:
            text = ans.get("answerText") or ans.get("value", {}).get("text", "")
            if text:
                texts.append(text.strip())

        # join multiple answers with comma
        row[qcode] = ", ".join(texts) if texts else ""

    excel_data.append(row)

df = pd.DataFrame(excel_data)

# export to Excel
df.to_excel(output_path, index=False)

print("Process completed! File saved to:", output_path)
