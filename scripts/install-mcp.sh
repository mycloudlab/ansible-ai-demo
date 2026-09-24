#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
mcp_dir="${MCP_INSTALL_DIR:-$HOME/.local/share/caixa-ai-demo/aap-mcp-server}"
mkdir -p "$(dirname "$mcp_dir")"
if [[ ! -d "$mcp_dir/.git" ]]; then git clone https://github.com/ansible/aap-mcp-server.git "$mcp_dir"; fi
cd "$mcp_dir"
git checkout 1108adb8309fb4da566285479a11c0b9f0f90469
# Upstream currently binds all interfaces; restrict this workshop bridge to loopback.
python3 - <<'PYTHON'
from pathlib import Path
p=Path('src/index.ts');s=p.read_text();s=s.replace('app.listen(PORT, () => {','app.listen(PORT, "127.0.0.1", () => {');p.write_text(s)
PYTHON
npm ci --ignore-scripts
npm run build
cp "$repo_root/config/aap-mcp.yaml" aap-mcp.yaml
mkdir -p "$HOME/.config/systemd/user"
node_bin="$(command -v node)"
cat > "$HOME/.config/systemd/user/caixa-demo-mcp.service" <<UNIT
[Unit]
Description=CAIXA demo official AAP MCP bridge (loopback)
[Service]
WorkingDirectory=$mcp_dir
ExecStart=$node_bin $mcp_dir/dist/index.js
Environment=MCP_PORT=3017
Environment=ALLOW_WRITE_OPERATIONS=true
Restart=on-failure
NoNewPrivileges=true
[Install]
WantedBy=default.target
UNIT
systemctl --user daemon-reload
systemctl --user enable --now caixa-demo-mcp.service
