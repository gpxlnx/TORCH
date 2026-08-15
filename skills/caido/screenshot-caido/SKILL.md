---
name: screenshot-caido
description: Capture a Caido HTTP History or Replay request and response as a report-ready PoC image under targets/<eng>/poc/. Use after a Caido replay, edit, or send returns a request ID that proves an in-scope finding.
---

# Capture Caido evidence

Render the exact request and response stored by Caido, while retaining the named
Replay session for interactive operator review.

## Capture

Get the request ID from `edit`, `replay`, `send-raw`, or `caido-hunt.sh`, then run:

```bash
bash scripts/capture.sh caido <eng> <slug> <request-id> [highlight-regex]
```

The command:

1. Fetches the complete exchange through `scripts/caido/caido-client.sh`.
2. Renders a deterministic request/response card with `shot.py` on Kali.
3. Saves `targets/<eng>/poc/NN-<slug>.png`.
4. Prints the Markdown reference for `walkthrough.md`.

Use a narrow highlight regex for the proof string, such as a changed user ID,
privileged field, flag, or command output. Never highlight an expected value that
does not actually appear in the captured response.

## Preconditions and failure handling

- Confirm `bash scripts/caido/caido-transport.sh` returns `native` or `sdk`.
- Confirm the request ID belongs to the active engagement and remains in scope.
- If the request has no response, replay it through Caido first and capture the new
  request ID.
- Do not substitute a synthetic request. Evidence must come from the stored Caido
  exchange that established the result.

## Boundary

Request and response bodies may contain credentials, tokens, and PII. Keep images
under the engagement directory, run `Skill(evidence)` before reporting, and never
embed client traffic in the shared wiki.

Report the saved PNG path, its Markdown reference, the Caido request ID, and the
Replay session name when available.
