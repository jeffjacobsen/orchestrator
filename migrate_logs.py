#!/usr/bin/env python3
"""
Migrate agent logs from flat structure to task-based structure.

Old structure: agent_logs/{agent_id}_{name}_{timestamp}/
New structure: agent_logs/{task_id}/{agent_id}_{name}_{timestamp}/

This script:
1. Reads the database to find agent->task mappings
2. Moves log directories into task-specific subdirectories
3. Preserves logs that have no associated task (keeps in root)
4. Creates a backup before migration
"""

import sqlite3
import shutil
from pathlib import Path
from datetime import datetime


def migrate_logs(
    db_path: str = "dashboard/backend/orchestrator.db",
    logs_dir: str = "dashboard/backend/agent_logs",
    dry_run: bool = False
):
    """
    Migrate agent logs to task-based structure.

    Args:
        db_path: Path to SQLite database
        logs_dir: Path to agent logs directory
        dry_run: If True, only print what would be done without making changes
    """
    logs_path = Path(logs_dir)

    if not logs_path.exists():
        print(f"❌ Log directory not found: {logs_dir}")
        return

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all agents with their task_ids
    cursor.execute("""
        SELECT id, task_id, role
        FROM agents
        WHERE task_id IS NOT NULL
    """)
    agents = cursor.fetchall()

    # Create mapping of agent_id (short form) -> task_id
    agent_to_task = {}
    for agent_id, task_id, role in agents:
        short_id = agent_id[:8]
        agent_to_task[short_id] = {
            'task_id': task_id,
            'full_id': agent_id,
            'role': role
        }

    conn.close()

    print(f"\n📊 Migration Summary")
    print(f"{'='*60}")
    print(f"Database: {db_path}")
    print(f"Logs directory: {logs_dir}")
    print(f"Agents in database: {len(agent_to_task)}")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE (will move files)'}")
    print(f"{'='*60}\n")

    # Create backup if not dry run
    if not dry_run:
        backup_path = logs_path.parent / f"agent_logs_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"📦 Creating backup: {backup_path}")
        shutil.copytree(logs_path, backup_path)
        print(f"✅ Backup created\n")

    # Scan log directories
    moved_count = 0
    orphaned_count = 0
    already_nested_count = 0

    for log_dir in logs_path.iterdir():
        # Skip if not a directory
        if not log_dir.is_dir():
            continue

        # Skip if already in task subdirectory (UUID pattern)
        if len(log_dir.name) == 36 and log_dir.name.count('-') == 4:
            already_nested_count += 1
            continue

        # Extract agent_id from directory name (first 8 chars)
        dir_name = log_dir.name
        agent_short_id = dir_name[:8]

        # Check if we have a task mapping for this agent
        if agent_short_id in agent_to_task:
            task_info = agent_to_task[agent_short_id]
            task_id = task_info['task_id']

            # Create task subdirectory
            task_dir = logs_path / task_id
            new_path = task_dir / dir_name

            print(f"📁 {dir_name}")
            print(f"   → Moving to: {task_id}/{dir_name}")
            print(f"   → Agent: {task_info['role']} ({task_info['full_id'][:8]})")

            if not dry_run:
                task_dir.mkdir(exist_ok=True)
                shutil.move(str(log_dir), str(new_path))
                print(f"   ✅ Moved")
            else:
                print(f"   [DRY RUN - would move]")

            print()
            moved_count += 1
        else:
            # Orphaned log (no matching agent in database)
            print(f"⚠️  {dir_name}")
            print(f"   → No matching agent in database, keeping in root")
            print()
            orphaned_count += 1

    # Print summary
    print(f"\n{'='*60}")
    print(f"✨ Migration {'Preview' if dry_run else 'Complete'}")
    print(f"{'='*60}")
    print(f"Moved to task directories: {moved_count}")
    print(f"Orphaned (kept in root): {orphaned_count}")
    print(f"Already in task directories: {already_nested_count}")

    if dry_run:
        print(f"\n💡 To perform the migration, run with: --live")
    else:
        print(f"\n✅ Logs successfully migrated!")
        print(f"📦 Backup saved at: {backup_path}")

    print()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate agent logs from flat to task-based structure"
    )
    parser.add_argument(
        "--db",
        default="dashboard/backend/orchestrator.db",
        help="Path to SQLite database (default: dashboard/backend/orchestrator.db)"
    )
    parser.add_argument(
        "--logs",
        default="dashboard/backend/agent_logs",
        help="Path to agent logs directory (default: dashboard/backend/agent_logs)"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Perform the migration (default is dry-run)"
    )

    args = parser.parse_args()

    migrate_logs(
        db_path=args.db,
        logs_dir=args.logs,
        dry_run=not args.live
    )
