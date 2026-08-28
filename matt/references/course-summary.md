# AI Coding for Real Engineers

## Summary of Concepts and Workflows for Working with Coding Agents

## Executive Summary

The recurring problems throughout the material are not only that an agent cannot write code. They also come from unclear requirements, unsuitable context, work that is too large for one session, or the absence of feedback that can verify whether the result is correct.

Working with a coding agent therefore requires managing the whole process, not merely writing a more detailed prompt.

The core process is:

**Grill → Research → prototype → PRD → plan/issues → Implement → Review**

Different forms of uncertainty call for different steps:

- The requirement is still unclear → **Grill**
- Technical alternatives are still uncertain → **Research**
- It is not yet known whether a UI or integration works in practice → **prototype**
- The work is large and spans several sessions → **PRD + plan**
- The work has been divided into clear pieces → **issue + Implement**
- An implementation exists → **Feedback + Review**

The goal is not to let the agent make every decision for the human. It is to give the agent clearly bounded work together with the context and verification system appropriate to that work.

Another important goal is to make the implementation stage reliable enough to run **AFK**, allowing the human to use the same time to plan, decide, or prepare the next work instead of watching the agent throughout implementation.

---

# 1. Mental Model: What an Agent Works From

An agent works from several principal sources:

**Task Context** — the work and information needed in the current session
**Project Instructions** — repository rules and conventions
**skills** — methods for specific kinds of work
**Codebase** — the system's real state and existing patterns
**Feedback** — results from tests, type checks, commands, and review

Quality therefore depends on more than the prompt. It also depends on how much suitable context, project guidance, real codebase state, and feedback the agent has for the work at hand.

Not every task needs a dedicated skill or Project Instruction, but each source matters when the task calls for it.

---

# 2. LLM and Context-Window Constraints

## Context Window

The context window is the information space the model uses to produce an answer in the current session. It may contain the prompt, conversation, files read, and command results.

As information accumulates, important details can be buried under irrelevant material. The lessons call the period in which excess context begins to reduce work quality the "dumb zone."

Adding more information therefore does not always improve the result. The important practices are selecting information relevant to the task and knowing when to begin a fresh session.

Showing token count or context percentage in a status line makes context use visible without interrupting the workflow.

## Session Strategy

Context management has no single answer; it depends on the work:

- **Multi-phase work** — the demonstrated approach starts each phase with fresh context, supplies the complete PRD and plan, and asks the agent to perform only the current phase. The agent may have to explore some existing implementation again, but the new phase begins near the start of the context window.
- **Interrupting work discovered during a session** — create a temporary handoff document containing the state, the next session's task, potentially useful skills, and links to existing artifacts without copying all of those artifacts.
- **Debugging or work that needs experimental history** — compact may preserve a shortened form of the conversation, but repeated compaction can retain accumulated material that makes results less predictable.

Resuming an interrupted conversation helps return to that session, but it is not the same as starting with fresh context.

## Stateless Model

When a new session begins, the agent does not remember all the reasoning behind the design. It must explore the codebase and read the relevant documents again.

If the reasons behind decisions are not recorded in code or documentation, the agent may see the system's current state without knowing why it was designed that way.

## Non-determinism

Agent outputs can differ even with the same prompt, codebase, and procedure because the model selects outputs probabilistically.

Verification and feedback loops are therefore needed to evaluate real system behavior rather than trusting one agent response.

---

# 3. Steering: Instructions, Skills, Memory, and Subagents

## Project Instructions

Files such as `Claude.md` hold repository rules and guidance, including coding conventions, service patterns, and testing practices.

They give the agent consistent project rules. However, placing frontend, database, testing, and deployment guidance in one file loads irrelevant instructions even when the current task concerns only one area.

When the agent repeats the same mistake, consider whether the correction should become a durable project rule—for example, requiring every service to have tests. A rule worth recording should be high-leverage, durable, and not tied to a file name or one transient case.

## Progressive Disclosure

Progressive disclosure separates guidance into parts and lets the main file point to the relevant information.

It addresses the problem of combining frontend, database, testing, and deployment rules in one `Claude.md` even when only one area matters.

The main file becomes a map: database work points to database documentation, and frontend work points to frontend documentation when needed.

Unrelated information therefore does not have to enter context at the same time.

## Skills

A skill is a set of instructions, scripts, and resources for a particular kind of work.

Project Instructions contain general repository rules. A skill contains a specific method, such as creating a skill, planning, working through a feedback loop, or building a prototype.

