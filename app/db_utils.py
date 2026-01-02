from app.db import get_connection

def get_repo_name_by_experiment_id(exp_id: str) -> str:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT repo_name
        FROM experiments
        WHERE uuid = %s
        """,
        (exp_id,),
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        raise ValueError(f"Experiment {exp_id} not found")

    return row[0]

