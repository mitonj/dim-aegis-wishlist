from typing import Dict, List
from googleapiclient.discovery import build

class GoogleSheetsClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.service = None
    
    def authenticate(self):
        self.service = build('sheets', 'v4', developerKey=self.api_key)
        return self.service
    
    def read_sheet(self, spreadsheet_id: str, range_name: str) -> List[List[str]]:
        if not self.service:
            self.authenticate()
        
        try:
            sheet = self.service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            values = result.get('values', [])
            return values
        except Exception as e:
            print(f"Error reading sheet: {e}")
            return []