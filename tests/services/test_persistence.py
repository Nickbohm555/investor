from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models import Base, RunRecord


def test_create_run_record_persists_status():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        run = RunRecord(run_id="run-123", status="created")
        session.add(run)
        session.commit()

        stored = session.get(RunRecord, "run-123")

    assert stored is not None
    assert stored.status == "created"
