# server/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager

from .vault import init_vault  

from .routers import pipeline, vault_routes  

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_vault()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(pipeline.router)
app.include_router(vault_routes.router)