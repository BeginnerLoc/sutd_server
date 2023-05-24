from fastapi import FastAPI
from routes.answer_route import answer_api_router

app = FastAPI()

app.include_router(answer_api_router)