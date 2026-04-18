from decimal import Decimal

WORKLOAD_DENSITY_COLORS = {
    "GREEN": "#27AE60",
    "YELLOW": "#F39C12",
    "RED": "#E74C3C",
}

STATUS_COLORS = {
    "not_started": "#95A5A6",
    "in_progress": "#F39C12",
    "complete": "#27AE60",
}

DASHBOARD_WIDGETS = [
    {
        "id": "upcoming_deadlines",
        "name": "Upcoming Deadlines",
        "default_shown": True,
        "limit": 5,
    },
    {
        "id": "workload_density",
        "name": "Workload This Week",
        "default_shown": True,
        "show_color_coding": True,
    },
    {
        "id": "todays_time_blocks",
        "name": "Today's Schedule",
        "default_shown": True,
        "show_work_shifts": True,
        "show_classes": True,
    },
    {
        "id": "progress_summary",
        "name": "Progress Summary",
        "default_shown": True,
        "show_completion_stats": True,
    },
    {
        "id": "group_project_updates",
        "name": "Group Project Updates",
        "default_shown": True,
        "show_teammate_completions": True,
    },
    {
        "id": "workload_alerts",
        "name": "Workload Warnings",
        "default_shown": True,
        "show_recommendations": True,
    },
]

NOTIFICATIONS = {
    "workload_alerts": {
        "green_week": {
            "enabled": False,
        },
        "yellow_week": {
            "enabled": True,
            "title": "Heads up: Heavy week ahead",
            "message": "Week {week_number} is looking busy ({assignment_count} assignments, {total_hours} estimated hours). You've got this, but plan ahead.",
            "display_on_board": True,
            "push_notification": True,
            "advance_notice_days": 14,
        },
        "red_week": {
            "enabled": True,
            "title": "Warning: Week {week_number} is overloaded",
            "message": "You have {assignment_count} assignments due Week {week_number}, totaling {total_hours} hours. Your available time is {available_hours} hours. This is tight. Consider moving work to earlier weeks or adjusting your schedule.",
            "display_on_board": True,
            "push_notification": True,
            "email": True,
            "advance_notice_days": 14,
            "show_recommendations": True,
        },
        "deadline_cluster": {
            "enabled": True,
            "title": "Deadline cluster detected",
            "message": "{major_count} major assignments + {other_count} others within 48 hours (Week {week_number}). Start studying now.",
            "display_on_board": True,
            "push_notification": True,
            "advance_notice_days": 14,
            "cluster_threshold": 3,
        },
    },
    "task_breakdown_prompts": {
        "large_project": {
            "enabled": True,
            "trigger_hours": Decimal("8.0"),
            "title": "This looks like a big project",
            "message": "'{assignment_title}' is estimated at {hours} hours. Break it into smaller steps?",
            "show_examples": True,
            "examples": [
                "Choose topic",
                "Find sources",
                "Create outline",
                "Write draft",
                "Revise and proofread",
            ],
        },
        "major_project_flag": {
            "enabled": True,
            "message": "Your professor marked this as a major project. Breaking it into steps helps you start without feeling overwhelmed.",
        },
    },
    "time_block_reminders": {
        "fifteen_min_before": {
            "enabled": True,
            "title": "Work session starting soon",
            "message": "'{time_block_title}' starts in 15 minutes",
            "allow_snooze": True,
            "snooze_duration_min": 15,
        },
        "at_start_time": {
            "enabled": True,
            "title": "Time to work on: {time_block_title}",
            "message": "Scheduled for {duration} minutes. You've got this.",
            "show_location": True,
        },
        "overdue_time_block": {
            "enabled": False,
        },
    },
    "progress_notifications": {
        "subtask_completed": {
            "enabled": True,
            "message": "✓ {subtask_title} complete! {remaining} steps left.",
            "show_progress_bar": True,
        },
        "assignment_completed": {
            "enabled": True,
            "message": "✓ {assignment_title} complete! Nice work.",
        },
        "week_completion": {
            "enabled": True,
            "trigger_day": "sunday",
            "trigger_time": "20:00",
            "message": "You completed {completed_count} assignments this week. {remaining_count} due next week.",
        },
    },
}
