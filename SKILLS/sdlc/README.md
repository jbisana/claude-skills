# SDLC Automation Skill

This module provides a robust suite of AI-powered functions to automate the Software Development Lifecycle (SDLC) using Google's Gemini models. It facilitates the transition from a raw app idea to a production-ready execution plan.

## Core Capabilities

- **Feature Discovery**: Identifies the 10 most critical MVP features for any application idea, focusing on core value rather than generic CRUD.
- **Architectural Design**: Recommends a pragmatic, security-conscious technology stack with detailed rationales for every layer.
- **Database Engineering**: Generates production-ready SQL (PostgreSQL) schemas with built-in Row-Level Security (RLS), audit trails, and UUIDs.
- **UI/UX Strategy**: Defines a comprehensive design system, including brand identity, Tailwind-compatible tokens, and layout architecture.
- **Security Architecture**: Maps out a defense-in-depth strategy covering authentication, data protection, and OWASP Top 10 mitigations.
- **Agile Execution Planning**: Decomposes the entire project into sequential, independently verifiable micro-tasks from environment setup to production deployment.
- **Agent Orchestration**: Compiles all architectural and feature requirements into a single "Master System Prompt" designed to drive agentic coding workflows.

## API Reference

### Configuration

All functions accept an `AIConfig` object:

```typescript
export interface AIConfig {
  model: string;
  apiKey?: string;
  temperature?: number;
  maxOutputTokens?: number;
}
```

### Exported Functions

| Function | Description |
| :--- | :--- |
| `generateFeatures(appIdea, config)` | Generates a list of critical MVP features. |
| `generateTechStack(appIdea, features, config)` | Returns a recommended tech stack with rationales. |
| `generateSqlSchema(appIdea, features, techStack, config)` | Generates a complete, secure DDL script. |
| `generateDesignSystem(appIdea, features, techStack, config)` | Defines brand identity and component library. |
| `generateSecurityArchitecture(...)` | Defines the security posture and OWASP mitigations. |
| `generateExecutionPlan(masterPrompt, config)` | Decomposes a master prompt into a 14-phase task list. |
| `compileMasterPrompt(...)` | Aggregates all context into a unified system prompt. |

## Prerequisites

- **Environment**: A valid `GEMINI_API_KEY` must be set in your environment variables.
- **Dependencies**: `@google/genai` package must be installed.

## Usage Example

```typescript
import * as sdlc from './sdlc.md';

const config = { model: 'gemini-1.5-pro' };
const appIdea = "A peer-to-peer equipment rental marketplace for film professionals.";

// 1. Identify features
const features = await sdlc.generateFeatures(appIdea, config);

// 2. Build the stack
const techStack = await sdlc.generateTechStack(appIdea, features, config);

// 3. Generate Schema
const schema = await sdlc.generateSqlSchema(appIdea, features, techStack, config);
```
