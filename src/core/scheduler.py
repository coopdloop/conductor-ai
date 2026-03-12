import json
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum


class ScheduleType(Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


@dataclass
class ScheduledTask:
    """Represents a scheduled task."""
    id: str
    name: str
    description: str
    schedule_type: ScheduleType
    scheduled_for: str  # ISO datetime
    callback_type: str  # reminder, workflow_action, custom
    callback_params: Dict[str, Any]
    completed: bool = False
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    recurring: bool = False
    created_at: Optional[str] = None


class Scheduler:
    """Handles scheduling and reminders for workflows."""

    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path('.conductor')
        self.data_dir.mkdir(exist_ok=True)

        self.schedule_file = self.data_dir / 'schedule.json'
        self.tasks: Dict[str, ScheduledTask] = {}
        self.callbacks: Dict[str, Callable] = {}
        self.running = False
        self.thread = None

        self.load_schedule()
        self.register_default_callbacks()

    def register_callback(self, callback_type: str, callback_func: Callable):
        """Register a callback function for a specific type."""
        self.callbacks[callback_type] = callback_func

    def schedule_reminder(self,
                         message: str,
                         scheduled_for: datetime,
                         recurring: bool = False,
                         schedule_type: ScheduleType = ScheduleType.ONCE,
                         metadata: Dict[str, Any] = None) -> str:
        """Schedule a reminder."""

        task_id = self._generate_task_id(message)

        task = ScheduledTask(
            id=task_id,
            name=f"Reminder: {message[:50]}...",
            description=message,
            schedule_type=schedule_type,
            scheduled_for=scheduled_for.isoformat(),
            callback_type="reminder",
            callback_params={
                "message": message,
                "metadata": metadata or {}
            },
            recurring=recurring,
            next_run=scheduled_for.isoformat(),
            created_at=datetime.now().isoformat()
        )

        self.tasks[task_id] = task
        self.save_schedule()
        return task_id

    def schedule_workflow_action(self,
                                workflow_id: str,
                                action_id: str,
                                scheduled_for: datetime,
                                action_description: str = "") -> str:
        """Schedule a workflow action to be executed."""

        task_id = self._generate_task_id(f"workflow_{workflow_id}_{action_id}")

        task = ScheduledTask(
            id=task_id,
            name=f"Workflow Action: {action_description[:50]}...",
            description=action_description,
            schedule_type=ScheduleType.ONCE,
            scheduled_for=scheduled_for.isoformat(),
            callback_type="workflow_action",
            callback_params={
                "workflow_id": workflow_id,
                "action_id": action_id,
                "description": action_description
            },
            next_run=scheduled_for.isoformat(),
            created_at=datetime.now().isoformat()
        )

        self.tasks[task_id] = task
        self.save_schedule()
        return task_id

    def schedule_custom_task(self,
                           name: str,
                           callback_type: str,
                           scheduled_for: datetime,
                           params: Dict[str, Any],
                           recurring: bool = False,
                           schedule_type: ScheduleType = ScheduleType.ONCE) -> str:
        """Schedule a custom task."""

        task_id = self._generate_task_id(name)

        task = ScheduledTask(
            id=task_id,
            name=name,
            description=params.get('description', name),
            schedule_type=schedule_type,
            scheduled_for=scheduled_for.isoformat(),
            callback_type=callback_type,
            callback_params=params,
            recurring=recurring,
            next_run=scheduled_for.isoformat(),
            created_at=datetime.now().isoformat()
        )

        self.tasks[task_id] = task
        self.save_schedule()
        return task_id

    def get_due_tasks(self) -> List[ScheduledTask]:
        """Get tasks that are due to run."""
        now = datetime.now()
        due_tasks = []

        for task in self.tasks.values():
            if not task.completed and task.next_run:
                try:
                    next_run = datetime.fromisoformat(task.next_run)
                    if next_run <= now:
                        due_tasks.append(task)
                except:
                    continue

        return sorted(due_tasks, key=lambda t: t.next_run)

    def get_upcoming_tasks(self, hours: int = 24) -> List[ScheduledTask]:
        """Get tasks scheduled in the next X hours."""
        now = datetime.now()
        future = now + timedelta(hours=hours)
        upcoming = []

        for task in self.tasks.values():
            if not task.completed and task.next_run:
                try:
                    next_run = datetime.fromisoformat(task.next_run)
                    if now < next_run <= future:
                        upcoming.append(task)
                except:
                    continue

        return sorted(upcoming, key=lambda t: t.next_run)

    def execute_due_tasks(self) -> List[Dict[str, Any]]:
        """Execute all due tasks and return results."""
        due_tasks = self.get_due_tasks()
        results = []

        for task in due_tasks:
            result = self.execute_task(task)
            results.append(result)

        return results

    def execute_task(self, task: ScheduledTask) -> Dict[str, Any]:
        """Execute a single task."""
        result = {
            "task_id": task.id,
            "name": task.name,
            "executed_at": datetime.now().isoformat(),
            "success": False,
            "message": "",
            "output": None
        }

        try:
            if task.callback_type in self.callbacks:
                callback = self.callbacks[task.callback_type]
                output = callback(task.callback_params)
                result["output"] = output
                result["success"] = True
                result["message"] = "Task executed successfully"
            else:
                result["message"] = f"No callback registered for type: {task.callback_type}"

            # Update task
            task.last_run = datetime.now().isoformat()

            # Handle recurring tasks
            if task.recurring:
                task.next_run = self._calculate_next_run(task)
            else:
                task.completed = True
                task.next_run = None

            self.save_schedule()

        except Exception as e:
            result["message"] = f"Error executing task: {str(e)}"
            result["error"] = str(e)

        return result

    def start_scheduler(self):
        """Start the background scheduler thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.thread.start()

    def stop_scheduler(self):
        """Stop the background scheduler thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

    def _scheduler_loop(self):
        """Main scheduler loop that runs in background thread."""
        while self.running:
            try:
                # Execute due tasks
                self.execute_due_tasks()

                # Sleep for 60 seconds before next check
                time.sleep(60)
            except Exception as e:
                print(f"Scheduler error: {e}")
                time.sleep(60)  # Continue running even if there's an error

    def _calculate_next_run(self, task: ScheduledTask) -> str:
        """Calculate next run time for recurring tasks."""
        current_run = datetime.fromisoformat(task.next_run)

        if task.schedule_type == ScheduleType.DAILY:
            next_run = current_run + timedelta(days=1)
        elif task.schedule_type == ScheduleType.WEEKLY:
            next_run = current_run + timedelta(weeks=1)
        elif task.schedule_type == ScheduleType.MONTHLY:
            # Add one month (approximately)
            if current_run.month == 12:
                next_run = current_run.replace(year=current_run.year + 1, month=1)
            else:
                next_run = current_run.replace(month=current_run.month + 1)
        else:
            # Default to daily for custom types
            next_run = current_run + timedelta(days=1)

        return next_run.isoformat()

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.save_schedule()
            return True
        return False

    def complete_task(self, task_id: str) -> bool:
        """Mark a task as completed."""
        if task_id in self.tasks:
            self.tasks[task_id].completed = True
            self.tasks[task_id].next_run = None
            self.save_schedule()
            return True
        return False

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status information for a task."""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            return {
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "completed": task.completed,
                "last_run": task.last_run,
                "next_run": task.next_run,
                "recurring": task.recurring,
                "schedule_type": task.schedule_type.value
            }
        return None

    def register_default_callbacks(self):
        """Register default callback functions."""

        def reminder_callback(params: Dict[str, Any]) -> Dict[str, Any]:
            """Handle reminder callbacks."""
            message = params.get('message', 'Reminder')
            metadata = params.get('metadata', {})

            # This could be enhanced to send notifications
            # For now, just return the reminder info
            return {
                "type": "reminder",
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata
            }

        def workflow_action_callback(params: Dict[str, Any]) -> Dict[str, Any]:
            """Handle workflow action callbacks."""
            workflow_id = params.get('workflow_id')
            action_id = params.get('action_id')
            description = params.get('description', '')

            # This would integrate with the workflow engine
            return {
                "type": "workflow_action",
                "workflow_id": workflow_id,
                "action_id": action_id,
                "description": description,
                "timestamp": datetime.now().isoformat(),
                "status": "executed"
            }

        self.register_callback("reminder", reminder_callback)
        self.register_callback("workflow_action", workflow_action_callback)

    def load_schedule(self):
        """Load scheduled tasks from file."""
        if self.schedule_file.exists():
            try:
                with open(self.schedule_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for task_data in data.get('tasks', []):
                    # Convert schedule_type back to enum
                    task_data['schedule_type'] = ScheduleType(task_data['schedule_type'])
                    task = ScheduledTask(**task_data)
                    self.tasks[task.id] = task
            except Exception as e:
                print(f"Error loading schedule: {e}")

    def save_schedule(self):
        """Save scheduled tasks to file."""
        data = {
            "tasks": [],
            "last_updated": datetime.now().isoformat()
        }

        for task in self.tasks.values():
            task_dict = asdict(task)
            # Convert enum to string
            task_dict['schedule_type'] = task.schedule_type.value
            data["tasks"].append(task_dict)

        try:
            with open(self.schedule_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving schedule: {e}")

    def _generate_task_id(self, base_name: str) -> str:
        """Generate a unique task ID."""
        import re
        base_id = re.sub(r'[^a-z0-9]+', '_', base_name.lower()).strip('_')
        base_id = base_id[:30]  # Limit length

        # Ensure uniqueness
        counter = 1
        task_id = base_id
        while task_id in self.tasks:
            task_id = f"{base_id}_{counter}"
            counter += 1

        return task_id

    def cleanup_completed_tasks(self, older_than_days: int = 30):
        """Clean up old completed tasks."""
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        to_remove = []

        for task_id, task in self.tasks.items():
            if task.completed and task.last_run:
                try:
                    last_run = datetime.fromisoformat(task.last_run)
                    if last_run < cutoff_date:
                        to_remove.append(task_id)
                except:
                    continue

        for task_id in to_remove:
            del self.tasks[task_id]

        if to_remove:
            self.save_schedule()

        return len(to_remove)

    def get_schedule_summary(self) -> Dict[str, Any]:
        """Get a summary of the current schedule."""
        now = datetime.now()

        total_tasks = len(self.tasks)
        completed_tasks = len([t for t in self.tasks.values() if t.completed])
        active_tasks = total_tasks - completed_tasks

        due_now = len(self.get_due_tasks())
        upcoming_24h = len(self.get_upcoming_tasks(24))

        return {
            "total_tasks": total_tasks,
            "active_tasks": active_tasks,
            "completed_tasks": completed_tasks,
            "due_now": due_now,
            "upcoming_24h": upcoming_24h,
            "last_check": now.isoformat()
        }