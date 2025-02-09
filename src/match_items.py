import asyncio
from typing import Dict, List, Set, Optional, Tuple
from bungie_api import BungieAPI
from sheet_parser import SheetParser, WeaponRoll

class ItemMatcher:
    def __init__(self, bungie_api_key: str, google_sheets_api_key: str):
        self.bungie = BungieAPI(bungie_api_key)
        self.sheet_parser = SheetParser(google_sheets_api_key)
        self.weapons = {}
        self.missing_weapons = set()
        self.missing_perks = set()
        self.weapon_matches = {}  # name -> [possible matches]
        self.perk_matches = {}    # name -> [possible matches]
    
    def normalize_name(self, name: str) -> str:
        """Normalize a name for comparison by removing special characters and extra spaces"""
        # Remove special characters and convert to lowercase
        normalized = name.lower()
        normalized = normalized.replace('_', ' ')
        normalized = normalized.replace('-', ' ')
        normalized = normalized.replace('.', ' ')
        # Remove multiple spaces and trim
        normalized = ' '.join(normalized.split())
        return normalized

    def get_search_variants(self, name: str) -> List[str]:
        """Get different search variants for a weapon name"""
        # Start with the original name
        variants = [name]
        
        # Handle version numbers in various formats
        version_patterns = [
            '_v', ' v', 'version ', '_ver', ' ver',
            '.0.', '.1.', '.2.', '.3.', '.4.', '.5.'
        ]
        
        base_name = name
        for pattern in version_patterns:
            if pattern in name.lower():
                base_name = name.split(pattern)[0]
                break
        
        if base_name != name:
            variants.append(base_name)
            
        # Add normalized variants
        variants.append(self.normalize_name(name))
        if base_name != name:
            variants.append(self.normalize_name(base_name))
        
        return list(set(variants))
    
    def compare_names(self, name1: str, name2: str) -> Tuple[bool, float]:
        """
        Compare two names and return if they match exactly and a similarity score
        Returns: (exact_match, similarity_score)
        """
        norm1 = self.normalize_name(name1)
        norm2 = self.normalize_name(name2)
        
        # Check for exact match
        if norm1 == norm2:
            return True, 1.0
            
        # Check if one is a complete subset of the other
        if norm1 in norm2 or norm2 in norm1:
            # Calculate length ratio as similarity score
            min_len = min(len(norm1), len(norm2))
            max_len = max(len(norm1), len(norm2))
            return False, min_len / max_len
            
        return False, 0.0
    
    async def find_weapon_matches(self, weapon_name: str) -> List[Dict]:
        """Find all possible matches for a weapon name"""
        if weapon_name in self.weapon_matches:
            return self.weapon_matches[weapon_name]
        
        all_matches = []
        search_variants = self.get_search_variants(weapon_name)
        
        # Try each search variant
        for variant in search_variants:
            results = await self.bungie.search_destiny_items(variant)
            weapon_matches = [item for item in results if self.bungie.is_weapon(item)]
            all_matches.extend(weapon_matches)
        
        # Remove duplicates based on hash
        unique_matches = {match['hash']: match for match in all_matches}.values()
        
        # Score and sort matches
        scored_matches = []
        for match in unique_matches:
            match_name = match['displayProperties']['name']
            exact_match, similarity = self.compare_names(weapon_name, match_name)
            
            if exact_match or similarity > 0.8:  # Only keep good matches
                scored_matches.append((match, exact_match, similarity))
        
        # Sort by exact match first, then by similarity score
        scored_matches.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        # Extract just the matches
        matches = [match for match, _, _ in scored_matches]
        
        # Store matches for future use
        self.weapon_matches[weapon_name] = matches
        return matches
    
    async def find_perk_matches(self, perk_name: str) -> List[Dict]:
        """Find all possible matches for a perk name"""
        if perk_name in self.perk_matches:
            return self.perk_matches[perk_name]
        
        results = await self.bungie.search_destiny_items(perk_name)
        perk_matches = [item for item in results if self.bungie.is_perk(item)]
        
        # Score and filter matches
        scored_matches = []
        for match in perk_matches:
            match_name = match['displayProperties']['name']
            exact_match, similarity = self.compare_names(perk_name, match_name)
            
            if exact_match or similarity > 0.9:  # Stricter matching for perks
                scored_matches.append((match, exact_match, similarity))
        
        # Sort by exact match first, then by similarity score
        scored_matches.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        # Extract just the matches
        matches = [match for match, _, _ in scored_matches]
        
        # Store matches for future use
        self.perk_matches[perk_name] = matches
        return matches
    
    async def match_weapon(self, weapon: WeaponRoll) -> Optional[Dict]:
        """Match a weapon with its Bungie data and perk IDs"""
        print(f"\nMatching weapon: {weapon.name}")
        
        # Try to find the weapon
        matches = await self.find_weapon_matches(weapon.name)
        if not matches:
            # Debug: Print all potential matches before filtering
            results = await self.bungie.search_destiny_items(weapon.name)
            if results:
                print(f"  Found {len(results)} potential matches before filtering:")
                for item in results[:3]:  # Show first 3 matches
                    print(f"    - {item['displayProperties']['name']} "
                          f"(Hash: {item['hash']}, "
                          f"Type: {item.get('itemTypeDisplayName', 'Unknown')}, "
                          f"SubType: {item.get('itemSubType', 'Unknown')})")
            print(f"  No valid weapon matches found for: {weapon.name}")
            self.missing_weapons.add(weapon.name)
            return None
        
        # Show all matches found
        print(f"  Found {len(matches)} possible matches:")
        for i, match in enumerate(matches):
            print(f"    {i+1}. {match['displayProperties']['name']} "
                  f"(Hash: {match['hash']}, Type: {match.get('itemTypeDisplayName', 'Unknown')})")
        
        # Use the first match
        weapon_match = matches[0]
        print(f"  Using: {weapon_match['displayProperties']['name']}")
        
        # Match perks and separate by columns
        print("  Matching perks:")
        column1_perks = []
        column2_perks = []
        
        # Process Column 1 perks
        for perk in weapon.perks[:len(weapon.perks)//2]:  # First half of perks
            print(f"    - Looking for perk: {perk}")
            perk_results = await self.find_perk_matches(perk)
            if perk_results:
                # Use the first match
                perk_match = perk_results[0]
                column1_perks.append({
                    'name': perk,
                    'hash': perk_match['hash'],
                    'description': perk_match['displayProperties'].get('description', ''),
                    'column': 1
                })
                print(f"      Found: {perk_match['displayProperties']['name']} "
                      f"(Hash: {perk_match['hash']}, "
                      f"Type: {perk_match.get('itemTypeDisplayName', 'Unknown')})")
            else:
                # Debug: Print all potential matches before filtering
                results = await self.bungie.search_destiny_items(perk)
                if results:
                    print(f"      Found {len(results)} potential matches before filtering:")
                    for item in results[:3]:  # Show first 3 matches
                        print(f"        - {item['displayProperties']['name']} "
                              f"(Hash: {item['hash']}, "
                              f"Type: {item.get('itemTypeDisplayName', 'Unknown')})")
                print(f"      No valid perk matches found for: {perk}")
                self.missing_perks.add(perk)
        
        # Process Column 2 perks
        for perk in weapon.perks[len(weapon.perks)//2:]:  # Second half of perks
            print(f"    - Looking for perk: {perk}")
            perk_results = await self.find_perk_matches(perk)
            if perk_results:
                # Use the first match
                perk_match = perk_results[0]
                column2_perks.append({
                    'name': perk,
                    'hash': perk_match['hash'],
                    'description': perk_match['displayProperties'].get('description', ''),
                    'column': 2
                })
                print(f"      Found: {perk_match['displayProperties']['name']} "
                      f"(Hash: {perk_match['hash']}, "
                      f"Type: {perk_match.get('itemTypeDisplayName', 'Unknown')})")
            else:
                # Debug: Print all potential matches before filtering
                results = await self.bungie.search_destiny_items(perk)
                if results:
                    print(f"      Found {len(results)} potential matches before filtering:")
                    for item in results[:3]:  # Show first 3 matches
                        print(f"        - {item['displayProperties']['name']} "
                              f"(Hash: {item['hash']}, "
                              f"Type: {item.get('itemTypeDisplayName', 'Unknown')})")
                print(f"      No valid perk matches found for: {perk}")
                self.missing_perks.add(perk)
        
        return {
            'name': weapon.name,
            'hash': weapon_match['hash'],
            'type': weapon_match.get('itemTypeDisplayName', 'Unknown'),
            'tier': weapon.tier,
            'perks_column1': column1_perks,
            'perks_column2': column2_perks
        }
    
    async def process_all_weapons(self):
        """Process all weapons from the spreadsheet"""
        await self.bungie.init_session()
        
        # Get all weapons from spreadsheet
        all_weapons = self.sheet_parser.parse_all_tabs()
        total_weapons = sum(len(weapons) for weapons in all_weapons.values())
        
        print(f"\nProcessing {total_weapons} weapons...")
        
        # Process all weapons
        processed = 0
        matched = 0
        for weapon_type, weapons in all_weapons.items():
            print(f"\nProcessing {weapon_type} weapons ({len(weapons)} found)...")
            for weapon in weapons:
                result = await self.match_weapon(weapon)
                if result:
                    if weapon_type not in self.weapons:
                        self.weapons[weapon_type] = []
                    self.weapons[weapon_type].append(result)
                    matched += 1
                processed += 1
                # Show progress
                print(f"Progress: {processed}/{total_weapons} weapons processed", end='\r')
        
        await self.bungie.close_session()
        
        # Print summary
        print("\n=== MATCHING SUMMARY ===")
        print(f"\nTotal weapons processed: {processed}")
        print(f"Successfully matched: {matched}")
        print(f"Missing weapons: {len(self.missing_weapons)}")
        print(f"Missing perks: {len(self.missing_perks)}")
        
        if self.missing_weapons:
            print("\nMissing weapons:")
            for weapon in sorted(self.missing_weapons):
                print(f"  - {weapon}")
        
        if self.missing_perks:
            print("\nMissing perks:")
            for perk in sorted(self.missing_perks):
                print(f"  - {perk}")
        
        # Show successful matches
        print("\nSuccessful matches:")
        for weapon_type, weapons in self.weapons.items():
            if weapons:
                for weapon in weapons:
                    print(f"\n{weapon['name']} (Hash: {weapon['hash']})")
                    print(f"Type: {weapon['type']}")
                    print(f"Tier: {weapon['tier']}")
                    print("Column 1 Perks:")
                    for perk in weapon['perks_column1']:
                        print(f"  - {perk['name']} (Hash: {perk['hash']})")
                        if perk['description']:
                            print(f"    {perk['description']}")
                    print("Column 2 Perks:")
                    for perk in weapon['perks_column2']:
                        print(f"  - {perk['name']} (Hash: {perk['hash']})")
                        if perk['description']:
                            print(f"    {perk['description']}")

async def main():
    # Load environment variables
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    
    # Get API keys from environment
    bungie_api_key = os.getenv('BUNGIE_API_KEY')
    google_sheets_api_key = os.getenv('GOOGLE_SHEETS_API_KEY')
    
    # Validate API keys
    if not bungie_api_key:
        print("Error: BUNGIE_API_KEY not found in environment variables")
        return
    if not google_sheets_api_key:
        print("Error: GOOGLE_SHEETS_API_KEY not found in environment variables")
        return
    
    # Initialize matcher and process weapons
    matcher = ItemMatcher(bungie_api_key, google_sheets_api_key)
    await matcher.process_all_weapons()
    
    # Generate wishlist
    from wishlist_generator import WishlistGenerator
    generator = WishlistGenerator()
    
    # Collect all matched weapons
    all_matched_weapons = []
    for weapon_type, weapons in matcher.weapons.items():
        all_matched_weapons.extend(weapons)
    
    # Generate wishlist content
    wishlist_content = generator.generate_dim_wishlist(all_matched_weapons)
    
    # Save wishlist
    output_path = "dim_wishlist.txt"
    generator.save_wishlist(wishlist_content, output_path)
    print(f"\nWishlist saved to {output_path}")
    
    # Print preview of the wishlist
    print("\nWishlist Preview (first 500 characters):")
    print("=" * 50)
    print(wishlist_content[:500])
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())