"""
AngularJS to Angular 16+ Migration Engine
Pattern-Based Architecture (No MCP)
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
from config import DEFAULT_MODEL, DEFAULT_FILE_EXTENSIONS;

sys.path.insert(0, str(Path(__file__).parent))

from connectivity import ChatCopilot, get_copilot_token_via_internal_endpoint
from langchain_core.messages import HumanMessage, SystemMessage
from classifier import FileClassifier
from pattern_registry import PatternRegistry
from validator import CodeValidator


class MigrationEngine:
    """Main migration engine coordinating all components"""
    
    def __init__(self, model: str = DEFAULT_MODEL):
        print("🚀 Initializing Migration Engine")
        print("=" * 70)
        
        self.registry = PatternRegistry()
        self.validator = CodeValidator()
        
        print("🔑 Acquiring GitHub Copilot token...")
        token = get_copilot_token_via_internal_endpoint()
        if not token:
            raise RuntimeError("Failed to get Copilot token. Set GITHUB_TOKEN.")
        
        print(f"🤖 Initializing {model}...")
        self.llm = ChatCopilot(token=token, model=model)
        self.classifier = FileClassifier(llm=self.llm)

        self.model = model
        
        # Track component-template relationships
        self.component_template_map = {}
        
        print("✅ Engine Ready")
        print("=" * 70)
        print()
    
    def migrate_directory(self, input_dir: str, output_dir: str = None, 
                         file_extensions: List[str] = ['.js', '.html'], 
                         validate: bool = True,
                         pair_templates: bool = True) -> Dict:
        """
        Migrate all AngularJS files in a directory to Angular 16+
        
        Args:
            input_dir: Directory containing AngularJS files
            output_dir: Directory for migrated files (default: input_dir/../output)
            file_extensions: List of file extensions to process (default: ['.js', '.html'])
            validate: Whether to validate migrated code
            pair_templates: Whether to pair controllers with templates using LLM
            
        Returns:
            Dictionary with migration results for all files
        """
        input_path = Path(input_dir)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
        if not input_path.is_dir():
            raise NotADirectoryError(f"Input path is not a directory: {input_dir}")
        
        # Set output directory
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = input_path.parent / "output"
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        print("┌─────────────────────────────────────────────────────────────────┐")
        print("│           BATCH MIGRATION - DIRECTORY PROCESSING                │")
        print("└─────────────────────────────────────────────────────────────────┘")
        print()
        print(f"📁 Input Directory:  {input_path}")
        print(f"📁 Output Directory: {output_path}")
        print(f"📄 File Extensions:  {', '.join(file_extensions)}")
        print(f"🔗 Template Pairing: {'Enabled (LLM-based)' if pair_templates else 'Disabled'}")
        print()
        
        # Scan for files
        print("🔍 Scanning for files...")
        files_to_migrate = []
        for ext in file_extensions:
            found_files = list(input_path.rglob(f"*{ext}"))
            files_to_migrate.extend(found_files)
        
        if not files_to_migrate:
            print("❌ No files found to migrate!")
            return {
                'total_files': 0,
                'successful': 0,
                'failed': 0,
                'results': []
            }
        
        print(f"   Found {len(files_to_migrate)} file(s) to migrate")
        print()
        
        # Categorize files by type for optimal processing order
        print("📋 Categorizing files...")
        categorized = self._categorize_files(files_to_migrate)
        
        print(f"   Services:    {len(categorized['services'])}")
        print(f"   Controllers: {len(categorized['controllers'])}")
        print(f"   Directives:  {len(categorized['directives'])}")
        print(f"   Filters:     {len(categorized['filters'])}")
        print(f"   Templates:   {len(categorized['templates'])}")
        print(f"   Other:       {len(categorized['other'])}")
        print()
        
        # Step 5: Detect component-template pairs using LLM
        pairs_map = {}
        if pair_templates and categorized['controllers'] and categorized['templates']:
            print("🔗 Using LLM to detect component-template pairs...")
            pairs_map = self._detect_pairs_with_llm(
                categorized['controllers'],
                categorized['templates']
            )
            if pairs_map:
                print(f"   Found {len(pairs_map)} controller-template pair(s)")
                for ctrl_file, tmpl_file in pairs_map.items():
                    print(f"   • {ctrl_file.name} ↔ {tmpl_file.name}")
            else:
                print("   No pairs detected")
            print()
        
        # Process files in order: services → controllers → directives → filters → templates → other
        processing_order = [
            ('services', categorized['services']),
            ('controllers', categorized['controllers']),
            ('directives', categorized['directives']),
            ('filters', categorized['filters']),
            ('templates', categorized['templates']),
            ('other', categorized['other'])
        ]
        
        results = []
        successful = 0
        failed = 0
        
        print("=" * 70)
        print("🚀 STARTING BATCH MIGRATION")
        print("=" * 70)
        print()
        
        for category, files in processing_order:
            if not files:
                continue
            
            print(f"📦 Processing {category.upper()}...")
            print("-" * 70)
            
            for i, file_path in enumerate(files, 1):
                print(f"\n[{i}/{len(files)}] {file_path.name}")
                print("-" * 70)
                
                try:
                    # Find paired template if this is a controller
                    paired_template = None
                    if category == 'controllers' and pair_templates:
                        paired_template = pairs_map.get(file_path)
                        if paired_template:
                            print(f"🔗 Paired with template: {paired_template.name}")
                    
                    # Migrate the file
                    result = self.migrate_file(
                        input_file=str(file_path),
                        output_file=None,
                        validate=validate,
                        paired_template_path=paired_template
                    )
                    
                    results.append({
                        'file': str(file_path),
                        'status': 'success',
                        'result': result,
                        'paired_template': str(paired_template) if paired_template else None
                    })
                    successful += 1
                    
                except Exception as e:
                    print(f"❌ Failed to migrate {file_path.name}: {e}")
                    results.append({
                        'file': str(file_path),
                        'status': 'failed',
                        'error': str(e)
                    })
                    failed += 1
            
            print()
        
        # Final summary
        print()
        print("=" * 70)
        print("📊 BATCH MIGRATION SUMMARY")
        print("=" * 70)
        print(f"Total Files:     {len(files_to_migrate)}")
        print(f"Successful:      {successful} ✅")
        print(f"Failed:          {failed} ❌")
        print(f"Success Rate:    {(successful/len(files_to_migrate)*100):.1f}%")
        print(f"Output Location: {output_path}")
        
        if pair_templates and self.component_template_map:
            print(f"\n🔗 Component-Template Pairs: {len(self.component_template_map)}")
            for comp, tmpl in self.component_template_map.items():
                print(f"   • {Path(comp).name} → {Path(tmpl).name}")
        
        print("=" * 70)
        
        return {
            'total_files': len(files_to_migrate),
            'successful': successful,
            'failed': failed,
            'results': results,
            'output_directory': str(output_path),
            'component_template_pairs': self.component_template_map
        }
    
    def _detect_pairs_with_llm(self, controllers: List[Path], 
                               templates: List[Path]) -> Dict[Path, Path]:
        """
        Use LLM to intelligently detect which controllers match with which templates
        
        The LLM analyzes:
        - Controller code (looks for templateUrl, component definitions)
        - Controller names and structure
        - Template filenames
        - Template content and structure
        
        Returns:
            Dictionary mapping controller Path to template Path
        """
        if not controllers or not templates:
            return {}
        
        print("   🤖 Analyzing controllers and templates with AI...")
        
        # Prepare data for LLM
        controllers_info = []
        for ctrl in controllers:
            try:
                content = ctrl.read_text(encoding='utf-8')
                # Truncate large files for LLM context
                content_preview = content[:1500] + ("..." if len(content) > 1500 else "")
                controllers_info.append({
                    'filename': ctrl.name,
                    'path': str(ctrl),
                    'content_preview': content_preview
                })
            except Exception as e:
                print(f"   ⚠️  Could not read {ctrl.name}: {e}")
        
        templates_info = []
        for tmpl in templates:
            try:
                content = tmpl.read_text(encoding='utf-8')
                content_preview = content[:1000] + ("..." if len(content) > 1000 else "")
                templates_info.append({
                    'filename': tmpl.name,
                    'path': str(tmpl),
                    'content_preview': content_preview
                })
            except Exception as e:
                print(f"   ⚠️  Could not read {tmpl.name}: {e}")
        
        # Build LLM prompt
        prompt = f"""Analyze these AngularJS controllers and templates to determine which pairs belong together.

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
{{
  "controller1.js": "template1.html",
  "user.controller.js": "user-view.html"
}}

