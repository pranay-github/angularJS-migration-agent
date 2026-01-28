"""
AngularJS to Angular 16+ Migration Engine
Pattern-Based Architecture (No MCP)
WITH Context-Aware HTML Template Migration
"""

import sys
import re
import json
import time
import requests
import datetime
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from config import DEFAULT_MODEL, DEFAULT_FILE_EXTENSIONS
from suggestions import generate_suggestions_report
from prompt_templates import pairs_prompt, insights_prompt, pairs_prompt_system, dependencies_prompt, dependencies_prompt_system, import_update_prompt, import_update_prompt_system, template_with_component_prompt, validate_template_prompt, attribute_suggestion_prompt


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
        # Track migration context for dependency awareness
        self.migration_map = {}  # old_path -> new_path
        self.dependency_graph = {}  # file -> list of dependencies
        
        print("✅ Engine Ready")
        print("=" * 70)
        print()

    def _topological_sort(self, files: List[Path], 
                        dependency_map: Dict[Path, List[Path]]) -> List[Path]:
        """Sort files by dependency order using topological sort (dependencies first)"""
        from collections import deque, defaultdict
        
        # Build in-degree map (how many dependencies does each file have)
        in_degree = {f: 0 for f in files}
        graph = defaultdict(list)
        
        for file, deps in dependency_map.items():
            for dep in deps:
                if dep in in_degree:  # Only consider deps that are in our migration set
                    graph[dep].append(file)
                    in_degree[file] += 1
        
        # Start with files that have no dependencies
        queue = deque([f for f in files if in_degree[f] == 0])
        sorted_files = []
        
        while queue:
            current = queue.popleft()
            sorted_files.append(current)
            
            # Process files that depend on current
            for dependent in graph[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)
        
        # Handle circular dependencies or remaining files
        remaining = [f for f in files if f not in sorted_files]
        if remaining:
            print(f"   ⚠️  {len(remaining)} file(s) have circular dependencies, adding at end")
            sorted_files.extend(remaining)
        
        return sorted_files
    
    def migrate_directory(self, input_dir: str, output_dir: str = None, 
                        file_extensions: List[str] = ['.js', '.html'], 
                        validate: bool = True,
                        pair_templates: bool = True,
                        analyze_dependencies: bool = True,
                        fix_imports: bool = True) -> Dict:
        """
        Migrate all AngularJS files in a directory to Angular 16+
        
        Args:
            input_dir: Directory containing AngularJS files
            output_dir: Directory for migrated files (default: input_dir/../output)
            file_extensions: List of file extensions to process (default: ['.js', '.html'])
            validate: Whether to validate migrated code
            pair_templates: Whether to pair controllers with templates using LLM
            analyze_dependencies: Whether to analyze and respect file dependencies
            fix_imports: Whether to automatically fix import paths after migration
            
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
        print(f"🔍 Dependency Analysis: {'Enabled (LLM-based)' if analyze_dependencies else 'Disabled'}")
        print(f"🔄 Import Fixing: {'Enabled' if fix_imports else 'Disabled'}")
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
        
        # Analyze dependencies for code files using LLM
        print("🔍 Analyzing dependencies...")
        all_code_files = (categorized['services'] + categorized['controllers'] + 
                        categorized['directives'] + categorized['filters'] + 
                        categorized['other'])

        dependency_map = {}
        sorted_code_files = all_code_files

        if all_code_files and analyze_dependencies:
            # Use LLM for intelligent dependency analysis
            dependency_map = self._analyze_dependencies_with_llm(all_code_files)
            
            # Show dependency information
            deps_found = sum(1 for deps in dependency_map.values() if deps)
            if deps_found > 0:
                print(f"   ✅ Found {deps_found} file(s) with dependencies")
                for file, deps in dependency_map.items():
                    if deps:
                        print(f"      {file.name} depends on:")
                        for dep in deps:
                            print(f"         └─ {dep.name}")
                
                # Sort by dependency order
                sorted_code_files = self._topological_sort(all_code_files, dependency_map)
                print(f"   🔄 Established migration order ({len(sorted_code_files)} files)")
            else:
                print(f"   ℹ️  No dependencies detected between files")
            print()

        # Store for later use
        self.dependency_graph = dependency_map
        
        # Detect component-template pairs using LLM
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
                    print(f"      {ctrl_file.name} → {tmpl_file.name}")
            else:
                print("   No pairs detected")
            print()
        
        # Build processing order respecting dependencies
        processing_order = []
        
        # Add sorted code files first (respecting dependencies)
        if sorted_code_files:
            processing_order.append(('code (dependency-ordered)', sorted_code_files, None))
        
        # Add templates last with pairs_map for context-aware migration
        if categorized['templates']:
            processing_order.append(('templates', categorized['templates'], pairs_map))
        
        results = []
        successful = 0
        failed = 0
        
        print("=" * 70)
        print("🚀 STARTING BATCH MIGRATION")
        print("=" * 70)
        print()
        
        for category_data in processing_order:
            # Unpack with support for optional pairs_map
            if len(category_data) == 3:
                category, files, category_pairs_map = category_data
            else:
                category, files = category_data[:2]
                category_pairs_map = None
            
            if not files:
                continue
            
            print(f"📦 Processing {category.upper()}...")
            print("-" * 70)
            
            for i, file_path in enumerate(files, 1):
                print(f"\n[{i}/{len(files)}] {file_path.name}")
                print("-" * 70)
                
                try:
                    # Determine output file path
                    rel_path = file_path.relative_to(input_path)
                    output_file = output_path / rel_path
                    
                    # Check if this file is paired with a template
                    paired_template = category_pairs_map.get(file_path) if category_pairs_map else None
                    
                    # If this IS a template, check if it's paired with a component
                    paired_component_code = None
                    if file_path.suffix.lower() in ['.html', '.htm'] and category_pairs_map:
                        # Find controller that pairs with this template
                        for ctrl_file, tmpl_file in category_pairs_map.items():
                            if tmpl_file == file_path:
                                # Load the controller code for context
                                try:
                                    paired_component_code = ctrl_file.read_text(encoding='utf-8')
                                except Exception:
                                    paired_component_code = None
                                break
                    
                    # Migrate with dependency context
                    dependency_context = {
                        'fix_imports': fix_imports,
                        'migration_map': self.migration_map
                    } if fix_imports else None
                    
                    result = self.migrate_file(
                        input_file=str(file_path),
                        output_file=str(output_file),
                        validate=validate,
                        paired_template_path=paired_template,
                        paired_component_code=paired_component_code,
                        dependency_context=dependency_context
                    )
                    
                    # Track migration for import fixing
                    self.migration_map[str(file_path)] = result.get('output_file', str(output_file))
                    
                    # Track component-template pairs
                    if paired_template:
                        self.component_template_map[result.get('output_file', str(output_file))] = str(output_path / paired_template.relative_to(input_path))
                    
                    results.append({
                        'file': str(file_path),
                        'status': 'success',
                        'result': result
                    })
                    successful += 1
                    print("✅ Success")
                    
                except Exception as e:
                    results.append({
                        'file': str(file_path),
                        'status': 'failed',
                        'error': str(e)
                    })
                    failed += 1
                    print(f"❌ Failed: {e}")
            
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
        
        if analyze_dependencies and self.dependency_graph:
            deps_count = sum(1 for deps in self.dependency_graph.values() if deps)
            if deps_count > 0:
                print(f"\n📦 Dependencies Tracked: {deps_count} file(s)")
        
        # Generate LLM-powered insights
        print()
        print("🤖 Generating AI-powered migration analysis...")
        llm_insights = self._generate_llm_insights(
            categorized=categorized,
            dependency_map=dependency_map,
            pairs_map=pairs_map,
            results=results
        )
        
        # Generate suggestions report (including LLM insights)
        print()
        print("📝 Generating comprehensive suggestions report...")
        suggestions_content = generate_suggestions_report(
            self,
            categorized,
            dependency_map,
            pairs_map,
            results,
            output_path,
            llm_insights
        )
        
        suggestions_file = output_path / "suggestions.txt"
        suggestions_file.write_text(suggestions_content, encoding='utf-8')
        print(f"   ✅ Saved: {suggestions_file}")
        
        return {
            'total_files': len(files_to_migrate),
            'successful': successful,
            'failed': failed,
            'results': results,
            'output_directory': str(output_path),
            'suggestions_file': str(suggestions_file),
            'llm_insights': llm_insights,
            'component_template_pairs': self.component_template_map,
            'dependency_graph': {str(k): [str(v) for v in vals] for k, vals in self.dependency_graph.items()}
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
        prompt = pairs_prompt(controllers_info, templates_info)

        system_msg = pairs_prompt_system()

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
                    print(f"   ⚠️  Could not resolve pair: {ctrl_filename} → {tmpl_filename}")
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"   ⚠️  LLM response parsing failed: {e}")
            print(f"   Response: {content[:200]}")
            return {}
        except Exception as e:
            print(f"   ⚠️  LLM pairing failed: {e}")
            return {}
    
    def _analyze_dependencies_with_llm(self, files: List[Path]) -> Dict[Path, List[Path]]:
        """Use LLM to analyze dependencies between files (more accurate than regex)"""
        
        if not files:
            return {}
        
        print("   🤖 Using AI to analyze file dependencies...")
        
        # Prepare file information for LLM
        files_info = []
        for file in files:
            try:
                content = file.read_text(encoding='utf-8')
                # Include more context for LLM (up to 2000 chars)
                content_preview = content[:2000] + ("..." if len(content) > 2000 else "")
                files_info.append({
                    'filename': file.name,
                    'path': str(file.relative_to(file.parent.parent)),
                    'extension': file.suffix,
                    'content': content_preview
                })
            except Exception as e:
                print(f"   ⚠️  Could not read {file.name}: {e}")
        
        # Build LLM prompt
        prompt = dependencies_prompt(files_info)

        system_msg = dependencies_prompt_system()

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
            deps_dict = json.loads(content)
            
            # Convert filenames back to Path objects
            result = {}
            filename_to_path = {f.name: f for f in files}
            
            for filename, dep_filenames in deps_dict.items():
                file_path = filename_to_path.get(filename)
                if file_path:
                    dep_paths = [filename_to_path[df] for df in dep_filenames if df in filename_to_path]
                    result[file_path] = dep_paths
            
            # Ensure all files are in result (even if no deps found by LLM)
            for file in files:
                if file not in result:
                    result[file] = []
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"   ⚠️  LLM response parsing failed: {e}")
            print(f"   Response: {content[:200]}")
            # Fallback to regex-based analysis
            return self._analyze_dependencies_regex_fallback(files)
        except Exception as e:
            print(f"   ⚠️  LLM dependency analysis failed: {e}")
            # Fallback to regex-based analysis
            return self._analyze_dependencies_regex_fallback(files)

    def _update_import_paths_with_llm(self, code: str, current_file_name: str,
                                    input_path: Path, output_path: Path,
                                    migration_map: Dict[str, str]) -> str:
        """Use LLM to intelligently update import paths"""
        
        if not migration_map:
            return code
        
        # Build context about migrated files
        migration_info = []
        for old_path, new_path in migration_map.items():
            migration_info.append({
                'old': str(Path(old_path).name),
                'new': str(Path(new_path).name),
                'old_full': old_path,
                'new_full': new_path
            })
        
        prompt = import_update_prompt(current_file_name, str(output_path), code[:3000], migration_info)

        system_msg = import_update_prompt_system()

        try:
            messages = [
                SystemMessage(content=system_msg),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            updated_code = response.content.strip()
            
            # Clean code blocks
            if '```typescript' in updated_code:
                updated_code = updated_code.split('```typescript')[1].split('```')[0].strip()
            elif '```ts' in updated_code:
                updated_code = updated_code.split('```ts')[1].split('```')[0].strip()
            elif '```' in updated_code:
                updated_code = updated_code.split('```')[1].split('```')[0].strip()
            
            return updated_code
            
        except Exception as e:
            print(f"   ⚠️  LLM import update failed: {e}, using original code")
            return code

    def _analyze_dependencies_regex_fallback(self, files: List[Path]) -> Dict[Path, List[Path]]:
        """Fallback regex-based dependency analysis if LLM fails"""
        
        print("   ⚙️  Falling back to regex-based analysis...")
        dependency_map = {}
        
        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8')
                dependencies = []
                
                # Find ES6 imports
                es6_imports = re.findall(r'import\s+.*?\s+from\s+[\'"](\..+?)[\'"]', content)
                
                # Find CommonJS require
                commonjs_imports = re.findall(r'require\s*\([\'"](\..+?)[\'"]\)', content)
                
                all_imports = es6_imports + commonjs_imports
                
                # Resolve each import
                for imp in all_imports:
                    resolved = self._resolve_import_path(file_path, imp, files)
                    if resolved:
                        dependencies.append(resolved)
                
                dependency_map[file_path] = list(set(dependencies))
                
            except Exception as e:
                dependency_map[file_path] = []
        
        return dependency_map

    def _resolve_import_path(self, from_file: Path, import_path: str, 
                            all_files: List[Path]) -> Optional[Path]:
        """Resolve relative import path to actual file"""
        from_dir = from_file.parent
        
        # Clean path
        import_path = import_path.strip('\'"')
        
        # Try different extensions
        for ext in ['.ts', '.js', '.tsx', '.jsx', '/index.ts', '/index.js', '']:
            try:
                if ext.startswith('/'):
                    resolved_path = (from_dir / import_path).resolve()
                else:
                    resolved_path = (from_dir / (import_path + ext)).resolve()
                
                # Check if exists in file list
                for file in all_files:
                    if file.resolve() == resolved_path:
                        return file
            except:
                continue
        
        return None

    def _build_template_prompt_with_component_context(self, 
                                                       template_code: str,
                                                       component_code: str,
                                                       features: Dict) -> str:
        """Build template migration prompt with component context for semantic validation"""
        
        # Truncate component code if too large
        component_preview = component_code[:2500] + ("..." if len(component_code) > 2500 else "")
        
        return template_with_component_prompt(component_preview, template_code, features)

    def _validate_template_against_component(self,
                                             html_code: str,
                                             component_code: str) -> Dict:
        """Use LLM to validate template bindings against component structure"""
        
        # Truncate for LLM
        html_preview = html_code[:2000] + ("..." if len(html_code) > 2000 else "")
        component_preview = component_code[:2500] + ("..." if len(component_code) > 2500 else "")
        
        prompt = validate_template_prompt(component_preview, html_preview)

        system_msg = """You are an expert Angular template validator.
