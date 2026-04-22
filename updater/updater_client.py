from __future__ import annotations

import requests
from dataclasses import dataclass
from packaging.version import Version

from .version import (
    APP_VERSION,
    GITHUB_OWNER,
    GITHUB_REPO,
    UPDATE_ASSET_NAME,
    UPDATER_ASSET_NAME,
)


@dataclass(slots=True)
class UpdateInfo:
    version: str
    update_url: str
    updater_url: str


def get_latest_release() -> UpdateInfo | None:
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"

    response = requests.get(
        url,
        timeout=20,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
        },
    )
    response.raise_for_status()

    data = response.json()
    tag_name = str(data.get("tag_name", "")).lstrip("v")
    assets = data.get("assets", [])

    update_url = ""
    updater_url = ""

    for asset in assets:
        name = asset.get("name", "")
        download_url = asset.get("browser_download_url", "")

        if name == UPDATE_ASSET_NAME:
            update_url = download_url
        elif name == UPDATER_ASSET_NAME:
            updater_url = download_url

    if not tag_name or not update_url or not updater_url:
        return None

    return UpdateInfo(
        version=tag_name,
        update_url=update_url,
        updater_url=updater_url,
    )


def is_update_available(latest_version: str) -> bool:
    return Version(latest_version) > Version(APP_VERSION)