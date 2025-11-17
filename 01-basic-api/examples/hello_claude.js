#!/usr/bin/env node
/**
 * Your first Claude API call!
 *
 * This script demonstrates:
 * - Loading environment variables
 * - Creating an Anthropic client
 * - Making a simple API call
 * - Displaying the response and token usage
 *
 * Usage:
 *     node hello_claude.js
 */

import Anthropic from '@anthropic-ai/sdk';
import dotenv from 'dotenv';

// Load environment variables from .env file
dotenv.config();

// Initialize the Anthropic client
const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY
});

async function main() {
  console.log('🤖 Making your first Claude API call...\n');

  // Create a message
  const message = await client.messages.create({
    model: 'claude-3-5-haiku-20241022',
    max_tokens: 1024,
    messages: [
      {
        role: 'user',
        content: 'Say hello and introduce yourself in one sentence!'
      }
    ]
  });

  // Extract the response text
  const responseText = message.content[0].text;

  // Display results
  console.log('='.repeat(60));
  console.log('Claude\'s Response:');
  console.log('='.repeat(60));
  console.log(responseText);
  console.log('\n' + '='.repeat(60));
  console.log('📊 Token Usage:');
  console.log('='.repeat(60));
  console.log(`  Input tokens:  ${message.usage.input_tokens}`);
  console.log(`  Output tokens: ${message.usage.output_tokens}`);
  console.log(`  Total tokens:  ${message.usage.input_tokens + message.usage.output_tokens}`);

  // Calculate approximate cost (Haiku pricing as of 2025)
  const inputCost = (message.usage.input_tokens / 1_000_000) * 0.25;
  const outputCost = (message.usage.output_tokens / 1_000_000) * 1.25;
  const totalCost = inputCost + outputCost;

  console.log(`\n💰 Approximate cost: $${totalCost.toFixed(6)}`);
  console.log('='.repeat(60));
}

main().catch(error => {
  console.error('Error:', error.message);
  process.exit(1);
});