Analyze component-template relationships and identify binding errors.
Check if template references match component class members.
Return ONLY valid JSON with validation results."""

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
            
            result = json.loads(content)
            
            # Ensure required keys exist
            if 'valid' not in result:
                result['valid'] = result.get('score', 0) >= 70
            if 'valid_bindings' not in result:
                result['valid_bindings'] = []
            if 'invalid_bindings' not in result:
                result['invalid_bindings'] = []
            if 'warnings' not in result:
                result['warnings'] = []
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"   ⚠️  Validation JSON parsing failed: {e}")
            print(f"   Response: {content[:200]}")
            # Fallback to basic validation
            return self._validate_template(html_code, {})
        except Exception as e:
            print(f"   ⚠️  Component-aware validation failed: {e}")
            # Fallback to basic validation
            return self._validate_template(html_code, {})

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
                paired_template_path: Optional[Path] = None,
                paired_component_code: Optional[str] = None,
                dependency_context: Optional[Dict] = None) -> Dict:
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
        
        # NEW: Build context-aware prompt for templates
        if classification['primary_type'] == 'template' and paired_component_code:
            print(f"   Using component-aware migration")
            prompt = self._build_template_prompt_with_component_context(
                code_for_prompt,
                paired_component_code,
                classification['features']
            )
        else:
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
            if paired_component_code:
                system_msg = """You are an expert Angular template migration specialist with semantic validation.
