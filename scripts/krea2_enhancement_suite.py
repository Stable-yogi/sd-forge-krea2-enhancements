"""
Krea 2 Enhancement Suite — Stable Yogi Edition (free from stableyogi.com).

Companion to the sd-forge-krea2 base extension (required). Adds:
  * Prompt-Adherence Engine — runs the DiT's txtfusion twice (clean + deep-tap-boosted) and
    blends with a per-token relative clamp, pushing prompt adherence hard without destabilising
    any token. Port of capitan01R/ComfyUI-Krea2T-Enhancer (MIT — credit).
  * Detail Boost PRO — custom per-layer weights on top of the base extension's Detail Boost.
    Technique credit: huwhitememes/comfyui-krea2-conditioning (Apache-2.0) / nova452.

Everything is opt-in (off by default) and only affects Krea 2 models.
"""
import os
import sys

import gradio as gr
import torch

# Reach the base extension's package (sd-forge-krea2 must be installed).
_BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "sd-forge-krea2")
if os.path.isdir(_BASE) and _BASE not in sys.path:
    sys.path.insert(0, _BASE)

try:
    from krea2 import enhance as base_enhance
    _HAVE_BASE = True
except Exception:
    base_enhance = None
    _HAVE_BASE = False

from modules import scripts, shared

try:                                              # header-checkbox accordion (Forge/A1111 built-in)
    from modules.ui_components import InputAccordion
except Exception:
    InputAccordion = None

# ---- Prompt-Adherence engine constants (port of Krea2T-Enhancer, MIT) ----
_PROFILE_12 = (1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 2.5, 5.0, 1.1, 4.0, 1.0)
_CHUNK_PROFILE = _PROFILE_12 + _PROFILE_12          # 24 chunks of 1280 over the flattened 12x2560
_CHUNKS, _CHUNK_DIM = 24, 1280
_GLOBAL_MULT = 15.0
_TOKEN_REL_CAP = 0.75


def _get_krea2_dit():
    """The loaded SingleStreamDiT, or None if the current model isn't Krea 2."""
    try:
        dm = shared.sd_model.forge_objects.unet.model.diffusion_model
        if hasattr(dm, "txtfusion") and hasattr(dm, "_unpack_context"):
            return dm
    except Exception:
        pass
    return None


def _adherence_forward(orig_forward, strength):
    """Wrap txtfusion.forward: clean pass + boosted pass, blended under a per-token clamp."""

    def wrapped(x, mask=None, transformer_options={}):
        b, seq, taps, dim = x.shape
        if taps * dim != _CHUNKS * _CHUNK_DIM:
            return orig_forward(x, mask=mask, transformer_options=transformer_options)

        reference = orig_forward(x, mask=mask, transformer_options=transformer_options)

        gains = torch.tensor(_CHUNK_PROFILE, device=x.device, dtype=torch.float32)
        gains = (1.0 + strength * (gains - 1.0)).to(x.dtype)
        global_mult = 1.0 + strength * (_GLOBAL_MULT - 1.0)
        scaled = (x.reshape(b, seq, _CHUNKS, _CHUNK_DIM) * gains.view(1, 1, _CHUNKS, 1) * global_mult).reshape_as(x)
        candidate = orig_forward(scaled, mask=mask, transformer_options=transformer_options)

        # per-token relative clamp: never move any token more than TOKEN_REL_CAP of its own RMS
        delta = candidate.detach().float() - reference.detach().float()
        base_rms = reference.detach().float().pow(2).mean(dim=-1, keepdim=True).sqrt().clamp_min(1e-8)
        delta_rms = delta.pow(2).mean(dim=-1, keepdim=True).sqrt().clamp_min(1e-8)
        scale = (_TOKEN_REL_CAP / (delta_rms / base_rms)).clamp(max=1.0)
        return (reference.detach().float() + delta * scale).to(candidate.dtype)

    return wrapped


