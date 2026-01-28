# src/prompt_templates.py
import json
from typing import Dict, List

def pairs_prompt(controllers_info: List[Dict], templates_info: List[Dict]) -> str:
    return f"""Analyze these AngularJS controllers and templates to determine which pairs belong together.

CONTROLLERS:
{json.dumps(controllers_info, indent=2)}

TEMPLATES:
{json.dumps(templates_info, indent=2)}

TASK:
Match each controller with its corresponding template based on:
1. templateUrl declarations in controller code
2. Controller names and template filenames
3. Code structure and content relationships
4. AngularJS naming conventions

Return ONLY a JSON object mapping controller filenames to template filenames:
{{ "controller1.js": "template1.html" }}

If a controller has no matching template, omit it from the result.
Return ONLY the JSON object, no explanations."""

def pairs_prompt_system() -> str:
    return """You are an expert AngularJS code analyzer.
Analyze controller and template files to determine which belong together.
Look for templateUrl, naming patterns, and code structure.
Return ONLY valid JSON mapping controller filenames to template filenames."""

def dependencies_prompt(files_info: List[Dict]) -> str:
    return f"""Analyze these TypeScript/JavaScript files and identify their dependencies.

FILES TO ANALYZE:
{json.dumps(files_info, indent=2)}

TASK:
For each file, identify which OTHER files it depends on by analyzing:
1. Import statements (import ... from './path')
2. Require statements (require('./path'))
3. Type imports (import type {{ Type }} from './path')
4. Referenced classes, interfaces, or types from other files
5. Base classes being extended
6. Services being injected
7. Shared utilities or helpers

Return a JSON object mapping each filename to an array of filenames it depends on.
Rules:
- Only include files from the provided list (no external node_modules)
- If a file has no dependencies, map it to an empty array
Return ONLY the JSON object, no explanations."""

def dependencies_prompt_system() -> str:
    return """You are an expert TypeScript/JavaScript code analyzer.
Analyze import statements, type dependencies, and code relationships.
Identify both explicit (import/require) and implicit (extends, implements) dependencies.
Return ONLY valid JSON mapping filenames to their dependency arrays."""

def import_update_prompt(current_file: str, output_location: str, code_preview: str, migration_info: List[Dict]) -> str:
    return f"""Update import statements in this TypeScript file to point to migrated files.

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
4. Preserve import structure (named imports, default imports, etc.)
5. Ensure paths remain relative and use './' or '../' notation

Return the COMPLETE updated code with corrected import paths.
Return ONLY the code, no explanations."""

def import_update_prompt_system() -> str:
    return """You are an expert at refactoring TypeScript import statements.
Update import paths while preserving code structure and functionality.
Ensure all relative paths are correct based on file locations.
Return ONLY the updated code."""

def template_with_component_prompt(component_preview: str, template_code: str, features: Dict) -> str:
    return f"""Migrate this AngularJS template to Angular 16+ WITH SEMANTIC VALIDATION against its paired component.

PAIRED COMPONENT CODE (TypeScript):
{component_preview}

TEMPLATE CODE TO MIGRATE (HTML):
{template_code}

TASK - CONTEXT-AWARE MIGRATION:
1. Analyze the component class to extract:
   - Available properties (public fields, getters)
   - Available methods (public functions)
   - @Input() and @Output() decorators
   - Constructor-injected services
   - Component metadata

2. Migrate the template ensuring ALL bindings are valid:
   - {{{{ interpolations }}}} must reference actual component properties
   - (event)="method()" must call existing component methods
   - [property]="value" must bind to existing component properties
   - *ngFor, *ngIf, etc. must use existing data
   
3. Remove or fix invalid bindings:
   - Remove bindings to non-existent properties/methods
   - Update 'vm.property' → 'property' based on actual component structure
   - Update 'ctrl.method()' → 'method()' based on actual methods
   - Fix method signatures (parameters must match component)

4. Convert AngularJS syntax to Angular:
   - ng-repeat → *ngFor
   - ng-if → *ngIf
   - ng-click → (click)
   - ng-model → [(ngModel)]
   - ng-show/ng-hide → *ngIf or [hidden]
   - ng-class → [ngClass] or [class.xxx]

5. Add trackBy for *ngFor loops if possible

IMPORTANT:
- Only use bindings that exist in the component
- Preserve HTML structure and styling
- Return ONLY the migrated HTML template
- Do NOT add explanations or comments

Return the complete migrated Angular template."""