Analyze the paired component class to ensure all template bindings are valid.
Convert AngularJS template syntax to Angular 16+ while validating against component structure.
Remove or fix bindings that reference non-existent properties or methods.
Return ONLY the migrated HTML template code, no explanations."""
            else:
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

        migrated_code = None
        max_retries = 3
        backoff_base = 2

        for attempt in range(1, max_retries + 1):
            try:
                response = self.llm.invoke(messages)
                migrated_code = response.content
                break
            except Exception as e:
                err = str(e)

                # Handle payload-too-large (422) by retrying once immediately with a simplified prompt
                if "422" in err:
                    print(f"   ⚠️  Request too large, retrying with simplified prompt...")
                    simplified_prompt = self._build_simplified_prompt(
                        classification['primary_type'],
                        code_for_prompt[:5000]
                    )
                    messages = [
                        SystemMessage(content=system_msg),
                        HumanMessage(content=simplified_prompt)
                    ]
                    try:
                        response = self.llm.invoke(messages)
                        migrated_code = response.content
                        break
                    except Exception as e2:
                        print(f"   ⚠️  Simplified prompt failed: {e2}")
                        err = str(e2)

                # Treat read timeouts / transient network errors with exponential backoff
                is_timeout = "timed out" in err.lower() or "read timed out" in err.lower() or isinstance(e, requests.exceptions.ReadTimeout)
                if is_timeout and attempt < max_retries:
                    wait = backoff_base ** attempt
                    print(f"   ⚠️  Read timed out, retrying in {wait}s (attempt {attempt}/{max_retries})...")
                    time.sleep(wait)
                    continue

                # Generic retry for other transient failures
                if attempt < max_retries:
                    wait = backoff_base ** attempt
                    print(f"   ⚠️  LLM call failed: {err} — retrying in {wait}s (attempt {attempt}/{max_retries})...")
                    time.sleep(wait)
                    continue

                # Final attempt failed — surface the error
                raise

        if migrated_code is None:
            raise RuntimeError(f"LLM did not return a response after {max_retries} attempts")
                
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
            
            # NEW: Context-aware validation if component available
            if paired_component_code:
                print("   Using component context for validation...")
                validation_result = self._validate_template_against_component(
                    migrated_code,
                    paired_component_code
                )
            else:
                validation_result = self._validate_template(migrated_code, classification['features'])
            
            print(f"   Valid: {'✅ Yes' if validation_result.get('valid', True) else '⚠️  With warnings'}")
            print(f"   Score: {validation_result.get('score', 0)}/100")
            if validation_result.get('warnings'):
                print(f"   Warnings: {len(validation_result['warnings'])}")
            if validation_result.get('invalid_bindings'):
                print(f"   Invalid bindings: {len(validation_result['invalid_bindings'])}")
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
                    migrated_code = self._update_component_template_url(
                        migrated_code,
                        paired_template_path.with_suffix('.component.html').name
                    )
                    
            elif classification['primary_type'] == 'directive':
                output_name += '.directive.ts'
            elif classification['primary_type'] == 'filter':
                output_name += '.pipe.ts'
            else:
                output_name += '.ts'
            
            output_path = output_dir / output_name
        if classification['primary_type'] != 'template' and output_path:
            base = output_path.stem
            parent = output_path.parent

            if classification['primary_type'] == 'service':
                output_path = parent / f"{base}.service.ts"
            elif classification['primary_type'] == 'controller':
                output_path = parent / f"{base}.component.ts"
            elif classification['primary_type'] == 'directive':
                output_path = parent / f"{base}.directive.ts"
            elif classification['primary_type'] == 'filter':
                output_path = parent / f"{base}.pipe.ts"
            else:
                output_path = parent / f"{base}.ts"
        # Update import paths using LLM if we have dependency context
        if (dependency_context and 
            dependency_context.get('fix_imports') and 
            dependency_context.get('migration_map') and
            classification['primary_type'] != 'template'):  # Only for code files
            
            print("🔄 Updating import paths with AI...")
            migrated_code = self._update_import_paths_with_llm(
                migrated_code,
                input_path.name,
                input_path,
                output_path,
                dependency_context['migration_map']
            )
            print()
        
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
            print(f"Valid:       {'✅ Yes' if validation_result.get('valid', True) else '❌ No'}")
            print(f"Score:       {validation_result.get('score', 0)}/100")
        
        if paired_template_path:
            print(f"Paired With: {paired_template_path.name}")
        
        if paired_component_code:
            print(f"Component Context: ✅ Used for semantic validation")
        
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
        
        # NEW: Show invalid bindings if present
        if validation.get('invalid_bindings'):
            lines.append("\n❌ INVALID BINDINGS:")
            for binding in validation['invalid_bindings']:
                if isinstance(binding, dict):
                    lines.append(f"  • {binding.get('binding', 'Unknown')} ({binding.get('type', 'unknown')} - {binding.get('line_hint', 'no location')})")
                else:
                    lines.append(f"  • {binding}")
        
        if validation.get('warnings'):
            lines.append("\n⚠️  WARNINGS:")
            for i, warning in enumerate(validation['warnings'], 1):
                lines.append(f"  {i}. {warning}")
        
        # NEW: Show valid bindings if from component validation
        if validation.get('valid_bindings'):
            lines.append(f"\n✅ VALID BINDINGS: {len(validation['valid_bindings'])}")
            if len(validation['valid_bindings']) <= 10:
                for binding in validation['valid_bindings']:
                    lines.append(f"  • {binding}")
            else:
                lines.append(f"  (showing first 10 of {len(validation['valid_bindings'])})")
                for binding in validation['valid_bindings'][:10]:
                    lines.append(f"  • {binding}")
        
        # Original feature detection (if available)
        if 'has_interpolation' in validation:
            lines.append("\n✨ FEATURES DETECTED:")
            lines.append(f"  • Interpolation: {'✅' if validation['has_interpolation'] else '❌'}")
            lines.append(f"  • Event Bindings: {'✅' if validation.get('has_event_bindings') else '❌'}")
            lines.append(f"  • Property Bindings: {'✅' if validation.get('has_property_bindings') else '❌'}")
        
        # NEW: Show suggestions if available
        if validation.get('suggestions'):
            lines.append("\n💡 SUGGESTIONS:")
            for suggestion in validation['suggestions']:
                lines.append(f"  • {suggestion}")
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)
    
    def _generate_llm_insights(self, 
                            categorized: Dict[str, List[Path]],
                            dependency_map: Dict[Path, List[Path]],
                            pairs_map: Dict[Path, Path],
                            results: List[Dict]) -> Dict:
        """Use LLM to analyze migration results and provide intelligent recommendations"""
        
        print("   🤖 Analyzing migration with AI for intelligent insights...")
        
        # Prepare summary of migration for LLM
        migration_summary = {
            'total_files': len(results),
            'successful': len([r for r in results if r['status'] == 'success']),
            'failed': len([r for r in results if r['status'] == 'failed']),
            'file_types': {
                'services': len(categorized.get('services', [])),
                'controllers': len(categorized.get('controllers', [])),
                'directives': len(categorized.get('directives', [])),
                'filters': len(categorized.get('filters', [])),
                'templates': len(categorized.get('templates', []))
            },
            'dependencies_found': sum(1 for deps in dependency_map.values() if deps),
            'component_template_pairs': len(pairs_map)
        }
        
        # Collect validation issues
        validation_issues = []
        for result in results:
            if result['status'] == 'success' and 'result' in result:
                validation = result['result'].get('validation')
                if validation and (not validation.get('valid', True) or validation.get('warnings')):
                    validation_issues.append({
                        'file': Path(result['file']).name,
                        'score': validation.get('score', 0),
                        'issues': validation.get('warnings', []) + [b.get('binding', str(b)) for b in validation.get('invalid_bindings', [])]
                    })
        
        # Collect failed migrations
        failed_migrations = []
        for result in results:
            if result['status'] == 'failed':
                failed_migrations.append({
                    'file': Path(result['file']).name,
                    'error': str(result.get('error', 'Unknown error'))[:200]
                })
        
        # Collect external dependencies
        external_deps = set()
        angular_modules = set()
        for result in results:
            if result['status'] == 'success' and 'result' in result:
                code = result['result'].get('migrated_code', '')
                imports = re.findall(r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]', code)
                for imp in imports:
                    if not imp.startswith('.'):
                        if imp.startswith('@angular/'):
                            angular_modules.add(imp)
                        else:
                            external_deps.add(imp)
        
        # Build LLM prompt
        prompt = insights_prompt(migration_summary, validation_issues, failed_migrations, angular_modules, external_deps)

        system_msg = """You are an expert Angular migration consultant with deep knowledge of:
