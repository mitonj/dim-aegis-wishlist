from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from itertools import product
from config_manager import ConfigManager, PerkOption, TierConfig

@dataclass
class Perk:
    name: str
    hash: int
    description: str = ""

@dataclass
class WeaponRoll:
    name: str
    hash: int
    type: str
    tier: str
    perks_column1: List[Perk]
    perks_column2: List[Perk]

class WishlistGenerator:
    def __init__(self, configs: List[TierConfig] = None):
        self.configs = configs or []
        self.config_manager = ConfigManager()
    
    def _format_weapon_rolls(self, weapon: WeaponRoll) -> Optional[str]:
        """Format all rolls for a weapon in DIM wishlist format"""
        # Check if weapon should be included based on tier
        perk_option = self.config_manager.should_include_weapon(weapon.tier, self.configs)
        if not perk_option:
            return None
            
        # Add weapon header
        output = [f"{weapon.name} - Tier: {weapon.tier}"]
        
        # Generate combinations based on perk option
        all_combinations = set()  # Use set to avoid duplicates
        
        # Include base weapon if option is ANY_PERKS
        if perk_option == PerkOption.ANY_PERKS:
            output.append(f"dimwishlist:item={weapon.hash}")
        
        # Include single perks if option is ANY_COLUMN or ANY_PERKS
        if perk_option in [PerkOption.ANY_COLUMN, PerkOption.ANY_PERKS]:
            # Add single perks from column 1
            if weapon.perks_column1:
                for perk1 in weapon.perks_column1:
                    all_combinations.add(f"dimwishlist:item={weapon.hash}&perks={perk1.hash}")
            
            # Add single perks from column 2
            if weapon.perks_column2:
                for perk2 in weapon.perks_column2:
                    all_combinations.add(f"dimwishlist:item={weapon.hash}&perks={perk2.hash}")
        
        # Include combinations with both perks if both columns have perks
        if weapon.perks_column1 and weapon.perks_column2:
            for perk1, perk2 in product(weapon.perks_column1, weapon.perks_column2):
                all_combinations.add(f"dimwishlist:item={weapon.hash}&perks={perk1.hash},{perk2.hash}")
        
        # Add all combinations to output
        if all_combinations:
            output.extend(sorted(all_combinations))
            # Join with newlines and add an extra newline at the end
            return "\n".join(output) + "\n"
        elif perk_option == PerkOption.ANY_PERKS:
            # Return just the base weapon if ANY_PERKS and no perk combinations
            return "\n".join(output) + "\n"
        else:
            # No valid combinations for this configuration
            return None
    
    def process_matched_weapon(self, weapon_data: Dict) -> Optional[WeaponRoll]:
        """Convert matched weapon data into WeaponRoll format"""
        if not weapon_data:
            return None
            
        # Create Perk objects for each column
        perks_column1 = []
        for perk in weapon_data.get('perks_column1', []):
            if 'hash' not in perk:
                continue
            perks_column1.append(Perk(
                name=perk['name'],
                hash=perk['hash'],
                description=perk.get('description', '')
            ))
            
        perks_column2 = []
        for perk in weapon_data.get('perks_column2', []):
            if 'hash' not in perk:
                continue
            perks_column2.append(Perk(
                name=perk['name'],
                hash=perk['hash'],
                description=perk.get('description', '')
            ))
        
        return WeaponRoll(
            name=weapon_data['name'],
            hash=weapon_data['hash'],
            type=weapon_data['type'],
            tier=weapon_data['tier'],
            perks_column1=perks_column1,
            perks_column2=perks_column2
        )
    
    def generate_dim_wishlist(self, matched_weapons: List[Dict]) -> str:
        """Generate DIM wishlist content from matched weapons data"""
        output = []
        
        # Process each weapon
        for weapon_data in matched_weapons:
            weapon_roll = self.process_matched_weapon(weapon_data)
            if not weapon_roll:
                continue
            
            # Format all rolls for this weapon
            entry = self._format_weapon_rolls(weapon_roll)
            if entry:  # Only add non-None entries
                output.append(entry)
        
        # Join all entries with newlines
        return "\n".join(output) if output else ""
    
    def save_wishlist(self, content: str, output_path: str):
        """Save wishlist content to a file"""
        with open(output_path, 'w') as f:
            f.write(content)