class Krea2EnhancementSuite(scripts.Script):
    def title(self):
        return "Krea 2 Enhancement Suite (Stable Yogi)"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        def _body():
            if not _HAVE_BASE:
                gr.Markdown("⚠️ Requires the **sd-forge-krea2** base extension (github.com/Stable-yogi/sd-forge-krea2).")
            gr.Markdown("Free from [stableyogi.com](https://stableyogi.com). All features opt-in; Krea 2 models only.")
            with gr.Group():
                adh_enable = gr.Checkbox(label="Prompt-Adherence Engine", value=False)
                adh_strength = gr.Slider(label="Adherence strength", minimum=0.0, maximum=2.0, step=0.05, value=1.0)
            with gr.Group():
                db_enable = gr.Checkbox(label="Detail Boost PRO (custom per-layer weights)", value=False)
                db_weights = gr.Textbox(
                    label="12 per-layer weights (shallow → deep)",
                    value=", ".join(str(w) for w in _PROFILE_12),
                )
                db_strength = gr.Slider(label="Boost strength", minimum=0.0, maximum=2.0, step=0.05, value=1.0)
                db_renorm = gr.Checkbox(label="RMS renormalize (recommended)", value=True)
            return adh_enable, adh_strength, db_enable, db_weights, db_strength, db_renorm

        # Master enable lives in the accordion header — one toggle to arm/disarm the whole
        # Suite and read its status from the top (same pattern as LoRA Block Weight).
        label = "Krea 2 Enhancement Suite — Stable Yogi"
        if InputAccordion is not None:
            with InputAccordion(False, label=label) as suite_enable:
                adh_enable, adh_strength, db_enable, db_weights, db_strength, db_renorm = _body()
        else:                                          # older Forge without InputAccordion
            with gr.Accordion(label, open=False):
                suite_enable = gr.Checkbox(label="Enable Suite", value=False)
                adh_enable, adh_strength, db_enable, db_weights, db_strength, db_renorm = _body()
        return [suite_enable, adh_enable, adh_strength, db_enable, db_weights, db_strength, db_renorm]

    def process(self, p, suite_enable=False, adh_enable=False, adh_strength=1.0,
                db_enable=False, db_weights="", db_strength=1.0, db_renorm=True):
        # Master gate: header checkbox off → do nothing (and tear down any prior-run patch).
        if not suite_enable:
            self._restore_adherence()
            return
        # --- Detail Boost PRO (custom weights via the base extension's engine) ---
        if _HAVE_BASE:
            if db_enable and db_strength > 0.0:
                weights = base_enhance.parse_weights(db_weights)
                if weights:
                    base_enhance.CONFIG["detail_boost"] = {
                        "weights": weights, "strength": float(db_strength), "renormalize": bool(db_renorm),
                    }
                    p.extra_generation_params["Krea2 Detail Boost PRO"] = f"custom (s={db_strength:g})"
            # (when disabled, leave the base extension's own Detail Boost setting alone)

        # --- Prompt-Adherence engine (txtfusion double-run) ---
        self._restore_adherence()
        if adh_enable and adh_strength > 0.0:
            dm = _get_krea2_dit()
            if dm is not None:
                tf = dm.txtfusion
                if not hasattr(tf, "_sy_orig_forward"):
                    tf._sy_orig_forward = tf.forward
                tf.forward = _adherence_forward(tf._sy_orig_forward, float(adh_strength))
                self._patched_tf = tf
                p.extra_generation_params["Krea2 Prompt Adherence"] = f"s={adh_strength:g}"

    def postprocess(self, p, processed, *args):
        self._restore_adherence()

    def _restore_adherence(self):
        tf = getattr(self, "_patched_tf", None)
        if tf is not None and hasattr(tf, "_sy_orig_forward"):
            tf.forward = tf._sy_orig_forward
            del tf._sy_orig_forward
        self._patched_tf = None
