#!/usr/bin/env python3
"""image-ocean2: generate super-high-quality random PG images locally.

Pipelines supported:
  * sdxl-refined  (default)  SDXL 1.0 base → SDXL 1.0 refiner — highest classic SDXL quality
  * sdxl-base                SDXL 1.0 base only — faster, still great
  * juggernaut               Juggernaut-XL v9 photoreal fine-tune — best for photoreal
  * flux                     FLUX.1-schnell — modern, different aesthetic, slower w/ CPU offload

Checkpoints are discovered relative to --models-root (default: ../ComfyUI/models).

Usage:
  python generate.py                       # 1 random image with sdxl-refined
  python generate.py --count 4             # 4 random images
  python generate.py --category whimsical  # restrict to one category
  python generate.py --model juggernaut    # photoreal
  python generate.py --prompt "a fox reading a book in a mossy forest"
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

# Silence a few noisy warnings that don't affect output.
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")

import torch  # noqa: E402

from prompts import (  # noqa: E402
    NEGATIVE_PROMPT,
    Prompt,
    decorate,
    get_default_resolution,
    get_random_prompt,
    list_categories,
)


# Quality knobs applied to every SDXL-style pipeline. See
# docs/superpowers/specs/2026-05-02-quality-upgrades-design.md for the rationale.
SDXL_VAE_REPO = "madebyollin/sdxl-vae-fp16-fix"
FREEU_SDXL = dict(b1=1.3, b2=1.4, s1=0.9, s2=0.2)
REFINER_AESTHETIC_SCORE = 6.0
REFINER_NEGATIVE_AESTHETIC_SCORE = 2.5


DEFAULT_MODELS_ROOT = Path(__file__).resolve().parent.parent / "ComfyUI" / "models"


@dataclass
class GenParams:
    model: str
    prompt_subject: str
    prompt_full: str
    negative_prompt: str
    category: Optional[str]
    seed: int
    steps: int
    refiner_steps: int
    guidance_scale: float
    width: int
    height: int
    high_noise_frac: float  # fraction of steps handled by base when using refiner
    elapsed_seconds: float = 0.0
    extra: dict = field(default_factory=dict)


# -------------------------------------------------------------------
# Checkpoint discovery
# -------------------------------------------------------------------


def _must_exist(p: Path, label: str) -> Path:
    if not p.exists():
        sys.exit(
            f"ERROR: {label} not found at {p}\n"
            "Point --models-root at a directory that contains "
            "checkpoints/sd_xl_base_1.0.safetensors etc."
        )
    return p


def resolve_checkpoints(models_root: Path, model: str) -> dict[str, Path]:
    ckpt_dir = models_root / "checkpoints"
    if model == "sdxl-refined":
        return {
            "base": _must_exist(ckpt_dir / "sd_xl_base_1.0.safetensors", "SDXL base"),
            "refiner": _must_exist(
                ckpt_dir / "sd_xl_refiner_1.0.safetensors", "SDXL refiner"
            ),
        }
    if model == "sdxl-base":
        return {"base": _must_exist(ckpt_dir / "sd_xl_base_1.0.safetensors", "SDXL base")}
    if model == "juggernaut":
        return {
            "base": _must_exist(
                ckpt_dir / "Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors",
                "Juggernaut-XL v9",
            )
        }
    if model == "flux":
        return {}  # FLUX is pulled from the HF cache, not a local .safetensors
    raise ValueError(f"Unknown model: {model}")


# -------------------------------------------------------------------
# Pipeline loading (cached on process)
# -------------------------------------------------------------------


_PIPE_CACHE: dict[str, object] = {}


def _load_fp16_fix_vae(dtype: torch.dtype):
    """Load the SDXL VAE that's numerically stable in fp16.

    The stock SDXL VAE has known precision problems in fp16 (washed-out colors,
    occasional NaN latents). The community fp16-fix VAE retrains the decoder in
    fp32 then quantizes — visually identical at full precision, stable at fp16.
    """
    from diffusers import AutoencoderKL

    return AutoencoderKL.from_pretrained(SDXL_VAE_REPO, torch_dtype=dtype)


def _apply_sdxl_quality_upgrades(pipe) -> None:
    """Swap to DPM++ 2M Karras and turn on FreeU.

    DPM++ 2M Karras is the modern SDXL default — better detail per step than Euler.
    FreeU rebalances U-Net skip connections for sharper outputs at no extra cost.
    """
    from diffusers import DPMSolverMultistepScheduler

    pipe.scheduler = DPMSolverMultistepScheduler.from_config(
        pipe.scheduler.config,
        algorithm_type="dpmsolver++",
        use_karras_sigmas=True,
    )
    pipe.enable_freeu(**FREEU_SDXL)


def _load_sdxl_single_file(path: Path, dtype: torch.dtype, vae=None):
    from diffusers import StableDiffusionXLPipeline

    kwargs: dict = dict(
        torch_dtype=dtype,
        use_safetensors=True,
        add_watermarker=False,
    )
    if vae is not None:
        kwargs["vae"] = vae
    pipe = StableDiffusionXLPipeline.from_single_file(str(path), **kwargs)
    pipe.to("cuda")
    return pipe


def _load_sdxl_refiner(path: Path, dtype: torch.dtype, base_pipe):
    from diffusers import StableDiffusionXLImg2ImgPipeline

    refiner = StableDiffusionXLImg2ImgPipeline.from_single_file(
        str(path),
        torch_dtype=dtype,
        use_safetensors=True,
        add_watermarker=False,
        # Share text encoder + VAE with the base pipeline to save VRAM.
        text_encoder_2=base_pipe.text_encoder_2,
        vae=base_pipe.vae,
    )
    refiner.to("cuda")
    return refiner


def load_pipelines(model: str, ckpts: dict[str, Path], dtype: torch.dtype) -> dict[str, object]:
    if model in _PIPE_CACHE:
        return _PIPE_CACHE[model]  # type: ignore[return-value]

    pipes: dict[str, object] = {}
    if model == "sdxl-refined":
        print("[load] fp16-fix VAE…", flush=True)
        vae = _load_fp16_fix_vae(dtype)
        print("[load] SDXL base…", flush=True)
        base = _load_sdxl_single_file(ckpts["base"], dtype, vae=vae)
        _apply_sdxl_quality_upgrades(base)
        print("[load] SDXL refiner…", flush=True)
        refiner = _load_sdxl_refiner(ckpts["refiner"], dtype, base)
        _apply_sdxl_quality_upgrades(refiner)
        pipes["base"] = base
        pipes["refiner"] = refiner
    elif model == "sdxl-base":
        print("[load] fp16-fix VAE…", flush=True)
        vae = _load_fp16_fix_vae(dtype)
        print("[load] SDXL base…", flush=True)
        base = _load_sdxl_single_file(ckpts["base"], dtype, vae=vae)
        _apply_sdxl_quality_upgrades(base)
        pipes["base"] = base
    elif model == "juggernaut":
        print("[load] fp16-fix VAE…", flush=True)
        vae = _load_fp16_fix_vae(dtype)
        print("[load] Juggernaut-XL v9…", flush=True)
        base = _load_sdxl_single_file(ckpts["base"], dtype, vae=vae)
        _apply_sdxl_quality_upgrades(base)
        pipes["base"] = base
    elif model == "flux":
        print("[load] FLUX.1-schnell (HF cache)…", flush=True)
        from diffusers import FluxPipeline

        pipe = FluxPipeline.from_pretrained(
            "black-forest-labs/FLUX.1-schnell",
            torch_dtype=torch.bfloat16,
        )
        # 24GB VRAM isn't enough for full FLUX bf16 on device; sequential offload is required.
        pipe.enable_sequential_cpu_offload()
        pipes["base"] = pipe
    else:
        raise ValueError(f"Unknown model: {model}")

    _PIPE_CACHE[model] = pipes
    return pipes


# -------------------------------------------------------------------
# Generation
# -------------------------------------------------------------------


def slugify(text: str, max_len: int = 50) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:max_len] or "image"


def _draw_seed(rng: random.Random) -> int:
    return rng.randint(0, 2**31 - 1)


def generate_one(
    model: str,
    pipes: dict[str, object],
    prompt: Prompt,
    seed: int,
    steps: int,
    refiner_steps: int,
    guidance: float,
    width: int,
    height: int,
    high_noise_frac: float,
) -> tuple:
    gen = torch.Generator(device="cuda").manual_seed(seed)
    full_prompt = decorate(prompt.subject)
    t0 = time.perf_counter()

    if model == "sdxl-refined":
        # Two-stage pipeline: base produces latents for the first portion of the noise
        # schedule, refiner finishes. This is the canonical way to squeeze the most
        # detail out of SDXL 1.0.
        base = pipes["base"]
        refiner = pipes["refiner"]
        latents = base(  # type: ignore[operator]
            prompt=full_prompt,
            negative_prompt=NEGATIVE_PROMPT,
            num_inference_steps=steps,
            denoising_end=high_noise_frac,
            guidance_scale=guidance,
            width=width,
            height=height,
            output_type="latent",
            generator=gen,
        ).images
        image = refiner(  # type: ignore[operator]
            prompt=full_prompt,
            negative_prompt=NEGATIVE_PROMPT,
            num_inference_steps=refiner_steps,
            denoising_start=high_noise_frac,
            image=latents,
            generator=gen,
            aesthetic_score=REFINER_AESTHETIC_SCORE,
            negative_aesthetic_score=REFINER_NEGATIVE_AESTHETIC_SCORE,
        ).images[0]
    elif model in ("sdxl-base", "juggernaut"):
        pipe = pipes["base"]
        image = pipe(  # type: ignore[operator]
            prompt=full_prompt,
            negative_prompt=NEGATIVE_PROMPT,
            num_inference_steps=steps,
            guidance_scale=guidance,
            width=width,
            height=height,
            generator=gen,
        ).images[0]
    elif model == "flux":
        pipe = pipes["base"]
        # FLUX-schnell is a 4-step distilled model; respect that default.
        flux_steps = min(steps, 4) if steps else 4
        image = pipe(  # type: ignore[operator]
            prompt=full_prompt,
            num_inference_steps=flux_steps,
            guidance_scale=0.0,
            width=width,
            height=height,
            generator=torch.Generator("cpu").manual_seed(seed),
            max_sequence_length=256,
        ).images[0]
    else:
        raise ValueError(f"Unknown model: {model}")

    elapsed = time.perf_counter() - t0
    params = GenParams(
        model=model,
        prompt_subject=prompt.subject,
        prompt_full=full_prompt,
        negative_prompt=NEGATIVE_PROMPT,
        category=prompt.category,
        seed=seed,
        steps=steps,
        refiner_steps=refiner_steps,
        guidance_scale=guidance,
        width=width,
        height=height,
        high_noise_frac=high_noise_frac,
        elapsed_seconds=round(elapsed, 2),
    )
    return image, params


def save_outputs(image, params: GenParams, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    slug = slugify(params.prompt_subject)
    base_name = f"{ts}_{params.category or 'custom'}_{slug}_s{params.seed}"
    img_path = out_dir / f"{base_name}.png"
    meta_path = out_dir / f"{base_name}.json"
    image.save(img_path, "PNG", optimize=True)
    meta_path.write_text(json.dumps(asdict(params), indent=2))
    return img_path


# -------------------------------------------------------------------
# CLI
# -------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate super high quality random images locally (SDXL / FLUX).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--count", type=int, default=1, help="Number of images to generate.")
    p.add_argument(
        "--forever",
        action="store_true",
        help="Generate images indefinitely until interrupted (Ctrl-C). Overrides --count.",
    )
    p.add_argument(
        "--model",
        choices=["sdxl-refined", "sdxl-base", "juggernaut", "flux"],
        default="sdxl-refined",
        help="Which model pipeline to use.",
    )
    p.add_argument(
        "--category",
        choices=list_categories(),
        default=None,
        help="Restrict prompt selection to a category. Default: weighted random.",
    )
    p.add_argument(
        "--prompt",
        default=None,
        help="Custom subject prompt. Overrides category/random selection.",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Base seed. Each image gets seed + index. Default: random.",
    )
    p.add_argument("--steps", type=int, default=40, help="Base inference steps.")
    p.add_argument(
        "--refiner-steps",
        type=int,
        default=15,
        help="Refiner inference steps (sdxl-refined only).",
    )
    p.add_argument("--guidance", type=float, default=7.0, help="Classifier-free guidance scale.")
    p.add_argument(
        "--width",
        type=int,
        default=None,
        help="Image width. Default: SDXL bucket size for the chosen category.",
    )
    p.add_argument(
        "--height",
        type=int,
        default=None,
        help="Image height. Default: SDXL bucket size for the chosen category.",
    )
    p.add_argument(
        "--high-noise-frac",
        type=float,
        default=0.8,
        help="Fraction of steps handled by base before refiner kicks in (sdxl-refined).",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent / "output",
        help="Output directory for PNGs and JSON sidecars.",
    )
    p.add_argument(
        "--models-root",
        type=Path,
        default=DEFAULT_MODELS_ROOT,
        help="Path to a ComfyUI-style models directory (with a `checkpoints/` subdir).",
    )
    p.add_argument(
        "--list-categories",
        action="store_true",
        help="Print available prompt categories and exit.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.list_categories:
        for c in list_categories():
            print(c)
        return 0

    if not torch.cuda.is_available():
        print("WARNING: CUDA not available — this script is tuned for an RTX 4090.")

    # SDXL fine-tunes expect bf16-friendly sizes (multiples of 8). Only validate when the
    # user supplied a value — defaults come from CATEGORY_RESOLUTIONS, which is curated.
    for label, value in (("--width", args.width), ("--height", args.height)):
        if value is not None and value % 8:
            sys.exit(f"{label} must be a multiple of 8.")

    ckpts = resolve_checkpoints(args.models_root, args.model)
    dtype = torch.float16  # SDXL default; stable on 40-series GPUs.
    pipes = load_pipelines(args.model, ckpts, dtype)

    rng = random.Random(args.seed)

    def _index_stream():
        if args.forever:
            i = 0
            while True:
                yield i
                i += 1
        else:
            yield from range(args.count)

    count_label = "∞" if args.forever else str(args.count)
    seed_label = "random-per-image" if args.seed is None else str(args.seed)
    size_label = (
        f"{args.width}x{args.height}"
        if args.width and args.height
        else "per-category SDXL bucket"
    )
    print(
        f"[run] model={args.model} count={count_label} seed={seed_label} "
        f"size={size_label} steps={args.steps}",
        flush=True,
    )
    if args.forever:
        print("[run] Press Ctrl-C to stop; all completed images remain on disk.", flush=True)

    made = 0
    try:
        for i in _index_stream():
            if args.prompt:
                prompt = Prompt(category="custom", subject=args.prompt)
            else:
                prompt = get_random_prompt(args.category, rng)

            # Seed policy: explicit --seed is reproducible (seed + i); otherwise draw fresh
            # per image so an indefinite run keeps producing varied outputs.
            seed = args.seed + i if args.seed is not None else _draw_seed(rng)

            # Per-image resolution: respect user override if both --width and --height were
            # passed; otherwise pick the SDXL bucket size that matches the prompt's category.
            if args.width and args.height:
                width, height = args.width, args.height
            else:
                width, height = get_default_resolution(prompt.category)

            label = f"#{i + 1}" if args.forever else f"{i + 1}/{args.count}"
            print(
                f"[{label}] ({prompt.category}) {width}x{height} {prompt.subject!r}",
                flush=True,
            )
            image, params = generate_one(
                model=args.model,
                pipes=pipes,
                prompt=prompt,
                seed=seed,
                steps=args.steps,
                refiner_steps=args.refiner_steps,
                guidance=args.guidance,
                width=width,
                height=height,
                high_noise_frac=args.high_noise_frac,
            )
            img_path = save_outputs(image, params, args.out)
            made += 1
            print(f"       → {img_path}  ({params.elapsed_seconds:.1f}s)", flush=True)
    except KeyboardInterrupt:
        print(
            f"\n[interrupted] Stopped after {made} image(s). Outputs in {args.out}/",
            flush=True,
        )
        return 0

    print(f"\nDone. Wrote {made} image(s) to {args.out}/", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
