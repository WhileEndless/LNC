"""
Global Accessibility Manager

Provides a singleton instance of AccessibilityChecker that can be accessed
from anywhere in the application.
"""

from typing import Optional
from lnc.multi.accessibility_checker import AccessibilityChecker

class AccessibilityManager:
    """Singleton manager for accessibility checker"""
    _instance: Optional[AccessibilityChecker] = None
    
    @classmethod
    def initialize(cls, config: dict, console) -> AccessibilityChecker:
        """Initialize the global accessibility checker"""
        if not config.get('network_accessibility_check', True):
            return None
        
        cls._instance = AccessibilityChecker(config, console)
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> Optional[AccessibilityChecker]:
        """Get the current accessibility checker instance"""
        return cls._instance
    
    @classmethod
    def cleanup(cls):
        """Cleanup the accessibility checker"""
        if cls._instance:
            cls._instance.cleanup()
            cls._instance = None