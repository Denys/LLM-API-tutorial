#!/usr/bin/env node
/**
 * Interactive chat with Claude - Multi-turn conversation
 *
 * This script demonstrates:
 * - Maintaining conversation history
 * - Multi-turn interactions
 * - Context awareness
 * - Interactive CLI interface
 * - Token tracking across conversation
 *
 * Usage:
 *     node chat_conversation.js
 */

import Anthropic from '@anthropic-ai/sdk';
import dotenv from 'dotenv';
import * as readline from 'readline';

dotenv.config();

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY
});

class ChatSession {
  constructor(model = 'claude-3-5-haiku-20241022', maxTokens = 1024) {
    this.model = model;
    this.maxTokens = maxTokens;
    this.conversation = [];
    this.totalInputTokens = 0;
    this.totalOutputTokens = 0;
    this.messageCount = 0;
  }

  async sendMessage(userMessage) {
    // Add user message to conversation history
    this.conversation.push({
      role: 'user',
      content: userMessage
    });

    // Get Claude's response
    const response = await client.messages.create({
      model: this.model,
      max_tokens: this.maxTokens,
      messages: this.conversation
    });

    // Extract assistant's message
    const assistantMessage = response.content[0].text;

    // Add assistant's response to conversation history
    this.conversation.push({
      role: 'assistant',
      content: assistantMessage
    });

    // Track usage
    this.totalInputTokens += response.usage.input_tokens;
    this.totalOutputTokens += response.usage.output_tokens;
    this.messageCount += 1;

    return { message: assistantMessage, usage: response.usage };
  }

  getStats() {
    const totalTokens = this.totalInputTokens + this.totalOutputTokens;
    const inputCost = (this.totalInputTokens / 1_000_000) * 0.25;
    const outputCost = (this.totalOutputTokens / 1_000_000) * 1.25;
    const totalCost = inputCost + outputCost;

    return {
      messages: this.messageCount,
      inputTokens: this.totalInputTokens,
      outputTokens: this.totalOutputTokens,
      totalTokens,
      estimatedCost: totalCost
    };
  }

  clearHistory() {
    this.conversation = [];
    console.log('🗑️  Conversation history cleared!');
  }
}

function printStats(stats) {
  console.log('\n' + '='.repeat(60));
  console.log('📊 Conversation Statistics:');
  console.log('='.repeat(60));
  console.log(`  Messages:      ${stats.messages}`);
  console.log(`  Input tokens:  ${stats.inputTokens}`);
  console.log(`  Output tokens: ${stats.outputTokens}`);
  console.log(`  Total tokens:  ${stats.totalTokens}`);
  console.log(`  Cost estimate: $${stats.estimatedCost.toFixed(6)}`);
  console.log('='.repeat(60) + '\n');
}

async function main() {
  console.log('🤖 Claude Chat - Interactive Conversation');
  console.log('='.repeat(60));
  console.log('Commands:');
  console.log('  /stats  - Show conversation statistics');
  console.log('  /clear  - Clear conversation history');
  console.log('  /quit   - Exit chat');
  console.log('='.repeat(60) + '\n');

  const session = new ChatSession();

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  const askQuestion = () => {
    rl.question('You: ', async (input) => {
      const userInput = input.trim();

      if (!userInput) {
        askQuestion();
        return;
      }

      // Handle commands
      if (['/quit', '/exit', '/q'].includes(userInput.toLowerCase())) {
        console.log('\n👋 Goodbye!');
        if (session.messageCount > 0) {
          console.log('\n📊 Final Statistics:');
          printStats(session.getStats());
        }
        rl.close();
        return;
      }

      if (userInput.toLowerCase() === '/stats') {
        printStats(session.getStats());
        askQuestion();
        return;
      }

      if (userInput.toLowerCase() === '/clear') {
        session.clearHistory();
        askQuestion();
        return;
      }

      try {
        // Send message to Claude
        const { message, usage } = await session.sendMessage(userInput);

        // Display Claude's response
        console.log(`\nClaude: ${message}`);
        console.log(`[Tokens: ${usage.input_tokens} in, ${usage.output_tokens} out]\n`);
      } catch (error) {
        console.error(`\n❌ Error: ${error.message}\n`);
      }

      askQuestion();
    });
  };

  askQuestion();
}

main().catch(error => {
  console.error('Error:', error.message);
  process.exit(1);
});
