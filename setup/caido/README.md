# Caido on the Kali tooling VM

Run Caido on Kali so Replay, Automate, the proxied browser, and direct sends use
the same VPN and target routes as the rest of TORCH.

## Kali

1. Install and start Caido as the graphical seat user.
2. Keep the Caido API on `127.0.0.1:8080`; do not expose it to the LAN.
3. Create a Personal Access Token under Dashboard > Developer.
4. Configure Chromium to use Caido's HTTP proxy and install Caido's CA certificate
   in the isolated browser profile used for testing.
5. Install and enable the Caido MCP server you use with Claude. Restart the Claude
   session after adding it because MCP tools are attached at session start.

## Debian host

Forward the loopback API through SSH:

```bash
ssh -N -L 127.0.0.1:8080:127.0.0.1:8080 gxavier@KALI_IP
```

Then configure the SDK fallback. Do not put the PAT in the repository:

```bash
bash scripts/caido/caido-client.sh setup <PAT> http://127.0.0.1:8080
bash scripts/caido/caido-client.sh health
bash scripts/caido/caido-transport.sh
```

The preferred transport is native `mcp__caido__*`. The SDK client remains the
deterministic shell fallback for scripts, tests, and sessions where MCP was not
attached.

## TORCH workflow

```bash
python3 scripts/caido/caido-scope-sync.py <eng>
bash scripts/caido/caido-client.sh recent --limit 5
bash scripts/capture.sh caido <eng> <slug> <request-id>
```

Use interactsh/OAST for blind callbacks. Caido scope is a second safety boundary;
`scope.md` and the TORCH scope guard remain authoritative.
