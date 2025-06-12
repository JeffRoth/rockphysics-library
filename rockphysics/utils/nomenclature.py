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
        
    def set_log_type(self, mnemonic: str, canonical_type: str):
        """
        Manually sets or overrides the canonical type for a specific mnemonic.

        This is useful for correcting misclassifications or defining types for
        non-standard mnemonics. This change only affects the current instance.

        Args:
            mnemonic (str): The log mnemonic to assign (e.g., 'MY_CUSTOM_GR').
            canonical_type (str): The canonical type to assign it to (e.g., 'GAMMA_RAY').
        """
        mnemonic_upper = str(mnemonic).upper()
        canonical_type_upper = str(canonical_type).upper()

        # Get the list of aliases for the canonical type, or an empty list if it's new
        aliases = self.alias_map.get(canonical_type_upper, [])
        
        # Add the new mnemonic to the list if it's not already there
        if mnemonic_upper not in aliases:
            aliases.append(mnemonic_upper)
        
        # Update the map with the modified (or new) list of aliases
        self.alias_map[canonical_type_upper] = aliases

    def get_log_type(self, mnemonic: str) -> str:
        """
        Finds the canonical log type for a given mnemonic by finding the longest
        matching prefix alias.

        This method checks for all possible prefix matches and returns the one
        corresponding to the longest alias, ensuring that 'DTS' matches 'S_SONIC'
        over 'P_SONIC' (which matches 'DT').

        Args:
            mnemonic (str): The log mnemonic to classify (e.g., 'DTS').

        Returns:
            str: The canonical log type (e.g., 'S_SONIC') if a match is found,
                 otherwise the original mnemonic in uppercase.
        """
        if not self.alias_map:
            return str(mnemonic).upper()

        mnemonic_upper = str(mnemonic).upper()
        
        best_match_type = None
        max_match_len = 0

        # Find the best (longest) matching alias across all canonical types
        for canonical_name, aliases in self.alias_map.items():
            for alias in aliases:
                if mnemonic_upper.startswith(alias):
                    # If this match is longer than the previous best, it becomes the new best.
                    if len(alias) > max_match_len:
                        max_match_len = len(alias)
                        best_match_type = canonical_name
        
        # Return the best match found, or the original mnemonic if no match was made.
        if best_match_type:
            return best_match_type
        else:
            return mnemonic_upper

    def get_log_type_map(self, curve_mnemonics: list[str]) -> dict[str, str]:
        """
        Creates a mapping from a list of curve mnemonics to their canonical types.
        """
        mapping = {}
        for mnem in curve_mnemonics:
            mapping[mnem] = self.get_log_type(mnem)
        return mapping