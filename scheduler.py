import time
import logging
from redis import Redis
from rq import Queue
from config import REDIS_HOST, REDIS_PORT, REDIS_DB
from tasks import check_for_new_versions

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

redis_conn = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
queue = Queue('default', connection=redis_conn)


if __name__ == '__main__':
    logging.info("Scheduler running. Scanning every 10 seconds...")
    try:
        while True:
            queue.enqueue(check_for_new_versions)
            time.sleep(10)

    except KeyboardInterrupt:
        logging.info('The scheduler stopped')