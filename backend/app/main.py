from fastapi import FastAPI

app = FastAPI(
    title="Career Network Copilot API",
    version="0.1.0",
    description="Human-in-the-loop career networking assistant API.",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}