Skills are discovered first through their names and descriptions, and their details are loaded only when the task calls for them. Every category of guidance does not need to be loaded on every request.

## Automatic Memory

Automatic memory creates memory files from patterns the agent finds in a project and distinguishes user memory, project memory, and automatic memory.

Project Instructions are explicitly written repository rules. Automatic memory instead comes from information or patterns the agent observes while working.

Memory can carry information across tasks, but it can become too specific, stale, or inconsistent with the repository's real state. Unnecessary rules should be reviewed and removed.

## Subagents

A subagent receives a specific part of the work and has its own context.

Uses shown in the material include asking a subagent to explore the codebase or compare alternatives and then report a summary to the main agent.

Separating context prevents large explorations from consuming the space the main agent needs for requirements, decisions, and implementation.

Subagents therefore suit separable exploration or work, not every case of a large context. Their reports still need verification before use.

---

# 4. Core Workflow

Different types of uncertainty should be addressed by different steps:

- Unclear requirement → Grill
- Uncertain technical alternatives → Research
- Unknown UI or integration viability → prototype
- Large, multi-session work → PRD and plan
- Clearly defined work items → issue and Implement
- Existing code → Feedback and Review

Every task does not need every step. A bug fix or an extension of a well-understood component may not need Research or a prototype, while a new feature, external integration, or large effort may require more discovery and experimentation.

## 4.1 Grill

Grill uses questions to understand the problem and make design decisions.

Questions may cover:

- what each type of user may do;
- how the feature should appear;
- how deletion or editing behaves;
- the scope of V1;
- what is outside scope.

The agent should explore the codebase before asking the human about facts that can be discovered from the repository.

The result of Grill is a shared understanding of the problem and an initial direction before writing a PRD or beginning implementation.

The human should not merely pick from the agent's proposed answers. The human can challenge the alternatives. A useful V1 question is which option is easiest to reverse or extend later, avoiding complexity that is not yet necessary.

## 4.2 Research

Research applies when several technical alternatives exist, an external service is involved, or an expensive exploration would otherwise be repeated across sessions.

Research might compare polling, WebSockets, and external services against constraints such as scale, real-time requirements, managed-service preferences, and data shape.

The result is a document covering requirements, alternatives and trade-offs, a recommended approach, and implementation or integration points. It caches exploration so later sessions do not repeat the same search.

Research is HITL work: the agent searches and compares, while human judgment chooses the direction. For production work, important claims should be verified against primary sources.

Research documents also have a lifecycle. When an external service, SDK, or codebase changes, old research may become incorrect context. Temporary research that has no remaining value after implementation and QA can be removed because Git history still preserves it.

## 4.3 Prototype

A prototype turns an idea into something that can be tried and reviewed. Its goal is to eliminate unknowns and test important assumptions, not to complete the feature.

In the live-presence-indicator example, a separate throwaway route tested whether the integration and real-time behavior worked before entering the real implementation.

Testing through several browser sessions exposed behavior before production implementation began.

A prototype therefore suits uncertain UI, interaction, library, or integration questions. A bug fix or extension of a clearly understood component may not require it.

Even as an experiment, a prototype can use suitable feedback loops and code standards because a proven component or integration may inform the real implementation. Stop prototyping when the important assumptions are proven and the remaining work can proceed with confidence; carry the reusable knowledge or proven parts into implementation.

## 4.4 PRD

A PRD states what is being built, the problem, and the desired outcome.

It can contain:

- problem statement;
- solution;
- user stories;
- scope;
- implementation decisions;
- technical decisions;
- testing decisions;
- items outside scope.

The PRD anchors the goal so several sessions or agents continue toward the same outcome.

## 4.5 Plan

A plan divides the route from the PRD to implementation.

A multi-phase plan makes large work possible across context windows. Dividing by layer—analytics service, then dashboard component, then route—can delay the discovery of integration problems.

Tracer bullets and vertical slices instead let each phase connect several layers from the beginning.

After the PRD, the material shows two ways to organize work:

- **Multi-phase plan** — suitable for sequential phases in which every phase sees the complete PRD and plan and therefore avoids duplicating another phase's work.
- **Kanban/issues** — suitable when work must be added, reordered, or done independently. Issues declare dependencies such as `blocked by` and separate AFK work from HITL work.

Both can use vertical slices and tracer bullets. A plan and issues do not have to be layered on top of each other every time.

## 4.6 Issue

An issue is a backlog unit that an agent can pick up and perform.

When an agent is connected to GitHub Issues, it can read an issue, select work, implement it, commit, and report progress through comments or closure.

