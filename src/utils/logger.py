import os
import datetime
import json
import logging
import re
from rich.console import Console
from rich.theme import Theme

# Define a custom theme inspired by Claude's project
_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "step": "bold magenta",
    "agent": "bold blue",
    "success": "bold green"
})

class ExecutionLogger:
    def __init__(self, test_goal: str):
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.console = Console(theme=_THEME)
        
        # Create a safe directory name from the test goal
        test_slug = re.sub(r'[^a-zA-Z0-9]', '_', test_goal).strip('_')[:50]
        self.run_id = f"{self.timestamp}_{test_slug}"
        self.run_dir = f"run_logs/{self.run_id}"
        os.makedirs(self.run_dir, exist_ok=True)
        
        # Setup standard logging for file output
        self.logger = logging.getLogger(f"Execution_{self.timestamp}")
        self.logger.setLevel(logging.INFO)
        
        # File handler (standard text for dashboard parsing)
        fh = logging.FileHandler(f"{self.run_dir}/execution.log")
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        
        self.console.print(f"[*] Initialized execution logger in: [bold cyan]{self.run_dir}[/bold cyan]")
        self.console.print(f"[*] Test Goal: [bold yellow]{test_goal}[/bold yellow]\n")

    def info(self, message: str):
        self.logger.info(message)
        self.console.print(f"[info]INFO:[/info] {message}")

    def warning(self, message: str):
        self.logger.warning(message)
        self.console.print(f"[warning]WARNING:[/warning] {message}")

    def error(self, message: str):
        # Specific prefix for framework errors that we want to catch in tests
        self.logger.error(f"[FRAMEWORK_ERROR] {message}")
        self.console.print(f"[error]ERROR:[/error] {message}")

    def step(self, step_number: int, description: str):
        self.logger.info(f"STEP {step_number}: {description}")
        self.console.print(f"\n[step]>>> STEP {step_number}:[/step] [bold]{description}[/bold]")

    def agent_call(self, agent_name: str, action: str):
        self.logger.info(f"Agent {agent_name} -> {action}")
        self.console.print(f"[agent]{agent_name}[/agent] \u2192 {action}")

    def save_screenshot(self, name: str, data: bytes):
        path = f"{self.run_dir}/{name}.png"
        try:
            with open(path, "wb") as f:
                f.write(data)
            self.console.print(f"  [dim]Screenshot saved: {name}.png[/dim]")
            return path
        except Exception as e:
            self.error(f"Failed to save screenshot {name}: {e}")
            return None

    def save_plan(self, plan: list):
        path = f"{self.run_dir}/plan.json"
        try:
            with open(path, "w") as f:
                json.dump(plan, f, indent=4)
            self.console.print(f"  [dim]Plan saved to {path}[/dim]")
            return path
        except Exception as e:
            self.error(f"Failed to save plan: {e}")
            return None