- AngularJS 1.x architecture and patterns
- Angular 16+ modern features
- Common migration pitfalls
- TypeScript best practices
- Dependency management

Provide actionable, specific recommendations based on the actual migration results.
Focus on root causes, not symptoms.
Prioritize recommendations by impact.
Return ONLY valid JSON."""

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
            
            insights = json.loads(content)
            return insights
            
        except json.JSONDecodeError as e:
            print(f"   ⚠️  LLM insights parsing failed: {e}")
            return {
                "overall_assessment": "Unable to generate AI insights",
                "root_causes": [],
                "migration_priority": [],
                "dependency_recommendations": {},
                "code_quality_issues": [],
                "next_steps": [],
                "risks": []
            }
        except Exception as e:
            print(f"   ⚠️  LLM insights generation failed: {e}")
            return {
                "overall_assessment": "Unable to generate AI insights",
                "root_causes": [],
                "migration_priority": [],
                "dependency_recommendations": {},
                "code_quality_issues": [],
                "next_steps": [],
                "risks": []
            }

    def _format_llm_insights_section(self, insights: Dict) -> List[str]:
        """Format LLM insights into report section"""
        lines = []
        
        lines.append("┌" + "─" * 78 + "┐")
        lines.append("│ 🤖 AI-POWERED MIGRATION ANALYSIS" + " " * 44 + "│")
        lines.append("└" + "─" * 78 + "┘")
        lines.append("")
        
        # Overall Assessment
        lines.append("📊 OVERALL ASSESSMENT:")
        lines.append(f"   {insights.get('overall_assessment', 'No assessment available')}")
        lines.append("")
        
        # Root Causes
        if insights.get('root_causes'):
            lines.append("🔍 ROOT CAUSE ANALYSIS:")
            for i, cause in enumerate(insights['root_causes'], 1):
                lines.append(f"   {i}. {cause}")
            lines.append("")
        
        # Migration Priority
        if insights.get('migration_priority'):
            lines.append("⚡ MIGRATION PRIORITY (Re-migrate these first):")
            for item in insights['migration_priority']:
                priority_icon = "🔴" if item.get('priority') == 'HIGH' else "🟡" if item.get('priority') == 'MEDIUM' else "🟢"
                lines.append(f"   {priority_icon} {item.get('file', 'Unknown')}")
                lines.append(f"      └─ {item.get('reason', 'No reason provided')}")
            lines.append("")
        
        # Dependency Recommendations
        dep_recs = insights.get('dependency_recommendations', {})
        if any(dep_recs.values()):
            lines.append("📦 DEPENDENCY RECOMMENDATIONS:")
            
            if dep_recs.get('install_first'):
                lines.append("   Install First:")
                for dep in dep_recs['install_first']:
                    lines.append(f"      • {dep}")
            
            if dep_recs.get('update_required'):
                lines.append("   Update Required:")
                for dep in dep_recs['update_required']:
                    lines.append(f"      • {dep}")
            
            if dep_recs.get('incompatible'):
                lines.append("   Incompatible:")
                for dep in dep_recs['incompatible']:
                    lines.append(f"      • {dep}")
            lines.append("")
        
        # Code Quality Issues
        if insights.get('code_quality_issues'):
            lines.append("🎯 CODE QUALITY IMPROVEMENTS:")
            for i, issue in enumerate(insights['code_quality_issues'], 1):
                lines.append(f"   {i}. {issue}")
            lines.append("")
        
        # Next Steps
        if insights.get('next_steps'):
            lines.append("📋 RECOMMENDED NEXT STEPS:")
            for step in insights['next_steps']:
                lines.append(f"   {step.get('step', '?')}. {step.get('action', 'No action specified')}")
                lines.append(f"      └─ {step.get('reason', 'No reason provided')}")
            lines.append("")
        
        # Risks
        if insights.get('risks'):
            lines.append("⚠️  RISK ASSESSMENT:")
            for risk in insights['risks']:
                severity_icon = "🔴" if risk.get('severity') == 'HIGH' else "🟡" if risk.get('severity') == 'MEDIUM' else "🟢"
                lines.append(f"   {severity_icon} {risk.get('risk', 'Unknown risk')}")
                lines.append(f"      └─ Mitigation: {risk.get('mitigation', 'No mitigation provided')}")
            lines.append("")
        
        return lines

    def _clean_code_for_processing(self, code: str, file_extension: str) -> str:
        """Clean code by removing comments and excessive whitespace"""
        
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
    print("│     WITH Context-Aware HTML Template Migration                 │")
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
            pair_templates=True,
            analyze_dependencies=True,
            fix_imports=True
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