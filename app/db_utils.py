from app.db import get_connection
from dataclasses import dataclass
from typing import Optional

@dataclass
class ExperimentRow:
    uuid: str
    repo_name: str
    owner_sub: str
    created_at: str


def fetch_experiment(exp_id: str) -> Optional[ExperimentRow]:
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            SELECT uuid, repo_name, owner_sub, created_at
            FROM experiments
            WHERE uuid = %s
            """,
            (exp_id,),
        )

        row = cur.fetchone()
        if not row:
            return None

        return ExperimentRow(
            uuid=row[0],
            repo_name=row[1],
            owner_sub=row[2],
            created_at=row[3],
        )

    finally:
        cur.close()
        conn.close()
