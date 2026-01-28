"""
Validator - Validates migrated TypeScript code
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, List


class CodeValidator:
    """Validates TypeScript code using tsc and custom checks"""
    
    def __init__(self):
        self.temp_dir = Path(__file__).parent / "temp"
        self.temp_dir.mkdir(exist_ok=True)
    
    def validate(self, code: str, filename: str = "temp.ts") -> Dict:
        """
        Validate TypeScript code
        
        Returns:
            {
                'valid': True/False,
                'typescript_errors': [],
                'angular_warnings': [],
                'suggestions': []
            }
        """
        result = {
            'valid': True,
            'typescript_errors': [],
            'angular_warnings': [],
            'suggestions': [],
            'score': 100
        }
        
        # 1. TypeScript compilation check
        ts_result = self._check_typescript(code, filename)
        if not ts_result['valid']:
            result['valid'] = False
            result['typescript_errors'] = ts_result['errors']
            result['score'] -= len(ts_result['errors']) * 10
        
        # 2. Angular pattern checks
        angular_result = self._check_angular_patterns(code)
        result['angular_warnings'] = angular_result['warnings']
        result['score'] -= len(angular_result['warnings']) * 5
        
        # 3. Code quality checks
        quality_result = self._check_code_quality(code)
        result['suggestions'] = quality_result['suggestions']
        result['score'] -= len(quality_result['suggestions']) * 3
        
        # Ensure score is not negative
        result['score'] = max(0, result['score'])
        
        return result
    
    def _check_typescript(self, code: str, filename: str) -> Dict:
        """Check TypeScript compilation"""
        temp_file = self.temp_dir / filename
        
        try:
            # Write temp file
            temp_file.write_text(code, encoding='utf-8')
            
            # Run TypeScript compiler
            result = subprocess.run(
                ['npx', 'tsc', '--noEmit', '--strict', '--lib', 'es2022,dom', str(temp_file)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {'valid': True, 'errors': []}
            else:
                # Parse errors
                errors = []
                for line in result.stderr.split('\n'):
                    if line.strip() and not line.startswith('node_modules'):
                        errors.append(line.strip())
                
                return {'valid': False, 'errors': errors[:10]}
        
        except FileNotFoundError:
            return {
                'valid': False,
                'errors': [' TypeScript not found. Run: npm install -g typescript']
            }
        except subprocess.TimeoutExpired:
            return {
                'valid': False,
                'errors': ['TypeScript compilation timeout']
            }
        finally:
            # Cleanup
            if temp_file.exists():
                temp_file.unlink()
    
    def _check_angular_patterns(self, code: str) -> Dict:
        """Check Angular-specific patterns"""
        warnings = []
        
        if '@Component' in code and 'standalone' not in code:
            warnings.append("Consider using standalone: true for components")
        
        if '@Injectable' in code and "providedIn: 'root'" not in code:
            warnings.append("Consider using providedIn: 'root' for services")
        
        if 'subscribe(' in code and 'async' not in code:
            warnings.append("Consider using async pipe instead of manual subscription")
        
        if 'Observable' in code and "from 'rxjs'" not in code:
            warnings.append("Missing RxJS imports for Observable")
        
        if 'HttpClient' in code and "'@angular/common/http'" not in code:
            warnings.append("Missing @angular/common/http import")
        
        if 'subscribe(' in code and 'OnDestroy' not in code:
            warnings.append("Implement OnDestroy to unsubscribe from observables")
        
        return {'warnings': warnings}
    
    def _check_code_quality(self, code: str) -> Dict:
        """Check general code quality"""
        suggestions = []
        
        if 'export class' in code:
            class_count = code.count('export class')
            jsdoc_count = code.count('/**')
            if jsdoc_count < class_count:
                suggestions.append("Add JSDoc comments for public classes")
        
        if 'http.' in code and 'catchError' not in code:
            suggestions.append("Add error handling with catchError operator")
        
        if ': any' in code:
            suggestions.append("Replace 'any' types with specific interfaces")
        
        return {'suggestions': suggestions}
    
    def format_validation_report(self, validation_result: Dict) -> str:
        """Format validation result as readable report"""
        lines = ["=" * 70, " VALIDATION REPORT", "=" * 70, ""]
        
        score = validation_result.get('score', 0)
        if score >= 90:
            status = " EXCELLENT"
        elif score >= 70:
            status = "✔️ GOOD"
        elif score >= 50:
            status = " NEEDS IMPROVEMENT"
        else:
            status = " POOR"
        
        lines.append(f"Overall Score: {score}/100 {status}")
        lines.append("")
        
        ts_errors = validation_result.get('typescript_errors', [])
        if ts_errors:
            lines.append(" TypeScript Errors:")
            for error in ts_errors:
                lines.append(f"   {error}")
            lines.append("")
        else:
            lines.append(" TypeScript Compilation: Passed")
            lines.append("")
        
        warnings = validation_result.get('angular_warnings', [])
        if warnings:
            lines.append(" Angular Pattern Warnings:")
            for warning in warnings:
                lines.append(f"   • {warning}")
            lines.append("")
        
        suggestions = validation_result.get('suggestions', [])
        if suggestions:
            lines.append(" Code Quality Suggestions:")
            for suggestion in suggestions:
                lines.append(f"   • {suggestion}")
            lines.append("")
        
        lines.append("=" * 70)
        return "\n".join(lines)