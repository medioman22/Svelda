# ecom-founder-os

LangGraph-based multi-agent ecommerce operating system (dry-run only).

## Requirements

- Python 3.10+
- An OpenAI API key is optional; the system runs in deterministic dry-run mode without it.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python -m app.main
```

## Demo transcript

```
$ python -m app.main
Ecom Founder OS (dry-run). Type your request.
> Draft a promo for our summer bundles and update the homepage banner

Approval Required:
{
  "gated_risks": [
    "external_message",
    "site_change"
  ],
  "summary": "Approval required for actions touching sensitive areas.",
  "plan": {
    "constraints": [
      "Dry-run only"
    ],
    "decisions_needed": [
      "Approval for outreach and pricing review"
    ],
    "intent": "Support request: Draft a promo for our summer bundles and update the homepage banner",
    "missing_info": [
      "Target audience"
    ],
    "plan": [
      "Clarify goals and constraints",
      "Draft channel-specific actions",
      "Collect approvals for risky actions"
    ],
    "proposed_actions": [
      {
        "action": "Draft customer outreach message",
        "risk_type": "external_message"
      },
      {
        "action": "Evaluate pricing update",
        "risk_type": "price_change"
      }
    ]
  },
  "specialists": [
    {
      "draft_steps": [
        "Review constraints",
        "Draft recommended actions",
        "Flag risks for approval"
      ],
      "risks": [
        "external_message",
        "site_change"
      ],
      "role": "ExecutiveAssistant",
      "summary": "ExecutiveAssistant prepared a dry-run draft for: Draft a promo for our summer bundles and update the homepage banner"
    }
  ]
}
Approve? (yes/no): yes

Wrapup Summary:
{"approved":true,"decisions":["Approval for outreach and pricing review"],"execution_log":["Dry-run execution only. No external systems contacted.","Approved: True","Plan JSON: {\"constraints\":[\"Dry-run only\"],\"decisions_needed\":[\"Approval for outreach and pricing review\"],\"intent\":\"Support request: Draft a promo for our summer bundles and update the homepage banner\",\"missing_info\":[\"Target audience\"],\"plan\":[\"Clarify goals and constraints\",\"Draft channel-specific actions\",\"Collect approvals for risky actions\"],\"proposed_actions\":[{\"action\":\"Draft customer outreach message\",\"risk_type\":\"external_message\"},{\"action\":\"Evaluate pricing update\",\"risk_type\":\"price_change\"}]}","Specialist draft: {\"draft_steps\":[\"Review constraints\",\"Draft recommended actions\",\"Flag risks for approval\"],\"risks\":[\"external_message\",\"site_change\"],\"role\":\"ExecutiveAssistant\",\"summary\":\"ExecutiveAssistant prepared a dry-run draft for: Draft a promo for our summer bundles and update the homepage banner\"}","Specialist draft: {\"draft_steps\":[\"Review constraints\",\"Draft recommended actions\",\"Flag risks for approval\"],\"risks\":[\"external_message\",\"site_change\"],\"role\":\"Webmaster\",\"summary\":\"Webmaster prepared a dry-run draft for: Draft a promo for our summer bundles and update the homepage banner\"}","Specialist draft: {\"draft_steps\":[\"Review constraints\",\"Draft recommended actions\",\"Flag risks for approval\"],\"risks\":[\"external_message\",\"site_change\"],\"role\":\"CreativeDirector\",\"summary\":\"CreativeDirector prepared a dry-run draft for: Draft a promo for our summer bundles and update the homepage banner\"}","Specialist draft: {\"draft_steps\":[\"Review constraints\",\"Draft recommended actions\",\"Flag risks for approval\"],\"risks\":[\"external_message\",\"site_change\"],\"role\":\"SupplyManager\",\"summary\":\"SupplyManager prepared a dry-run draft for: Draft a promo for our summer bundles and update the homepage banner\"}"],"intent":"Support request: Draft a promo for our summer bundles and update the homepage banner","next_steps":["Collect missing info","Schedule follow-up"]}
```
