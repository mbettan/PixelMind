import os
import json
import datetime
from pathlib import Path
import re

# Configuration
RUN_LOGS_DIR = Path("run_logs")
OUTPUT_DIR = Path("dashboard")

# Premium Glassmorphic Colors & Styles
CSS_CONTENT = """
:root {
    --primary: #6366f1;
    --primary-hover: #4f46e5;
    --bg: #0b0f1a;
    --card-bg: rgba(30, 41, 59, 0.5);
    --glass-border: rgba(255, 255, 255, 0.1);
    --text: #f8fafc;
    --text-muted: #94a3b8;
    --success: #10b981;
    --fail: #f43f5e;
    --accent: #8b5cf6;
}

* { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Outfit', sans-serif; }
body { background: var(--bg); color: var(--text); min-height: 100vh; overflow-x: hidden; }

.glass-bg {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: radial-gradient(circle at 20% 30%, #1e1b4b 0%, #0b0f1a 100%);
    z-index: -1;
}

.container { max-width: 1400px; margin: 0 auto; padding: 2.5rem; }

header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 3rem; }
.logo { display: flex; align-items: center; gap: 1rem; }
.logo .icon { font-size: 2.5rem; filter: drop-shadow(0 0 15px var(--primary)); }
.logo h1 { font-size: 1.8rem; font-weight: 600; letter-spacing: -0.05rem; }
.logo h1 span { color: var(--primary); }

.hidden { display: none !important; }

/* Execution Control */
.control-card { 
    background: var(--card-bg); backdrop-filter: blur(20px); 
    padding: 2.5rem; border-radius: 2rem; border: 1px solid var(--glass-border);
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    margin-bottom: 3rem;
}
.input-group { display: flex; gap: 1rem; margin-top: 1.5rem; }
.input-group input { 
    flex: 1; background: rgba(0,0,0,0.3); border: 1px solid var(--glass-border); 
    padding: 1.2rem 1.5rem; border-radius: 1.2rem; color: #fff; font-size: 1rem; 
    transition: all 0.3s;
}
.input-group input:focus { border-color: var(--primary); background: rgba(0,0,0,0.4); box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.15); outline: none; }
.input-group button { 
    background: linear-gradient(135deg, var(--primary), var(--accent)); 
    color: #fff; border: none; padding: 1rem 2.5rem; border-radius: 1.2rem; 
    font-weight: 600; cursor: pointer; transition: all 0.3s;
}
.input-group button:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(99, 102, 241, 0.3); }

/* Run Explorer Table */
.explorer-card {
    background: var(--card-bg); backdrop-filter: blur(20px);
    border-radius: 2rem; border: 1px solid var(--glass-border);
    padding: 2rem; overflow: hidden;
}

.filter-bar { display: none; } /* Hide old filter bar */
.filter-row td { padding: 0.5rem 1.2rem 1.5rem 1.2rem; }
.filter-row input { 
    width: 100%; background: rgba(0,0,0,0.2); border: 1px solid var(--glass-border); 
    padding: 0.6rem 1rem; border-radius: 0.8rem; color: var(--text); font-size: 0.85rem;
    transition: all 0.3s;
}
.filter-row input:focus { border-color: var(--primary); outline: none; background: rgba(0,0,0,0.4); }

.run-table { width: 100%; border-collapse: collapse; text-align: left; }
.run-table th { padding: 1.2rem; color: var(--text-muted); font-weight: 500; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05rem; border-bottom: 1px solid var(--glass-border); }
.run-table .header-row th { border-bottom: none; }
.run-table td { padding: 1.5rem 1.2rem; border-bottom: 1px solid rgba(255,255,255,0.03); vertical-align: middle; }
.run-table tr:last-child td { border-bottom: none; }
.run-table tr:hover { background: rgba(255,255,255,0.02); }

.status-pill { 
    display: inline-flex; align-items: center; gap: 0.5rem; 
    padding: 0.4rem 1rem; border-radius: 2rem; font-size: 0.8rem; font-weight: 600;
}
.status-pill.success { background: rgba(16, 185, 129, 0.15); color: var(--success); }
.status-pill.fail { background: rgba(244, 63, 94, 0.15); color: var(--fail); }

.run-name { font-weight: 600; font-size: 1rem; margin-bottom: 0.2rem; display: block; }
.run-url { font-size: 0.8rem; color: var(--text-muted); opacity: 0.7; }
.run-duration { font-family: monospace; color: var(--text-muted); }

.view-btn { 
    color: #fff; text-decoration: none; font-weight: 500; font-size: 0.8rem; 
    padding: 0.5rem 1rem; border-radius: 0.6rem; 
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--glass-border);
    transition: all 0.2s;
    display: inline-flex; align-items: center; gap: 0.5rem;
}
.view-btn:hover { background: var(--primary); border-color: var(--primary); transform: translateX(2px); }
.view-btn::after { content: '→'; font-size: 1rem; }

/* Report Specific Fixes */
.step-card { background: rgba(255,255,255,0.02); padding: 3rem; border-radius: 2.5rem; margin-bottom: 4rem; border: 1px solid var(--glass-border); }
.step-header { margin-bottom: 2rem; display: flex; justify-content: space-between; align-items: center; }
.step-num { font-size: 1.2rem; font-weight: 600; color: var(--primary); letter-spacing: 0.3rem; }

.img-row { display: flex; gap: 2.5rem; }
.img-wrap { flex: 1; position: relative; border-radius: 2rem; overflow: hidden; box-shadow: 0 15px 35px rgba(0,0,0,0.4); }
.img-label { 
    position: absolute; top: 1.5rem; left: 1.5rem; 
    background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(10px);
    color: var(--primary); padding: 0.5rem 1.2rem; border-radius: 1rem; 
    font-size: 0.75rem; font-weight: 700; letter-spacing: 0.1rem;
    border: 1px solid var(--glass-border); z-index: 10;
}
.img-wrap img { width: 100%; display: block; border: 1px solid rgba(255,255,255,0.05); }

.log-box { background: #05070a; padding: 2.5rem; border-radius: 2rem; border: 1px solid var(--glass-border); color: #818cf8; }
.back-link { color: var(--text-muted); text-decoration: none; transition: color 0.3s; }
.back-link:hover { color: var(--text); }
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Testing Platform - Run Explorer</title>
    <link rel="stylesheet" href="style.css">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600&display=swap" rel="stylesheet">
</head>
<body>
    <div class="glass-bg"></div>
    <div class="container">
        <header>
            <div class="logo">
                <span class="icon">🚀</span>
                <h1>Pixel<span>Mind</span></h1>
            </div>
            <div class="stats">
                <div class="stat-card">
                    <span class="label">Total Test Extractions</span>
                    <span class="value">{total_runs}</span>
                </div>
            </div>
        </header>

        <section class="execution-control">
            <div class="control-card">
                <h2>Launch Autonomous Agent</h2>
                <div class="input-group">
                    <input type="text" id="test-url" placeholder="Enter Target URL (e.g. https://www.mrgnyc.com/)">
                    <input type="text" id="test-goal" placeholder="Define Test Goal (e.g. Verify availability)">
                    <button id="run-btn" onclick="startTest()">Run AI Agent</button>
                </div>
                <div id="live-status" class="live-status hidden">
                    <div class="pulse-icon"></div>
                    <span id="status-text">Initialising...</span>
                    <div class="progress-bar"><div id="progress-fill"></div></div>
                </div>
            </div>
        </section>

        <main>
            <section class="explorer-card">
                <div class="table-container">
                    <table class="run-table" id="runs-table">
                        <thead>
                            <tr class="header-row">
                                <th>Prompt execution</th>
                                <th>Run ID</th>
                                <th>Status</th>
                                <th>Steps</th>
                                <th>Start Time</th>
                                <th>Duration</th>
                                <th>Action</th>
                            </tr>
                            <tr class="filter-row">
                                <td><input type="text" id="filter-name" placeholder="Filter Name..." onkeyup="filterTable()"></td>
                                <td><input type="text" id="filter-id" placeholder="Filter ID..." onkeyup="filterTable()"></td>
                                <td><input type="text" id="filter-status" placeholder="Filter Status..." onkeyup="filterTable()"></td>
                                <td></td>
                                <td></td>
                                <td></td>
                                <td></td>
                            </tr>
                        </thead>
                        <tbody>
                            {run_rows}
                        </tbody>
                    </table>
                </div>
            </section>
        </main>
    </div>
    <script src="script.js"></script>
</body>
</html>
"""

