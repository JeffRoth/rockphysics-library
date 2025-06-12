import yaml
from pathlib import Path
import pandas as pd # Assuming you use pandas for log data

# Define a default path or allow it to be configured
# DEFAULT_ALIAS_FILEPATH = Path(__file__).resolve().parent.parent / "resources/log_mnemonic_aliases.yaml"

class LogNomenclature:
    def __init__(self, alias_filepath=None):
        if alias_filepath is None: alias_filepath = Path(__file__).resolve().parent.parent / "resources/log_mnemonic_aliases.yaml"
        self.alias_map = self._load_aliases(alias_filepath)

    def _load_aliases(self, filepath: Path) -> dict:
        try:
            with open(filepath, 'r') as file:
                data = yaml.safe_load(file)
                processed_map = {}
                for canonical, aliases in data.get('LOG_MNEMONIC_ALIASES', {}).items():
                    processed_map[canonical] = [str(alias).upper() for alias in aliases if alias is not None]
                return processed_map
        except FileNotFoundError: return {}
        except yaml.YAMLError: return {}
        except Exception: return {}

    def set_log_type(self, mnemonic: str, canonical_type: str):
        mnemonic_upper = str(mnemonic).upper()
        canonical_type_upper = str(canonical_type).upper()
        aliases = self.alias_map.get(canonical_type_upper, [])
        if mnemonic_upper not in aliases: aliases.append(mnemonic_upper)
        self.alias_map[canonical_type_upper] = aliases

    def get_log_type(self, mnemonic: str) -> str:
        mnemonic_upper = str(mnemonic).upper()
        best_match_type = None; max_match_len = 0
        for canonical_name, aliases in self.alias_map.items():
            for alias in aliases:
                if mnemonic_upper.startswith(alias):
                    if len(alias) > max_match_len:
                        max_match_len = len(alias)
                        best_match_type = canonical_name
        return best_match_type if best_match_type else mnemonic_upper
    
    def get_log_type_map(self, curve_mnemonics: list[str]) -> dict[str, str]:
        return {mnem: self.get_log_type(mnem) for mnem in curve_mnemonics}