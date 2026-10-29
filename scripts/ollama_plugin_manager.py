#!/usr/bin/env python3
"""
Ollama Smart Context Manager
━━━━━━━━━━━━━━━━━━━━━━━━━━━
Reduces token/context usage by loading system prompt "plugins"
only when needed — then creating a focused Ollama model on-the-fly.

Works with: Ollama Desktop, Continue.dev, Open WebUI, Aider, CLI

Usage:
  ollama-pm enable coding          # Enable coding plugin
  ollama-pm enable web-dev data-science   # Enable multiple
  ollama-pm disable coding         # Disable one plugin
  ollama-pm list                   # Show active plugins
  ollama-pm status                 # Show current model info
  ollama-pm build                  # Build model with active plugins
  ollama-pm reset                  # Reset all, use base model
  ollama-pm show-tokens            # Estimate token cost of active plugins
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
PLUGINS_DIR = BASE_DIR / "plugins"
MODELFILES_DIR = BASE_DIR / "modelfiles"
STATE_FILE = Path.home() / ".ollama_pm_state.json"
CONTINUE_CONFIG = Path.home() / ".continue" / "config.json"

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_BASE_MODEL = "llama3.2"   # Change to your preferred model
MANAGED_MODEL_NAME = "smart-assistant"  # The model we create/update


# ── State management ──────────────────────────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"active_plugins": [], "base_model": DEFAULT_BASE_MODEL}


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ── Plugin loading ────────────────────────────────────────────────────────────
def get_available_plugins() -> list[str]:
    if not PLUGINS_DIR.exists():
        return []
    return [
        d.name for d in PLUGINS_DIR.iterdir()
        if d.is_dir() and (d / "plugin.json").exists()
    ]


def load_plugin_meta(plugin_name: str) -> dict:
    meta_file = PLUGINS_DIR / plugin_name / "plugin.json"
    if not meta_file.exists():
        print(f"❌ Plugin '{plugin_name}' not found!")
        sys.exit(1)
    with open(meta_file) as f:
        return json.load(f)


def load_plugin_prompt(plugin_name: str) -> str:
    prompt_file = PLUGINS_DIR / plugin_name / "system_prompt.md"
    if not prompt_file.exists():
        return ""
    return prompt_file.read_text().strip()


def estimate_tokens(text: str) -> int:
    """Rough estimate: ~4 chars per token (good enough for comparison)."""
    return len(text) // 4


# ── Modelfile builder ─────────────────────────────────────────────────────────
def build_modelfile(base_model: str, active_plugins: list[str]) -> str:
    base_prompt_file = MODELFILES_DIR / "base_system_prompt.md"
    base_prompt = base_prompt_file.read_text().strip() if base_prompt_file.exists() else ""

    sections = [base_prompt] if base_prompt else []
    for plugin in active_plugins:
        prompt = load_plugin_prompt(plugin)
        if prompt:
            meta = load_plugin_meta(plugin)
            sections.append(f"## {meta.get('name', plugin)}\n{prompt}")

    combined_system = "\n\n---\n\n".join(sections)

    modelfile = f'FROM {base_model}\n\nSYSTEM """\n{combined_system}\n"""\n'

    # Add performance parameters
    modelfile += "\nPARAMETER temperature 0.7\n"
    modelfile += "PARAMETER num_ctx 4096\n"

    return modelfile


def create_ollama_model(modelfile_content: str, model_name: str) -> bool:
    """Write Modelfile and call ollama create."""
    tmp_modelfile = Path("/tmp/Modelfile.smart")
    tmp_modelfile.write_text(modelfile_content)

    print(f"🔨 Building Ollama model '{model_name}'...")
    result = subprocess.run(
        ["ollama", "create", model_name, "-f", str(tmp_modelfile)],
        capture_output=True, text=True
    )

    if result.returncode == 0:
        print(f"✅ Model '{model_name}' ready!")
        return True
    else:
        print(f"❌ Failed to create model:\n{result.stderr}")
        return False


def update_continue_config(model_name: str):
    """Update Continue.dev config to use the new model."""
    if not CONTINUE_CONFIG.exists():
        return

    try:
        with open(CONTINUE_CONFIG) as f:
            config = json.load(f)

        # Update first Ollama model entry, or add one
        updated = False
        for model in config.get("models", []):
            if model.get("provider") == "ollama":
                old = model.get("model", "")
                model["model"] = model_name
                model["title"] = f"Smart Assistant ({model_name})"
                print(f"🔄 Continue.dev: updated model {old!r} → {model_name!r}")
                updated = True
                break

        if not updated:
            config.setdefault("models", []).insert(0, {
                "title": f"Smart Assistant ({model_name})",
                "provider": "ollama",
                "model": model_name
            })
            print(f"➕ Continue.dev: added model '{model_name}'")

        with open(CONTINUE_CONFIG, "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"⚠️  Could not update Continue.dev config: {e}")


# ── Commands ──────────────────────────────────────────────────────────────────
def cmd_enable(plugins: list[str], auto_build: bool = True):
    state = load_state()
    active = set(state["active_plugins"])
    available = get_available_plugins()

    for plugin in plugins:
        if plugin not in available:
            print(f"❌ Unknown plugin: '{plugin}'. Available: {', '.join(available)}")
            continue
        if plugin in active:
            print(f"ℹ️  '{plugin}' already active.")
        else:
            meta = load_plugin_meta(plugin)
            active.add(plugin)
            tokens = estimate_tokens(load_plugin_prompt(plugin))
            print(f"✅ Enabled: {meta['name']} (~{tokens} tokens)")

    state["active_plugins"] = sorted(active)
    save_state(state)

    if auto_build and active:
        cmd_build(silent=False)


def cmd_disable(plugins: list[str], auto_build: bool = True):
    state = load_state()
    active = set(state["active_plugins"])

    for plugin in plugins:
        if plugin not in active:
            print(f"ℹ️  '{plugin}' was not active.")
        else:
            active.discard(plugin)
            print(f"🚫 Disabled: '{plugin}'")

    state["active_plugins"] = sorted(active)
    save_state(state)

    if auto_build:
        cmd_build(silent=False)


def cmd_list():
    state = load_state()
    available = get_available_plugins()
    active = set(state["active_plugins"])

    print(f"\n📦 Ollama Smart Context Manager")
    print(f"   Base model : {state['base_model']}")
    print(f"   Output model: {MANAGED_MODEL_NAME}\n")

    print("Available plugins:")
    for name in sorted(available):
        meta = load_plugin_meta(name)
        tokens = estimate_tokens(load_plugin_prompt(name))
        status = "✅ ON " if name in active else "⭕ OFF"
        print(f"  {status}  {meta['name']:<20} ~{tokens:>4} tokens  — {meta.get('description', '')}")

    total = sum(estimate_tokens(load_plugin_prompt(p)) for p in active)
    base_tokens = estimate_tokens(
        (MODELFILES_DIR / "base_system_prompt.md").read_text()
        if (MODELFILES_DIR / "base_system_prompt.md").exists() else ""
    )
    print(f"\n💰 Active context cost: ~{base_tokens + total} tokens "
          f"(base={base_tokens} + plugins={total})")


def cmd_status():
    state = load_state()
    print(f"\n🤖 Current model : {MANAGED_MODEL_NAME}")
    print(f"📌 Base model    : {state['base_model']}")
    print(f"🔌 Active plugins: {', '.join(state['active_plugins']) or 'None (lean base mode)'}")
    cmd_show_tokens()


def cmd_build(silent: bool = False):
    state = load_state()
    modelfile = build_modelfile(state["base_model"], state["active_plugins"])

    # Save for inspection
    out = MODELFILES_DIR / "current.Modelfile"
    out.write_text(modelfile)
    if not silent:
        print(f"📄 Modelfile saved to: {out}")

    success = create_ollama_model(modelfile, MANAGED_MODEL_NAME)
    if success:
        update_continue_config(MANAGED_MODEL_NAME)
        if not silent:
            print(f"\n💡 Use model name: '{MANAGED_MODEL_NAME}' in your tools")
            print(f"   Continue.dev: already updated ✅")
            print(f"   Ollama Desktop: select '{MANAGED_MODEL_NAME}'")


def cmd_reset():
    state = load_state()
    state["active_plugins"] = []
    save_state(state)
    print("🔄 All plugins disabled. Rebuilding lean base model...")
    cmd_build(silent=False)


def cmd_show_tokens():
    state = load_state()
    active = state["active_plugins"]

    base_text = ""
    base_file = MODELFILES_DIR / "base_system_prompt.md"
    if base_file.exists():
        base_text = base_file.read_text()

    base_tok = estimate_tokens(base_text)
    print(f"\n📊 Token cost estimate:")
    print(f"   Base system prompt : ~{base_tok} tokens")

    total_plugin_tok = 0
    for plugin in active:
        prompt = load_plugin_prompt(plugin)
        tok = estimate_tokens(prompt)
        total_plugin_tok += tok
        meta = load_plugin_meta(plugin)
        print(f"   + {meta['name']:<20}: ~{tok} tokens")

    total = base_tok + total_plugin_tok
    all_tok = base_tok + sum(estimate_tokens(load_plugin_prompt(p)) for p in get_available_plugins())
    saved = all_tok - total

    print(f"   {'─'*35}")
    print(f"   Total active        : ~{total} tokens")
    print(f"   If ALL loaded       : ~{all_tok} tokens")
    print(f"   💰 You're saving    : ~{saved} tokens per turn!")


def cmd_set_base(model_name: str):
    state = load_state()
    state["base_model"] = model_name
    save_state(state)
    print(f"✅ Base model set to: '{model_name}'")
    print("   Run 'ollama-pm build' to apply.")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Ollama Smart Context Manager — load only what you need"
    )
    subparsers = parser.add_subparsers(dest="command")

    p_enable = subparsers.add_parser("enable", help="Enable plugin(s)")
    p_enable.add_argument("plugins", nargs="+")
    p_enable.add_argument("--no-build", action="store_true")

    p_disable = subparsers.add_parser("disable", help="Disable plugin(s)")
    p_disable.add_argument("plugins", nargs="+")
    p_disable.add_argument("--no-build", action="store_true")

    subparsers.add_parser("list", help="List all plugins")
    subparsers.add_parser("status", help="Show current status")
    subparsers.add_parser("build", help="Rebuild Ollama model")
    subparsers.add_parser("reset", help="Disable all, rebuild lean model")
    subparsers.add_parser("show-tokens", help="Estimate token costs")

    p_base = subparsers.add_parser("set-base", help="Set base Ollama model")
    p_base.add_argument("model")

    args = parser.parse_args()

    if args.command == "enable":
        cmd_enable(args.plugins, auto_build=not args.no_build)
    elif args.command == "disable":
        cmd_disable(args.plugins, auto_build=not args.no_build)
    elif args.command == "list":
        cmd_list()
    elif args.command == "status":
        cmd_status()
    elif args.command == "build":
        cmd_build()
    elif args.command == "reset":
        cmd_reset()
    elif args.command == "show-tokens":
        cmd_show_tokens()
    elif args.command == "set-base":
        cmd_set_base(args.model)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
