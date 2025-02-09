from typing import Dict, Set, List, Optional
from dataclasses import dataclass
from enum import Enum

class TierSelection(Enum):
    S_ONLY = 1
    S_A = 2
    S_A_B = 3
    ALL = 4

    @staticmethod
    def get_tiers(selection: 'TierSelection') -> Set[str]:
        tier_map = {
            TierSelection.S_ONLY: {'S'},
            TierSelection.S_A: {'S', 'A'},
            TierSelection.S_A_B: {'S', 'A', 'B'},
            TierSelection.ALL: {'S', 'A', 'B', 'C', 'D', 'F'}
        }
        return tier_map[selection]

class PerkOption(Enum):
    BOTH_COLUMNS = 1  # Only combinations with perks in both columns
    ANY_COLUMN = 2    # Combinations with at least one perk
    ANY_PERKS = 3     # Include weapon even without perks

@dataclass
class TierConfig:
    tier: str
    perk_option: PerkOption

class ConfigManager:
    @staticmethod
    def get_tier_selection() -> TierSelection:
        while True:
            print("\nSelect tiers to include in wishlist:")
            print("1. S tier only")
            print("2. S and A tiers")
            print("3. S, A, and B tiers")
            print("4. All tiers")
            
            try:
                choice = int(input("Enter your choice (1-4): "))
                if 1 <= choice <= 4:
                    return TierSelection(choice)
                print("Invalid choice. Please enter a number between 1 and 4.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    @staticmethod
    def get_perk_option(tier: str) -> PerkOption:
        while True:
            print(f"\nSelect perk configuration for {tier} tier:")
            print("1. Only combinations with perks in both columns")
            print("2. Combinations with at least one perk")
            print("3. Include weapon even without perks")
            
            try:
                choice = int(input("Enter your choice (1-3): "))
                if 1 <= choice <= 3:
                    return PerkOption(choice)
                print("Invalid choice. Please enter a number between 1 and 3.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def get_config(self) -> List[TierConfig]:
        # Get tier selection
        tier_selection = self.get_tier_selection()
        tiers = TierSelection.get_tiers(tier_selection)
        
        # Get perk options for each selected tier
        configs = []
        for tier in sorted(tiers):  # Sort to ensure consistent order (S, A, B, etc.)
            perk_option = self.get_perk_option(tier)
            configs.append(TierConfig(tier=tier, perk_option=perk_option))
        
        return configs

    @staticmethod
    def should_include_weapon(tier: str, configs: List[TierConfig]) -> Optional[PerkOption]:
        """Check if a weapon should be included based on its tier"""
        for config in configs:
            if config.tier == tier:
                return config.perk_option
        return None