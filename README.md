# Krea 2 Enhancement Suite — Stable Yogi Edition

Free companion to **[sd-forge-krea2](https://github.com/Stable-yogi/sd-forge-krea2)** (required).
By **[Stable Yogi](https://stableyogi.com)**.

## Features (all opt-in, off by default — Krea 2 models only)
- **Prompt-Adherence Engine** — runs the DiT's text-fusion twice (clean + deep-tap-boosted) and
  blends under a per-token safety clamp: noticeably stronger prompt adherence without
  destabilising the image. Strength 0–2.
- **Detail Boost PRO** — full custom per-layer weights (12 taps, shallow → deep) on top of the
  base extension's preset Detail Boost, with RMS-safe renormalisation.
- *(Coming next: Image Reference — guide generations with a reference photo through the
  Qwen3-VL vision path.)*

## Install
1. Install the base extension first: `github.com/Stable-yogi/sd-forge-krea2`.
2. Add this one: Forge → **Extensions → Install from URL** →
   `https://github.com/Stable-yogi/sd-forge-krea2-enhancements` (or drop the folder into `extensions/`).
3. Restart Forge → open the **"Krea 2 Enhancement Suite — Stable Yogi"** accordion in txt2img.

## Usage tips
- Start with **Adherence strength 1.0**; raise toward 2.0 for stubborn prompts.
- Detail Boost PRO: the deep taps (positions 8–11) carry identity/texture — boost those.
  Keep **RMS renormalize on** unless you deliberately want a hotter conditioning signal.

## Credits & license
GPL-3.0. Prompt-Adherence engine ported from **capitan01R/ComfyUI-Krea2T-Enhancer** (MIT);
per-layer rebalance technique from **huwhitememes/comfyui-krea2-conditioning** (Apache-2.0),
a fork of **nova452/ComfyUI-ConditioningKrea2Rebalance**. Thanks to all three authors.
Integration & packaging by **Stable Yogi** — [stableyogi.com](https://stableyogi.com).
