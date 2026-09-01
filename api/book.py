from flask import Flask, request, jsonify, send_from_directory
from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
import json
from datetime import datetime, timedelta

app = Flask(__name__, static_folder='../', static_url_path='')

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    if os.path.exists('credentials.json'):
        creds = service_account.Credentials.from_service_account_file(
            'credentials.json', scopes=SCOPES
        )
    else:
        creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if not creds_json:
            raise Exception("Credenziali Google non trovate (variabile d'ambiente mancante)")
        creds_dict = json.loads(creds_json)
        creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        
    return build('calendar', 'v3', credentials=creds)

# Rotta per aprire la pagina web principale (index.html)
@app.route('/')
def serve_index():
    return send_from_directory('../', 'index.html')

@app.route('/api/book', methods=['POST'])
def book_appointment():
    try:
        data = request.get_json()
        name = data.get('name')
        service = data.get('service')
        date_str = data.get('date')
        time_str = data.get('time')
        
        calendar_id = os.environ.get('GOOGLE_CALENDAR_ID')
        
        if not all([name, service, date_str, time_str, calendar_id]):
            return jsonify({"error": "Dati mancanti nella richiesta"}), 400
            
        service_client = get_calendar_service()
        
        start_datetime_str = f"{date_str}T{time_str}:00"
        start_dt = datetime.strptime(start_datetime_str, "%Y-%m-%dT%H:%M:%S")
        end_dt = start_dt + timedelta(minutes=30)
        
        event_body = {
            'summary': f'Taglio: {name} ({service})',
            'description': f'Prenotazione web automatica.\nCliente: {name}\nServizio: {service}',
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'Europe/Rome',
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'Europe/Rome',
            },
        }
        
        service_client.events().insert(calendarId=calendar_id, body=event_body).execute()
        
        return jsonify({"success": True, "message": "Appuntamento aggiunto con successo!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)