import os

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FTP_DIR = os.path.join(BASE_DIR, 'ftp_dir')