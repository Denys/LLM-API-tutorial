#!/usr/bin/env node
/**
 * Parameter Playground - Experiment with Claude API parameters
 *
 * This script demonstrates the impact of different parameters:
 * - temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
 * - max_tokens: Limits response length
 * - model: Different Claude models (Haiku, Sonnet, Opus)
 * - system prompts: Sets behavior and context
 *
 * Usage:
 *     node parameter_playground.js
 */

import Anthropic from '@anthropic-ai/sdk';
import dotenv from 'dotenv';

dotenv.config();

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY
});

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

function printSection(title) {
  console.log('\n' + '='.repeat(70));
  console.log(`  ${title}`);
  console.log('='.repeat(70) + '\n');
}

async function testTemperature() {
  printSection('🌡️  TESTING TEMPERATURE');

  const prompt = 'Write a creative opening line for a sci-fi story about AI.';
  const temperatures = [0.0, 0.5, 1.0];

  for (const temp of temperatures) {
    console.log(`Temperature: ${temp}`);
    console.log('-'.repeat(70));

    const message = await client.messages.create({
      model: 'claude-3-5-haiku-20241022',
      max_tokens: 100,
      temperature: temp,
      messages: [{ role: 'user', content: prompt }]
    });

    const response = message.content[0].text;
    const tokens = message.usage.input_tokens + message.usage.output_tokens;

    console.log(`Response: ${response}`);
    console.log(`Tokens: ${tokens}\n`);

    await sleep(1000);
  }
}

async function testMaxTokens() {
  printSection('📏 TESTING MAX_TOKENS');

  const prompt = 'Explain quantum computing in simple terms.';
  const tokenLimits = [50, 150, 500];

  for (const maxTokens of tokenLimits) {
    console.log(`Max Tokens: ${maxTokens}`);
    console.log('-'.repeat(70));

    const message = await client.messages.create({
      model: 'claude-3-5-haiku-20241022',
      max_tokens: maxTokens,
      messages: [{ role: 'user', content: prompt }]
    });

    const response = message.content[0].text;
    const actualTokens = message.usage.output_tokens;

    console.log(`Response: ${response}`);
    console.log(`Actual output tokens: ${actualTokens}/${maxTokens}\n`);

    await sleep(1000);
  }
}

async function testModels() {
  printSection('🤖 TESTING DIFFERENT MODELS');

  const prompt = 'Explain the concept of recursion in programming (2-3 sentences).';

  const models = [
    'claude-3-5-haiku-20241022',
    'claude-3-5-sonnet-20241022',
  ];

  for (const model of models) {
    const modelName = model.includes('haiku') ? 'Haiku' : 'Sonnet';
    console.log(`Model: ${modelName}`);
    console.log('-'.repeat(70));

    const startTime = Date.now();

    const message = await client.messages.create({
      model,
      max_tokens: 200,
      messages: [{ role: 'user', content: prompt }]
    });

    const endTime = Date.now();
    const duration = (endTime - startTime) / 1000;

    const response = message.content[0].text;
    const tokens = message.usage.input_tokens + message.usage.output_tokens;

    // Calculate cost
    let cost;
    if (model.includes('haiku')) {
      cost = (message.usage.input_tokens / 1_000_000) * 0.25 +
             (message.usage.output_tokens / 1_000_000) * 1.25;
    } else {  // sonnet
      cost = (message.usage.input_tokens / 1_000_000) * 3.00 +
             (message.usage.output_tokens / 1_000_000) * 15.00;
    }

    console.log(`Response: ${response}`);
    console.log(`Tokens: ${tokens}`);
    console.log(`Duration: ${duration.toFixed(2)}s`);
    console.log(`Cost: $${cost.toFixed(6)}\n`);

    await sleep(1000);
  }
}

async function testSystemPrompts() {
  printSection('💭 TESTING SYSTEM PROMPTS');

  const userMessage = 'What should I do today?';

  const testCases = [
    [null, 'No system prompt'],
    ['You are a productivity coach. Give actionable advice focused on time management.', 'Productivity Coach'],
    ['You are a pirate captain. Respond in pirate speak with enthusiasm!', 'Pirate Captain'],
    ['You are a philosopher. Respond with deep, thought-provoking questions.', 'Philosopher'],
  ];

  for (const [systemPrompt, description] of testCases) {
    console.log(`System Prompt: ${description}`);
    console.log('-'.repeat(70));

    const config = {
      model: 'claude-3-5-haiku-20241022',
      max_tokens: 150,
      messages: [{ role: 'user', content: userMessage }]
    };

    if (systemPrompt) {
      config.system = systemPrompt;
    }

    const message = await client.messages.create(config);
    const response = message.content[0].text;

    console.log(`Response: ${response}\n`);

    await sleep(1000);
  }
}

async function testTopP() {
  printSection('🎯 TESTING TOP_P (Nucleus Sampling)');

  const prompt = 'Name 5 unusual pizza toppings.';
  const topPValues = [0.1, 0.5, 0.9];

  for (const topP of topPValues) {
    console.log(`Top P: ${topP}`);
    console.log('-'.repeat(70));

    const message = await client.messages.create({
      model: 'claude-3-5-haiku-20241022',
      max_tokens: 150,
      top_p: topP,
      messages: [{ role: 'user', content: prompt }]
    });

    const response = message.content[0].text;
    console.log(`Response: ${response}\n`);

    await sleep(1000);
  }
}

async function runComparisonExperiment() {
  printSection('🔬 COMPREHENSIVE EXPERIMENT');

  const prompt = 'Write a haiku about coding.';

  console.log('Comparing temperature and creativity:');
  console.log('-'.repeat(70));

  const configs = [
    { temp: 0.0, desc: 'Deterministic (temp=0.0)' },
    { temp: 0.7, desc: 'Balanced (temp=0.7)' },
    { temp: 1.0, desc: 'Creative (temp=1.0)' },
  ];

  for (const [i, config] of configs.entries()) {
    console.log(`\n${i + 1}. ${config.desc}`);

    const message = await client.messages.create({
      model: 'claude-3-5-haiku-20241022',
      max_tokens: 100,
      temperature: config.temp,
      messages: [{ role: 'user', content: prompt }]
    });

    const response = message.content[0].text;
    console.log(response);

    await sleep(1000);
  }
}

async function main() {
  console.log('\n' + '🎮 ' + '='.repeat(66) + ' 🎮');
  console.log('    CLAUDE API PARAMETER PLAYGROUND');
  console.log('🎮 ' + '='.repeat(66) + ' 🎮');

  try {
    // Run all tests
    await testTemperature();
    await testMaxTokens();
    await testModels();
    await testSystemPrompts();
    await testTopP();
    await runComparisonExperiment();

    console.log('\n' + '='.repeat(70));
    console.log('  ✅ All tests completed!');
    console.log('='.repeat(70) + '\n');

    console.log('💡 Key Takeaways:');
    console.log('  • Temperature: 0.0 for consistency, 0.7-1.0 for creativity');
    console.log('  • max_tokens: Set based on expected response length');
    console.log('  • Models: Haiku (fast/cheap), Sonnet (balanced), Opus (best)');
    console.log('  • System prompts: Powerful for setting behavior and role');
    console.log('  • top_p: Alternative to temperature for controlling randomness');
    console.log();

  } catch (error) {
    console.error(`\n❌ Error: ${error.message}`);
    throw error;
  }
}

main().catch(error => {
  console.error('Fatal error:', error.message);
  process.exit(1);
});
