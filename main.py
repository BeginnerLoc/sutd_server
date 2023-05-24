from fastapi import FastAPI
from routes.answer_route import answer_api_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.include_router(answer_api_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)