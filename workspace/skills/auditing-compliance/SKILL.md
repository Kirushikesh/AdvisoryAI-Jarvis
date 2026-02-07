---
name: auditing-compliance
description: Audits financial advice (emails/reports) for UK Consumer Duty compliance, risk warnings, and vulnerability handling. Use BEFORE sending any draft to a client.
---

# Auditing Compliance

## Audit Process
To audit a draft, follow these steps strictly. If any step fails, return a "FAIL" status with specific fix instructions.

### Step 1: Check Prohibited Terminology
Run this grep command to catch immediate regulatory red flags (Promissory Language):
```bash
grep -iE "guaranteed|will return|promise|safe investment|no risk" <file_path>
```
If matches are found, fail immediately citing "Promissory Language Risk".

### Step 2: Consumer Duty Assessment
Read ./CONSUMER_DUTY.md. Compare the draft against the "Cross-Cutting Rules".

Does it avoid causing foreseeable harm?

Is the pricing/value clear?

### Step 3: Vulnerability Check
If the client context indicates vulnerability (age >75, health issues, recent bereavement), read ./VULNERABILITY_GUIDE.md.

Does the draft meet the "Clear Communications" guidelines for vulnerable clients?
