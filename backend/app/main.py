
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models.source import Source
from app.models.document import Document

from app.api.sources import router as sources_router
from app.api.documents import router as documents_router
from app.api.surahs import router as surahs_router
from app.api.translations import router as translations_router
from app.api.search import router as search_router
from app.api.hadiths import router as hadiths_router
from app.api.research import router as research_router
from app.api.evidence_sets import router as evidence_sets_router
from app.api.ai_context import router as ai_context_router
from app.api.ai_answer import router as ai_answer_router
from app.api.arguments import router as arguments_router
from app.api.argument_evidence import router as argument_evidence_router
from app.api.quran import router as quran_router
from app.api.evidence import router as evidence_router


app = FastAPI(
    title="Burhān",
    description="Islamic Knowledge Engine",
    version="0.1.0",
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# UTF-8 JSON responses
# ---------------------------------------------------------

@app.middleware("http")
async def add_utf8_charset(request, call_next):
    response = await call_next(request)

    if response.headers.get("content-type") == "application/json":
        response.headers["content-type"] = (
            "application/json; charset=utf-8"
        )

    return response


# ---------------------------------------------------------
# Routers
# ---------------------------------------------------------

app.include_router(sources_router)
app.include_router(documents_router)
app.include_router(surahs_router)
app.include_router(translations_router)
app.include_router(search_router)
app.include_router(hadiths_router)
app.include_router(research_router)
app.include_router(evidence_sets_router)
app.include_router(ai_context_router)
app.include_router(ai_answer_router)
app.include_router(arguments_router)
app.include_router(argument_evidence_router)
app.include_router(quran_router)
app.include_router(evidence_router)

# ---------------------------------------------------------
# Health check
# ---------------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "name": "Burhān",
        "status": "operational",
        "version": "0.1.0",
    }