If a controller has no matching template, omit it from the result.
Return ONLY the JSON object, no explanations."""

        system_msg = """You are an expert AngularJS code analyzer.
Analyze controller and template files to determine which belong together.
Look for templateUrl, naming patterns, and code structure.
Return ONLY valid JSON mapping controller filenames to template filenames."""

        try:
            messages = [
                SystemMessage(content=system_msg),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            content = response.content.strip()
            
            # Clean JSON from response
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
            # Parse LLM response
            pairs_dict = json.loads(content)
            
            # Convert filenames back to Path objects
            result = {}
            for ctrl_filename, tmpl_filename in pairs_dict.items():
                # Find the actual Path objects
                ctrl_path = next((c for c in controllers if c.name == ctrl_filename), None)
                tmpl_path = next((t for t in templates if t.name == tmpl_filename), None)
                
                if ctrl_path and tmpl_path:
                    result[ctrl_path] = tmpl_path
                else:
                    print(f"   ⚠️  Could not find paths for: {ctrl_filename} → {tmpl_filename}")
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"   ⚠️  LLM response parsing failed: {e}")
            print(f"   Response: {content[:200]}")
            return {}
        except Exception as e:
            print(f"   ⚠️  LLM pairing failed: {e}")
            return {}
    
    def _categorize_files(self, files: List[Path]) -> Dict[str, List[Path]]:
        """Categorize files by type based on filename and extension"""
        categories = {
            'services': [],
            'controllers': [],
            'directives': [],
            'filters': [],
            'templates': [],
            'other': []
        }
        
        for file_path in files:
            filename = file_path.name.lower()
            extension = file_path.suffix.lower()
            
            # HTML files are templates
            if extension in ['.html', '.htm']:
                categories['templates'].append(file_path)
            
            # Categorize JavaScript AND TypeScript files by naming convention
            elif extension in ['.js', '.ts']:
                if 'service' in filename or 'factory' in filename or 'resource' in filename:
                    categories['services'].append(file_path)
                elif 'controller' in filename or 'ctrl' in filename or 'component' in filename:
                    categories['controllers'].append(file_path)
                elif 'directive' in filename:
                    categories['directives'].append(file_path)
                elif 'filter' in filename or 'pipe' in filename:
                    categories['filters'].append(file_path)
                else:
                    categories['other'].append(file_path)
            else:
                categories['other'].append(file_path)
        
        return categories

    def migrate_file(self, input_file: str, output_file: str = None, validate: bool = True,
                    paired_template_path: Optional[Path] = None) -> Dict:
        """Migrate a single AngularJS file to Angular 16+"""
        input_path = Path(input_file)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        print(f"📄 Processing: {input_path.name}")
        print("-" * 70)
        
        # Step 1: Load legacy code
        print("1️⃣ Loading AngularJS code...")
        legacy_code = input_path.read_text(encoding='utf-8')
        print(f"   Size: {len(legacy_code)} characters")
        
        # Clean code for processing (remove comments, trim whitespace)
        cleaned_code = self._clean_code_for_processing(legacy_code, input_path.suffix.lower())
        print(f"   Cleaned size: {len(cleaned_code)} characters")
        print()
        
        # Detect file extension
        file_extension = input_path.suffix.lower()
        
        # Step 2: Classify file
        print("2️⃣ Classifying file type...")
        classification = self.classifier.classify(cleaned_code, file_extension=file_extension)
        print(f"   Type: {classification['primary_type']}")
        print(f"   Confidence: {classification['confidence']}")
        print(f"   Complexity: {classification['complexity']}")
        print(f"   Features: {', '.join([k for k, v in classification['features'].items() if v])}")
        strategy = self.classifier.get_migration_strategy(classification)
        print(f"   Strategy: {strategy}")
        print()
        
        # Step 3: Build prompt from patterns
        print("3️⃣ Loading migration patterns...")
        
        # Use cleaned code for prompt (limit size for LLM)
        code_for_prompt = cleaned_code
        if len(code_for_prompt) > 10000:
            print(f"   ⚠️  Code too large ({len(code_for_prompt)} chars), truncating to 10000 chars")
            code_for_prompt = code_for_prompt[:10000] + "\n\n... [truncated]"
        
        prompt = self.registry.build_prompt(
            classification['primary_type'],
            code_for_prompt,
            classification['features']
        )
        print(f"   Pattern: {classification['primary_type']}")
        print(f"   Rules: {len(self.registry.get_migration_rules(classification['primary_type']))} rules loaded")
        print()
        
        # Step 4: Run LLM migration
        print(f"4️⃣ Running AI migration ({self.model})...")
        
        # Different system messages for templates vs TypeScript
        if classification['primary_type'] == 'template':
            system_msg = """You are an expert Angular template migration specialist.
    Follow the provided patterns and rules exactly.
    Convert AngularJS template syntax to Angular 16+ template syntax.
    Return ONLY the migrated HTML template code, no explanations.
    Preserve the HTML structure and styling.
    Convert all ng-* directives to Angular equivalents."""
        else:
            system_msg = """You are an expert Angular migration specialist.
    Follow the provided patterns and rules exactly.
    Generate clean, production-ready TypeScript code.
    Use Angular 16+ features: standalone components, HttpClient, RxJS Observables.
    Return ONLY the TypeScript code, no explanations."""
        
        messages = [
            SystemMessage(content=system_msg),
            HumanMessage(content=prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            migrated_code = response.content
        except Exception as e:
            if "422" in str(e):
                print(f"   ⚠️  Request too large, retrying with simplified prompt...")
                # Fallback: use simplified prompt
                simplified_prompt = self._build_simplified_prompt(
                    classification['primary_type'],
                    code_for_prompt[:5000]  # Further reduce
                )
                messages = [
                    SystemMessage(content=system_msg),
                    HumanMessage(content=simplified_prompt)
                ]
                response = self.llm.invoke(messages)
                migrated_code = response.content
            else:
                raise
        
        # Clean code blocks
        if classification['primary_type'] == 'template':
            # For HTML templates, clean HTML code blocks
            if "```html" in migrated_code:
                migrated_code = migrated_code.split("```html")[1].split("```")[0].strip()
            elif "```" in migrated_code:
                migrated_code = migrated_code.split("```")[1].split("```")[0].strip()
        else:
            # For TypeScript files, clean TS code blocks
            if "```typescript" in migrated_code:
                migrated_code = migrated_code.split("```typescript")[1].split("```")[0].strip()
            elif "```ts" in migrated_code:
                migrated_code = migrated_code.split("```ts")[1].split("```")[0].strip()
            elif "```" in migrated_code:
                migrated_code = migrated_code.split("```")[1].split("```")[0].strip()
        
        print(f"   Generated: {len(migrated_code)} characters")
        print()
        
        # Step 5: Validate (only for TypeScript files)
        validation_result = None
        if validate and classification['primary_type'] != 'template':
            print("5️⃣ Validating TypeScript code...")
            validation_result = self.validator.validate(
                migrated_code,
                output_file or input_path.with_suffix('.service.ts').name
            )
            print(f"   Valid: {'✅ Yes' if validation_result['valid'] else '❌ No'}")
            print(f"   Score: {validation_result['score']}/100")
            
            if validation_result['typescript_errors']:
                print(f"   Errors: {len(validation_result['typescript_errors'])}")
            if validation_result['angular_warnings']:
                print(f"   Warnings: {len(validation_result['angular_warnings'])}")
            if validation_result['suggestions']:
                print(f"   Suggestions: {len(validation_result['suggestions'])}")
            print()
        elif classification['primary_type'] == 'template':
            print("5️⃣ Validating HTML template...")
            validation_result = self._validate_template(migrated_code, classification['features'])
            print(f"   Valid: {'✅ Yes' if validation_result['valid'] else '⚠️  With warnings'}")
            print(f"   Score: {validation_result['score']}/100")
            if validation_result['warnings']:
                print(f"   Warnings: {len(validation_result['warnings'])}")
            print()
        
        # Step 6: Save output
        if output_file:
            output_path = Path(output_file)
        else:
            output_dir = input_path.parent.parent / "output"
            output_dir.mkdir(exist_ok=True)
            
            output_name = input_path.stem
            
            # Determine output extension based on type
            if classification['primary_type'] == 'template':
                output_name += '.component.html'
            elif classification['primary_type'] == 'service':
                output_name += '.service.ts'
            elif classification['primary_type'] == 'controller':
                output_name += '.component.ts'
                
                # If controller has paired template, update component decorator
                if paired_template_path:
                    template_output_name = f"{input_path.stem}.component.html"
                    migrated_code = self._update_component_template_url(
                        migrated_code, 
                        template_output_name
                    )
                    # Track the relationship
                    self.component_template_map[str(output_dir / output_name)] = str(output_dir / template_output_name)
                    print(f"🔗 Updated templateUrl to: ./{template_output_name}")
                    
            elif classification['primary_type'] == 'directive':
                output_name += '.directive.ts'
            elif classification['primary_type'] == 'filter':
                output_name += '.pipe.ts'
            else:
                output_name += '.ts'
            
            output_path = output_dir / output_name
        
        print(f"6️⃣ Saving output...")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(migrated_code, encoding='utf-8')
        print(f"   Saved: {output_path}")
        print()
        
        # Summary
        print("=" * 70)
        print("📊 MIGRATION SUMMARY")
        print("=" * 70)
        print(f"Input:       {input_path}")
        print(f"Output:      {output_path}")
        print(f"Type:        {classification['primary_type']}")
        print(f"Strategy:    {strategy}")
        print(f"Complexity:  {classification['complexity']}")
        print(f"Model:       {self.model}")
        
        if validation_result:
            print(f"Valid:       {'✅ Yes' if validation_result['valid'] else '❌ No'}")
            print(f"Score:       {validation_result['score']}/100")
        
        if paired_template_path:
            print(f"Paired With: {paired_template_path.name}")
        
        print("=" * 70)
        
        if validate and validation_result and classification['primary_type'] != 'template':
            print()
            print(self.validator.format_validation_report(validation_result))
        elif classification['primary_type'] == 'template' and validation_result:
            print()
            print(self._format_template_validation(validation_result))
        
        return {
            'input_file': str(input_path),
            'output_file': str(output_path),
            'classification': classification,
            'strategy': strategy,
            'validation': validation_result,
            'migrated_code': migrated_code,
            'paired_template': str(paired_template_path) if paired_template_path else None
        }
    
    def _update_component_template_url(self, component_code: str, template_filename: str) -> str:
        """Update @Component decorator to reference the paired template"""
        # Look for @Component decorator and update templateUrl
        pattern = r'(@Component\s*\(\s*\{[^}]*)(template\s*:\s*[\'"`][^\'"`]*[\'"`])'
        replacement = rf'\1templateUrl: "./{template_filename}"'
        
        updated_code = re.sub(pattern, replacement, component_code, flags=re.DOTALL)
        
        # If no template property found, try to add templateUrl
        if updated_code == component_code:
            pattern = r'(@Component\s*\(\s*\{[^}]*)(standalone\s*:\s*true)'
            replacement = rf'\1\2,\n  templateUrl: "./{template_filename}"'
            updated_code = re.sub(pattern, replacement, component_code, flags=re.DOTALL)
        
        return updated_code
    
    def _validate_template(self, html_code: str, features: Dict) -> Dict:
        """Validate migrated HTML template"""
        import re
        
        warnings = []
        score = 100
        
        # Check for AngularJS directives that weren't migrated
        angularjs_directives = [
            'ng-repeat', 'ng-if', 'ng-show', 'ng-hide', 'ng-click', 'ng-model',
            'ng-class', 'ng-style', 'ng-src', 'ng-href', 'ng-bind', 'ng-submit',
            'ng-disabled', 'ng-readonly', 'ng-checked', 'ng-selected'
        ]
        
        for directive in angularjs_directives:
            if re.search(rf'\b{directive}\b', html_code):
                warnings.append(f"AngularJS directive '{directive}' still present - should be migrated")
                score -= 10
        
        # Check for *ngFor without trackBy
        ngfor_matches = re.findall(r'\*ngFor="[^"]*"', html_code)
        for match in ngfor_matches:
            if 'trackBy' not in match:
                warnings.append("*ngFor without trackBy - consider adding for performance")
                score -= 5
        
        # Check for proper Angular syntax
        if '*ngFor' in html_code and not re.search(r'let\s+\w+\s+of\s+', html_code):
            warnings.append("*ngFor syntax may be incorrect - should use 'let item of items'")
            score -= 10
        
        # Check for double curly braces (should be present for interpolation)
        has_interpolation = '{{' in html_code and '}}' in html_code
        
        # Check for event bindings
        has_event_bindings = bool(re.search(r'\([a-zA-Z]+\)=', html_code))
        
        # Check for property bindings
        has_property_bindings = bool(re.search(r'\[[a-zA-Z]+\]="', html_code))
        
        score = max(0, score)
        
        return {
            'valid': score >= 70,
            'score': score,
            'warnings': warnings,
            'has_interpolation': has_interpolation,
            'has_event_bindings': has_event_bindings,
            'has_property_bindings': has_property_bindings
        }
    
    def _format_template_validation(self, validation: Dict) -> str:
        """Format template validation report"""
        lines = []
        lines.append("📋 TEMPLATE VALIDATION REPORT")
        lines.append("=" * 70)
        
        if validation['warnings']:
            lines.append("\n⚠️  WARNINGS:")
            for i, warning in enumerate(validation['warnings'], 1):
                lines.append(f"  {i}. {warning}")
        
        lines.append("\n✨ FEATURES DETECTED:")
        lines.append(f"  • Interpolation: {'✅' if validation['has_interpolation'] else '❌'}")
        lines.append(f"  • Event Bindings: {'✅' if validation['has_event_bindings'] else '❌'}")
        lines.append(f"  • Property Bindings: {'✅' if validation['has_property_bindings'] else '❌'}")
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)

    def _clean_code_for_processing(self, code: str, file_extension: str) -> str:
        """Clean code by removing comments and excessive whitespace"""
        import re
        
        if file_extension in ['.html', '.htm']:
            # Remove HTML comments (including copyright headers)
            code = re.sub(r'<!--.*?-->', '', code, flags=re.DOTALL)
        elif file_extension in ['.js', '.ts']:
            # Remove multi-line comments
            code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
            # Remove single-line comments
            code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)
        
        # Remove excessive whitespace
        code = re.sub(r'\n\s*\n\s*\n', '\n\n', code)
        code = code.strip()
        
        return code

    def _build_simplified_prompt(self, pattern_type: str, code: str) -> str:
        """Build a simplified prompt for large files"""
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

def main():
    """Main entry point"""
    # Example 1: Single file migration
    # INPUT_FILE = Path(__file__).parent / "legacy-code" / "api.js"
    
    # Example 2: Directory batch migration
    INPUT_DIR = Path(__file__).parent / "legacy-code"
    
    MODEL = DEFAULT_MODEL
    
    print("┌─────────────────────────────────────────────────────────────────┐")
    print("│     AngularJS → Angular 16+ Migration Engine                   │")
    print("│     Pattern-Based Architecture (No MCP)                        │")
    print("└─────────────────────────────────────────────────────────────────┘")
    print()
    
    try:
        engine = MigrationEngine(model=MODEL)
        
        # Uncomment for single file migration:
        # result = engine.migrate_file(input_file=str(INPUT_FILE), validate=True)
        
        # Batch migration of directory with LLM-based template pairing:
        result = engine.migrate_directory(
            input_dir=str(INPUT_DIR),
            file_extensions=['.js', '.html', '.ts'],
            validate=True,
            pair_templates=True  # Enable LLM-based component-template pairing
        )
        
        print()
        print("✨ Migration completed successfully!")
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()