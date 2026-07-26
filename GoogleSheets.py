import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1wALF3JSAUKt-m8P8DTKonHvBS45ycQyCGKp_sxPW-uA"
RANGE_NAME = "Sheet1!A:Z"


def authenticate_google(): #Google authentication - holds user's active authorization
    credentials = None

    if os.path.exists("token.json"):
        credentials = Credentials.from_authorized_user_file(
            "token.json",
            SCOPES
        )

    if not credentials or not credentials.valid:

        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json',
                SCOPES
            )

            credentials = flow.run_local_server(port=0)

    with open('token.json', 'w') as token:
        token.write(credentials.to_json())

    return credentials


def connect_to_google_sheets():
    credentials = authenticate_google()

    service = build(
        "sheets",
        "v4",
        credentials=credentials
    )

    return service

inscriptions = []

def read_sheet_data():
    import Database

    service = connect_to_google_sheets()

    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME
    ).execute()

    values = result.get("values", [])
    inscriptions.clear()

    for all in values[1:]:

        first_name = all[0].strip()
        last_name = all[1].strip()
        full_name = f"{first_name} {last_name}".lower()

        participant = {
            "name": full_name,
            "age": int(all[2]) if all[2] else 0,
            "phone": all[3],
            "medical": all[4],
            "transportation": all[5].lower().strip(),
            "email": all[6],
            "accommodation": all[7].strip().lower() if all[7] else 'cabine',
            "inscription": all[8].strip().lower(),
            "payment": float(all[9]) if all[9] else 0.0,
            "food": all[10].lower().strip(),
            "id": all[13]
        }

        inscriptions.append(participant)
    Database.save_data(inscriptions)

    return inscriptions

def delete(id):

    service = connect_to_google_sheets()

    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME
    ).execute()

    values = result.get("values", [])

    row_number = None

    # Row 1 contains the column titles.
    # Therefore, the first participant is on row 2.
    for number, all in enumerate(values[1:], start=2):

        if len(all) > 13 and str(all[13]).strip() == str(id).strip():
            row_number = number
            break

    if row_number is None:
        print("Participante não encontrado no Google Sheets.")
        return False

    # Gets the name of the tab from RANGE_NAME
    sheet_name = RANGE_NAME.split("!")[0].strip("'")

    spreadsheet = service.spreadsheets().get(
        spreadsheetId=SPREADSHEET_ID,
        fields="sheets.properties(sheetId,title)"
    ).execute()

    sheet_id = None

    for sheet in spreadsheet["sheets"]:

        if sheet["properties"]["title"] == sheet_name:
            sheet_id = sheet["properties"]["sheetId"]
            break

    if sheet_id is None:
        print("A página da planilha não foi encontrada.")
        return False

    request = {
        "requests": [
            {
                "deleteDimension": {
                    "range": {
                        "sheetId": sheet_id,
                        "dimension": "ROWS",
                        "startIndex": row_number - 1,
                        "endIndex": row_number
                    }
                }
            }
        ]
    }

    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body=request
    ).execute()

    return True
