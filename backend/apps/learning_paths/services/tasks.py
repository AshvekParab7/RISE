from threading import Thread
from django.db import close_old_connections
from ..models import LearningPath
from .processor import process_learning_path


def enqueue_learning_path(path_id):
    thread = Thread(target=_run_learning_path, args=(str(path_id),), daemon=True, name=f'rise-youtube-{path_id}')
    thread.start()


def _run_learning_path(path_id):
    close_old_connections()
    try:
        path = LearningPath.objects.get(id=path_id)
        process_learning_path(path)
    finally:
        close_old_connections()
