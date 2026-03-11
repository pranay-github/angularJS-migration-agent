# src/prompt_templates.py
import json
from typing import Dict, List

VERSION = "2.0.0"
MAX_TOKEN_ESTIMATE = 4000

COMMON_ANGULAR_MIGRATION_RULES = """
Convert to Angular 16+ using:
- Standalone Components (no NgModules)
- Modern Angular syntax and lifecycle hooks
- HttpClient for HTTP requests
- RxJS Observables for async operations
- Proper TypeScript types with strict mode
- Signals for reactive state (Angular 16+)
"""

COMMON_OUTPUT_FORMAT = """
Return ONLY the migrated code.
Do NOT include:
- Explanations or commentary
- Markdown code fences
- File paths or headers
"""

COMMON_VALIDATION_INSTRUCTIONS = """
Ensure the migrated code:
✓ Compiles without TypeScript errors
✓ Uses correct import paths
✓ Has proper type annotations
✓ Follows Angular style guide
✓ Has no deprecated APIs
"""

JSON_OUTPUT_ONLY = "Return ONLY valid JSON, no explanations or text."

ERROR_HANDLING_GUIDANCE = """
If you encounter unclear code:
- Make reasonable assumptions based on AngularJS best practices
- Add TODO comments for ambiguous sections
- Prefer compilation-safe code over perfect semantics
"""

def _estimate_token_count(text: str) -> int:
    return len(text.split())

def _validate_prompt_length(prompt: str, max_tokens: int = MAX_TOKEN_ESTIMATE) -> str:
    estimated = _estimate_token_count(prompt)
    if estimated > max_tokens:
        print(f"⚠️  Warning: Prompt may exceed token limit (~{estimated} tokens > {max_tokens})")
    return prompt

def pairs_prompt(controllers_info: List[Dict], templates_info: List[Dict]) -> str:
    prompt = f"""[Migration Assistant v{VERSION}] Analyze AngularJS controller-template pairs.

CONTROLLERS:
{json.dumps(controllers_info, indent=2)}

TEMPLATES:
{json.dumps(templates_info, indent=2)}

TASK:
Match each controller with its corresponding template based on:
1. templateUrl declarations in controller code
2. Controller names matching template filenames (e.g., userController.js → user.html)
3. Code structure and content relationships
4. AngularJS naming conventions (camelCase controllers, kebab-case templates)

EXAMPLE:
Input: controller: "userProfileController.js", template: "user-profile.html"
Output: {{ "userProfileController.js": "user-profile.html" }}

Return format: JSON object mapping controller filenames to template filenames.
If a controller has no matching template, omit it from the result.

{JSON_OUTPUT_ONLY}"""
    return _validate_prompt_length(prompt)

def pairs_prompt_system() -> str:
    return f"""[v{VERSION}] You are an expert AngularJS code analyzer.
Analyze controller and template files to determine which belong together.
Look for templateUrl, naming patterns, and code structure.
{JSON_OUTPUT_ONLY}"""

def dependencies_prompt(files_info: List[Dict]) -> str:
    prompt = f"""[Migration Assistant v{VERSION}] Analyze TypeScript/JavaScript file dependencies.

FILES TO ANALYZE:
{json.dumps(files_info, indent=2)}

TASK:
For each file, identify which OTHER files it depends on by analyzing:
1. Import statements: import {{ X }} from './path'
2. Require statements: require('./path')
3. Type imports: import type {{ Type }} from './path'
4. Referenced classes, interfaces, or types from other files
5. Base classes being extended
6. Services being injected
7. Shared utilities or helpers

EXAMPLE:
If user.service.ts imports {{ BaseService }} from './base.service.ts':
{{"user.service.ts": ["base.service.ts"]}}

Rules:
- Only include files from the provided list (ignore node_modules)
- If a file has no dependencies, map it to an empty array: {{"standalone.ts": []}}
- Use exact filenames as they appear in the list

{JSON_OUTPUT_ONLY}"""
    return _validate_prompt_length(prompt)

def dependencies_prompt_system() -> str:
    return f"""[v{VERSION}] You are an expert TypeScript/JavaScript code analyzer.
Analyze import statements, type dependencies, and code relationships.
Identify both explicit (import/require) and implicit (extends, implements) dependencies.
{JSON_OUTPUT_ONLY}"""

