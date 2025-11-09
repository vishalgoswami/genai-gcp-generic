#!/usr/bin/env python3
"""
Safety Configuration
Manages safety mode selection and configuration
"""

import os
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class SafetyMode(Enum):
    """Safety scanning modes"""
    VERTEX_AI_ONLY = "vertex_ai"          # Use only Vertex AI native safety filters
    MODEL_ARMOR_ONLY = "model_armor"      # Use only Model Armor API
    BOTH = "both"                          # Use both (maximum protection)
    
    @classmethod
    def from_string(cls, mode: str) -> "SafetyMode":
        """Convert string to SafetyMode"""
        mode_map = {
            "vertex_ai": cls.VERTEX_AI_ONLY,
            "vertex": cls.VERTEX_AI_ONLY,
            "model_armor": cls.MODEL_ARMOR_ONLY,
            "armor": cls.MODEL_ARMOR_ONLY,
            "both": cls.BOTH,
            "all": cls.BOTH,
        }
        return mode_map.get(mode.lower(), cls.VERTEX_AI_ONLY)
    
    def __str__(self) -> str:
        """Get display name"""
        names = {
            SafetyMode.VERTEX_AI_ONLY: "Vertex AI Safety Filters Only",
            SafetyMode.MODEL_ARMOR_ONLY: "Model Armor Only",
            SafetyMode.BOTH: "Both (Vertex AI + Model Armor)",
        }
        return names[self]
    
    def get_short_name(self) -> str:
        """Get short display name"""
        names = {
            SafetyMode.VERTEX_AI_ONLY: "Vertex AI",
            SafetyMode.MODEL_ARMOR_ONLY: "Model Armor",
            SafetyMode.BOTH: "Vertex AI + Armor",
        }
        return names[self]


@dataclass
class SafetyConfig:
    """Safety configuration settings"""
    mode: SafetyMode
    model_armor_prompt_template: Optional[str] = None
    model_armor_response_template: Optional[str] = None
    enable_logging: bool = True
    fail_open: bool = True  # Allow requests if Model Armor API fails
    auto_fallback: bool = True  # Automatically fallback to Vertex AI if Model Armor unavailable
    
    @classmethod
    def from_env(cls) -> "SafetyConfig":
        """Create configuration from environment variables with safe defaults"""
        mode_str = os.getenv("SAFETY_MODE", "vertex_ai")
        mode = SafetyMode.from_string(mode_str)
        
        config = cls(
            mode=mode,
            model_armor_prompt_template=os.getenv("MODEL_ARMOR_PROMPT_TEMPLATE"),
            model_armor_response_template=os.getenv("MODEL_ARMOR_RESPONSE_TEMPLATE"),
            enable_logging=os.getenv("SAFETY_LOGGING", "true").lower() == "true",
            fail_open=os.getenv("SAFETY_FAIL_OPEN", "true").lower() == "true",
            auto_fallback=os.getenv("SAFETY_AUTO_FALLBACK", "true").lower() == "true",
        )
        
        # Auto-fallback to Vertex AI if Model Armor config is incomplete
        if config.requires_model_armor():
            valid, error = config.validate()
            if not valid:
                if config.enable_logging:
                    print(f"⚠️  Model Armor configuration incomplete: {error}")
                    print(f"⚠️  Falling back to Vertex AI only mode")
                config.mode = SafetyMode.VERTEX_AI_ONLY
        
        return config
    
    def requires_vertex_ai(self) -> bool:
        """Check if Vertex AI safety filters are required"""
        return self.mode in (SafetyMode.VERTEX_AI_ONLY, SafetyMode.BOTH)
    
    def requires_model_armor(self) -> bool:
        """Check if Model Armor scanning is required"""
        return self.mode in (SafetyMode.MODEL_ARMOR_ONLY, SafetyMode.BOTH)
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if self.requires_model_armor():
            if not self.model_armor_prompt_template and not self.model_armor_response_template:
                return False, "Model Armor mode requires at least one template ID"
        
        return True, None
    
    def get_description(self) -> str:
        """Get detailed description of configuration"""
        lines = [
            f"Safety Mode: {self.mode}",
            f"Vertex AI Filters: {'✅ Enabled' if self.requires_vertex_ai() else '❌ Disabled'}",
            f"Model Armor: {'✅ Enabled' if self.requires_model_armor() else '❌ Disabled'}",
        ]
        
        if self.requires_model_armor():
            lines.append(f"  - Prompt Template: {self.model_armor_prompt_template or 'None'}")
            lines.append(f"  - Response Template: {self.model_armor_response_template or 'None'}")
        
        lines.append(f"Logging: {'✅ Enabled' if self.enable_logging else '❌ Disabled'}")
        lines.append(f"Fail Open: {'✅ Yes' if self.fail_open else '❌ No'}")
        
        return "\n".join(lines)


# Default configuration
DEFAULT_CONFIG = SafetyConfig(
    mode=SafetyMode.VERTEX_AI_ONLY,
    enable_logging=True,
    fail_open=True
)


# Example usage
if __name__ == "__main__":
    print("Safety Configuration Examples\n")
    
    # From environment
    config = SafetyConfig.from_env()
    print("Configuration from environment:")
    print(config.get_description())
    print()
    
    # Validate
    valid, error = config.validate()
    if valid:
        print("✅ Configuration is valid")
    else:
        print(f"❌ Configuration error: {error}")
    print()
    
    # Test all modes
    print("Available safety modes:")
    for mode in SafetyMode:
        print(f"  • {mode.value}: {mode}")
