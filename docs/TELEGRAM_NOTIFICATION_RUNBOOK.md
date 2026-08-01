# Exact morning Telegram receipt runbook

Status: approved for production cutover
Owner: David Friedhof
Runtime: `telegram-publication-receipt` in `.github/workflows/ddb-bake.yml`

## Product boundary

The receipt is a private notification after a successful morning publish. Its
only source is the one `archive.json` entry whose date, `morning` slot, and
`editions/YYYY-MM-DD-morning.html` file all match the workflow inputs. The
adapter includes the exact archive lead and canonical URL. It does not use an
AI model, choose the newest available entry, or fall back to a prior date.

The separate Spark watchdog is allowed to send a not-ready alert after the
morning deadline only when that exact entry is absent. It must not include an
older edition's stories or describe an older edition as current.

## Credential and enablement boundary

The protected `telegram-notification-production` GitHub environment is limited
to `main` and owns:

- secrets `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`;
- variable `DDB_TELEGRAM_NOTIFY_ENABLED`, which must be exactly `true` to send;
- variable `DDB_TELEGRAM_NOTIFY_KILL_SWITCH`, which must be exactly `false` to
  permit credentials to load. Missing or any other value keeps the switch on.

The bake job and editorial model never receive Telegram credentials. The
notification job has only `actions: read` and `contents: read`. Never place the
bot token in workflow inputs, repository files, prompts, artifacts, or logs.

## Preview and activation

Preview an exact archived package without provider access:

```bash
python3 distribution/telegram_notification.py preview \
  --archive archive.json --date YYYY-MM-DD --slot morning
```

Before activation, keep the kill switch on. Confirm the environment branch
policy, secrets, variables, test results, and preview. Then set enablement to
`true` and the kill switch to `false`. The next eligible date after the cutover
watermark is `2026-08-02-morning`; the reported August 1 message cannot be sent
again by this adapter.

## Duplicate and failure behavior

Before credentials load, the job checks committed reconciliation state and
non-expired Actions receipt and reservation artifacts. It uploads a durable
reservation before calling Telegram. A receipt is success only when Telegram
returns a positive message ID, the configured chat ID, and the exact text.

The adapter performs no automatic POST retries. A timeout, network loss, 5xx,
unreadable success response, wrong recipient, or wrong text writes a blocking
`needs_reconciliation` receipt. Inspect Telegram and the redacted workflow
artifacts before clearing a block. Clear only a proven non-delivery by a
reviewed pull request adding the exact remote artifact ID to
`clearedRemoteArtifactIds`; never delete evidence merely to force a retry.

The site remains published if notification fails. The Daily bake run fails
visibly after preserving the attempt and receipt evidence.

## Emergency disable

1. Set `DDB_TELEGRAM_NOTIFY_KILL_SWITCH=true`.
2. If credentials may be exposed, revoke the bot token with BotFather and
   replace the environment secret.
3. Preserve the workflow URL, edition ID, reservation, attempt, receipt, and
   commit SHA.
4. Determine whether Telegram accepted the message before any retry.
5. Merge a tested forward fix before reenabling.
