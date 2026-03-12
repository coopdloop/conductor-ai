#!/usr/bin/env python3
"""
Enhanced Conductor - Workflow & Documentation Orchestrator

A comprehensive daily workflow orchestrator with documentation processing,
skill-based workflows, scheduling, and MCP service integration.
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import click
from rich.columns import Columns
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.doc_processor import DocumentProcessor
from core.mcp_manager import MCPManager
from core.scheduler import Scheduler

# Removed simple_workflow - now using AI-native orchestration
from core.workflow_engine import WorkflowEngine, WorkflowStatus

console = Console()


@click.group()
@click.version_option(version="2.0.0")
def cli():
    """Enhanced Conductor - Workflow & Documentation Orchestrator"""
    pass


@cli.command()
@click.option(
    "--shell",
    type=click.Choice(["bash", "zsh", "fish"]),
    help="Shell type for completion script",
)
@click.option("--install", is_flag=True, help="Install completion for current shell")
def completion(shell, install):
    """Generate shell completion scripts for conductor commands."""
    import subprocess

    # Detect shell if not provided
    if not shell and not install:
        current_shell = os.environ.get("SHELL", "").split("/")[-1]
        if current_shell in ["bash", "zsh", "fish"]:
            shell = current_shell
        else:
            shell = "bash"  # Default to bash

    if install:
        # Auto-detect shell for installation
        current_shell = os.environ.get("SHELL", "").split("/")[-1]

        if current_shell == "bash":
            completion_script = "_CONDUCTOR_COMPLETE=bash_source conductor.py"
            config_file = os.path.expanduser("~/.bashrc")
            install_line = f'eval "$({completion_script})"'

        elif current_shell == "zsh":
            completion_script = "_CONDUCTOR_COMPLETE=zsh_source conductor.py"
            config_file = os.path.expanduser("~/.zshrc")
            install_line = f'eval "$({completion_script})"'

        elif current_shell == "fish":
            completion_script = "_CONDUCTOR_COMPLETE=fish_source conductor.py"
            config_file = os.path.expanduser("~/.config/fish/config.fish")
            install_line = f"eval ({completion_script})"

        else:
            console.print(
                "❌ Unsupported shell. Supported shells: bash, zsh, fish", style="red"
            )
            return

        # Check if already installed
        try:
            with open(config_file, "r") as f:
                content = f.read()
                if "conductor.py" in content and "COMPLETE" in content:
                    console.print(
                        f"✅ Completion already installed in {config_file}",
                        style="green",
                    )
                    console.print(
                        "\n💡 To activate completion in current session, run:"
                    )
                    console.print(f"   [bold]source {config_file}[/bold]")
                    return
        except FileNotFoundError:
            pass

        # Add completion to config file
        try:
            with open(config_file, "a") as f:
                f.write(f"\n# Conductor CLI completion\n{install_line}\n")

            console.print(f"✅ Completion installed to {config_file}", style="green")
            console.print(f"\n💡 To activate completion, run:")
            console.print(f"   [bold]source {config_file}[/bold]")
            console.print("\nOr restart your terminal.")

        except Exception as e:
            console.print(f"❌ Failed to install completion: {e}", style="red")
            console.print(f"\n💡 Manual installation:")
            console.print(f"   Add this line to {config_file}:")
            console.print(f"   [bold]{install_line}[/bold]")

    else:
        # Generate completion script
        if shell == "bash":
            env_var = "_CONDUCTOR_COMPLETE=bash_source"
        elif shell == "zsh":
            env_var = "_CONDUCTOR_COMPLETE=zsh_source"
        elif shell == "fish":
            env_var = "_CONDUCTOR_COMPLETE=fish_source"
        else:
            console.print("❌ Unsupported shell. Use: bash, zsh, or fish", style="red")
            return

        console.print(f"# {shell.upper()} completion for conductor")
        console.print(f"# Add this to your {shell} config file:")
        console.print(f'eval "$({env_var} conductor.py)"')
        console.print(f"\n# Or run: ./conductor.py completion --install")


# Initialize core components
def get_components():
    """Get initialized core components."""
    workflow_engine = WorkflowEngine()
    scheduler = Scheduler()
    doc_processor = DocumentProcessor()
    mcp_manager = MCPManager()
    return workflow_engine, scheduler, doc_processor, mcp_manager


@cli.command()
@click.option("--dashboard", "-d", is_flag=True, help="Show enhanced dashboard")
@click.option("--auto-start", "-a", is_flag=True, help="Auto-start scheduler")
def start(dashboard, auto_start):
    """Start your work day with enhanced dashboard."""

    workflow_engine, scheduler, doc_processor, mcp_manager = get_components()

    if auto_start:
        scheduler.start_scheduler()
        console.print("[green]📅 Scheduler started in background[/green]")

    if dashboard:
        show_dashboard(workflow_engine, scheduler, doc_processor, mcp_manager)
    else:
        # Show simple startup message
        console.print(
            Panel.fit(
                "[bold blue]🌅 Starting Your Work Day[/bold blue]\n"
                "Conductor is ready!",
                border_style="blue",
            )
        )
        console.print(
            "\n[green]✅ Ready to start your day! Use 'conductor workflows' or 'conductor start -d' for enhanced view.[/green]"
        )


def show_dashboard(workflow_engine, scheduler, doc_processor, mcp_manager):
    """Show enhanced dashboard with all information."""

    console.print(
        Panel.fit(
            "[bold blue]🚀 Enhanced Conductor Dashboard[/bold blue]\n"
            "Workflow orchestration, documentation, and task management",
            border_style="blue",
        )
    )

    # Get data
    workflows = (
        workflow_engine.get_active_workflows() + workflow_engine.get_pending_workflows()
    )
    priorities = workflow_engine.get_today_priorities()
    reminders = workflow_engine.get_due_reminders()
    scheduler_summary = scheduler.get_schedule_summary()
    service_status = mcp_manager.get_services_status()

    # Create layout
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3),
    )

    layout["body"].split_row(Layout(name="left"), Layout(name="right"))

    layout["left"].split_column(
        Layout(name="workflows", ratio=2), Layout(name="priorities", ratio=1)
    )

    layout["right"].split_column(
        Layout(name="schedule", ratio=1), Layout(name="services", ratio=1)
    )

    # Header
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    layout["header"].update(
        Panel(
            f"[bold]Current Time:[/bold] {current_time}",
            title="Status",
            border_style="blue",
        )
    )

    # Workflows table
    if workflows:
        workflows_table = Table(title="Active Workflows", show_header=True)
        workflows_table.add_column("Title", style="cyan")
        workflows_table.add_column("Status", style="white")
        workflows_table.add_column("Priority", style="yellow")

        for workflow in workflows[:10]:  # Limit display
            priority_str = (
                "🔴"
                if workflow.priority <= 2
                else "🟡" if workflow.priority <= 3 else "🟢"
            )
            workflows_table.add_row(
                (
                    workflow.title[:50] + "..."
                    if len(workflow.title) > 50
                    else workflow.title
                ),
                workflow.status.value,
                priority_str,
            )
        layout["workflows"].update(workflows_table)
    else:
        layout["workflows"].update(Panel("No active workflows", title="Workflows"))

    # Today's priorities
    if priorities:
        priorities_table = Table(title="Today's Priorities", show_header=True)
        priorities_table.add_column("Title", style="red")
        priorities_table.add_column("Due", style="white")

        for priority in priorities[:5]:  # Top 5
            due_str = (
                priority.due_date.split("T")[0] if priority.due_date else "No due date"
            )
            priorities_table.add_row(
                (
                    priority.title[:40] + "..."
                    if len(priority.title) > 40
                    else priority.title
                ),
                due_str,
            )
        layout["priorities"].update(priorities_table)
    else:
        layout["priorities"].update(Panel("No high priorities", title="Priorities"))

    # Scheduler summary
    schedule_text = f"""
