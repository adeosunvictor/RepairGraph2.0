from __future__ import annotations

import argparse
import asyncio
import json

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from repairgraph.config import Settings, settings
from repairgraph.models import Issue, RepairReport
from repairgraph.service import repair
from repairgraph.tools.github import verify_webhook_signature

app = FastAPI(title="RepairGraph", version="2.0.0")


class RepairRequest(BaseModel):
    issue: Issue
    repo_source: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "repairgraph", "version": "2.0.0"}


@app.post("/repair", response_model=RepairReport)
async def repair_endpoint(payload: RepairRequest) -> RepairReport:
    return await repair(payload.issue, payload.repo_source, settings)


@app.post("/webhooks/github")
async def github_webhook(request: Request) -> dict:
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_webhook_signature(settings.github_webhook_secret, body, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    event = request.headers.get("X-GitHub-Event")
    payload = json.loads(body)
    if event != "issues" or payload.get("action") not in {"opened", "reopened"}:
        return {"accepted": False, "reason": "event ignored"}
    issue_data = payload["issue"]
    issue = Issue(
        id=str(issue_data["number"]),
        title=issue_data["title"],
        body=issue_data.get("body") or "",
        url=issue_data.get("html_url"),
        labels=[item["name"] for item in issue_data.get("labels", [])],
    )
    report = await repair(issue, payload["repository"]["clone_url"], settings)
    return {"accepted": True, "status": report.status, "attempts": report.attempts}


def cli() -> None:
    parser = argparse.ArgumentParser(
        description="RepairGraph 2.0 multi-agent software maintenance engineer"
    )
    parser.add_argument("--repo", required=True, help="Local repository path or HTTPS git URL")
    parser.add_argument("--issue-id", default="local-1")
    parser.add_argument("--title", required=True)
    parser.add_argument("--body", default="")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument(
        "--sandbox",
        choices=["docker", "local"],
        default=None,
        help="Override sandbox backend. Use local only for trusted repositories.",
    )
    args = parser.parse_args()

    overrides: dict[str, object] = {
        "use_mock_llm": args.mock,
        "llm_provider": "mock" if args.mock else settings.llm_provider,
    }
    if args.sandbox:
        overrides["sandbox_backend"] = args.sandbox
    local_settings = Settings(**overrides)
    issue = Issue(id=args.issue_id, title=args.title, body=args.body)
    report = asyncio.run(repair(issue, args.repo, local_settings))
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    cli()
