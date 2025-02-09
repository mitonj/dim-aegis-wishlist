import aiohttp
import asyncio
from typing import Dict, List, Optional, Tuple
import json
import time

class BungieAPI:
    BASE_URL = "https://www.bungie.net/Platform"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = None
        self.cache_file = "bungie_cache.json"
        self.cache = self.load_cache()
        self.request_counter = 0
        self.last_request_time = 0
    
    def load_cache(self) -> Dict:
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                'weapons': {},  # name -> id mapping
                'perks': {},    # name -> id mapping
                'manifest': {}  # item definitions
            }
    
    def save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={
                    "X-API-Key": self.api_key,
                    "Accept": "application/json"
                }
            )
    
    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _make_request(self, endpoint: str) -> Optional[Dict]:
        """Make a rate-limited request to Bungie API"""
        # Rate limiting: max 25 requests per second
        current_time = time.time()
        if current_time - self.last_request_time < 0.04:  # 1/25 second
            await asyncio.sleep(0.04 - (current_time - self.last_request_time))
        
        url = f"{self.BASE_URL}{endpoint}"
        try:
            async with self.session.get(url) as response:
                self.last_request_time = time.time()
                if response.status == 200:
                    data = await response.json()
                    return data.get('Response')
                else:
                    print(f"Error {response.status} for {url}")
                    print(await response.text())
                    return None
        except Exception as e:
            print(f"Request failed: {e}")
            return None
    
    async def get_manifest_urls(self) -> Dict[str, str]:
        """Get the current manifest URLs"""
        manifest = await self.get_manifest()
        if not manifest:
            return {}
        return manifest.get('jsonWorldComponentContentPaths', {}).get('en', {})
    
    async def download_manifest_component(self, url: str) -> Dict:
        """Download a manifest component"""
        if not self.session:
            await self.init_session()
        
        full_url = f"https://www.bungie.net{url}"
        try:
            async with self.session.get(full_url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Error {response.status} downloading manifest from {full_url}")
                    return {}
        except Exception as e:
            print(f"Failed to download manifest: {e}")
            return {}
    
    async def load_item_definitions(self):
        """Load all item definitions from manifest"""
        urls = await self.get_manifest_urls()
        items_url = urls.get('DestinyInventoryItemDefinition')
        if not items_url:
            print("Failed to get item definitions URL")
            return
        
        print("Downloading item definitions...")
        self.cache['manifest'] = await self.download_manifest_component(items_url)
        self.save_cache()
        print("Item definitions downloaded and cached.")
    
    async def search_destiny_items(self, search_term: str) -> List[Dict]:
        """Search for items in the manifest"""
        if not self.cache['manifest']:
            await self.load_item_definitions()
        
        search_term_lower = search_term.lower()
        results = []
        
        for item_hash, item in self.cache['manifest'].items():
            if 'displayProperties' not in item:
                continue
            
            name = item['displayProperties'].get('name', '').lower()
            if search_term_lower in name:
                item['hash'] = int(item_hash)
                results.append(item)
        
        return results
    
    async def get_manifest(self) -> Dict:
        """Get the current version of the Destiny 2 manifest"""
        endpoint = "/Destiny2/Manifest/"
        return await self._make_request(endpoint)
    
    async def get_item_definition(self, item_hash: int) -> Optional[Dict]:
        """Get detailed definition for an item"""
        # Check cache first
        cache_key = str(item_hash)
        if cache_key in self.cache['manifest']:
            return self.cache['manifest'][cache_key]
        
        endpoint = f"/Destiny2/Manifest/DestinyInventoryItemDefinition/{item_hash}/"
        result = await self._make_request(endpoint)
        if result:
            self.cache['manifest'][cache_key] = result
            self.save_cache()
        return result
    
    def is_weapon(self, item: Dict) -> bool:
        """Check if an item is a weapon"""
        # First check if it's explicitly marked as a weapon
        if item.get('itemType') == 3:  # Weapon type
            # Define all known weapon subtypes
            weapon_subtypes = {
                6: "Auto Rifle",
                7: "Hand Cannon",
                8: "Pulse Rifle",
                9: "Scout Rifle",
                10: "Fusion Rifle",
                11: "Sniper Rifle",
                12: "Shotgun",
                13: "Machine Gun",
                14: "Rocket Launcher",
                17: "Submachine Gun",
                18: "Linear Fusion Rifle",
                19: "Grenade Launcher",
                20: "Trace Rifle",
                21: "Bow",
                22: "Glaive",
                23: "Sword",
                24: "Special Grenade Launcher",
                25: "Heavy Grenade Launcher",
                26: "Stasis Auto Rifle",
                27: "Stasis Hand Cannon",
                28: "Stasis Pulse Rifle",
                29: "Stasis Scout Rifle",
                30: "Stasis Fusion Rifle",
                31: "Stasis Sniper Rifle",
                32: "Stasis Shotgun",
                33: "Stasis Machine Gun",
                34: "Stasis Rocket Launcher",
                35: "Stasis Submachine Gun",
                36: "Stasis Linear Fusion Rifle",
                37: "Stasis Grenade Launcher",
                38: "Stasis Trace Rifle",
                39: "Stasis Bow",
                40: "Stasis Glaive",
                41: "Strand Auto Rifle",
                42: "Strand Hand Cannon",
                43: "Strand Pulse Rifle",
                44: "Strand Scout Rifle",
                45: "Strand Fusion Rifle",
                46: "Strand Sniper Rifle",
                47: "Strand Shotgun",
                48: "Strand Machine Gun",
                49: "Strand Rocket Launcher",
                50: "Strand Submachine Gun",
                51: "Strand Linear Fusion Rifle",
                52: "Strand Grenade Launcher",
                53: "Strand Trace Rifle",
                54: "Strand Bow",
                55: "Strand Glaive"
            }
            
            # Check if it's a known weapon subtype
            if item.get('itemSubType') in weapon_subtypes:
                return True
                
            # If subtype is not in our list, check the display name
            display_name = item.get('itemTypeDisplayName', '').lower()
            weapon_type_names = {name.lower() for name in weapon_subtypes.values()}
            if any(type_name in display_name for type_name in weapon_type_names):
                return True
        
        # Check item type display name as fallback
        display_name = item.get('itemTypeDisplayName', '').lower()
        weapon_keywords = ['rifle', 'cannon', 'launcher', 'sword', 'shotgun', 'bow', 'glaive', 'smg']
        return any(keyword in display_name for keyword in weapon_keywords)
    
    def is_perk(self, item: Dict) -> bool:
        """Check if an item is a weapon perk"""
        # First, check if it's a Trait
        if item.get('itemTypeDisplayName') == 'Trait':
            return True
            
        # Fallback to checking if it's a valid perk type
        valid_perk = (
            item.get('itemType') == 19 or  # Mod
            item.get('itemType') == 20     # Talent Grid
        )
        
        if not valid_perk:
            return False
            
        # Check if it's specifically a weapon perk
        item_type = item.get('itemTypeDisplayName', '').lower()
        item_desc = item.get('displayProperties', {}).get('description', '').lower()
        
        # Keywords that indicate weapon perks
        weapon_keywords = ['weapon', 'rounds', 'magazine', 'reload', 'precision', 'damage', 
                         'final blow', 'kills', 'defeating', 'precision hits', 'burst']
        
        # Check if any weapon-related keyword is in the description
        has_weapon_context = any(keyword in item_desc for keyword in weapon_keywords)
        
        return has_weapon_context
    
    async def find_weapon_id(self, weapon_name: str) -> Optional[int]:
        """Find the item hash for a weapon by name"""
        # Check cache first
        if weapon_name in self.cache['weapons']:
            return self.cache['weapons'][weapon_name]
        
        results = await self.search_destiny_items(weapon_name)
        for item in results:
            if (self.is_weapon(item) and 
                item['displayProperties']['name'].lower() == weapon_name.lower()):
                item_hash = item['hash']
                self.cache['weapons'][weapon_name] = item_hash
                self.save_cache()
                return item_hash
        return None
    
    async def find_perk_id(self, perk_name: str) -> Optional[int]:
        """Find the item hash for a perk by name"""
        # Check cache first
        if perk_name in self.cache['perks']:
            return self.cache['perks'][perk_name]
        
        results = await self.search_destiny_items(perk_name)
        for item in results:
            if (self.is_perk(item) and 
                item['displayProperties']['name'].lower() == perk_name.lower()):
                item_hash = item['hash']
                self.cache['perks'][perk_name] = item_hash
                self.save_cache()
                return item_hash
        return None

async def main():
    # Test the API client
    api = BungieAPI("77da3a2dc3064cc99c354b72bb4d39c4")
    await api.init_session()
    
    # Load manifest data
    print("Loading Destiny 2 manifest data...")
    await api.load_item_definitions()
    
    # Test some weapon searches
    test_weapons = [
        "Trustee",
        "The Recluse",
        "Fatebringer",
        "IKELOS_SMG_v1.0.2"
    ]
    
    print("\nTesting weapon searches:")
    for weapon_name in test_weapons:
        print(f"\nSearching for '{weapon_name}'...")
        results = await api.search_destiny_items(weapon_name)
        
        weapons = [item for item in results if api.is_weapon(item)]
        if weapons:
            print(f"Found {len(weapons)} matching weapons:")
            for weapon in weapons:
                print(f"  - {weapon['displayProperties']['name']} (Hash: {weapon['hash']})")
                print(f"    Type: {weapon.get('itemTypeDisplayName', 'Unknown')}")
                print(f"    Tier: {weapon.get('inventory', {}).get('tierTypeName', 'Unknown')}")
        else:
            print("No matching weapons found")
    
    # Test some perk searches
    test_perks = [
        "Rapid Hit",
        "Outlaw",
        "Rampage",
        "Demolitionist"
    ]
    
    print("\nTesting perk searches:")
    for perk_name in test_perks:
        print(f"\nSearching for '{perk_name}'...")
        results = await api.search_destiny_items(perk_name)
        
        perks = [item for item in results if api.is_perk(item)]
        if perks:
            print(f"Found {len(perks)} matching perks:")
            for perk in perks:
                print(f"  - {perk['displayProperties']['name']} (Hash: {perk['hash']})")
                if 'description' in perk['displayProperties']:
                    print(f"    Description: {perk['displayProperties']['description']}")
        else:
            print("No matching perks found")
    
    await api.close_session()

if __name__ == "__main__":
    asyncio.run(main())