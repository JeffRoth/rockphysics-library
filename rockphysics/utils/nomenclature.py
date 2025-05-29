import yaml
from pathlib import Path
import pandas as pd # Assuming you use pandas for log data

# Define a default path or allow it to be configured
DEFAULT_ALIAS_FILEPATH = Path(__file__).resolve().parent.parent / "resources/log_mnemonic_aliases.yaml"

class LogNomenclature:
    def __init__(self, alias_filepath=None):
        if alias_filepath is None:
            alias_filepath = DEFAULT_ALIAS_FILEPATH
        self.alias_map = self._load_aliases(alias_filepath)
        if not self.alias_map:
            print(f"Warning: Log mnemonic alias map could not be loaded from {alias_filepath}. Canonical type lookups may not work as expected.")

    def _load_aliases(self, filepath):
        try:
            with open(filepath, 'r') as file:
                data = yaml.safe_load(file)
                return data.get('LOG_MNEMONIC_ALIASES', {})
        except FileNotFoundError:
            print(f"Error: Alias file {filepath} not found.")
            return {}
        except yaml.YAMLError as e:
            print(f"Error parsing YAML alias file {filepath}: {e}")
            return {}
        except Exception as e:
            print(f"An unexpected error occurred while loading alias file {filepath}: {e}")
            return {}

    def get_log_type(self, mnemonic: str) -> str:
        """
        Finds the canonical log name for a given mnemonic.
        Returns the canonical name if found, otherwise the original mnemonic (uppercased).
        """
        if not self.alias_map: # No aliases loaded or loading failed
            return str(mnemonic).upper()

        mnemonic_upper = str(mnemonic).upper()
        for canonical_name, aliases in self.alias_map.items():
            # Ensure all aliases in the map are also uppercase and strings for consistent comparison
            if mnemonic_upper in [str(alias).upper() for alias in aliases if alias is not None]:
                return canonical_name
        return mnemonic_upper # Fallback to original mnemonic (uppercased)

    def get_log_type_map(self, curve_mnemonics: list[str]) -> dict[str, str]:
        """
        Creates a mapping from a list of curve mnemonics to their canonical types.
        """
        mapping = {}
        for mnem in curve_mnemonics:
            mapping[mnem] = self.get_log_type(mnem)
        return mapping