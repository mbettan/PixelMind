import asyncio
import json
import os
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import sys
import io

# Local imports
from main import run_test
from utils.dashboard_generator_v2 import generate_dashboard

app = FastAPI(title="AI-Driven Web Testing Platform")

# Paths
DASHBOARD_DIR = Path("dashboard")
RUN_LOGS_DIR = Path("run_logs")

# Ensure dashboard exists
DASHBOARD_DIR.mkdir(exist_ok=True)

# API Endpoints (Must be BEFORE static mount)
@app.get("/api/runs")
async def get_runs():
    try:
        with open(DASHBOARD_DIR / "runs_data.json") as f:
            return json.load(f)
    except:
        return []

@app.websocket("/ws/run")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        params = json.loads(data)
        url = params.get("url")
        goal = params.get("goal")

        if not url or not goal:
            await websocket.send_json({"type": "error", "message": "Missing URL or Goal"})
            return

        await websocket.send_json({"type": "status", "message": f"Starting test for: {url}"})
        
        async def status_callback(msg: str):
            try:
                await websocket.send_json({"type": "status", "message": msg})
            except:
                pass

        # Run test with live updates
        await run_test(goal, url, update_callback=status_callback)
        
        await websocket.send_json({"type": "finished", "message": "Test completed successfully!"})
        
        # Regenerate dashboard data
        generate_dashboard()
        
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})

# Static files for logs
app.mount("/run_logs", StaticFiles(directory=str(RUN_LOGS_DIR)), name="run_logs")

# Serve dashboard at root (THIS MUST BE LAST)
# This will serve index.html for / and any other files like style.css, script.js, report_*.html
app.mount("/", StaticFiles(directory=str(DASHBOARD_DIR), html=True), name="dashboard")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
