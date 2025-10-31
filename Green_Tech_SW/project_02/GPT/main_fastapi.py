# main_fastapi.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "ok", "msg": "FastAPI up"}

# 실행: uvicorn main_fastapi:app --reload --port 8000
