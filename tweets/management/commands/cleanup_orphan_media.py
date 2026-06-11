from django.core.management.base import BaseCommand

from twitmain.media_files import cleanup_orphan_media


class Command(BaseCommand):
    help = "Find orphan files in managed media folders."

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            action="store_true",
            help="Delete orphan media files instead of only reporting them.",
        )

    def handle(self, *args, **options):
        delete = options["delete"]
        report = cleanup_orphan_media(delete=delete)

        self.stdout.write(f"Scanned media files: {report.scanned}")
        self.stdout.write(f"Orphan media files: {len(report.orphaned)}")

        for name in report.orphaned:
            self.stdout.write(f"- {name}")

        if delete:
            self.stdout.write(self.style.SUCCESS(f"Deleted orphan media files: {len(report.deleted)}"))
        elif report.orphaned:
            self.stdout.write("Run again with --delete to remove these files.")
