from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import JWTAuthMiddleware
from app.routers import accounts, positions

app = FastAPI(title="Wheelhouse API", version="0.1.0")

app.add_middleware(JWTAuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts.router)
app.include_router(positions.router)


@app.get("/health")
def health():
    return {"status": "ok"}
