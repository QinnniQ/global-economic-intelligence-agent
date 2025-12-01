from fastapi import FastAPI
from src.backend.routes.health import router as health_router
from src.backend.routes.ask_basic import router as ask_basic_router 
from src.backend.routes.macro_basic import router as macro_basic_router
from src.backend.routes.macro_summary import router as macro_summary_router
from src.backend.routes.ask_economic import router as ask_economic_router
from src.backend.routes.rag_ingest import router as rag_ingest_router
from src.backend.routes.rag_search import router as rag_search_router
from src.backend.routes.report_generate import router as report_generate_router
from src.backend.routes.macro_live import router as macro_live_router









app = FastAPI(
    title="Global Economic Intelligence Agent",
    version="0.1.0",
)

# Register routes
app.include_router(health_router)
app.include_router(ask_basic_router)
app.include_router(macro_basic_router)
app.include_router(macro_summary_router)
app.include_router(ask_economic_router)
app.include_router(rag_ingest_router)
app.include_router(rag_search_router)
app.include_router(report_generate_router)
app.include_router(macro_live_router)





