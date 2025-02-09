from typing import Dict, List
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dataclasses import dataclass

@dataclass
class WeaponRoll:
    name: str
    tier: str
    perks: List[str]

class SheetParser:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.spreadsheet_id = "1JM-0SlxVDAi-C6rGVlLxa-J1WGewEeL8Qvq4htWZHhY"
        self.target_gids = {
            "1595979957", "1090554564", "1318165198", "657764751", 
            "1239299765", "288998351", "550485113", "1919916707", 
            "439751986", "473850359", "981030684", "29008106", 
            "1890042119", "324500912", "1315046624", "1712537582", 
            "946843299", "1594008157", "1405969509"
        }
        self.tab_names = self.get_tab_names()
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
    
    def get_tab_names(self) -> Dict[str, str]:
        """Get mapping of GID to tab name"""
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{self.spreadsheet_id}?key={self.api_key}"
        import requests
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception(f"Failed to get spreadsheet metadata: {response.text}")
        
        data = response.json()
        gid_to_name = {}
        for sheet in data['sheets']:
            properties = sheet['properties']
            gid = str(properties['sheetId'])
            if gid in self.target_gids:
                gid_to_name[gid] = properties['title']
        return gid_to_name

    def parse_perks(self, perk_string: str) -> List[str]:
        """Parse perks from a cell, splitting by newlines"""
        if not perk_string:
            return []
        return [perk.strip() for perk in str(perk_string).split('\n') if perk.strip()]
    
    def find_column_indices(self, headers):
        """Find the indices of required columns by their headers"""
        indices = {
            'name': -1,
            'column1': -1,
            'column2': -1,
            'tier': -1
        }
        
        for i, header in enumerate(headers):
            header_lower = str(header).lower().strip()
            if header_lower == 'name':
                indices['name'] = i
            elif header_lower == 'column 1':
                indices['column1'] = i
            elif header_lower == 'column 2':
                indices['column2'] = i
            elif header_lower == 'tier':
                indices['tier'] = i
        
        return indices

    def parse_tab(self, gid: str) -> List[WeaponRoll]:
        if gid not in self.tab_names:
            print(f"GID {gid} not found in sheet")
            return []
            
        tab_name = self.tab_names[gid]
        range_name = f"'{tab_name}'!A:Z"
        values = self.read_sheet(self.spreadsheet_id, range_name)
        
        if not values or len(values) < 2:  # Need at least headers and one row
            print(f"No data found in tab {tab_name} (GID: {gid})")
            return []
        
        # Find the correct column indices from headers
        headers = values[1]  # Headers are in row 2
        print(f"\nHeaders in tab {tab_name}:", headers)
        indices = self.find_column_indices(headers)
        
        # Verify we found all required columns
        if any(idx == -1 for idx in indices.values()):
            missing = [col for col, idx in indices.items() if idx == -1]
            print(f"Missing required columns in tab {tab_name}: {missing}")
            return []
        
        weapons = []
        for row in values[2:]:  # Start from row 3 (after headers)
            if len(row) <= max(indices.values()):
                continue
                
            name = row[indices['name']]
            perk1 = row[indices['column1']]
            perk2 = row[indices['column2']]
            tier = row[indices['tier']]
            
            # Skip rows without real weapon names or empty rows
            if not name or not tier:
                continue
            
            # Skip headers and placeholder weapons
            if (name.lower() in ['name', 'weapon'] or 
                tier.lower() == 'tier' or 
                name.lower() == 'ideal' or 
                tier == '/'):
                continue
                
            # Clean up weapon name (remove version info)
            name = name.split('\n')[0]  # Remove any newline additions
            name = name.split('BRAVE version')[0].strip()
            
            # Parse perks from both columns
            perks = []
            if perk1:
                perks.extend(self.parse_perks(perk1))
            if perk2:
                perks.extend(self.parse_perks(perk2))
            
            # Skip entries without perks
            if not perks:
                continue
            
            weapons.append(WeaponRoll(
                name=name.strip(),
                tier=tier.strip(),
                perks=perks
            ))
        
        return weapons
    
    def parse_all_tabs(self) -> Dict[str, List[WeaponRoll]]:
        all_weapons = {}
        
        for gid in self.target_gids:
            if gid in self.tab_names:
                print(f"\nParsing tab {self.tab_names[gid]} (GID: {gid})...")
                weapons = self.parse_tab(gid)
                if weapons:
                    all_weapons[gid] = weapons
            else:
                print(f"\nSkipping GID {gid} - tab not found")
        
        return all_weapons

def main():
    API_KEY = 'AIzaSyDJTliczEsmloKS44YeT94cN-Px_4UAJgw'
    
    parser = SheetParser(API_KEY)
    all_weapons = parser.parse_all_tabs()
    
    print("\n=== WEAPON DATA ANALYSIS ===\n")
    
    # Process each weapon type
    total_weapons = 0
    for gid, weapons in all_weapons.items():
        tab_name = parser.tab_names[gid]
        total_weapons += len(weapons)
        
        print(f"\n=== {tab_name} ===")
        print(f"Total weapons: {len(weapons)}")
        
        # Show example weapons with their perks
        print("\nExample weapons:")
        for weapon in weapons[:2]:  # Show first 2 weapons
            print(f"\n  {weapon.name} (Tier: {weapon.tier})")
            print("  Perks:")
            for perk in weapon.perks:
                print(f"    - {perk}")
    
    print(f"\n=== OVERALL STATISTICS ===")
    print(f"Total weapon types: {len(all_weapons)}")
    print(f"Total weapons: {total_weapons}")
    
    # Collect all unique perks
    all_perks = set()
    for weapons in all_weapons.values():
        for weapon in weapons:
            all_perks.update(weapon.perks)
    
    print(f"\nTotal unique perks found: {len(all_perks)}")
    print("\nSample of perks:")
    for perk in sorted(list(all_perks))[:20]:
        print(f"  - {perk}")

if __name__ == "__main__":
    main()