DETAIL_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Execution Report - {run_id}</title>
    <link rel="stylesheet" href="style.css">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600&display=swap" rel="stylesheet">
    {auto_refresh}
</head>
<body class="detail-page">
    <div class="glass-bg"></div>
    <div class="container">
        <header>
            <div class="logo" onclick="window.location.href='index.html'" style="cursor:pointer">
                <span class="icon">🚀</span>
                <h1>Visual <span>Report</span></h1>
            </div>
            <a href="index.html" class="back-link">← Return to Explorer</a>
        </header>

        <main>
            <div class="control-card detail-hero">
                <div class="status-pill {status}" style="margin-bottom:1rem;">{status_upper}</div>
                <h2 style="color:#fff; font-size:2rem; margin-bottom:1rem;">{goal}</h2>
                <p style="color:var(--text-muted); font-size:1.1rem; margin-bottom:0.5rem;">{url}</p>
                <p style="color:rgba(255,255,255,0.3); font-size:0.9rem;">ID: {run_id} • Executed on {timestamp}</p>
            </div>

            <section class="trace">
                <h3 style="margin-bottom:2rem; font-weight:400; color:var(--text-muted);">Self-Correction Evidence Trace</h3>
                {step_markup}
            </section>

            <section class="logs" style="margin-top:4rem;">
                <h3 style="margin-bottom:2rem; font-weight:400; color:var(--text-muted);">Low-Level Platform Logs</h3>
                <div class="log-box">
                    <pre>{log_content}</pre>
                </div>
            </section>
        </main>
    </div>
