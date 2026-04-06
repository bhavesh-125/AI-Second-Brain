from fastapi import FastAPI

app = FastAPI(title="AI Second Brain API")

@app.get("/")
def read_root():
    return {"message": "AI Second Brain backend is running"}