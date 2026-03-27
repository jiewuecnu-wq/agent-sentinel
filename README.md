# agent-sentinel

**A lightweight verification layer for agent actions under ambiguous grounding.**

---

## The Problem

Agents often fail **not because an action is obviously unsafe**,  
but because it is grounded to the **wrong entity**.

Examples:
- Sending a message to the wrong *John*
- Sharing a document with the wrong contact
- Deleting the wrong email thread

These actions look perfectly valid at the API level,  
yet can still cause costly mistakes.

Traditional safeguards focus on:
- permission control
- sandboxing
- explicit confirmations

But they miss a critical issue:

> **The agent may not know what it is actually acting on.**

---

## Core Idea

Before executing an external action, an agent should verify:

1. **What entity is this action targeting?**
2. **Is the grounding ambiguous?**
3. **Does the current context increase risk?**

Based on this, the system decides:

- ✅ **Allow** — safe and unambiguous  
- ❓ **Clarify** — entity is ambiguous, needs disambiguation  
- ⛔ **Block** — high-risk or inconsistent with context  

---

## Example

User instruction:

> "Send John a quick update that the meeting moved to 3pm."

System state:

- Multiple contacts named *John*
- One is CEO, one is teammate, one is external lawyer
- Recent context includes sensitive project information

Instead of executing immediately, the system may:

- ❓ Clarify: *"Do you mean John Chen (teammate) or John Smith (CEO)?"*
- ⛔ Block: if sensitive content is being sent externally

---

## What This Is (and Isn't)

**This is NOT:**
- a traditional entity linking system
- a static knowledge graph application
- a generic safety wrapper

**This IS:**
- a verification layer for **agent actions**
- a system for handling **ambiguous grounding at execution time**
- a decision engine for **allow / clarify / block**

Entity linking and knowledge graphs are **enabling components**,  
not the end goal.

---

## Scope (v0)

The initial version focuses on:

- message / email recipient verification
- small-scale personal world modeling
- lightweight grounding + rule-based reasoning

Future versions may extend to:
- file sharing
- tool chains
- cross-step action verification

---

## Why It Matters

In many real-world scenarios, the most dangerous failures are:

> **Silent failures that look correct, but act on the wrong entity.**

Reducing these failures requires more than permission checks —  
it requires **grounded understanding at action time**.

---

## Status

🚧 Early prototype (v0)  
Focused on minimal working example and core decision flow.

---

## License

MIT
