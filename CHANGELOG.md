# Changelog

## v1.0.1 — 2026-08-19 (Forge Neo 2.28 compatibility — the Suite did nothing)
- **Fixed: nothing happened at all on Forge Neo 2.28.** The Suite recognised a Krea 2 model by two attributes on the DiT, and 2.28 deleted one of them (`_unpack_context`) — so it concluded "not a Krea 2 model", skipped the Prompt-Adherence patch, and said nothing. It now recognises the model by its **text-fusion block** alone — present in every Forge generation, and the very block this engine patches.
- **Detail Boost PRO needs base extension v1.3.3+.** The boost is applied by `sd-forge-krea2`, whose 2.28 hook broke on the same removal — **update both extensions**.
- **No more silent no-ops:** when the Suite is enabled but the model has no Krea 2 text-fusion block (or the base extension is missing), it now says so in the console instead of quietly doing nothing.
- Verified on a **fresh Forge Neo 2.28 install**: Prompt-Adherence off vs on now renders different pixels (they were identical before), and Detail Boost PRO likewise.

## v1.0.0
- Initial public release.
- **Prompt-Adherence Engine** — stronger prompt adherence via a clamped clean/boosted text-fusion blend (strength 0–2).
- **Detail Boost PRO** — full custom per-layer weights on top of the base extension's Detail Boost, with RMS-safe renormalisation.
- Header on/off checkbox on the accordion; all features opt-in, off by default; Krea 2 models only.
