from fastapi import FastAPI

app=FastAPI(
    title="Geospatial Measurement API",
    description="API for processing geospatial files and calculating measurements.",
    version="1.0.0",
    )

@app.get("/")
def root():
    return {
        "message": "Welcome to the Geospatial Measurement API. Use the /measure endpoint to calculate measurements from geospatial files."
    }

