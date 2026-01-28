import re
import json
import datetime
from pathlib import Path
from typing import Dict, List, Set

def _detect_unknown_template_attributes(engine, templates_paths: List[Path]) -> Dict[str, Set[str]]:
    KNOWN_ATTRS = {
        'class','id','style','role','title','name','type',
        'ngModel','[(ngModel)]','*ngFor','*ngIf','translate','ngClass','ngStyle',
        'disabled','checked','value','href','src'
    }
    attr_re = re.compile(r'<[a-zA-Z0-9\-]+\s([^>]+)>', re.DOTALL)
    name_re = re.compile(r'([a-zA-Z][a-zA-Z0-9\-]*)\s*(?:=|>|$)')
    repo_root = Path.cwd()

    result = {}
    for tpl_path in templates_paths:
        try:
            text = Path(tpl_path).read_text(encoding='utf-8')
        except Exception:
            continue
        attrs_found = set()
        for tag_attrs in attr_re.findall(text):
            for m in name_re.findall(tag_attrs):
                name = m.strip()
                if not name or name in KNOWN_ATTRS:
                    continue
                if '-' not in name and not re.search(r'[A-Z]', name):
                    continue
                attrs_found.add(name)
        if not attrs_found:
            continue

        unresolved = set()
        for attr in attrs_found:
            variants = [
                attr,
                attr.replace('-', ''),
                ''.join(p.title() for p in attr.split('-')),
                attr.replace('-', '_')
            ]
            found_impl = False
            for f in repo_root.rglob('*.*'):
                if f.suffix.lower() not in ('.js', '.ts', '.html', '.scss', '.css'):
                    continue
                try:
                    content = f.read_text(encoding='utf-8', errors='ignore')
                except Exception:
                    continue
                for v in variants:
                    if (f"directive('{v}" in content or f'directive("{v}"' in content or
                        f"selector: '[{v}]'" in content or v in content):
                        found_impl = True
                        break
                if found_impl:
                    break
            if not found_impl:
                unresolved.add(attr)
        if unresolved:
            result[str(tpl_path)] = unresolved

    return result

def _attribute_suggestion_via_llm(engine, attribute_name: str, example_template: str = None) -> str:
    system_msg = "You are an expert Angular migration assistant. Provide concise migration guidance."
    prompt = f"""The template uses a custom attribute/attribute-directive `{attribute_name}`.
Describe succinctly:
- Likely intent/behavior (layout, DOM-tweak, event binding, data-binding).
- Minimal Angular migration options (attribute directive, component wrapper, or CSS-only).
- Example Angular attribute directive skeleton (TypeScript) if appropriate.

Return a short plain-text recommendation (2-6 lines)."""
    if example_template:
        prompt += f"\n\nExample snippet:\n{example_template[:800]}"

    try:
        messages = [engine.SystemMessage(content=system_msg), engine.HumanMessage(content=prompt)]
    except AttributeError:
        # Fallback if engine doesn't expose SystemMessage/HumanMessage classes
        messages = None

    try:
        if messages:
            resp = engine.llm.invoke(messages)
            return resp.content.strip()
        else:
            # Basic fallback text
            return f"No LLM suggestion available for `{attribute_name}` — consider migrating to an Angular directive or replacing with CSS."
    except Exception:
        return f"No LLM suggestion available for `{attribute_name}` — consider migrating to an Angular directive or replacing with CSS."

def generate_suggestions_report(engine,
                                categorized: Dict[str, List[Path]],
                                dependency_map: Dict[Path, List[Path]],
                                pairs_map: Dict[Path, Path],
                                results: List[Dict],
                                output_path: Path,
                                llm_insights: Dict = None) -> str:
    suggestions = []
    suggestions.append("=" * 80)
    suggestions.append("ANGULARJS TO ANGULAR 16+ MIGRATION - INTELLIGENT SUGGESTIONS")
    suggestions.append("=" * 80)
    suggestions.append(f"Generated: {output_path}")
    suggestions.append(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    suggestions.append("")

    # LLM insights (reuse engine formatter if available)
    if llm_insights:
        if hasattr(engine, '_format_llm_insights_section'):
            suggestions.extend(engine._format_llm_insights_section(llm_insights))
        else:
            suggestions.append("AI insights available but engine cannot format them here.")
            suggestions.append("")

    # Basic migration summary (mirrors previous behaviour)
    total_files = len(results)
    successful = len([r for r in results if r['status'] == 'success'])
    failed = len([r for r in results if r['status'] == 'failed'])
    suggestions.append("┌" + "─" * 78 + "┐")
    suggestions.append("│ 1. MIGRATION SUMMARY" + " " * 57 + "│")
    suggestions.append("└" + "─" * 78 + "┘")
    suggestions.append("")
    suggestions.append(f"Total Files Processed:  {total_files}")
    suggestions.append(f"Successful Migrations:  {successful} ")
    suggestions.append(f"Failed Migrations:      {failed} ")
    suggestions.append(f"Success Rate:           {(successful/total_files*100):.1f}%" if total_files else "Success Rate: N/A")
    suggestions.append("")

    # File types
    suggestions.append(" FILE TYPE BREAKDOWN:")
    for file_type, files in categorized.items():
        if files:
            suggestions.append(f"   {file_type.capitalize()}: {len(files)}")
    suggestions.append("")

    # Dependencies
    if dependency_map:
        deps_found = sum(1 for deps in dependency_map.values() if deps)
        if deps_found > 0:
            suggestions.append(" DEPENDENCY ANALYSIS:")
            suggestions.append(f"   Files with dependencies: {deps_found}")
            for file, deps in dependency_map.items():
                if deps:
                    suggestions.append(f"   • {Path(file).name} depends on:")
                    for dep in deps:
                        suggestions.append(f"      └─ {Path(dep).name}")
            suggestions.append("")

    # Component-template pairs
    if pairs_map:
        suggestions.append(" COMPONENT-TEMPLATE PAIRS:")
        suggestions.append(f"   Detected pairs: {len(pairs_map)}")
        for ctrl, tmpl in pairs_map.items():
            suggestions.append(f"   • {Path(ctrl).name} → {Path(tmpl).name}")
        suggestions.append("")

    # Detect unknown/custom attributes in templates and ask LLM for succinct migration advice
    template_paths = [p for p in categorized.get('templates', [])]
    if template_paths:
        unknown_attrs = _detect_unknown_template_attributes(engine, template_paths)
        if unknown_attrs:
            suggestions.append("\n🔎 CUSTOM/UNKNOWN TEMPLATE ATTRIBUTES FOUND:")
            for tpl, attrs in unknown_attrs.items():
                suggestions.append(f"  • {Path(tpl).name}: {', '.join(sorted(attrs))}")
                for a in sorted(attrs):
                    snippet = ""
                    try:
                        text = Path(tpl).read_text(encoding='utf-8', errors='ignore')
                        idx = text.find(a)
                        snippet = text[max(0, idx-40):idx+40].replace('\n',' ')
                    except Exception:
                        snippet = None
                    llm_reco = _attribute_suggestion_via_llm(engine, a, snippet)
                    for line in llm_reco.splitlines():
                        suggestions.append(f"    └─ {line}")
            suggestions.append("")

    suggestions.append("=" * 80)
    suggestions.append("END OF SUGGESTIONS REPORT")
    suggestions.append("=" * 80)

    return "\n".join(suggestions)