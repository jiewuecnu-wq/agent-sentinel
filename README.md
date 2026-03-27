# agent-sentinel

**A lightweight verification layer for agent actions under ambiguous grounding.**

---

## Motivation

Agents often fail not because an action is obviously unsafe,  
but because they execute actions on the **wrong targets under ambiguous grounding**.

These failures are subtle:
- Sending a message to the wrong contact  
- Sharing a file with the wrong recipient  
- Acting on the wrong thread or resource  

From the system's perspective, these actions appear valid.  
From the user's perspective, they are costly mistakes.

---

## The Problem

This is not merely an entity recognition or linking problem.

The core challenge is:

> **How should an agent decide whether to execute an action when the target is ambiguous and the context is incomplete?**

At the moment of execution, the agent must reason about:
- what the action is actually targeting  
- whether the grounding is uncertain  
- whether the current context increases risk  

This turns the problem into **action-time verification under uncertainty**,  
rather than static entity resolution.

---

## Core Idea

Before executing any external action, the system performs a verification step:

- Identify candidate targets from the agent's internal world
- Evaluate ambiguity and contextual consistency
- Estimate potential risk given current session state

Then decide:

- ✅ **Allow** — target is clear and consistent  
- ❓ **Clarify** — ambiguity is present, needs disambiguation  
- ⛔ **Block** — action is high-risk or contextually inconsistent  

---

## Key Insight

The most dangerous failures in agent systems are often **silent failures**:

> Actions that look correct, but operate on the wrong target.

Preventing these failures requires more than permissions or sandboxing.  
It requires **grounded verification at the moment of action**.

---

## What This Is (and Isn't)

**This is NOT:**
- a traditional entity linking system  
- a static knowledge graph application  
- a rule-based safety filter  

**This IS:**
- a verification layer for agent actions  
- a system for handling ambiguity at execution time  
- a decision engine for **allow / clarify / block**  

Entity linking and knowledge graphs are **supporting components**,  
not the problem definition.

---

## Scope (v0)

The initial version focuses on:

- recipient verification for messaging/email actions  
- lightweight personal world modeling  
- minimal grounding + decision logic  

Future directions include:
- file sharing and data flow verification  
- multi-step action chains  
- context-aware risk propagation  

---

## Status

🚧 Early prototype focused on minimal working example.
