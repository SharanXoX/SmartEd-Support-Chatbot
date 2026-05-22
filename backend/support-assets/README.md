# Adaptive support assets

Add a new support category by creating a folder only — **no backend code changes**.

```
support-assets/
└── your_issue_type/
    ├── metadata.json      # required (keywords, title, description)
    ├── steps.json         # optional (step text + image filenames)
    ├── step1.png
    ├── step2.png
    └── step3.png
```

## metadata.json

```json
{
  "title": "Refund Requests",
  "keywords": ["refund", "money back", "cancel order"],
  "description": "Help users request refunds",
  "intro": "Here's how to start a refund:",
  "suggested_replies": ["How long do refunds take?"]
}
```

## steps.json (optional)

```json
[
  { "image": "step1.png", "text": "Open Billing → Refunds" },
  { "image": "step2.png", "text": "Select the charge and submit" }
]
```

If `steps.json` is omitted, the indexer auto-detects `step1.png`, `step2.png`, … and generates short placeholder text.

After adding folders, restart the API or call `POST /api/admin/support/reindex` (admin auth).
