#!/usr/bin/env python3
"""Restore IntelliCode-SL Hugging Face artifacts into the local folder layout.

This script discovers model repositories owned by the project account, maps
them back onto the ignored local artifact folders, and downloads the complete
snapshot for each matched repo.

Typical usage:

    source ~/anaconda3/etc/profile.d/conda.sh
    conda activate intellicode-sl
    export HF_TOKEN=...
    python scripts/restore_hf_artifacts.py

You can also pass ``--overwrite`` to replace any existing local artifact
folder before downloading.
"""

from __future__ import annotations

import argparse
import os
import shutil
from dataclasses import dataclass
from getpass import getpass
from pathlib import Path
from typing import Optional

from huggingface_hub import HfApi, snapshot_download


REPO_OWNER = "Spartan1-1-7"


@dataclass(frozen=True)
class ArtifactTarget:
    name: str
    repo_id: str
    relative_path: Path


ARTIFACT_TARGETS: tuple[ArtifactTarget, ...] = (
    ArtifactTarget(
        "classifier_merged",
        "Spartan1-1-7/intellicode-classifier-merged-qwen2.5-coder-0.5b",
        Path("merged_models/classifier_merged"),
    ),
    ArtifactTarget(
        "coding_adapter",
        "Spartan1-1-7/intellicode-coding-adapter-qwen2.5-coder-3b",
        Path("adapters/coding_adapter"),
    ),
    ArtifactTarget(
        "docs_explanation_adapter",
        "Spartan1-1-7/intellicode-docs-explain-adapter-llama3.2-1b",
        Path("adapters/docs_explanation_adapter"),
    ),
    ArtifactTarget(
        "formatter_merged",
        "Spartan1-1-7/intellicode-formatter-merged-llama3.2-1b",
        Path("merged_models/formatter_merged"),
    ),
)


def resolve_token(explicit_token: Optional[str]) -> Optional[str]:
    """Return a Hugging Face token from args, env, or an interactive prompt."""

    if explicit_token:
        return explicit_token

    for env_name in ("HF_TOKEN", "HUGGINGFACE_HUB_TOKEN", "HUGGINGFACE_TOKEN"):
        token = os.environ.get(env_name)
        if token:
            return token

    if os.environ.get("CI"):
        return None

    entered = getpass("Hugging Face token (leave blank to use cached login): ").strip()
    return entered or None


def discover_matching_repos(api: HfApi, owner: str, token: Optional[str]) -> list[tuple[str, ArtifactTarget]]:
    """Return ``(repo_id, target)`` pairs for repos that match the artifact layout."""

    expected_by_repo_id = {target.repo_id: target for target in ARTIFACT_TARGETS}
    matches: list[tuple[str, ArtifactTarget]] = []
    for model_info in api.list_models(author=owner, token=token):
        repo_id = getattr(model_info, "modelId", None) or getattr(model_info, "id", None)
        if not repo_id:
            continue

        target = expected_by_repo_id.get(repo_id)
        if target is not None:
            matches.append((repo_id, target))

    matches.sort(key=lambda item: item[1].relative_path.as_posix())
    return matches


def restore_repo(repo_id: str, target_root: Path, token: Optional[str], overwrite: bool) -> None:
    """Download a repo snapshot into the requested target folder."""

    if target_root.exists() and overwrite:
        shutil.rmtree(target_root)

    target_root.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {repo_id} -> {target_root}")
    snapshot_download(
        repo_id=repo_id,
        repo_type="model",
        token=token,
        local_dir=str(target_root),
        local_dir_use_symlinks=False,
    )
    print(f"Done: {target_root}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore IntelliCode-SL artifacts from Hugging Face.")
    parser.add_argument("--owner", default=REPO_OWNER, help="Hugging Face account or org that owns the repos.")
    parser.add_argument("--token", default=None, help="Hugging Face token. Falls back to HF_TOKEN or cached login.")
    parser.add_argument("--overwrite", action="store_true", default=True, help="Replace existing local artifact folders.")
    parser.add_argument("--no-overwrite", dest="overwrite", action="store_false", help="Keep existing local folders.")
    parser.add_argument("--list-only", action="store_true", help="Print matching repos without downloading.")
    args = parser.parse_args()

    token = resolve_token(args.token)
    api = HfApi(token=token)
    matches = discover_matching_repos(api, args.owner, token)

    if not matches:
        print(f"No matching model repos found for owner '{args.owner}'.")
        return 1

    print("Matched repos:")
    for repo_id, target in matches:
        print(f"  - {repo_id} -> {target.relative_path}")

    if args.list_only:
        return 0

    base_dir = Path(__file__).resolve().parents[1]
    for repo_id, target in matches:
        restore_repo(repo_id, base_dir / target.relative_path, token, args.overwrite)

    print("All matched Hugging Face artifacts have been restored.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())