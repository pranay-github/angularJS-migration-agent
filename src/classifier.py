"""
File Classifier - Detects AngularJS component types using LLM
"""

import json
from typing import Dict
from pathlib import Path


class FileClassifier:
    """Classifies AngularJS files by type using LLM intelligence"""
    
    def __init__(self, llm=None):
        """
        Initialize classifier with optional LLM instance
        
        Args:
            llm: LangChain LLM instance (ChatCopilot). If None, will be lazy-loaded.
        """
        self.llm = llm
    
    def classify(self, code: str) -> Dict[str, any]:
        """
        Classify AngularJS code using LLM
        
        Returns:
            {
                'primary_type': 'service' | 'controller' | 'directive' | 'filter' | 'router' | 'module',
                'detected_types': ['service', 'controller'],
                'confidence': 0.95,
                'features': {
                    'uses_resource': True,
                    'uses_scope': False,
                    'has_http_calls': True
                },
                'complexity': 'low' | 'medium' | 'high'
            }
        """
        if not self.llm:
            raise RuntimeError("LLM not initialized. Pass llm instance to FileClassifier constructor.")
        
        # Build classification prompt
        prompt = self._build_classification_prompt(code)
        
        # Get LLM response
        from langchain_core.messages import HumanMessage, SystemMessage
        
        system_msg = SystemMessage(content="""You are an AngularJS expert classifier.
Analyze the code and return ONLY a valid JSON object with this exact structure:
{
  "primary_type": "service|controller|directive|filter|router|module",
  "detected_types": ["service", "controller"],
  "confidence": 0.95,
  "features": {
    "uses_resource": true,
    "uses_http": false,
    "uses_scope": false,
    "uses_rootscope": false,
    "uses_q_promises": false,
    "uses_timeout": false,
    "uses_interval": false,
    "has_watchers": false,
    "has_broadcasts": false,
    "has_ui_router": false,
    "has_filters": false,
    "has_directives": false
  },
  "complexity": "low|medium|high",
  "reasoning": "Brief explanation"
}

Return ONLY the JSON, no other text.""")
        
        response = self.llm.invoke([system_msg, HumanMessage(content=prompt)])
        
        # Parse LLM response
        try:
            # Clean response (remove markdown code blocks if present)
            content = response.content.strip()
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            result = json.loads(content)
            
            # Validate required fields
            if 'primary_type' not in result:
                result['primary_type'] = 'service'
            if 'confidence' not in result:
                result['confidence'] = 0.8
            if 'features' not in result:
                result['features'] = {}
            if 'complexity' not in result:
                result['complexity'] = 'medium'
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"⚠️  LLM classification failed, using fallback: {e}")
            return self._fallback_classify(code)
    
    def _build_classification_prompt(self, code: str) -> str:
        """Build classification prompt for LLM"""
        # Truncate code if too long (keep first 3000 chars for classification)
        code_sample = code[:3000] + ("..." if len(code) > 3000 else "")
        
        return f"""Classify this AngularJS code and identify its type and features.

CODE:
{code_sample}

CLASSIFICATION TYPES:
- service: .service(), .factory(), $resource-based APIs
- controller: .controller(), uses $scope
- directive: .directive(), DDO with link/compile functions
- filter: .filter(), data transformation pipes
- router: ui-router, $stateProvider, routing config
- module: angular.module() definitions

FEATURES TO DETECT:
- uses_resource: Uses $resource service
- uses_http: Uses $http service
- uses_scope: Uses $scope
- uses_rootscope: Uses $rootScope
- uses_q_promises: Uses $q promises
- uses_timeout: Uses $timeout
- uses_interval: Uses $interval
- has_watchers: Has $watch listeners
- has_broadcasts: Uses $broadcast or $emit
- has_ui_router: Uses ui-router or $state
- has_filters: Uses Angular filters (| syntax)
- has_directives: Uses ng-* directives

COMPLEXITY:
- low: < 50 lines, simple logic
- medium: 50-200 lines, moderate dependencies
- high: > 200 lines, many dependencies

Analyze and return the JSON classification."""
    
    def _fallback_classify(self, code: str) -> Dict:
        """Fallback classification using simple heuristics if LLM fails"""
        import re
        
        # Simple pattern detection as fallback
        primary_type = 'service'
        if '.controller(' in code or '$scope' in code:
            primary_type = 'controller'
        elif '.directive(' in code:
            primary_type = 'directive'
        elif '.filter(' in code:
            primary_type = 'filter'
        elif '$stateProvider' in code or 'ui-router' in code:
            primary_type = 'router'
        
        lines = len(code.split('\n'))
        complexity = 'low' if lines < 50 else 'medium' if lines < 200 else 'high'
        
        return {
            'primary_type': primary_type,
            'detected_types': [primary_type],
            'confidence': 0.6,
            'features': {
                'uses_resource': '$resource' in code,
                'uses_http': '$http' in code,
                'uses_scope': '$scope' in code,
                'uses_rootscope': '$rootScope' in code,
                'uses_q_promises': '$q.' in code,
                'uses_timeout': '$timeout' in code,
                'uses_interval': '$interval' in code,
                'has_watchers': '$watch(' in code,
                'has_broadcasts': '$broadcast' in code or '$emit' in code,
                'has_ui_router': 'ui-router' in code or '$state' in code,
                'has_filters': bool(re.search(r'\|\s*\w+', code)),
                'has_directives': bool(re.search(r'ng-\w+', code)),
            },
            'complexity': complexity,
            'reasoning': 'Fallback classification (LLM failed)'
        }
    
    def get_migration_strategy(self, classification: Dict) -> str:
        """Get recommended migration strategy based on classification"""
        primary_type = classification['primary_type']
        features = classification['features']
        
        if primary_type == 'service':
            if features.get('uses_resource'):
                return 'service_with_httpclient'
            elif features.get('uses_http'):
                return 'service_with_httpclient'
            else:
                return 'service_basic'
        
        elif primary_type == 'controller':
            if features.get('uses_scope') and features.get('has_watchers'):
                return 'component_with_signals'
            else:
                return 'component_basic'
        
        elif primary_type == 'directive':
            return 'directive_or_component'
        
        elif primary_type == 'filter':
            return 'pipe'
        
        elif primary_type == 'router':
            return 'angular_router'
        
        return 'generic'