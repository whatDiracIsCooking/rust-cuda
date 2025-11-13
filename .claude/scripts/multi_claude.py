#!/usr/bin/env python3
"""
Multi-Claude Command Executor

Executes multiple Claude CLI commands either sequentially or in parallel.
Always runs in batch mode to get direct responses without conversational back-and-forth.

Fixed timeouts:
- Per-worker timeout: 5 minutes
- Script-level timeout: 10 minutes

All task results are automatically saved as JSON logs in .logs/ directory.
Each log file contains: task metadata, command, stdout, stderr, and success status.

IMPORTANT: The 'tools' field is REQUIRED for each task.
See .claude/scripts/TOOLS_REFERENCE.md for complete tool documentation and usage guidelines.

Example configuration: .claude/scripts/example_tasks.json
"""

import subprocess
import argparse
import json
import sys
import re
import signal
from pathlib import Path
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


class ClaudeTask:
    """Represents a single Claude CLI task

    Args:
        prompt: The task prompt/instruction
        tools: List of allowed tools (REQUIRED - see TOOLS_REFERENCE.md)
        files: Optional list of files to include
        name: Optional task name (auto-generated if not provided)
        model: Optional Claude model to use
    """

    def __init__(self, prompt: str, tools: List[str], files: Optional[List[str]] = None,
                 name: Optional[str] = None, model: Optional[str] = None):
        self.prompt = prompt
        self.tools = tools
        self.files = files or []
        self.name = name or f"task_{id(self)}"
        self.model = model

    def build_command(self) -> List[str]:
        """Build the Claude CLI command"""
        cmd = ["claude", "--print", "--permission-mode", "bypassPermissions"]

        # Use minimal settings to bypass CLAUDE.md, then add simple batch mode prompt
        cmd.extend(["--setting-sources", ""])
        cmd.extend(["--system-prompt",
                   "You are a task executor. Execute the given task exactly as specified. Do not ask questions. Do not provide explanations unless requested. Output only the requested result."])

        # Add model if specified
        if self.model:
            cmd.extend(["--model", self.model])

        # Build prompt with file list (no @ syntax - workers must read files explicitly)
        if self.files:
            file_list = "\n".join([f"- {file}" for file in self.files])
            full_prompt = f"FILES TO PROCESS:\n{file_list}\n\n{self.prompt}"
        else:
            full_prompt = self.prompt

        # Add prompt as positional argument
        cmd.append(full_prompt)

        # Add tools AFTER prompt (space-separated as multiple args)
        if self.tools:
            cmd.append("--allowed-tools")
            cmd.extend(self.tools)

        return cmd

    def __str__(self):
        files_str = ", ".join(self.files) if self.files else "no files"
        tools_str = f", tools: {','.join(self.tools)}" if self.tools else ""
        return f"{self.name}: {self.prompt[:50]}... ({files_str}{tools_str})"