For a Kanban workflow, the final issue should be a manual QA plan containing the checks a human must perform after AFK work. Verification then belongs to the backlog from the start.

The roles are:

- **PRD** defines the goal and outcome.
- **plan** divides the route to the outcome.
- **issue** divides work into units that can be picked up.

## 4.7 Vertical Slice and Tracer Bullet

Layered work builds the database first, then the service, and finally the UI.

A vertical slice builds a small part across several layers from the beginning. A tracer bullet pushes one small path through the system to test whether the architecture and integration work.

In the instructor analytics dashboard example, the plan begins with an analytics service, instructor route, and summary cards using minimal data. It makes the path from data → service → route → UI work before adding charts, course breakdown, admin access, and empty states.

This produces earlier feedback and reveals integration or design problems before the rest is built.

Each phase should therefore end with a small, complete path that can actually be QA'd, rather than one layer that cannot yet be tried.

## 4.8 Implement

Implementation begins when the PRD, plan, or issue has a clear scope.

The agent reads the codebase, edits files, runs tests, verifies behavior, and commits the phase or issue.

Multi-phase work can use separate sessions while keeping the PRD and plan as the continuing reference.

### One Session per Phase

1. Create a PRD defining the goal and outcome.
2. Create a plan divided into phases.
3. Open a fresh session and provide the complete PRD and plan.
4. Ask the agent to perform only the current phase.
5. Run the repository's feedback loops and commit.
6. QA the phase result.
7. Start with fresh context, provide the same PRD and plan, and request the next phase.
8. Repeat until complete.

This is the demonstrated approach for multi-phase work, not a rule that every task needs a fresh session. A small task or feedback fix can continue in the same session while the context remains suitable.

## 4.9 Review

Review checks whether the implementation matches the goal and works in practice. The final workflow can be seen as:

**Implementation → Automated checks → Automated review → Human review**

- **Automated checks** use type checking, formatting, tests, and hooks for mechanically enforceable rules.
- **Automated review** uses an agent in fresh context to compare the diff with the PRD/spec and coding standards, addressing findings before handoff.
- **Human review** assesses product behavior, UX, taste, trade-offs, and final approval.

Checks include:

- whether behavior matches the PRD;
- whether acceptance criteria are complete;
- whether tests pass;
- whether coding standards are met;
- whether the UI behaves and renders correctly;
- whether other areas are affected.

Separating review from implementation reduces implementation-session load and lets the reviewer start with fresh context rather than inheriting the author's attachment to one approach.

---

# 5. Feedback Loop

The speed of code generation does not establish codebase quality. Faster generation must be paired with a system that can verify the result.

A feedback loop lets the agent observe the result of its work and use that result to improve the implementation.

The mechanisms in the material can be grouped as:

**Static feedback** — type checking, linting, and formatting
**Behavior feedback** — automated tests
**User-facing feedback** — browser testing and visual QA
**Process gates** — pre-commit, acceptance criteria, and review

## `do-work` Skill

The `do-work` skill combines planning, implementation, type checking, tests, and commit.

When a test fails, the agent must read the feedback and repair the implementation before continuing.

## Pre-commit

A pre-commit hook runs formatting, type checking, and tests before a commit. A failing test stops the commit.

## Red-Green-Refactor

Red-Green-Refactor consists of:

1. Write a test that does not yet pass.
2. Write the minimum implementation that makes it pass.
3. Refactor while keeping the test green.

This verifies implementation in pieces instead of postponing testing until everything is built.

Red-Green-Refactor can combine with a tracer bullet by building tests and implementation one vertical slice at a time rather than writing every test for a layer in advance.

---

# 6. HITL, AFK, and Sandboxing

## HITL

HITL, or Human In The Loop, describes work in which the human still participates in planning, decisions, and QA.

Human work includes:

- product direction;
- UX and taste;
- architectural trade-offs;
- choosing a Research direction;
- reviewing a prototype;
- QA;
- final review.

## AFK

AFK, or Away From Keyboard, lets an agent continue through a loop without a human issuing every instruction.

In the demonstrated workflow, the agent reads the PRD and plan, identifies the unfinished phase, implements, runs tests, and commits until it reaches a completion signal such as `no more tasks`.

AFK does not mean the agent has become more capable. It means the task and environment have enough structure for the agent to proceed. That structure includes a PRD, plan, feedback loop, completion signal, sandbox, and permissions.

## Sandboxing

Running an agent with bypassed permissions or in YOLO mode without a sandbox creates a risk of unintended deletion or data transmission.

