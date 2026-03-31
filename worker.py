from redis import Redis
from rq import Worker
from config import REDIS_HOST, REDIS_PORT, REDIS_DB

redis_conn = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

if __name__ == '__main__':
    print("Worker has started work. Waiting for tasks in the 'default' queue...")
    
    worker = Worker(['default'], connection=redis_conn)
    worker.work()