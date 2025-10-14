from ..extensions import make_celery


def init_tasks(app):
    celery = make_celery(app)

    @celery.task
    def export_applications():
        print("Exporting applications...")

    return celery