📅 Total Tasks: {scheduler_summary['total_tasks']}
⚡ Due Now: {scheduler_summary['due_now']}
📋 Upcoming 24h: {scheduler_summary['upcoming_24h']}
✅ Completed: {scheduler_summary['completed_tasks']}
    """.strip()
    layout["schedule"].update(Panel(schedule_text, title="Scheduler"))

    # Services status
    services_text = ""
    for service_name, status in service_status.items():
        status_emoji = (
            "✅" if status["connected"] else "⚠️" if status["configured"] else "❌"
        )
        services_text += f"{status_emoji} {service_name.title()}\n"

    layout["services"].update(
        Panel(services_text.strip() or "No services", title="MCP Services")
    )

    # Footer
    layout["footer"].update(
        Panel(
            "[bold green]Commands:[/bold green] workflows, schedule, docs, services | [bold yellow]Ctrl+C to exit[/bold yellow]",
            border_style="green",
        )
    )

    console.print(layout)

    # Show reminders if any
    if reminders:
        console.print("\n[bold red]🔔 Due Reminders:[/bold red]")
        for reminder in reminders[:3]:
            console.print(f"• {reminder.message}")


@cli.command()
@click.option("--task-id", "-t", help="JIRA task ID")
@click.option("--time", help="Time spent (e.g., 30m, 2h)")
def log(task_id, time):
    """Log work progress."""

    console.print(
        "[red]❌ Work logging requires AI-native workflow system. Use 'conductor ai chat' instead.[/red]"
    )
    return


@cli.command()
@click.option("--title", "-t", help="Documentation title")
@click.option("--publish", "-p", is_flag=True, help="Publish to targets")
@click.option("--format", "-f", multiple=True, help="Output formats (html, docx)")
@click.option("--version", "-v", is_flag=True, help="Create new version if changed")
@click.option("--file", help="Read content from file instead of input")
def docs(title, publish, format, version, file):
    """Create and manage documentation with versioning."""

    workflow_engine, scheduler, doc_processor, mcp_manager = get_components()

    console.print(
        Panel.fit(
            "[bold blue]📝 Enhanced Documentation System[/bold blue]\n"
            "Create, version, and publish documentation",
            border_style="blue",
        )
    )

    if not title:
        title = Prompt.ask("Documentation title")

    # Get content
    if file:
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            console.print(f"[red]Error reading file: {e}[/red]")
            return
    else:
        console.print("\n[yellow]Enter your content (markdown format):[/yellow]")
        console.print("(Press Ctrl+D when finished, or type 'END' on a new line)")

        lines = []
        try:
            while True:
                line = input()
                if line.strip() == "END":
                    break
                lines.append(line)
        except EOFError:
            pass

        content = "\n".join(lines)

    if not content.strip():
        console.print("[red]No content provided![/red]")
        return

    # Create document with versioning
    metadata = {
        "author": os.getenv("USER", "unknown"),
        "created_with": "Enhanced Conductor",
    }

    doc_result = doc_processor.create_document(
        title=title, content=content, metadata=metadata, auto_version=version
    )

    console.print(
        f"[green]✅ Document created:[/green] {doc_result['title']} v{doc_result['version']}"
    )
    console.print(f"📁 Location: {doc_result['file_path']}")

    # Convert to additional formats
    if format:
        formats_list = list(format)
    else:
        formats_list = ["html"] if not format else []

    if formats_list:
        convert_result = doc_processor.convert_to_formats(
            title, "current", formats_list
        )
        if convert_result["success"]:
            console.print("[blue]🔄 Converted to additional formats:[/blue]")
            for fmt, path in convert_result["files"].items():
                console.print(f"  • {fmt.upper()}: {path}")

    # Publish if requested
    if publish:
        targets = []
        if Confirm.ask("Publish to Confluence?", default=False):
            targets.append("confluence")
        if Confirm.ask("Publish to GitHub?", default=False):
            targets.append("github")

        if targets:
            pub_result = doc_processor.publish_document(title, "current", targets)
            if pub_result["success"]:
                console.print("[green]📤 Published successfully![/green]")
                for target, result in pub_result["published"].items():
                    if result.get("success"):
                        console.print(
                            f"  • {target.title()}: {result.get('url', 'Published')}"
                        )
            else:
                console.print(
                    f"[red]❌ Publishing failed: {pub_result.get('errors')}[/red]"
                )


@cli.command()
@click.option("--list-all", "-l", is_flag=True, help="List all workflows")
@click.option("--create", "-c", help="Create new workflow from file")
@click.option("--status", "-s", help="Update workflow status")
@click.option("--priority", "-p", is_flag=True, help="Show only high priority")
def workflows(list_all, create, status, priority):
    """Manage workflows and skills."""

    workflow_engine, scheduler, doc_processor, mcp_manager = get_components()

    if create:
        # Create workflow from markdown file
        try:
            with open(create, "r", encoding="utf-8") as f:
                content = f.read()

            workflow = workflow_engine.create_workflow_from_markdown(content)
            console.print(f"[green]✅ Workflow created:[/green] {workflow.title}")
            console.print(f"📋 ID: {workflow.id}")
            console.print(f"🏃 Actions: {len(workflow.actions)}")
            console.print(f"⏰ Reminders: {len(workflow.reminders)}")
            return
        except Exception as e:
            console.print(f"[red]Error creating workflow: {e}[/red]")
            return

    # List workflows
    if priority:
        workflows_list = workflow_engine.get_today_priorities()
        title = "High Priority Workflows"
    else:
        workflows_list = [*workflow_engine.workflows.values()]  # Convert to list
        title = "All Workflows"

    if not workflows_list:
        console.print("[yellow]No workflows found[/yellow]")
        return

    console.print(Panel.fit(f"[bold blue]{title}[/bold blue]", border_style="blue"))

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Status", style="green")
    table.add_column("Priority", style="yellow")
    table.add_column("Actions", style="blue")
    table.add_column("Due", style="red")

    for workflow in workflows_list:
        priority_emoji = (
            "🔴" if workflow.priority <= 2 else "🟡" if workflow.priority <= 3 else "🟢"
        )
        completed_actions = len([a for a in workflow.actions if a.completed])
        actions_str = f"{completed_actions}/{len(workflow.actions)}"
        due_str = workflow.due_date.split("T")[0] if workflow.due_date else "-"

        table.add_row(
            workflow.id,
            workflow.title[:40] + "..." if len(workflow.title) > 40 else workflow.title,
            workflow.status.value,
            f"{priority_emoji} {workflow.priority}",
            actions_str,
            due_str,
        )

    console.print(table)

    # Show workflow actions if specific workflow requested
    if status and status in workflow_engine.workflows:
        workflow = workflow_engine.workflows[status]
        console.print(f"\n[bold]Workflow Details: {workflow.title}[/bold]")

        if workflow.actions:
            actions_table = Table(title="Actions", show_header=True)
            actions_table.add_column("ID", style="cyan")
            actions_table.add_column("Description", style="white")
            actions_table.add_column("Status", style="green")

            for action in workflow.actions:
                status_icon = "✅" if action.completed else "⏳"
                actions_table.add_row(action.id, action.description, status_icon)
            console.print(actions_table)


@cli.command()
@click.option("--list-tasks", "-l", is_flag=True, help="List scheduled tasks")
@click.option("--due", "-d", is_flag=True, help="Show only due tasks")
@click.option("--execute", "-e", is_flag=True, help="Execute due tasks")
def schedule(list_tasks, due, execute):
    """Manage scheduled tasks and reminders."""

    workflow_engine, scheduler, doc_processor, mcp_manager = get_components()

    if execute:
        console.print("[blue]⚡ Executing due tasks...[/blue]")
        results = scheduler.execute_due_tasks()

        if results:
            for result in results:
                status_icon = "✅" if result["success"] else "❌"
                console.print(f"{status_icon} {result['name']}: {result['message']}")
        else:
            console.print("[green]No tasks due for execution[/green]")
        return

    # Show scheduled tasks
    if due:
        tasks = scheduler.get_due_tasks()
        title = "Due Tasks"
    else:
        tasks = [*scheduler.tasks.values()]  # Convert to list
        title = "All Scheduled Tasks"

    if not tasks:
        console.print(f"[yellow]No {title.lower()} found[/yellow]")
        return

    console.print(Panel.fit(f"[bold blue]{title}[/bold blue]", border_style="blue"))

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Type", style="green")
    table.add_column("Next Run", style="yellow")
    table.add_column("Status", style="blue")

    for task in tasks:
        status_icon = "✅" if task.completed else "⏳"
        next_run = task.next_run.split("T") if task.next_run else ["Never", ""]
        next_run_str = (
            f"{next_run[0]} {next_run[1][:5]}" if len(next_run) > 1 else next_run[0]
        )

        table.add_row(
            task.id,
            task.name[:40] + "..." if len(task.name) > 40 else task.name,
            task.callback_type,
            next_run_str,
            status_icon,
        )

    console.print(table)

    # Show summary
    summary = scheduler.get_schedule_summary()
    console.print(
        f"\n[bold]Summary:[/bold] {summary['total_tasks']} total, {summary['due_now']} due now, {summary['upcoming_24h']} upcoming"
    )


@cli.command()
@click.option("--list-available", "-l", is_flag=True, help="List available services")
@click.option("--status", "-s", is_flag=True, help="Show services status")
@click.option("--test", "-t", help="Test specific service")
@click.option(
    "--configure", "-c", is_flag=True, help="Configure services from environment"
)
def services(list_available, status, test, configure):
    """Manage MCP service integrations."""

    workflow_engine, scheduler, doc_processor, mcp_manager = get_components()

    if configure:
        console.print("[blue]🔧 Auto-configuring services from environment...[/blue]")
        results = mcp_manager.auto_configure_from_env()

        for service_name, result in results.items():
            status_icon = "✅" if result["success"] else "❌"
            console.print(
                f"{status_icon} {service_name.title()}: {result.get('status', 'configured' if result['success'] else 'failed')}"
            )
        return

    if test:
        console.print(f"[blue]🔌 Testing {test} service...[/blue]")
        result = mcp_manager.test_service(test)
        status_icon = "✅" if result.get("success") else "❌"
        console.print(
            f"{status_icon} {test.title()}: {result.get('message', 'Test completed')}"
        )
        return

    # Show services
    if list_available:
        services_list = mcp_manager.get_available_services()
        title = "Available Services"
    else:
        services_status = mcp_manager.get_services_status()
        title = "Services Status"

        console.print(Panel.fit(f"[bold blue]{title}[/bold blue]", border_style="blue"))

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Configured", style="green")
        table.add_column("Connected", style="yellow")

        for service_name, status_info in services_status.items():
            status_emoji = (
                "✅"
                if status_info["connected"]
                else "⚠️" if status_info["configured"] else "❌"
            )
            configured_icon = "✅" if status_info["configured"] else "❌"
            connected_icon = "✅" if status_info["connected"] else "❌"

            table.add_row(
                service_name.title(),
                f"{status_emoji} {status_info['status']}",
                configured_icon,
                connected_icon,
            )

        console.print(table)


@cli.command()
@click.option("--template", "-t", help="Template name to use")
@click.option("--list-templates", "-l", is_flag=True, help="List available templates")
@click.option("--title", help="Title for new workflow")
def create(template, list_templates, title):
    """Create new workflows from templates."""

    workflow_engine, scheduler, doc_processor, mcp_manager = get_components()

    templates_dir = Path("workflow_templates")
    templates_dir.mkdir(exist_ok=True)

    if list_templates:
        # List available templates
        template_files = list(templates_dir.glob("*_template.md"))

        if not template_files:
            console.print("[yellow]No templates found[/yellow]")
            return

        console.print(
            Panel.fit(
                "[bold blue]Available Workflow Templates[/bold blue]",
                border_style="blue",
            )
        )

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Template", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("File", style="yellow")

        for template_file in template_files:
            template_name = template_file.stem.replace("_template", "")

            # Try to read description from frontmatter
            try:
                with open(template_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            import yaml

                            frontmatter = yaml.safe_load(parts[1])
                            description = frontmatter.get(
                                "description", "No description"
                            )
                        else:
                            description = "Template file"
                    else:
                        description = "Template file"
            except:
                description = "Template file"

            table.add_row(template_name, description, template_file.name)

        console.print(table)
        console.print(
            '\n[green]Usage:[/green] conductor create -t template_name --title "My Workflow"'
        )
        return

    if not template:
        template = Prompt.ask("Template name")

    template_file = templates_dir / f"{template}_template.md"

    if not template_file.exists():
        console.print(f"[red]Template {template} not found[/red]")
        console.print("Use 'conductor create -l' to list available templates")
        return

    # Read template
    with open(template_file, "r", encoding="utf-8") as f:
        template_content = f.read()

    # Customize template
    if title:
        # Update title in frontmatter
        if template_content.startswith("---"):
            parts = template_content.split("---", 2)
            if len(parts) >= 3:
                import yaml

                frontmatter = yaml.safe_load(parts[1])
                frontmatter["title"] = title
                frontmatter["status"] = "pending"  # Reset status
                frontmatter["created_at"] = datetime.now().isoformat()

                new_content = "---\n"
                new_content += yaml.dump(frontmatter, default_flow_style=False)
                new_content += "---\n"
                new_content += parts[2].replace(
                    frontmatter.get("title", "Template"), title, 1
                )
                template_content = new_content

    # Create workflow
    try:
        workflow = workflow_engine.create_workflow_from_markdown(
            template_content, title
        )

        console.print(
            f"[green]✅ Workflow created from template:[/green] {workflow.title}"
        )
        console.print(f"📋 ID: {workflow.id}")
        console.print(f"🏃 Actions: {len(workflow.actions)}")
        console.print(f"⏰ Reminders: {len(workflow.reminders)}")
        console.print(f"📁 Template used: {template}")

        # Save to file
        workflow_file = templates_dir / f"{workflow.id}.md"
        workflow_engine.save_workflow_to_file(workflow.id)
        console.print(f"💾 Saved to: {workflow_file}")

        # Ask if user wants to activate immediately
        if Confirm.ask("Activate this workflow now?", default=True):
            workflow_engine.update_workflow_status(workflow.id, WorkflowStatus.ACTIVE)
            console.print("[green]🚀 Workflow activated![/green]")

    except Exception as e:
        console.print(f"[red]Error creating workflow: {e}[/red]")


@cli.command()
@click.option("--repo", "-r", help="GitHub repository (owner/repo)")
@click.option("--file", "-f", help="File path in repository")
@click.option("--message", "-m", help="Commit message")
def github(repo, file, message):
    """Update GitHub with work artifacts."""

    if not repo:
        repo = Prompt.ask("GitHub repository (owner/repo)")

    if not file:
        file = Prompt.ask("File path in repository")

    if not message:
        message = Prompt.ask("Commit message")

    console.print("\n[yellow]Enter file content:[/yellow]")
    console.print("(Press Ctrl+D when finished, or type 'END' on a new line)")

    lines = []
    try:
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
    except EOFError:
        pass

    content = "\n".join(lines)

    if not content.strip():
        console.print("[red]No content provided![/red]")
        return

    console.print(
        "[red]❌ GitHub integration requires AI-native workflow system. Use 'conductor ai chat' for assistance.[/red]"
    )
    return


@cli.command()
def summary():
    """Generate end of day summary."""

    console.print(
        Panel.fit("[bold blue]📊 End of Day Summary[/bold blue]", border_style="blue")
    )

    console.print(
        "[red]❌ Summary generation requires AI-native workflow system. Use 'conductor ai ask \"Generate my daily summary\"' instead.[/red]"
    )
    return


@cli.command()
def config():
    """Check and configure integrations."""

    console.print(
        Panel.fit("[bold blue]⚙️ Configuration Status[/bold blue]", border_style="blue")
    )

    # Check for .env file
    env_file = Path(".env")
    if env_file.exists():
        console.print("[green]✅ .env file found[/green]")
    else:
        console.print("[yellow]⚠️ .env file not found[/yellow]")
        console.print("Create a .env file with your API credentials:")
        console.print("""
