import base64
from datetime import datetime
import hashlib
from typing import List
from fastapi import UploadFile
from .models import PublishResponse
from .db_utils import get_repo_name_by_experiment_id
from .config import GITHUB_ORG, get_admin_org

from .templates.pr_template import pr_title_template, pr_doc_template


async def publish_experiment_backend(
    exp_id: str,
    files: List[UploadFile]
):

    repo_name = get_repo_name_by_experiment_id(exp_id)
    org = get_admin_org(GITHUB_ORG)
    repo = org.get_repo(repo_name)

    # 1. Read files + compute proposal hash
    file_contents = []
    hasher = hashlib.sha256()

    for f in files:
        content = await f.read()
        hasher.update(content)
        file_contents.append((f.filename, content))

    proposal_hash = hasher.hexdigest()[:8]
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    branch_name = f"publish/{timestamp}-{proposal_hash}"

    # 2. Get base commit (main)
    base_ref = repo.get_git_ref("heads/main")
    base_commit = repo.get_git_commit(base_ref.object.sha)
    base_tree = base_commit.tree

    # 3. Create blobs
    blobs = []
    for path, content in file_contents:
        blob = repo.create_git_blob(
            base64.b64encode(content).decode(),
            encoding="base64",
        )
        blobs.append({
            "path": path,
            "mode": "100644",
            "type": "blob",
            "sha": blob.sha,
        })

    # 4. Create tree
    new_tree = repo.create_git_tree(blobs, base_tree)

    # 5. Create commit
    commit = repo.create_git_commit(
        message=f"Propose experiment ({proposal_hash})",
        tree=new_tree,
        parents=[base_commit],
    )

    # 6. Create branch
    repo.create_git_ref(
        ref=f"refs/heads/{branch_name}",
        sha=commit.sha,
    )

    # 7. Create PR
    pr = repo.create_pull(
        title=pr_title_template.format(proposal_hash=proposal_hash),
        body=pr_doc_template.format(
            proposal_hash=proposal_hash,
            branch_name=branch_name,
        ),
        head=branch_name,
        base="main",
    )

    return PublishResponse(
        experiment_id=proposal_hash,
        pr_url=pr.html_url,
        message="Pull request created",
    )
