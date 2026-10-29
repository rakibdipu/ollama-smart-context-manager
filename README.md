# 🧠 Ollama Smart Context Manager

> **Token সাশ্রয় করো। শুধু দরকারি জিনিসটাই লোড করো।**

Ollama-র সাথে কাজ করার সময় সব system prompt একসাথে লোড হলে **context window ভরে যায় এবং token waste হয়।**  
এই টুলটা সেটা ঠিক করে — যখন যা দরকার, শুধু তখন সেটাই inject করে।

---

## ✅ যেসব টুলে কাজ করে

| Tool | সাপোর্ট |
|---|---|
| **Ollama Desktop** | ✅ `smart-assistant` model সিলেক্ট করো |
| **Continue.dev (VS Code)** | ✅ config auto-update হয় |
| **Open WebUI** | ✅ `smart-assistant` model ব্যবহার করো |
| **Aider** | ✅ `--model ollama/smart-assistant` |
| **Ollama CLI** | ✅ `ollama run smart-assistant` |

---

## ⚡ কীভাবে কাজ করে?

```
[Base Model: llama3.2]
        +
[Plugin: coding]  ← শুধু যখন enable করো
        +
[Plugin: web-dev] ← শুধু যখন enable করো
        ↓
ollama create smart-assistant  ← একটা focused model তৈরি হয়
```

প্রতিবার `enable` বা `disable` করলে `smart-assistant` model নতুনভাবে build হয়।  
তোমার tool-এ model নাম পরিবর্তন করতে হয় না — সবসময় `smart-assistant` ব্যবহার করো।

---

## 🚀 ইনস্টল

```bash
git clone https://github.com/rakibdipu/ollama-smart-context-manager.git
cd ollama-smart-context-manager
bash install.sh
```

> **Requirement:** Ollama + Python 3.8+

---

## 📦 Available Plugins

| Plugin | কী কাজ করে | Token |
|---|---|---|
| `coding` | Python, JS, Go, debugging, code review | ~120 |
| `web-dev` | HTML/CSS, React, APIs, browser tools | ~110 |
| `data-science` | pandas, numpy, ML, matplotlib | ~130 |
| `devops` | Docker, bash, Linux, CI/CD, nginx | ~125 |
| `bangla` | বাংলা লেখালিখি, অনুবাদ, ব্যাকরণ | ~80 |

---

## 🎮 ব্যবহার

### সব plugin দেখো + token cost
```bash
ollama-pm list
```
```
📦 Ollama Smart Context Manager
   Base model : llama3.2
   Output model: smart-assistant

Available plugins:
  ✅ ON  Coding Assistant        ~120 tokens  — programming, debugging
  ⭕ OFF Web Dev Assistant       ~110 tokens  — HTML, CSS, React
  ⭕ OFF Data Science Assistant  ~130 tokens  — pandas, ML
  ⭕ OFF DevOps / Linux          ~125 tokens  — Docker, bash
  ⭕ OFF Bangla Language         ~ 80 tokens  — বাংলা সাহায্য

💰 Active context cost: ~60 tokens (base=60 + plugins=120)
```

### Plugin চালু করো
```bash
ollama-pm enable coding          # একটা
ollama-pm enable coding web-dev  # একসাথে দুটো
```

### Plugin বন্ধ করো
```bash
ollama-pm disable web-dev
```

### Token savings দেখো
```bash
ollama-pm show-tokens
```
```
📊 Token cost estimate:
   Base system prompt : ~60 tokens
   + Coding Assistant : ~120 tokens
   ─────────────────────────────────
   Total active       : ~180 tokens
   If ALL loaded      : ~565 tokens
   💰 You're saving   : ~385 tokens per turn!
```

### সব বন্ধ করে lean mode-এ ফেরো
```bash
ollama-pm reset
```

### Base model পরিবর্তন করো
```bash
ollama-pm set-base mistral
ollama-pm set-base qwen2.5-coder:7b
ollama-pm build
```

---

## ➕ নিজে Plugin বানাও

```bash
mkdir plugins/my-plugin
```

**`plugins/my-plugin/plugin.json`:**
```json
{
  "name": "My Custom Plugin",
  "description": "যা খুশি তাই",
  "tags": ["custom"],
  "version": "1.0.0"
}
```

**`plugins/my-plugin/system_prompt.md`:**
```markdown
তোমার custom system prompt এখানে লেখো।
যত ছোট রাখবে, তত কম token খরচ।
```

```bash
ollama-pm enable my-plugin
```

---

## 🔗 Related

- [Antigravity Smart Plugin Manager](https://github.com/rakibdipu/antigravity-smart-plugin-manager) — Google AGY-এর জন্য একই কনসেপ্ট

---

## 📄 License

MIT — ব্যবহার করো, শেয়ার করো, উন্নত করো।
