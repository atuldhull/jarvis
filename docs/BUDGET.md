# JARVIS — Budget (in Indian Rupees)

Your stated budget: **₹1000 total, max ₹100 per dataset.**
Reality: **you need ₹0.** Here is every possible cost, accounted for.

---

## The required spend

| Item | What it is | Cost |
|---|---|---|
| Brain (Qwen3.5 4B via Ollama) | The LLM | **₹0** (free download) |
| Ears (faster-whisper) | Speech-to-text | **₹0** |
| Voice (Piper / Kokoro) | Text-to-speech | **₹0** |
| Wake word (openWakeWord) | "Hey Jarvis" | **₹0** |
| Browser control (Playwright) | Web automation | **₹0** |
| OS control (pyautogui, etc.) | App/file/key control | **₹0** |
| Memory (SQLite/Chroma) | Remembering things | **₹0** |
| Credential vault (keyring) | Password storage | **₹0** |
| Datasets | Not needed (you don't train) | **₹0** |
| Electricity | Your laptop runs anyway | ~negligible |
| **TOTAL REQUIRED** | | **₹0** |

You build the entire JARVIS — brain, voice, ears, browser control, memory — for **zero
rupees.** Nothing here needs a paid dataset or a paid model.

---

## Why "₹100 per dataset" doesn't apply

You imagined buying datasets to train the brain. But:
1. You **don't train the brain** — you download a finished one. No dataset needed.
2. If you ever *do* fine-tune (optional, advanced), the datasets on **Hugging Face are
   free** (Glaive, xLAM, Hermes, etc. — see
   [MODELS_AND_DATASETS.md](MODELS_AND_DATASETS.md) §7).
3. The best "personality dataset" is ~100 examples **you write yourself** — also free.

So you will **never pay ₹100 for a dataset** in this project. Keep that money.

---

## Optional spends (ONLY if you choose to — all skippable)

| Optional item | Why you might | Cost | Verdict |
|---|---|---|---|
| ElevenLabs voice | Most lifelike voice | Free tier, or ~₹420/mo | ❌ Skip — Piper/Kokoro are free & good |
| Google Colab Pro | Faster fine-tuning | ~₹1000/mo | ❌ Skip — free Colab works |
| A USB mic | Cleaner audio input | ₹300–₹800 one-time | 🤷 Optional, your laptop mic is fine |
| Cloud GPU (RunPod, etc.) | Heavy fine-tuning | pay-per-hour | ❌ Not needed |

Even if you bought the *one* thing that might help (a cheap mic), you'd still be under
your ₹1000 budget — and you don't need it to start.

---

## The verdict

```
Required budget:   ₹0
Your budget:       ₹1000
Money left over:   ₹1000  🎉
Datasets to buy:   none
Models to train:   none
```

This project is limited by your **time and learning**, not your money. Spend the ₹1000
on a celebratory coffee when "Hey Jarvis, open YouTube" works for the first time. ☕
