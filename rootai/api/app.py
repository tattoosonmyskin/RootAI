from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/secure-generate")
def secure_generate():
    return {"message": "Secure generation endpoint"}