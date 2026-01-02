from datetime import datetime
from typing import List
import uuid
from fastapi import FastAPI, File, Form, HTTPException, Header, Request, UploadFile

from app.github.github_ops import create_repo, initialize_gitops_repo, protect_main_branch
from app.merge import try_merge_pr
from app.publishing import publish_experiment_backend
from app.db import get_connection, init_db
from app.models import CreateExperimentRequest, CreateExperimentResponse, InitRequest, InitResponse, OnboardStatusResponse, PublishResponse
from app.utils import verify_signature

app = FastAPI(title="HEDA GitOps Service")

@app.get("/healthz")
def health():
    return {"status": "ok"}

@app.on_event("startup")
def startup():
    init_db()
    
@app.post("/experiments", response_model=CreateExperimentResponse)
def create_experiment(req: CreateExperimentRequest):
    exp_id = f"exp_{uuid.uuid4().hex[:8]}"
    repo_name = f"{exp_id}-{req.exp_name}-gitops"
    now = datetime.utcnow().isoformat()

    try:
        repo_url = create_repo(repo_name)
        initialize_gitops_repo(repo_url)
        protect_main_branch(repo_url)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create GitHub repo: {e}",
        )

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO experiments (uuid, repo_name, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (exp_id, repo_name, now),
        )

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {e}",
        )

    return CreateExperimentResponse(
        experiment_id=exp_id,
        repo_url=repo_url,
    )

@app.post("/publish", response_model=PublishResponse)
async def publish_experiment(
    exp_id: str = Form(...),
    files: List[UploadFile] = File(...),
):
 
    return await publish_experiment_backend(exp_id, files)


@app.post("/github/webhook")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None),
    x_github_event: str = Header(None),
):
    payload = await request.body()
    verify_signature(payload, x_hub_signature_256)

    data = await request.json()

    if (
    x_github_event == "check_run"
    and data["action"] == "completed"
    and data["check_run"]["name"] == "verify"
    and data["check_run"]["conclusion"] == "success"):
        await try_merge_pr(data)


    return {"status": "ok"}