A sandbox separates the agent from the main environment and limits the files or repositories it can access.

External connections such as GitHub require environment variables and tokens to be passed into the sandbox with appropriate permissions.

---

# 7. Roles of the Human and Agent

## Humans Suit

- product decisions;
- user experience;
- taste;
- architectural decisions;
- risk;
- choosing among Research alternatives;
- final review and approval.

## Agents Suit

- codebase exploration;
- code search;
- implementation;
- test creation;
- repetitive work;
- refactoring;
- work defined by an issue;
- verification through commands and tests.

This division separates work requiring judgment from labor and work with checkable feedback.

---

# 8. Designing Codebases for Humans and Agents

## Deep Module

A deep module has a small interface and hides complex implementation behind it.

When business logic is spread across several services, the agent must explore many relationships before understanding the system. Grouping related responsibilities in one module clarifies the boundary.

The quiz-subsystem example puts quiz, attempt, scoring, and XP logic inside a module with a clear interface and receives dependencies through a factory or injection.

The intended result is a shorter caller-facing interface and easier testing through the module boundary.

## ADR

An ADR records the reasoning and trade-offs behind an architectural decision.

Code and commit history show system state but do not always explain why an approach was chosen. An ADR preserves information the agent cannot derive directly from the current code.

## `context.md`

`context.md` records domain-specific vocabulary and knowledge, including the meaning of system terms and concepts that cannot be inferred from code.

This helps Grill and PRD work use the same language.

## Module Awareness

Refactoring one troubled module does not automatically prevent the same problem in the next feature.

Module awareness in the PRD skill makes planning consider major modules and possible deep-module seams from the beginning.

---

# 9. Greenfield Projects

A greenfield project has no existing codebase to explore and no established testing or feedback loop.

The project must therefore establish items such as:

- language and tools;
- testing strategy;
- module shape;
- coding standards;
- hooks;
- feedback loop;
- domain-knowledge documentation.

It can then enter the workflow:

**Grill → Research → prototype → PRD → plan/issues → Implement → Review**

---

# 10. Decision Guide

- **Is the problem unclear or are details still undecided?**
  → Grill first.

- **Is a technology or external service uncertain?**
  → Research the alternatives.

- **Is it unknown whether a UI or integration works in practice?**
  → Build a prototype.

- **Is the work large and spread across sessions?**
  → Write a PRD and divide it into a plan.

- **Has the work been divided into clear pieces?**
  → Create or select an issue and let the agent implement it.

- **Is part of the work separable exploration?**
  → Use a subagent to keep exploration out of the main context.

- **Is the agent's context becoming large or accumulated?**
  → Consider a fresh session or separate the relevant exploration.

- **Does code exist without evidence that it is correct?**
  → Use tests, type checking, validation, and review.

- **Should the agent continue without instruction at every step?**
  → Check scope, acceptance criteria, feedback loop, completion signal, sandbox, and permissions before AFK work.

---

# 11. One-page Cheat Sheet

## Mental Model

**Task Context** — the current session's work and information
**Project Instructions** — repository rules
**skills** — task-specific methods loaded when needed
**Codebase** — the system's real state
**Feedback** — results from tests, checks, commands, and review

## Core Workflow

**Grill** — clarify the problem
**Research** — compare alternatives
**prototype** — test an idea
**PRD** — define the goal and scope
**plan** — divide the route
**issue** — divide the work
**Implement** — do the work
**Review** — verify the result

## Feedback Loop

**Write → check → receive feedback → fix → check again**

## HITL and AFK

**HITL** — the human still participates in planning, decisions, and QA
**AFK** — the agent continues through a loop within a defined scope, feedback system, and environment

## Codebase

- Clear interfaces
- Business logic is not scattered
- Modules have boundaries
- Decision reasoning is recorded
- Domain vocabulary has documentation

---

# Source Map

- System preparation and Claude Code — episodes 001–014
- Context, Compact, and Handoff — episodes 015–023, 026–027, 035–036, 044–045
- Project Instructions, Progressive Disclosure, skills, and Memory — episodes 028–035
- PRD, plan, issues, Kanban, and Tracer Bullets — episodes 036–046, 066–074
- Feedback Loops and Red-Green-Refactor — episodes 049–058
- HITL, AFK, and Sandboxing — episodes 059–070
- Research and prototype — episodes 075–081
- Deep Modules, ADR, `context.md`, and Greenfield — episodes 082–088
- Quality, CI, and Automated Review — episodes 089–092