def import_update_prompt(current_file: str, output_location: str, code_preview: str, migration_info: List[Dict]) -> str:
    prompt = f"""[Migration Assistant v{VERSION}] Update import statements for migrated files.

CURRENT FILE: {current_file}
CURRENT OUTPUT LOCATION: {output_location}

CODE:
{code_preview}

MIGRATION MAP (old filename → new filename):
{json.dumps(migration_info, indent=2)}

TASK:
1. Find all import statements in the code
2. If an import points to a file that was migrated, update the path
3. Update both the relative path AND the filename if it changed
4. Preserve import structure (named imports, default imports, type imports)
5. Ensure paths remain relative and use './' or '../' notation

EXAMPLE:
Old: import {{ UserService }} from '../services/user.js'
If user.js → user.service.ts and location changed:
New: import {{ UserService }} from '../../services/user.service'

{ERROR_HANDLING_GUIDANCE}

{COMMON_OUTPUT_FORMAT}"""
    return _validate_prompt_length(prompt)

def import_update_prompt_system() -> str:
    return f"""[v{VERSION}] You are an expert at refactoring TypeScript import statements.
Update import paths while preserving code structure and functionality.
Ensure all relative paths are correct based on file locations.
{COMMON_OUTPUT_FORMAT}"""

ANGULARJS_TO_ANGULAR_SYNTAX = """
Convert AngularJS syntax to Angular:
  ng-repeat       → *ngFor="let item of items; trackBy: trackByFn"
  ng-if           → *ngIf="condition"
  ng-show/ng-hide → *ngIf or [hidden]
  ng-click        → (click)="method()"
  ng-model        → [(ngModel)]
  ng-class        → [ngClass]="{'class': condition}"
  ng-bind         → {{ interpolation }}
  {{ vm.prop }}   → {{ prop }}
  {{ ctrl.method() }} → {{ method() }}
"""

def template_with_component_prompt(component_preview: str, template_code: str, features: Dict) -> str:
    prompt = f"""[Migration Assistant v{VERSION}] Migrate AngularJS template WITH semantic validation.

PAIRED COMPONENT CODE (TypeScript):
{component_preview[:1500]}...
[Component code truncated for brevity - use this as reference for available properties/methods]

TEMPLATE CODE TO MIGRATE (HTML):
{template_code}

TASK - CONTEXT-AWARE MIGRATION:

Step 1: Analyze Component Structure
Extract from the component class:
  - Public properties (fields, getters)
  - Public methods (functions)
  - @Input() and @Output() decorators
  - Constructor-injected services
  - Component metadata

Step 2: Migrate Template with Validation
Ensure ALL bindings are valid:
  ✓ {{{{ interpolations }}}} must reference actual component properties
  ✓ (event)="method()" must call existing component methods
  ✓ [property]="value" must bind to existing component properties
  ✓ *ngFor, *ngIf must use existing data

Step 3: Remove or Fix Invalid Bindings
  - Remove bindings to non-existent properties/methods
  - Update 'vm.property' → 'property' based on actual component structure
  - Update 'ctrl.method()' → 'method()' based on actual methods
  - Fix method signatures (parameters must match component)

Step 4: Convert Syntax
{ANGULARJS_TO_ANGULAR_SYNTAX}

Step 5: Optimize
  - Add trackBy for *ngFor loops: trackBy: trackById
  - Use OnPush change detection where applicable
  - Preserve HTML structure and CSS classes

EXAMPLE MIGRATION:
AngularJS:
  <div ng-repeat="user in vm.users" ng-click="vm.selectUser(user)">
    {{{{ vm.user.name }}}}
  </div>

Angular (if component has 'users' property and 'selectUser' method):
  <div *ngFor="let user of users; trackBy: trackById" (click)="selectUser(user)">
    {{{{ user.name }}}}
  </div>

{ERROR_HANDLING_GUIDANCE}

IMPORTANT:
- Only use bindings that exist in the component
- If a binding doesn't exist, either remove it or add TODO comment
- Preserve HTML structure and styling

{COMMON_OUTPUT_FORMAT}"""
    return _validate_prompt_length(prompt, max_tokens=6000)

def validate_template_prompt(component_preview: str, html_preview: str) -> str:
    prompt = f"""[Migration Assistant v{VERSION}] Validate Angular template against component class.

COMPONENT CLASS:
{component_preview[:1000]}...

TEMPLATE:
{html_preview[:1500]}...

TASK:
Analyze if template bindings are valid by checking:
1. Do all {{{{ interpolations }}}} reference existing component properties?
2. Do all (event)="method()" calls reference existing component methods?
3. Do all [property]="value" bindings use existing component properties?
4. Are method signatures correct (parameters match)?
5. Are there any orphaned bindings (references to non-existent members)?

Return JSON with detailed validation:
{{
  "valid": true,
  "score": 85,
  "valid_bindings": ["userName", "loadUsers()", "isActive"],
  "invalid_bindings": [
    {{"binding": "nonExistentProp", "type": "property", "line_hint": "in interpolation"}},
    {{"binding": "missingMethod()", "type": "method", "line_hint": "in click event"}}
  ],
  "warnings": ["Property 'userName' exists but may be undefined at init"],
  "suggestions": ["Add trackBy to *ngFor", "Consider using OnPush change detection"]
}}

{JSON_OUTPUT_ONLY}"""
    return _validate_prompt_length(prompt)

