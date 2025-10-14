from ..extensions import make_celery


def init_tasks(app):
    celery = make_celery(app)

    @celery.task
    def send_reminder(user_id: int):
        print(f"Sending reminder to user {user_id}")

    return celery
