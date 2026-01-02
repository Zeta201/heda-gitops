from datetime import datetime
from typing import List
import uuid
from fastapi import Depends, FastAPI, File, Form, HTTPException, Header, Request, UploadFile, status

from app.github.github_ops import create_repo, initialize_gitops_repo, protect_main_branch
from app.merge import try_merge_pr
from app.publishing import publish_experiment
from app.db import get_connection, init_db
from app.db_utils import fetch_experiment
from app.models import CreateExperimentRequest, CreateExperimentResponse, PublishResponse
from app.utils import verify_signature
from app.auth import AuthenticatedUser, get_current_user

app = FastAPI(title="HEDA GitOps Service")

@app.get("/healthz")
def health():
    return {"status": "ok"}

@app.on_event("startup")
def startup():
    init_db()
    
@app.post("/experiments", response_model=CreateExperimentResponse, status_code=status.HTTP_201_CREATED)
def create_experiment(req: CreateExperimentRequest, 
                      user: AuthenticatedUser = Depends(get_current_user),
):
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
            INSERT INTO experiments (uuid, repo_name, owner_sub, created_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (exp_id, repo_name, user.sub, now),
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
        detail="Experiment successfully created",
    )


def require_experiment_owner(
    exp_id: str = Form(...),
    user: AuthenticatedUser = Depends(get_current_user),
):
    row = fetch_experiment(exp_id)

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found",
        )

    if row.owner_sub != user.sub:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this experiment",
        )

    return row


@app.post("/experiments/publish", response_model=PublishResponse)
async def publish(
    exp_id: str = Form(...),
    files: List[UploadFile] = File(...),
    experiment = Depends(require_experiment_owner),
): 
    return await publish_experiment(exp_id, files)


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
