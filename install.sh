#!/usr/bin/env bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Ollama Smart Context Manager — Installer
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_TARGET="$HOME/.local/bin/ollama-pm"
CONTINUE_CONFIG_DIR="$HOME/.continue"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " 🤖 Ollama Smart Context Manager Installer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. Check ollama
if ! command -v ollama &>/dev/null; then
    echo "⚠️  Ollama not found. Install from: https://ollama.com"
    echo "   Then run this installer again."
    exit 1
fi
echo "✅ Ollama found: $(ollama --version 2>/dev/null | head -1)"

# 2. Check python3
if ! command -v python3 &>/dev/null; then
    echo "❌ Python 3 required. Install: sudo apt install python3"
    exit 1
fi
echo "✅ Python: $(python3 --version)"

# 3. Install ollama-pm CLI
mkdir -p "$HOME/.local/bin"
cat > "$BIN_TARGET" << EOF
#!/usr/bin/env bash
python3 "$REPO_DIR/scripts/ollama_plugin_manager.py" "\$@"
EOF
chmod +x "$BIN_TARGET"
echo "✅ Installed: ollama-pm → $BIN_TARGET"

# 4. Add to PATH if needed
if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
    echo ""
    echo "⚠️  Add to your shell config (~/.bashrc or ~/.zshrc):"
    echo '   export PATH="$HOME/.local/bin:$PATH"'
    echo ""
    # Auto-add if bash
    if [ -f "$HOME/.bashrc" ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
        echo "✅ Auto-added to ~/.bashrc"
    fi
fi

# 5. Continue.dev config (optional)
echo ""
read -r -p "📝 Set up Continue.dev config? [y/N] " SETUP_CONTINUE
if [[ "$SETUP_CONTINUE" =~ ^[Yy]$ ]]; then
    if [ -f "$CONTINUE_CONFIG_DIR/config.json" ]; then
        cp "$CONTINUE_CONFIG_DIR/config.json" "$CONTINUE_CONFIG_DIR/config.json.bak"
        echo "   Backed up existing config → config.json.bak"
    fi
    mkdir -p "$CONTINUE_CONFIG_DIR"
    cp "$REPO_DIR/continue-config/config.json" "$CONTINUE_CONFIG_DIR/config.json"
    echo "✅ Continue.dev config installed"
fi

# 6. Ask base model
echo ""
echo "📦 Available Ollama models:"
ollama list 2>/dev/null || echo "   (none yet — run: ollama pull llama3.2)"
echo ""
read -r -p "🤖 Which base model to use? [llama3.2] " BASE_MODEL
BASE_MODEL="${BASE_MODEL:-llama3.2}"
python3 "$REPO_DIR/scripts/ollama_plugin_manager.py" set-base "$BASE_MODEL"

# 7. Build lean base model
echo ""
echo "🔨 Building lean 'smart-assistant' model (no plugins)..."
python3 "$REPO_DIR/scripts/ollama_plugin_manager.py" build

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Installation complete!"
echo ""
echo "Quick start:"
echo "  ollama-pm list              # See all plugins"
echo "  ollama-pm enable coding     # Enable coding mode"
echo "  ollama-pm enable web-dev    # Enable web dev mode"
echo "  ollama-pm show-tokens       # See token savings"
echo "  ollama-pm reset             # Back to lean mode"
echo ""
echo "Continue.dev / Ollama Desktop: use model 'smart-assistant'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