def validate_template_prompt(component_preview: str, html_preview: str) -> str:
    return f"""Validate this Angular template against its paired component class.

COMPONENT CLASS:
{component_preview}

TEMPLATE:
{html_preview}

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

Return ONLY the JSON object."""

def simplified_migration_prompt(pattern_type: str, code: str) -> str:
    return f"""Migrate this AngularJS {pattern_type} to Angular 16+.

SOURCE CODE (truncated):
{code}

Convert to Angular 16+ with:
- Standalone components (if component)
- Modern Angular syntax
- HttpClient (if service)
- RxJS Observables
- Proper TypeScript types

Return ONLY the migrated code."""

def insights_prompt(migration_summary: Dict, validation_issues: List[Dict], failed_migrations: List[Dict], angular_modules: List[str], external_deps: List[str]) -> str:
    return f"""Analyze this AngularJS to Angular 16+ migration and provide intelligent, actionable recommendations.

MIGRATION SUMMARY:
{json.dumps(migration_summary, indent=2)}

VALIDATION ISSUES ({len(validation_issues)} files):
{json.dumps(validation_issues[:10], indent=2)}

FAILED MIGRATIONS ({len(failed_migrations)} files):
{json.dumps(failed_migrations[:5], indent=2)}

EXTERNAL DEPENDENCIES DETECTED:
Angular Modules: {', '.join(sorted(angular_modules))}
Third-party: {', '.join(sorted(external_deps))}

TASK:
As an expert Angular migration consultant, analyze this migration and provide:

1. **Root Cause Analysis**: What are the main issues causing failures or low validation scores?

2. **Migration Priority**: Which files should be re-migrated first and why? 
List down custom attributes or directives which should be migrated in template?

3. **Dependency Recommendations**: 
   - Which dependencies need to be updated before re-running migration?
   - Are there missing Angular packages?
   - Are there incompatible third-party libraries?

4. **Code Quality Improvements**: What patterns or anti-patterns did you notice?

5. **Next Steps**: Concrete action items ranked by priority

6. **Risk Assessment**: What are the biggest risks or blockers?

Return JSON format:
{{
  "overall_assessment": "brief summary",
  "root_causes": ["cause 1", "cause 2"],
  "migration_priority": [
    {{"file": "filename", "reason": "why migrate first", "priority": "HIGH|MEDIUM|LOW"}}
  ],
  "dependency_recommendations": {{
    "install_first": ["package1", "package2"],
    "update_required": ["package3 to v16+"],
    "incompatible": ["package4 - use alternative X"]
  }},
  "code_quality_issues": ["issue 1", "issue 2"],
  "next_steps": [
    {{"step": 1, "action": "description", "reason": "why important"}}
  ],
  "risks": [
    {{"risk": "description", "severity": "HIGH|MEDIUM|LOW", "mitigation": "how to address"}}
  ]
}}

Return ONLY the JSON object."""

def attribute_suggestion_prompt(attribute_name: str, example_snippet: str = None) -> str:
    prompt = f"""The template uses a custom attribute/attribute-directive `{attribute_name}`.
Describe succinctly:
- Likely intent/behavior: classify as one of [Styling | Structural | Behavioral] and give 1-sentence rationale.
- Recommended migration approach: choose one of [Attribute Directive | Structural Directive/Component Wrapper | CSS-only] and explain why.
- Provide a minimal Angular attribute directive skeleton (TypeScript) for the recommended approach (≤20 lines).
- Provide quick detection hints (search tokens, likely file locations or directive names) that would help locate an existing implementation in the repo.

Return a short plain-text recommendation (3–6 lines) followed by a fenced TypeScript snippet if applicable. Do NOT include long explanations."""
    if example_snippet:
        prompt += f"\n\nExample snippet:\n{example_snippet[:800]}"
    return prompt