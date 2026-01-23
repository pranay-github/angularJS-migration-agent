"""
Pattern Registry - Loads and manages migration patterns
"""

import json
from pathlib import Path
from typing import Dict, List


class PatternRegistry:
    """Manages migration patterns from JSON configuration"""
    
    def __init__(self, patterns_file: str = None):
        if patterns_file is None:
            patterns_file = Path(__file__).parent / "patterns.json"
        
        self.patterns_file = Path(patterns_file)
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict:
        """Load patterns from JSON file"""
        if not self.patterns_file.exists():
            raise FileNotFoundError(f"Patterns file not found: {self.patterns_file}")
        
        with open(self.patterns_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_pattern(self, pattern_type: str) -> Dict:
        """Get migration pattern by type"""
        return self.patterns.get('patterns', {}).get(pattern_type, {})
    
    def get_migration_rules(self, pattern_type: str) -> List[str]:
        """Get migration rules for a specific pattern type"""
        pattern = self.get_pattern(pattern_type)
        return pattern.get('migration', {}).get('rules', [])
    
    def get_template(self, pattern_type: str) -> Dict:
        """Get code template for a specific pattern type"""
        pattern = self.get_pattern(pattern_type)
        return pattern.get('migration', {}).get('template', {})
    
    def get_common_replacements(self) -> Dict[str, str]:
        """Get common AngularJS to Angular replacements"""
        return self.patterns.get('common_replacements', {})
    
    def get_validation_rules(self) -> Dict:
        """Get validation rules"""
        return self.patterns.get('validation_rules', {})
    
    def build_prompt(self, pattern_type: str, code: str, features: Dict = None) -> str:
        """Build LLM prompt based on pattern type and code features"""
        pattern = self.get_pattern(pattern_type)
        
        if not pattern:
            return self._build_generic_prompt(code)
        
        migration = pattern.get('migration', {})
        target = migration.get('target', 'Angular 16+ Component')
        rules = migration.get('rules', [])
        
        # Build simple text prompt (no markdown)
        prompt_parts = [
            f"Migrate this AngularJS {pattern_type} to {target}.",
            "",
            "SOURCE CODE:",
            code.strip(),
            "",
            "MIGRATION RULES:",
        ]
        
        # Add rules
        for i, rule in enumerate(rules, 1):
            prompt_parts.append(f"{i}. {rule}")
        
        # Add detected features
        if features:
            active_features = [k.replace('_', ' ') for k, v in features.items() if v]
            if active_features:
                prompt_parts.append("")
                prompt_parts.append(f"Detected features: {', '.join(active_features[:5])}")
        
        prompt_parts.extend([
            "",
            "OUTPUT:",
            "Return ONLY the migrated TypeScript code. No explanations."
        ])
        
        return "\n".join(prompt_parts)
    
    def _build_generic_prompt(self, code: str) -> str:
        """Fallback generic prompt"""
        return """Migrate this AngularJS code to Angular 16+.

SOURCE CODE:
""" + code + """

REQUIREMENTS:
1. Convert to Angular 16+ Standalone Components
2. Replace AngularJS services with Angular services
3. Use HttpClient for HTTP calls
4. Use RxJS for async operations
5. Add proper TypeScript types
6. Include all imports

OUTPUT:
Return ONLY the migrated TypeScript code. No explanations.
"""