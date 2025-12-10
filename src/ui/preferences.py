"""
User preferences management for ErgoType.2
Saves and loads user choices to/from JSON file.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional


class Preferences:
    """Manages user preferences for the application"""
    
    def __init__(self, config_file: str = ".ergotype_config.json"):
        self.config_file = Path.home() / config_file
        self.data: Dict[str, Any] = self._load()
    
    def _load(self) -> Dict[str, Any]:
        """Load preferences from JSON file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # If file is corrupted, return empty dict
                return {}
        return {}
    
    def save(self) -> None:
        """Save preferences to JSON file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Warning: Could not save preferences: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a preference value"""
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a preference value"""
        self.data[key] = value
    
    def has(self, key: str) -> bool:
        """Check if a preference exists"""
        return key in self.data
    
    def delete(self, key: str) -> None:
        """Delete a preference"""
        if key in self.data:
            del self.data[key]
    
    def clear(self) -> None:
        """Clear all preferences"""
        self.data = {}
        self.save()
    
    # Convenience methods for common preferences
    
    def get_last_keyboard(self) -> Optional[str]:
        """Get the last selected keyboard file"""
        return self.get('last_keyboard')
    
    def set_last_keyboard(self, keyboard_file: str) -> None:
        """Set the last selected keyboard file"""
        self.set('last_keyboard', keyboard_file)
    
    def get_last_text_file(self) -> Optional[str]:
        """Get the last selected text file"""
        return self.get('last_text_file')
    
    def set_last_text_file(self, text_file: str) -> None:
        """Set the last selected text file"""
        self.set('last_text_file', text_file)
    
    def get_ga_params(self) -> Dict[str, Any]:
        """Get saved GA parameters"""
        return self.get('ga_params', {
            'population_size': 30,
            'max_iterations': 50,
            'stagnant_limit': 10,
            'max_processes': 4,
            'fitts_a': 0.5,
            'fitts_b': 0.3
        })
    
    def set_ga_params(self, params: Dict[str, Any]) -> None:
        """Set GA parameters"""
        self.set('ga_params', params)
    
    def get_worker_params(self) -> Dict[str, Any]:
        """Get saved worker parameters"""
        return self.get('worker_params', {
            'use_rabbitmq': True,
            'max_processes': 4
        })
    
    def set_worker_params(self, params: Dict[str, Any]) -> None:
        """Set worker parameters"""
        self.set('worker_params', params)
