from contextlib import asynccontextmanager
# from mangum import Mangum
from fastapi import FastAPI

from backend.routers.task_router import router as task_router
from backend.routers.user_router import router as user_router
from backend.routers.system_router import router as system_router
from backend.voice_router.websocket import router as voice_router
from backend.models.base_model import Base
from backend.models.user_model import User
from backend.auth_placeholder import MOCK_USER_ID
from backend.dependencies import db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan function to handle application startup and shutdown events. It creates the database tables on startup."""
    engine = db.get_engine()
    Base.metadata.create_all(engine)
    with db.get_session_factory()() as session:
        user = session.get(User, MOCK_USER_ID)
        if user is None:
            session.add(
                User(
                    id=MOCK_USER_ID,
                    username="local-user",
                    display_name="Local User",
                )
            )
            session.commit()
    yield
    engine.dispose()

app = FastAPI(
    title="Tasks Router API",
    description="API for managing tasks and users with local SQLite database integration.",
    version="1.0.0",
    redirect_slashes=False,
    lifespan=lifespan
)

# handler = Mangum(app)

app.include_router(task_router)
app.include_router(user_router)
app.include_router(system_router)
app.include_router(voice_router)
