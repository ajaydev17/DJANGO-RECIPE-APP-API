"""
Django command to wait for the database to be ready
"""

import time
from django.core.management.base import BaseCommand
from psycopg2 import OperationalError as Psycopg2OperationalError
from django.db.utils import OperationalError


class Command(BaseCommand):
    """
    Command to wait for the database to be ready
    """

    help = "Wait for the database to be ready"

    def handle(self, *args, **options):
        """
        Entry point for the command
        """

        self.stdout.write("Waiting for database...")

        db_up = False

        while not db_up:
            try:
                self.check(databases=['default'])
                db_up = True
            except (Psycopg2OperationalError, OperationalError):
                self.stdout.write("Database is not ready yet. Waiting for 1 second...  \r", end="")
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("\nDatabase is ready!"))