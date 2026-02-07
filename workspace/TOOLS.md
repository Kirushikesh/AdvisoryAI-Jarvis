# TOOLS.md - Tool Usage Guide

This file describes **when and how** to use your tools effectively. Tool definitions are already provided to you — this is about best practices.

## Sub-Agents

### Atlas (RAG Analysis)
**When to use:**
- Querying client history, meeting notes, or email context
- Finding relevant documents about a specific client or topic
- Answering questions that require client-specific knowledge

**Best practices:**
- Be specific in your queries: "What did Alan Partridge say about retirement?" beats "client info"
- Use for fact-finding, not decision-making
- Combine with market news for impact analysis

### Emma (Paraplanner)
**When to use:**
- Drafting client emails, letters, or recommendation summaries
- Converting raw analysis into professional documents
- Creating polished outputs from Atlas findings

**Best practices:**
- Always provide Emma with context (client name, purpose, tone)
- Review her output before sending — she drafts, you approve
- Use for structure and polish, not for compliance review

### Colin (Compliance)
**When to use:**
- Before sending ANY client-facing document
- When drafting investment recommendations
- If you're uncertain about regulatory requirements

**Best practices:**
- Send Colin the full document, not just snippets
- His PASS/FAIL is advisory — escalate to Abi if unsure
- Use proactively, not as an afterthought

## Direct Tools

### get_market_news
**When:** Checking latest financial news, compliance updates, market movements
**Tip:** Search specific topics: "UK FCA regulations" > "news"

### find_files_updated_after
**When:** During heartbeats to check for new client documents
**Tip:** Use with specific directories like `datasets/alan_partridge/email_archive/`

### Cron Tools (add_cron_job, list_cron_jobs, etc.)
**When:** Setting up scheduled tasks, reminders, or recurring reports
**Tip:** Use for precise timing. Use heartbeat for batched periodic checks.

## File System (Built-in)

### read, ls, write
**When:** Accessing workspace files, updating CRM, reading prompts
**Best practices:**
- Always read before writing (don't overwrite important data)
- Use relative paths within workspace
- Update memory files after significant actions

## Decision Tree

```
Need client info?        → Atlas
Need to draft document?  → Emma → Colin → Send
Market/news check?       → get_market_news
Scheduled task?          → Cron tools
Workspace files?         → read/write/ls
```

---

_Update this as you learn which tool combinations work best._
