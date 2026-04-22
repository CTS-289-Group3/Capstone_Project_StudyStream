from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from home.workload_engine import recompute_all_users_workload, recompute_and_persist_workload


class Command(BaseCommand):
    help = (
        "Recompute and persist workload analysis for the next N weeks. "
        "Use this command in a nightly scheduler."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--weeks",
            type=int,
            default=4,
            help="Number of weeks to forecast starting from current week (default: 4).",
        )
        parser.add_argument(
            "--user-id",
            type=int,
            help="Only recompute for a specific user id.",
        )
        parser.add_argument(
            "--date",
            type=str,
            help="Reference date in YYYY-MM-DD format (defaults to today in local timezone).",
        )

    def handle(self, *args, **options):
        weeks = options["weeks"]
        user_id = options.get("user_id")
        date_raw = options.get("date")

        if weeks < 1:
            raise CommandError("--weeks must be at least 1.")

        start_day = timezone.localdate()
        if date_raw:
            try:
                start_day = datetime.strptime(date_raw, "%Y-%m-%d").date()
            except ValueError as exc:
                raise CommandError("--date must be in YYYY-MM-DD format.") from exc

        if user_id:
            user_model = get_user_model()
            try:
                user = user_model.objects.get(pk=user_id, is_active=True)
            except user_model.DoesNotExist as exc:
                raise CommandError(f"Active user {user_id} was not found.") from exc
            recompute_and_persist_workload(user, start_day=start_day, weeks=weeks)
            self.stdout.write(self.style.SUCCESS(f"Workload analysis updated for user {user.id}."))
            return

        processed = recompute_all_users_workload(start_day=start_day, weeks=weeks)
        self.stdout.write(self.style.SUCCESS(f"Workload analysis updated for {processed} users."))
