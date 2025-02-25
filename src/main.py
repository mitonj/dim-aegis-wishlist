import asyncio
import os
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv
from bungie_api import BungieAPI
from match_items import ItemMatcher
from wishlist_generator import WishlistGenerator
from sheet_parser import SheetParser
from config_manager import ConfigManager

class WishlistBuilder:
    def __init__(self, bungie_api_key: str, google_sheets_api_key: str):
        self.bungie_api_key = bungie_api_key
        self.google_sheets_api_key = google_sheets_api_key
        self.matcher = ItemMatcher(bungie_api_key, google_sheets_api_key)
        self.generator = None  # Will be initialized after getting user config
        
    async def process_weapons(self) -> Dict[str, List[Dict]]:
        """Process all weapons from the spreadsheet"""
        print("\n=== Processing Weapons ===")
        await self.matcher.bungie.init_session()
        
        try:
            # Get all weapons from spreadsheet
            all_weapons = self.matcher.sheet_parser.parse_all_tabs()
            total_weapons = sum(len(weapons) for weapons in all_weapons.values())
            print(f"\nFound {total_weapons} weapons across {len(all_weapons)} weapon types")
            
            # Process each weapon type
            processed = 0
            matched = 0
            
            for weapon_type, weapons in all_weapons.items():
                print(f"\nProcessing {weapon_type} weapons ({len(weapons)} found)...")
                for weapon in weapons:
                    result = await self.matcher.match_weapon(weapon)
                    if result:
                        if weapon_type not in self.matcher.weapons:
                            self.matcher.weapons[weapon_type] = []
                        self.matcher.weapons[weapon_type].append(result)
                        matched += 1
                    processed += 1
                    # Show progress
                    print(f"Progress: {processed}/{total_weapons} weapons processed", end='\r')
            
            print("\n")  # Clear progress line
            return self.matcher.weapons
            
        finally:
            await self.matcher.bungie.close_session()
    
    def generate_wishlist(self, matched_weapons: Dict[str, List[Dict]], output_path: str):
        """Generate wishlist file from matched weapons"""
        print("\n=== Generating Wishlist ===")
        
        # Get user configuration
        config_manager = ConfigManager()
        configs = config_manager.get_config()
        
        # Initialize generator with configs
        self.generator = WishlistGenerator(configs)
        
        # Collect all matched weapons
        all_matched_weapons = []
        for weapon_type, weapons in matched_weapons.items():
            all_matched_weapons.extend(weapons)
        
        # Sort weapons by type and name
        all_matched_weapons.sort(key=lambda w: (w['type'], w['name']))
        
        # Generate wishlist content
        wishlist_content = self.generator.generate_dim_wishlist(all_matched_weapons)
        
        # Add header with metadata
        header = f"""// DIM Wishlist generated by dim-wishlist-builder
// Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
// Weapons processed: {len(all_matched_weapons)}
// Format: {output_path.split('/')[-1]}

"""
        wishlist_content = header + wishlist_content
        
        # Save wishlist
        self.generator.save_wishlist(wishlist_content, output_path)
        print(f"\nWishlist saved to {output_path}")
        
        # Print preview of the wishlist
        print("\nWishlist Preview (first 500 characters):")
        print("=" * 50)
        print(wishlist_content[:500])
        print("=" * 50)
        
        # Print configuration summary
        print("\nWishlist Configuration:")
        for config in configs:
            print(f"{config.tier} tier: {config.perk_option.name}")

async def async_main():
    # Load environment variables
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
    
    try:
        print("=== Destiny Wishlist Builder ===")
        
        # Initialize builder
        builder = WishlistBuilder(bungie_api_key, google_sheets_api_key)
        
        # Process all weapons
        matched_weapons = await builder.process_weapons()
        
        # Generate wishlist
        output_path = "dim_wishlist.txt"
        builder.generate_wishlist(matched_weapons, output_path)
        
    except Exception as e:
        print(f"\nError: {e}")
        raise

def main():
    """Entry point for synchronous code"""
    asyncio.run(async_main())

if __name__ == "__main__":
    main()