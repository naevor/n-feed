from celery import shared_task

from twitmain.media_files import cleanup_orphan_media


@shared_task
def cleanup_orphan_media_task():
    report = cleanup_orphan_media(delete=True)
    return {
        "scanned": report.scanned,
        "orphaned": len(report.orphaned),
        "deleted": len(report.deleted),
    }
