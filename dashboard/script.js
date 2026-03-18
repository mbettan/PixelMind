
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