def simplified_migration_prompt(pattern_type: str, code: str) -> str:
    prompt = f"""[Migration Assistant v{VERSION}] Migrate AngularJS {pattern_type} to Angular 16+.

SOURCE CODE (truncated):
{code[:2000]}...

{COMMON_ANGULAR_MIGRATION_RULES}

{COMMON_VALIDATION_INSTRUCTIONS}

{ERROR_HANDLING_GUIDANCE}

{COMMON_OUTPUT_FORMAT}"""
    return _validate_prompt_length(prompt)

def insights_prompt(migration_summary: Dict, validation_issues: List[Dict], failed_migrations: List[Dict], angular_modules: List[str], external_deps: List[str]) -> str:
    prompt = f"""[Migration Assistant v{VERSION}] Analyze AngularJS → Angular 16+ migration results.

MIGRATION SUMMARY:
{json.dumps(migration_summary, indent=2)}

VALIDATION ISSUES ({len(validation_issues)} files, showing first 10):
{json.dumps(validation_issues[:10], indent=2)}

FAILED MIGRATIONS ({len(failed_migrations)} files, showing first 5):
{json.dumps(failed_migrations[:5], indent=2)}

EXTERNAL DEPENDENCIES DETECTED:
Angular Modules: {', '.join(sorted(angular_modules)) or 'None'}
Third-party: {', '.join(sorted(external_deps)) or 'None'}

TASK:
As an expert Angular migration consultant, analyze this migration and provide actionable recommendations.

1. **Root Cause Analysis**: What are the main issues causing failures or low validation scores?

2. **Migration Priority**: Which files should be re-migrated first and why? 
   List custom attributes or directives which should be migrated in templates.

3. **Dependency Recommendations**: 
   - Which dependencies need to be installed/updated before re-running migration?
   - Are there missing Angular packages?
   - Are there incompatible third-party libraries?

4. **Code Quality Improvements**: What patterns or anti-patterns did you notice?

5. **Next Steps**: Concrete action items ranked by priority (max 5 steps)

6. **Risk Assessment**: What are the biggest risks or blockers?

EXAMPLE OUTPUT:
{{
  "overall_assessment": "70% success rate, main issues: missing services, invalid template bindings",
  "root_causes": [
    "Missing HttpClient imports in 15 service files",
    "Template bindings reference non-existent component properties"
  ],
  "migration_priority": [
    {{"file": "user.service.ts", "reason": "Core service used by 10+ components", "priority": "HIGH"}}
  ],
  "dependency_recommendations": {{
    "install_first": ["@angular/common@16", "@angular/forms@16"],
    "update_required": ["rxjs to v7+"],
    "incompatible": ["angular-ui-router - use @angular/router"]
  }},
  "code_quality_issues": ["Inconsistent naming conventions", "Missing error handling"],
  "next_steps": [
    {{"step": 1, "action": "Install missing @angular/common HttpClient", "reason": "Blocks 15 service files"}}
  ],
  "risks": [
    {{"risk": "Custom directives not migrated", "severity": "HIGH", "mitigation": "Create Angular directive equivalents"}}
  ]
}}

{JSON_OUTPUT_ONLY}"""
    return _validate_prompt_length(prompt, max_tokens=6000)

def attribute_suggestion_prompt(attribute_name: str, example_snippet: str = None) -> str:
    prompt = f"""[Migration Assistant v{VERSION}] Analyze custom AngularJS attribute directive.

CUSTOM ATTRIBUTE: {attribute_name}

{"EXAMPLE USAGE:\n" + example_snippet[:800] + "..." if example_snippet else ""}

TASK:
Provide a concise migration strategy for this custom attribute directive.

Answer these questions:
1. **Intent/Behavior**: Classify as [Styling | Structural | Behavioral] with 1-sentence rationale
2. **Migration Approach**: Choose [Attribute Directive | Structural Directive | Component Wrapper | CSS-only] and explain why
3. **Implementation**: Provide minimal Angular directive skeleton (≤20 lines TypeScript)
4. **Detection Hints**: Search tokens, likely file locations, or directive names to find existing implementation

EXAMPLE OUTPUT:
Intent: Behavioral - likely adds click tracking or analytics
Approach: Attribute Directive - simple DOM behavior modification
Implementation:
```typescript
@Directive({{ selector: '[appTrackClick]', standalone: true }})
export class TrackClickDirective {{
  @HostListener('click', ['$event'])
  onClick(event: MouseEvent) {{
    // Track click analytics
  }}
}}
```
Detection: Search for "directive('{attribute_name}'" in .js files

Keep response concise (3-6 lines + code snippet).
{COMMON_OUTPUT_FORMAT}"""
    return _validate_prompt_length(prompt)