class MultiClaudeExecutor:
    """Executes multiple Claude CLI commands"""

    def __init__(self, tasks: List[ClaudeTask], max_workers: int = 4, verbose: bool = False,
                 log_dir: str = ".logs"):
        self.tasks = tasks
        self.max_workers = max_workers
        self.verbose = verbose
        self.results = []
        self.parallel = max_workers > 1
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.worker_counter = 0

    def _sanitize_filename(self, name: str) -> str:
        """Convert task name to safe filename"""
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
        safe_name = re.sub(r'_+', '_', safe_name)
        return safe_name[:50]

    def execute_task(self, task: ClaudeTask, worker_id: int = 0) -> Dict:
        """Execute a single Claude task"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = self._sanitize_filename(task.name)
        log_filename = f"w{worker_id}_{safe_name}_{timestamp}.json"
        log_path = self.log_dir / log_filename

        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Worker {worker_id}: Starting {task.name}")
            print(f"  Command: {' '.join(task.build_command())}")
            print(f"  Log: {log_path}")

        try:
            result = subprocess.run(
                task.build_command(),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            task_result = {
                "name": task.name,
                "worker_id": worker_id,
                "timestamp": timestamp,
                "prompt": task.prompt,
                "files": task.files,
                "model": task.model,
                "tools": task.tools,
                "command": task.build_command(),
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0,
                "log_file": str(log_path)
            }

            # Write log file as JSON
            with open(log_path, 'w') as f:
                json.dump(task_result, f, indent=2)

            if self.verbose:
                status = "✓" if task_result["success"] else "✗"
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Worker {worker_id}: {status} Completed {task.name}")
                if not task_result["success"]:
                    print(f"  Error: {result.stderr[:200]}")

            return task_result

        except subprocess.TimeoutExpired:
            error_msg = "Command timed out after 5 minutes"

            error_result = {
                "name": task.name,
                "worker_id": worker_id,
                "timestamp": timestamp,
                "prompt": task.prompt,
                "files": task.files,
                "model": task.model,
                "tools": task.tools,
                "command": task.build_command(),
                "returncode": -1,
                "stdout": "",
                "stderr": error_msg,
                "success": False,
                "status": "TIMEOUT",
                "log_file": str(log_path)
            }

            # Write timeout log as JSON
            with open(log_path, 'w') as f:
                json.dump(error_result, f, indent=2)
            if self.verbose:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Worker {worker_id}: ✗ Timeout {task.name}")
            return error_result

        except Exception as e:
            error_msg = str(e)

            error_result = {
                "name": task.name,
                "worker_id": worker_id,
                "timestamp": timestamp,
                "prompt": task.prompt,
                "files": task.files,
                "model": task.model,
                "tools": task.tools,
                "command": task.build_command(),
                "returncode": -1,
                "stdout": "",
                "stderr": error_msg,
                "success": False,
                "status": "ERROR",
                "log_file": str(log_path)
            }

            # Write error log as JSON
            with open(log_path, 'w') as f:
                json.dump(error_result, f, indent=2)
            if self.verbose:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Worker {worker_id}: ✗ Error {task.name}: {e}")
            return error_result

    def execute_sequential(self) -> List[Dict]:
        """Execute tasks sequentially"""
        results = []
        for i, task in enumerate(self.tasks, 1):
            if self.verbose:
                print(f"\n--- Task {i}/{len(self.tasks)} ---")
            results.append(self.execute_task(task, worker_id=0))
        return results

    def execute_parallel(self) -> List[Dict]:
        """Execute tasks in parallel"""
        results = []
        worker_id = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_worker = {}
            for task in self.tasks:
                worker_id += 1
                future = executor.submit(self.execute_task, task, worker_id)
                future_to_worker[future] = worker_id

            for future in as_completed(future_to_worker):
                results.append(future.result())

        return results

    def execute(self) -> List[Dict]:
        """Execute all tasks"""
        if self.verbose:
            mode = "parallel" if self.parallel else "sequential"
            print(f"Executing {len(self.tasks)} tasks in {mode} mode")
            if self.parallel:
                print(f"Max workers: {self.max_workers}")
            print()

        if self.parallel:
            self.results = self.execute_parallel()
        else:
            self.results = self.execute_sequential()

        return self.results

    def print_summary(self):
        """Print execution summary"""
        successful = sum(1 for r in self.results if r["success"])
        failed = len(self.results) - successful

        print("\n" + "="*60)
        print("EXECUTION SUMMARY")
        print("="*60)
        print(f"Total tasks: {len(self.results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print()

        # Print all log files
        print("Log files:")
        for result in sorted(self.results, key=lambda r: r.get("worker_id", 0)):
            worker_id = result.get("worker_id", 0)
            status = "✓" if result["success"] else "✗"
            log_file = result.get("log_file", "N/A")
            print(f"  {status} Worker {worker_id}: {result['name']}")
            print(f"    {log_file}")
        print()

        if failed > 0:
            print("Failed tasks:")
            for result in self.results:
                if not result["success"]:
                    print(f"  - {result['name']}: {result['stderr'][:100]}")
            print()




def load_tasks_from_json(json_file: str) -> List[ClaudeTask]:
    """Load tasks from a JSON configuration file"""
    with open(json_file, 'r') as f:
        data = json.load(f)

    tasks = []
    for task_data in data.get("tasks", []):
        # Validate required fields
        if "prompt" not in task_data:
            raise ValueError(f"Task missing required 'prompt' field: {task_data.get('name', 'unnamed')}")
        if "tools" not in task_data or not task_data["tools"]:
            raise ValueError(f"Task missing required 'tools' field: {task_data.get('name', 'unnamed')}. See TOOLS_REFERENCE.md")

        task = ClaudeTask(
            prompt=task_data["prompt"],
            tools=task_data["tools"],
            files=task_data.get("files", []),
            name=task_data.get("name"),
            model=task_data.get("model")
        )
        tasks.append(task)

    return tasks


class ScriptTimeoutError(Exception):
    """Raised when the entire script exceeds its timeout"""
    pass


def timeout_handler(signum, frame):
    """Handle script-level timeout"""
    raise ScriptTimeoutError("Script exceeded 10-minute timeout")


def main():
    # Set up script-level timeout (10 minutes)
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(600)  # 10 minutes = 600 seconds

    parser = argparse.ArgumentParser(
        description="Execute multiple Claude CLI commands in batch mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Execute tasks from JSON config (parallel, 4 workers by default)
  %(prog)s --config tasks.json

  # Execute sequentially (1 worker)
  %(prog)s --config tasks.json --workers 1

  # Execute in parallel with 2 workers
  %(prog)s --config tasks.json --workers 2

  # Single task with specific tools (--tools is REQUIRED)
  %(prog)s --prompt "Summarize this code" --files main.cu utils.cu \
    --tools mcp__serena__read_file mcp__serena__get_symbols_overview

  # Find patterns in code
  %(prog)s --prompt "Find all CUDA kernels" --files src/kernels.cu \
    --tools mcp__serena__read_file mcp__serena__search_for_pattern

  # All results automatically saved as JSON logs in .logs/ directory

  # Use example configuration
  %(prog)s --config .claude/scripts/example_tasks.json --workers 3

Example tasks.json format (see .claude/scripts/example_tasks.json for full example):
{
  "tasks": [
    {
      "name": "summarize_main",
      "prompt": "Summarize this file",
      "files": ["src/main.cu"],
      "model": "sonnet",
      "tools": ["mcp__serena__read_file", "mcp__serena__get_symbols_overview"]
    },
    {
      "name": "find_bugs",
      "prompt": "Look for potential bugs",
      "files": ["src/utils.cu"],
      "tools": ["mcp__serena__read_file", "mcp__serena__find_symbol", "mcp__serena__search_for_pattern"]
    }
  ]
}

Tools Reference: See .claude/scripts/TOOLS_REFERENCE.md for complete tool list and usage guidelines.
        """
    )

    parser.add_argument("--config", "-c", help="JSON file with task configuration")
    parser.add_argument("--prompt", "-p", help="Single prompt to execute")
    parser.add_argument("--files", "-f", nargs="+", help="Files to include (for single prompt)")
    parser.add_argument("--model", "-m", default="haiku", help="Claude model to use (e.g. 'sonnet', 'opus', 'haiku')")
    parser.add_argument("--tools", "-t", nargs="+", help="Tools to allow (see TOOLS_REFERENCE.md)")
    parser.add_argument("--workers", "-w", type=int, default=4, help="Max parallel workers (1=sequential, 2-4=parallel, capped at 4)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Cap max workers at 4
    if args.workers > 4:
        args.workers = 4

    # Load tasks
    tasks = []
    if args.config:
        tasks = load_tasks_from_json(args.config)
    elif args.prompt:
        if not args.tools:
            print("Error: --tools is required. See .claude/scripts/TOOLS_REFERENCE.md for available tools.", file=sys.stderr)
            sys.exit(1)

        task = ClaudeTask(
            prompt=args.prompt,
            tools=args.tools,
            files=args.files or [],
            name="cli_task",
            model=args.model
        )
        tasks = [task]
    else:
        parser.print_help()
        sys.exit(1)

    if not tasks:
        print("Error: No tasks to execute", file=sys.stderr)
        sys.exit(1)

    try:
        # Execute tasks
        executor = MultiClaudeExecutor(
            tasks=tasks,
            max_workers=args.workers,
            verbose=args.verbose
        )

        results = executor.execute()
        executor.print_summary()

        # Cancel the timeout alarm
        signal.alarm(0)

        # Exit with error if any task failed
        if not all(r["success"] for r in results):
            sys.exit(1)

    except ScriptTimeoutError as e:
        signal.alarm(0)  # Cancel alarm
        print("\n" + "="*60, file=sys.stderr)
        print("SCRIPT TIMEOUT", file=sys.stderr)
        print("="*60, file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        print("\nThe entire script exceeded the 10-minute timeout.", file=sys.stderr)
        print("Consider reducing batch size or optimizing tasks.", file=sys.stderr)
        print("="*60, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
