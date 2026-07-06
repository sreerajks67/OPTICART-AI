from apscheduler.schedulers.background import BackgroundScheduler

from .utils import run_autonomous_agent


def start():

    scheduler = BackgroundScheduler()

    scheduler.add_job(
        run_autonomous_agent,
        'interval',
        hours=6,
        id='autonomous_agent',
        replace_existing=True,
    )

    scheduler.start()

    print("Scheduler started...")