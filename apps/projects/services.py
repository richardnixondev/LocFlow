"""GitHub integration service — fetches resource files from repos."""

import base64
import logging

import requests
from django.utils import timezone

from apps.projects.models import GitHubRepo
from apps.resources.services import detect_format_from_filename, process_upload

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"

SUPPORTED_EXTENSIONS = {"json", "po", "pot", "strings", "xliff", "xlf"}


def _headers(token: str = "") -> dict:
    h = {"Accept": "application/vnd.github.v3+json"}
    if token:
        h["Authorization"] = f"token {token}"
    return h


def _get(url: str, token: str = "") -> requests.Response:
    resp = requests.get(url, headers=_headers(token), timeout=30)
    resp.raise_for_status()
    return resp


def _resolve_branch(gh: GitHubRepo) -> str:
    """Try the configured branch; if 404, try common alternatives and update the model."""
    branches_to_try = [gh.branch]
    if gh.branch == "main":
        branches_to_try.append("master")
    elif gh.branch == "master":
        branches_to_try.append("main")

    for branch in branches_to_try:
        url = f"{GITHUB_API}/repos/{gh.owner}/{gh.repo}/git/trees/{branch}?recursive=1"
        resp = requests.get(url, headers=_headers(gh.access_token), timeout=30)
        if resp.status_code == 200:
            if branch != gh.branch:
                gh.branch = branch
                gh.save(update_fields=["branch"])
            return branch
        if resp.status_code != 404:
            resp.raise_for_status()

    # None worked — raise with the original branch
    url = f"{GITHUB_API}/repos/{gh.owner}/{gh.repo}/git/trees/{gh.branch}?recursive=1"
    _get(url, gh.access_token)  # will raise HTTPError
    return gh.branch  # unreachable


def list_repo_tree(gh: GitHubRepo) -> list[dict]:
    """List files in the repo using the Git Trees API (recursive)."""
    branch = _resolve_branch(gh)
    url = f"{GITHUB_API}/repos/{gh.owner}/{gh.repo}/git/trees/{branch}?recursive=1"
    data = _get(url, gh.access_token).json()

    files = []
    base = gh.base_path.strip("/")
    patterns = set(gh.file_patterns) if gh.file_patterns else SUPPORTED_EXTENSIONS

    for item in data.get("tree", []):
        if item["type"] != "blob":
            continue
        path = item["path"]

        # Filter by base_path
        if base and not path.startswith(base + "/") and path != base:
            continue

        # Filter by extension
        ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
        if ext not in patterns:
            continue

        files.append({
            "path": path,
            "sha": item["sha"],
            "size": item.get("size", 0),
            "extension": ext,
        })

    return files


def fetch_file_content(gh: GitHubRepo, file_path: str) -> str:
    """Fetch a single file's content from GitHub."""
    url = f"{GITHUB_API}/repos/{gh.owner}/{gh.repo}/contents/{file_path}?ref={gh.branch}"
    data = _get(url, gh.access_token).json()

    if data.get("encoding") == "base64":
        return base64.b64decode(data["content"]).decode("utf-8")

    return data.get("content", "")


def sync_repo(gh: GitHubRepo) -> dict:
    """Sync all resource files from the linked GitHub repo into the project."""
    results = {"files_found": 0, "files_synced": 0, "errors": [], "details": []}

    try:
        files = list_repo_tree(gh)
        results["files_found"] = len(files)

        for f in files:
            file_format = detect_format_from_filename(f["path"])
            if not file_format:
                continue

            try:
                content = fetch_file_content(gh, f["path"])
                result = process_upload(
                    project=gh.project,
                    file_content=content,
                    file_path=f["path"],
                    file_format=file_format,
                )
                results["details"].append({
                    "path": f["path"],
                    **result,
                })
                results["files_synced"] += 1
            except Exception as e:
                logger.warning("Failed to sync %s: %s", f["path"], e)
                results["errors"].append({"path": f["path"], "error": str(e)})

        gh.last_synced_at = timezone.now()
        if results["files_found"] == 0:
            exts = ", ".join(sorted(patterns))
            gh.last_sync_status = "warning"
            gh.last_sync_message = (
                f"No resource files found. "
                f"Looking for extensions: {exts}. "
                f"{'In path: ' + base + '. ' if base else ''}"
                f"Make sure the repository contains localization files."
            )
        else:
            gh.last_sync_status = "success"
            gh.last_sync_message = f"Synced {results['files_synced']}/{results['files_found']} files"
        gh.save(update_fields=["last_synced_at", "last_sync_status", "last_sync_message"])

    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else 0
        if status == 404:
            msg = "Repository not found. Check owner/repo/branch or provide an access token for private repos."
        elif status == 401:
            msg = "Authentication failed. Check the access token."
        elif status == 403:
            msg = "Rate limit exceeded or access denied."
        else:
            msg = f"GitHub API error: {e}"

        gh.last_synced_at = timezone.now()
        gh.last_sync_status = "error"
        gh.last_sync_message = msg
        gh.save(update_fields=["last_synced_at", "last_sync_status", "last_sync_message"])
        results["errors"].append({"error": msg})

    except Exception as e:
        msg = f"Unexpected error: {e}"
        gh.last_synced_at = timezone.now()
        gh.last_sync_status = "error"
        gh.last_sync_message = msg
        gh.save(update_fields=["last_synced_at", "last_sync_status", "last_sync_message"])
        results["errors"].append({"error": msg})

    return results
