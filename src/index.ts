import Anthropic from '@anthropic-ai/sdk';
import * as fs from 'fs';
import 'dotenv/config';

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY || '' });

async function runMigration(file: string) {
    const legacyCode = fs.readFileSync(`./legacy-code/${file}`, 'utf-8');
    const rules = fs.readFileSync(`./prompts/angularjs-to-angular.txt`, 'utf-8');

    const message = await anthropic.messages.create({
        model: "claude-3-5-sonnet-20241022",
        max_tokens: 4000,
        system: rules,
        messages: [{ role: "user", content: legacyCode }],
    });

    const textBlock = message.content[0];
    const newCode = textBlock.type === 'text' ? textBlock.text : '';
    const outputName = file.replace('.js', '.ts');
    fs.writeFileSync(`./output/${outputName}`, newCode);
}

runMigration('api.js').catch(console.error);