JIRA_SERVER_URL=https://your-jira.atlassian.net
JIRA_USERNAME=your-email@company.com
JIRA_API_TOKEN=your-jira-token

CONFLUENCE_SERVER_URL=https://your-confluence.atlassian.net
CONFLUENCE_API_TOKEN=your-confluence-token

GITHUB_TOKEN=your-github-token
        """)

    console.print("\n[bold]Integration Status:[/bold]")
    console.print("• JIRA: Optional (for task management)")
    console.print("• Confluence: Optional (for documentation publishing)")
    console.print("• GitHub: Optional (for code/artifact management)")
    console.print(
        "\n[blue]💡 The tool works offline - integrations are optional![/blue]"
    )


@cli.group()
def ai():
    """AI-powered workflow orchestration and management."""
    pass


@ai.command("chat")
@click.option(
    "--provider",
    "-p",
    type=click.Choice(["claude", "openai"]),
    help="AI provider to use",
)
@click.option("--session", "-s", help="Resume existing session ID")
@click.option("--stream", is_flag=True, help="Stream responses")
def ai_chat(provider, session, stream):
    """Start AI conversation for workflow management."""

    # Import AI components
    try:
        # Add src to path for AI imports
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from ai.context.memory import ConversationMemory
        from ai.orchestrator import AIOrchestrator
    except ImportError as e:
        console.print(f"[red]❌ AI features not available: {e}[/red]")
        console.print("Make sure aiohttp is installed: pip install aiohttp")
        return

    try:
        # Initialize AI orchestrator
        ai_config = {
            "providers": {
                "claude": {} if provider != "openai" else None,
                "openai": {} if provider == "openai" else None,
            }
        }
        orchestrator = AIOrchestrator(ai_config)

        if not orchestrator.providers:
            console.print("[red]❌ No AI providers available[/red]")
            console.print(
                "Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable"
            )
            return

        # Show available providers
        providers = orchestrator.list_available_providers()
        if not provider:
            provider = providers[0]["name"] if providers else "claude"

        console.print(
            Panel.fit(
                f"[bold blue]🤖 AI Workflow Assistant ({provider})[/bold blue]",
                border_style="blue",
            )
        )

        # Start or resume session
        import asyncio

        async def chat_session():
            if session:
                session_id = session
                console.print(f"[green]🔄 Resuming session: {session_id}[/green]")
            else:
                session_id = await orchestrator.start_conversation(provider=provider)
                console.print(f"[green]🚀 Started new session: {session_id}[/green]")

            console.print("\n[yellow]💬 Chat with your AI workflow assistant![/yellow]")
            console.print("[dim]Type 'quit', 'exit', or press Ctrl+C to end[/dim]\n")

            try:
                while True:
                    user_input = Prompt.ask("[bold blue]You[/bold blue]")

                    if user_input.lower() in ["quit", "exit", "bye"]:
                        console.print(
                            "[green]👋 Goodbye! Session saved for later.[/green]"
                        )
                        break

                    console.print(f"\n[bold green]AI Assistant[/bold green]:")

                    if stream:
                        # Streaming response
                        response_text = ""
                        async for chunk in await orchestrator.chat(
                            session_id, user_input, stream=True
                        ):
                            console.print(chunk, end="")
                            response_text += chunk
                        console.print()  # New line after streaming
                    else:
                        # Regular response
                        response = await orchestrator.chat(
                            session_id, user_input, stream=False
                        )
                        console.print(response.content)

                    console.print()  # Extra line for readability

            except KeyboardInterrupt:
                console.print("\n[green]👋 Chat ended. Session saved.[/green]")
            except Exception as e:
                console.print(f"\n[red]❌ Error: {e}[/red]")

        # Run async chat
        asyncio.run(chat_session())

    except Exception as e:
        console.print(f"[red]❌ Failed to start AI chat: {e}[/red]")


@ai.command("ask")
@click.argument("question")
@click.option("--provider", "-p", type=click.Choice(["claude", "openai"]))
def ai_ask(question, provider):
    """Ask a quick question to the AI assistant."""

    try:
        # Add src to path for AI imports
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from ai.orchestrator import AIOrchestrator
    except ImportError as e:
        console.print(f"[red]❌ AI features not available: {e}[/red]")
        return

    try:
        orchestrator = AIOrchestrator()
        providers = orchestrator.list_available_providers()

        if not providers:
            console.print("[red]❌ No AI providers available[/red]")
            return

        provider = provider or providers[0]["name"]

        import asyncio

        async def ask_question():
            session_id = await orchestrator.start_conversation(provider=provider)
            response = await orchestrator.chat(session_id, question, stream=False)

            console.print(f"\n[bold blue]Question:[/bold blue] {question}")
            console.print(f"[bold green]Answer:[/bold green] {response.content}\n")

        asyncio.run(ask_question())

    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")


@ai.command("status")
def ai_status():
    """Show AI provider status and capabilities."""

    try:
        # Add src to path for AI imports
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from ai.orchestrator import AIOrchestrator
    except ImportError as e:
        console.print(f"[red]❌ AI features not available: {e}[/red]")
        return

    try:
        orchestrator = AIOrchestrator()
        providers = orchestrator.list_available_providers()

        console.print(
            Panel.fit(
                "[bold blue]🤖 AI Provider Status[/bold blue]", border_style="blue"
            )
        )

        if not providers:
            console.print("[yellow]⚠️ No AI providers configured[/yellow]")
            console.print("\nTo configure providers, set environment variables:")
            console.print("• ANTHROPIC_API_KEY for Claude")
            console.print("• OPENAI_API_KEY for OpenAI")
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Provider", style="cyan")
        table.add_column("Model", style="white")
        table.add_column("Capabilities", style="green")

        for provider in providers:
            capabilities = ", ".join(provider["capabilities"][:3])  # Show first 3
            if len(provider["capabilities"]) > 3:
                capabilities += f" (+{len(provider['capabilities'])-3} more)"

            table.add_row(provider["name"], provider["model"], capabilities)

        console.print(table)

        # Show skills info
        from skills.base import SkillRegistry
        from skills.daily_ops import DailyOperationsSkills
        from skills.documentation import DocumentationSkills
        from skills.project_mgmt import ProjectManagementSkills

        registry = SkillRegistry()
        DocumentationSkills.register_all(registry)
        ProjectManagementSkills.register_all(registry)
        DailyOperationsSkills.register_all(registry)

        skills = registry.list_skills()

        console.print(f"\n[bold blue]Available Skills:[/bold blue] {len(skills)}")
        console.print(
            f"• Documentation: {len([s for s in skills if s['category'] == 'documentation'])}"
        )
        console.print(
            f"• Project Management: {len([s for s in skills if s['category'] == 'project_mgmt'])}"
        )
        console.print(
            f"• Daily Operations: {len([s for s in skills if s['category'] == 'daily_ops'])}"
        )

    except Exception as e:
        console.print(f"[red]❌ Error checking AI status: {e}[/red]")


@ai.command("skills")
@click.option("--category", "-c", help="Filter by category")
@click.option("--detail", is_flag=True, help="Show detailed information")
def ai_skills(category, detail):
    """List available AI skills and capabilities."""

    try:
        from skills.base import SkillRegistry
        from skills.daily_ops import DailyOperationsSkills
        from skills.documentation import DocumentationSkills
        from skills.project_mgmt import ProjectManagementSkills

        registry = SkillRegistry()
        DocumentationSkills.register_all(registry)
        ProjectManagementSkills.register_all(registry)
        DailyOperationsSkills.register_all(registry)

        skills = registry.list_skills(category)

        console.print(
            Panel.fit(
                "[bold blue]🛠️ Available AI Skills[/bold blue]", border_style="blue"
            )
        )

        if category:
            console.print(f"[bold]Category:[/bold] {category}")
            console.print()

        if not skills:
            console.print("[yellow]No skills found[/yellow]")
            return

        for skill in skills:
            console.print(f"[bold cyan]{skill['name']}[/bold cyan]")
            console.print(f"  [dim]{skill['description']}[/dim]")
            console.print(f"  Category: {skill['category']}")

            if detail:
                console.print(f"  Parameters:")
                for param in skill["parameters"]:
                    required = " (required)" if param["required"] else " (optional)"
                    console.print(
                        f"    • {param['name']}: {param['description']}{required}"
                    )

            console.print()

    except Exception as e:
        console.print(f"[red]❌ Error listing skills: {e}[/red]")


if __name__ == "__main__":
    cli()
