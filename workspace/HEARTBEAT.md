# HEARTBEAT INSTRUCTIONS

You are running a scheduled check. Your goal is to be proactive but unintrusive.

## Timing
- If it's between 23:00-08:00, only report truly urgent items.
- During work hours, be thorough.

## 1. File Monitoring
- Check the `datasets/` folder for any new files `meeting_transcripts/` that look recent or unprocessed.
- Use the email tool to check for any new emails that look recent or unprocessed.
- Use `find_files_updated_after` to check for recently added files.
- If you find relevant new files, read them to understand the context.

## 2. Market & Compliance Check
- The goal during the heartbeat is to check recent news and market data, and act on top of that to check on your clients.
- Use the following tools to gather market intelligence:
    - `get_macro_indicators` to check macro-economic indicators (e.g., interest rates, inflation).
    - `search_financial_news` to search for recent UK Financial Market news (last 24h) and UK Compliance/Regulatory news.
    - `get_asset_performance` to check performance snapshots for relevant client assets, funds, or indices.

## 3. Analysis (Atlas)
- If you find significant news OR new client files, ask **Atlas** to analyze the impact on your clients.
- Query Atlas specifically about the new information.

## 4. CRM Updates
- If Atlas identifies a material impact or new client information (e.g., "Client X is interested in Retirement"), update the relevant client's `crm.json` file in their folder (e.g., `datasets/alan_partridge/crm.json`).
- **CRITICAL**: Only update if you are confident. If unsure, ask the user first.

## 5. Reporting
- If you updated the CRM or found urgent news, generate a concise report for the Advisor.
- If **NO** significant action was taken and no urgent news found, simply output `NO_REPLY`. Do not say "I checked and found nothing". Just `NO_REPLY`.

## 6. Self-Correction
- If you find these instructions unclear or needing adjustment based on your experience, you are authorized to update this file (`HEARTBEAT.md`) with better instructions for your future self.

If something **does** need attention, you MUST take action by calling the appropriate tool:
- Use `send_important_notification` to push an urgent alert to the advisor's dashboard.
- Use `send_draft_email` to create a draft email for the advisor to review and approve before sending.(After getting emma subagent approval on the draft email)

Do NOT simply reply with alert text because the heartbeat response will not be sent to the advisor, the advisor can only see the draft emails and the notifications. So make sure to call these tools to notify the advisor only if something is important.