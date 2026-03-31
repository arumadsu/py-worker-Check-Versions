import os
import time 
import logging
from redis import Redis
from config import FTP_DIR, REDIS_HOST, REDIS_PORT, REDIS_DB

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')

redis_conn = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

def check_for_new_versions():
    logging.debug(f"Starting directory scanning: {FTP_DIR}")

    if not os.path.exists(FTP_DIR):
        logging.warning(f"Directory {FTP_DIR} not found ")
        return
    
    for item in os.listdir(FTP_DIR):
        folder_path = os.path.join(FTP_DIR, item)

        if os.path.isdir(folder_path):
            build_info_path = os.path.join(folder_path, 'build_info.py')

            if os.path.exists(build_info_path):
                current_mtime = os.path.getmtime(build_info_path)

                last_mtime = redis_conn.hget('processed_versions', item)

                if last_mtime is None or float(last_mtime) < current_mtime:
                    logging.info(f"NEW VERSION FOUND in folder '{item}'!")


                logging.info(f"Action for version {item}...")
                time.sleep(2) 
                # убрать

                redis_conn.hset('processed_versions', item, current_mtime)
                logging.debug(f"Version '{item}' successfully processed and saved to cache")

            else:
                logging.debug(f"Folder '{item}' hasn't changed. Skip")

        else:
            logging.debug(f"In folder '{item}' there's no file build_info.py. Skip")