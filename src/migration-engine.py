"""
AngularJS to Angular 16+ Migration Engine
Pattern-Based Architecture (No MCP)
"""

import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent))

from connectivity import ChatCopilot, get_copilot_token_via_internal_endpoint
from langchain_core.messages import HumanMessage, SystemMessage
from classifier import FileClassifier
from pattern_registry import PatternRegistry
from validator import CodeValidator


class MigrationEngine:
    """Main migration engine coordinating all components"""
    
    def __init__(self, model: str = "claude-sonnet-4"):
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
        
        print("✅ Engine Ready")
        print("=" * 70)
        print()
    
    def migrate_file(self, input_file: str, output_file: str = None, validate: bool = True) -> Dict:
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
        print()
        
        # Step 2: Classify file
        print("2️⃣ Classifying file type...")
        classification = self.classifier.classify(legacy_code)
        print(f"   Type: {classification['primary_type']}")
        print(f"   Confidence: {classification['confidence']}")
        print(f"   Complexity: {classification['complexity']}")
        print(f"   Features: {', '.join([k for k, v in classification['features'].items() if v])}")
        strategy = self.classifier.get_migration_strategy(classification)
        print(f"   Strategy: {strategy}")
        print()
        
        # Step 3: Build prompt from patterns
        print("3️⃣ Loading migration patterns...")
        prompt = self.registry.build_prompt(
            classification['primary_type'],
            legacy_code,
            classification['features']
        )
        print(f"   Pattern: {classification['primary_type']}")
        print(f"   Rules: {len(self.registry.get_migration_rules(classification['primary_type']))} rules loaded")
        print()
        
        # Step 4: Run LLM migration
        print(f"4️⃣ Running AI migration ({self.model})...")
        system_msg = """You are an expert Angular migration specialist.
Follow the provided patterns and rules exactly.
Generate clean, production-ready TypeScript code.
Use Angular 16+ features: standalone components, signals, inject() function.
Return ONLY the TypeScript code, no explanations."""
        
        messages = [
            SystemMessage(content=system_msg),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        migrated_code = response.content
        
        # Clean code blocks
        if "```typescript" in migrated_code:
            migrated_code = migrated_code.split("```typescript")[1].split("```")[0].strip()
        elif "```ts" in migrated_code:
            migrated_code = migrated_code.split("```ts")[1].split("```")[0].strip()
        elif "```" in migrated_code:
            migrated_code = migrated_code.split("```")[1].split("```")[0].strip()
        
        print(f"   Generated: {len(migrated_code)} characters")
        print()
        
        # Step 5: Validate
        validation_result = None
        if validate:
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
        
        # Step 6: Save output
        if output_file:
            output_path = Path(output_file)
        else:
            output_dir = input_path.parent.parent / "output"
            output_dir.mkdir(exist_ok=True)
            
            output_name = input_path.stem
            if classification['primary_type'] == 'service':
                output_name += '.service.ts'
            elif classification['primary_type'] == 'controller':
                output_name += '.component.ts'
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
        
        print("=" * 70)
        
        if validate and validation_result:
            print()
            print(self.validator.format_validation_report(validation_result))
        
        return {
            'input_file': str(input_path),
            'output_file': str(output_path),
            'classification': classification,
            'strategy': strategy,
            'validation': validation_result,
            'migrated_code': migrated_code
        }


def main():
    """Main entry point"""
    INPUT_FILE = Path(__file__).parent / "legacy-code" / "api.js"
    MODEL = "claude-sonnet-4"
    
    print("┌─────────────────────────────────────────────────────────────────┐")
    print("│     AngularJS → Angular 16+ Migration Engine                   │")
    print("│     Pattern-Based Architecture (No MCP)                        │")
    print("└─────────────────────────────────────────────────────────────────┘")
    print()
    
    try:
        engine = MigrationEngine(model=MODEL)
        result = engine.migrate_file(input_file=str(INPUT_FILE), validate=True)
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