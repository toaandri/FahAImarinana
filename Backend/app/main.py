from fastapi import FastAPI

app = FastAPI(title="FANILO Backend")

@app.get("/health")
def health():
    return {"status": "ok"}
