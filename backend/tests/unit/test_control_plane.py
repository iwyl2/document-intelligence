from pathlib import Path

from sqlalchemy import event, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from document_intelligence.db.models import Base, User, WorkspaceSession, DocumentRecord


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(bind=engine)
db = TestingSessionLocal()

user = User(email="test@example.com", password_hash="dummy_hash")


def test_create_user_session_and_document():
    db.add(user)
    db.commit()

    session = WorkspaceSession(user_id=user.id, name="Research Workspace")
    db.add(session)
    db.commit()

    doc = DocumentRecord(
        session_id=session.id, file_name="sample.pdf", num_pages=5, num_chunks=12
    )
    db.add(doc)
    db.commit()

    assert len(user.sessions) == 1
    assert user.sessions[0].name == "Research Workspace"
    assert len(user.sessions[0].documents) == 1
    assert user.sessions[0].documents[0].file_name == "sample.pdf"


def test_cascade_delete_cleans_up_orphans():
    db.delete(user)
    db.commit()

    assert db.query(User).count() == 0
    assert db.query(WorkspaceSession).count() == 0
    assert db.query(DocumentRecord).count() == 0