</body>
</html>
"""

SCRIPT_JS = """
function filterTable() {
    const filters = [
        { id: 'filter-name', col: 0 },
        { id: 'filter-id', col: 1 },
        { id: 'filter-status', col: 2 }
    ];
    
    const table = document.getElementById('runs-table');
    const rows = table.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

    for (let i = 0; i < rows.length; i++) {
        let show = true;
        for (const f of filters) {
            const query = document.getElementById(f.id).value.toLowerCase();
            const cell = rows[i].getElementsByTagName('td')[f.col];
            if (cell) {
                const text = cell.textContent || cell.innerText;
                if (text.toLowerCase().indexOf(query) === -1) {
                    show = false;
                    break;
                }
            }
        }
        rows[i].style.display = show ? "" : "none";
    }
}

function startTest() {
    const url = document.getElementById('test-url').value;
    const goal = document.getElementById('test-goal').value;
    const runBtn = document.getElementById('run-btn');
    const statusDiv = document.getElementById('live-status');
    const statusText = document.getElementById('status-text');
    const progressFill = document.getElementById('progress-fill');

    if (!url || !goal) {
        alert("Domain and Extraction Goal are required.");
        return;
    }

    // Prepend a "Running" row to the table
    const table = document.getElementById('runs-table').getElementsByTagName('tbody')[0];
    const newRow = table.insertRow(0);
    const ts = new Date();
    const tsStr = ts.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    const runId = ts.getFullYear() + ("0"+(ts.getMonth()+1)).slice(-2) + ("0"+ts.getDate()).slice(-2) + "_" + ("0"+ts.getHours()).slice(-2) + ("0"+ts.getMinutes()).slice(-2) + ("0"+ts.getSeconds()).slice(-2);
    
    newRow.innerHTML = `
        <td>
            <span class="run-name">${goal}</span>
            <span class="run-url">${url}</span>
        </td>
        <td>${runId.replace('_', '')}</td>
        <td><span class="status-pill fail" style="background:rgba(99, 102, 241, 0.2); color:#818cf8;">RUNNING</span></td>
        <td>-</td>
        <td>${tsStr}</td>
        <td class="run-duration">--</td>
        <td><a href="report_${runId}_${goal.replace(/ /g, '_')}.html" class="view-btn">View Report</a></td>
    `;
    newRow.classList.add('running-row');

    runBtn.disabled = true;
    runBtn.style.opacity = "0.5";
    statusDiv.classList.remove('hidden');
    progressFill.style.width = "10%";
    statusText.innerText = "Initializing GenAI Engine...";

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/run`);

    ws.onopen = () => ws.send(JSON.stringify({ url, goal }));

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'status') {
            statusText.innerText = data.message;
            let currentWidth = parseInt(progressFill.style.width) || 10;
            if (currentWidth < 95) progressFill.style.width = (currentWidth + 5) + "%";
        } else if (data.type === 'finished') {
            progressFill.style.width = "100%";
            statusText.innerText = "Execution Complete. Updating Explorer...";
            setTimeout(() => window.location.reload(), 2000);
        } else if (data.type === 'error') {
            alert("Agent Interrupt: " + data.message);
            window.location.reload();
        }
    };
}
"""

def get_duration(log_content):
    lines = log_content.splitlines()
    if not lines: return "N/A"
    
    ts_pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"
    start_ts = None
    end_ts = None
    
    for line in lines:
        match = re.search(ts_pattern, line)
        if match:
            start_ts = datetime.datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
            break
            
    for line in reversed(lines):
        match = re.search(ts_pattern, line)
        if match:
            end_ts = datetime.datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
            break
            
    if start_ts and end_ts:
        diff = end_ts - start_ts
        minutes, seconds = divmod(diff.seconds, 60)
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"
    return "N/A"

def generate_dashboard():
    OUTPUT_DIR.mkdir(exist_ok=True)
    if not RUN_LOGS_DIR.exists(): return

    runs = []
    table_rows = ""
    
    for run_dir in sorted(RUN_LOGS_DIR.iterdir(), reverse=True):
        if not run_dir.is_dir(): continue
        
        plan_path = run_dir / "plan.json"
        log_path = run_dir / "execution.log"
        if not plan_path.exists(): continue
        
        with open(plan_path) as f:
            plan = json.load(f)
        
        status = "success"
        log_content = ""
        if log_path.exists():
            with open(log_path) as f:
                log_content = f.read()
                if "ERROR" in log_content or "[Failure]" in log_content or "failed to fulfill" in log_content:
                    status = "fail"
        
        duration = get_duration(log_content)
        ts_str = run_dir.name[:15]
        try:
            ts = datetime.datetime.strptime(ts_str, "%Y%m%d_%H%M%S").strftime("%b %d, %H:%M")
        except:
            ts = ts_str

        goal = run_dir.name[16:].replace("_", " ")
        url = "N/A"
        if log_path.exists():
            for line in log_content.splitlines():
                if "Target URL:" in line:
                    url = line.split("Target URL:")[1].strip()
                    break

        run_data = {
            "id": run_dir.name,
            "goal": goal,
            "url": url,
            "timestamp": ts,
            "status": status,
            "duration": duration,
            "steps": len(plan) if isinstance(plan, list) else 1
        }
        runs.append(run_data)

        # Step Trace Generation
        step_items = ""
        for i in range(1, 20):
            before = run_dir / f"step_{i}_attempt_1_before.png"
            after = run_dir / f"step_{i}_attempt_1_after.png"
            # Fallbacks for retries
            best_after = after
            if not after.exists():
                for attempt in [2, 3]:
                    alt = run_dir / f"step_{i}_attempt_{attempt}_after.png"
                    if alt.exists():
                        best_after = alt
            
            if not before.exists(): before = run_dir / f"step_{i}_before.png"
            
            if before.exists() and best_after.exists():
                step_items += f"""
                <div class="step-card">
                    <div class="step-header">
                        <span class="step-num">STEP {i}</span>
                    </div>
                    <div class="img-row">
                        <div class="img-wrap">
                            <span class="img-label">PRE-ACTION</span>
                            <img src="../run_logs/{run_dir.name}/{before.name}">
                        </div>
                        <div class="img-wrap">
                            <span class="img-label">POST-ACTION</span>
                            <img src="../run_logs/{run_dir.name}/{best_after.name}">
                        </div>
                    </div>
                </div>
                """

        detail_filename = f"report_{run_dir.name}.html"
        is_finished = "Finished" in log_content or "Success" in log_content or "failed to fulfill" in log_content
        refresh_tag = '<meta http-equiv="refresh" content="5">' if not is_finished else ''
        
        with open(OUTPUT_DIR / detail_filename, "w") as f:
            f.write(DETAIL_TEMPLATE.format(
                run_id=run_dir.name, goal=goal, url=url, status=status, status_upper=status.upper(),
                timestamp=ts, step_markup=step_items, log_content=log_content, auto_refresh=refresh_tag
            ))

        table_rows += f"""
        <tr>
            <td>
                <span class="run-name">{goal}</span>
                <span class="run-url">{url}</span>
            </td>
            <td>{run_dir.name.split('_')[0]}{run_dir.name.split('_')[1]}</td>
            <td><span class="status-pill {status}">{status.upper()}</span></td>
            <td>{run_data['steps']}</td>
            <td>{ts}</td>
            <td class="run-duration">{duration}</td>
            <td><a href="{detail_filename}" class="view-btn">View Report</a></td>
        </tr>
        """

    with open(OUTPUT_DIR / "index.html", "w") as f:
        f.write(HTML_TEMPLATE.format(total_runs=len(runs), run_rows=table_rows))
    
    with open(OUTPUT_DIR / "style.css", "w") as f:
        f.write(CSS_CONTENT)

    with open(OUTPUT_DIR / "script.js", "w") as f:
        f.write(SCRIPT_JS)
        
    with open(OUTPUT_DIR / "runs_data.json", "w") as f:
        json.dump(runs, f)

if __name__ == "__main__":
    generate_dashboard()
