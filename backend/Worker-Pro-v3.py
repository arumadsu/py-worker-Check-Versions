import os
import time
import sys
import importlib.util
import configparser
import argparse
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import data_models

def read_config(config_path: str) -> data_models.AppConfig:
    config = configparser.ConfigParser()
    config.read(config_path)

    db_name = config.get('Settings', 'db_name', fallback='app.db')

    base_dir = os.path.dirname(os.path.abspath(__file__))

    return data_models.AppConfig(
        ftp_dir_name=config.get('Settings', 'ftp_dir', fallback='ftp_dir'),
        database_uri=f"sqlite:///{os.path.join(base_dir, db_name)}",
        scan_interval=config.get('Settings', 'scan_interval', fallback='10')
    )

# Parser and Helpers
def check_file_validity(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File is Not Exists: {filepath}")
    
    if os.path.getsize(filepath) == 0:
        raise ValueError(f"File is empty: {filepath}")
    return True

def import_build_info_dynamically(filepath):
    module_name = f"dynamic_build_info_{hash(filepath)}"
    spec = importlib.util.spec_from_file_location(module_name, filepath)

    if spec is None: 
        raise ImportError(f"Failed to create import specification for: {filepath}")
        
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    
    try:
        spec.loader.exec_module(module)
        build_info_class = getattr(module, 'build_info', None)
        
        if build_info_class is None:
            raise AttributeError(f"There is no class 'build_info' in file {filepath}")

        del sys.modules[module_name]        
        return build_info_class
    
    except Exception as e:
        if module_name in sys.modules:
            del sys.modules[module_name]
        raise RuntimeError(f"Error executing file {filepath}: {e}")

def get_real_datetime(date_str):
    """
    Safely converts the string (2026-02-10 14:28:56) to a Python datetime object.
    If the string is invalid or 'unknown', returns 1970 to ensure this version doesn't become the latest.
    """
    if date_str == 'unknown':
        return datetime.min # The most minimum date (0001y)
    try:
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return datetime.min

# Main Cycle

def main(config: data_models.AppConfig):

    engine = create_engine(config.database_uri, echo=False)
    Session = sessionmaker(bind=engine)
    data_models.Base.metadata.create_all(engine)

    print(f"Worker running. Interval: {config.scan_interval} sec. Folder: {config.ftp_dir_path}")
    
    while True:
        folders_on_disk = set()
        
        with Session() as db_session:
            
            if os.path.exists(config.ftp_dir_path):

                for folder in os.listdir(config.ftp_dir_path):
                    folder_path = os.path.join(config.ftp_dir_path, folder)
                    
                    if os.path.isdir(folder_path):
                        build_info_path = os.path.join(folder_path, 'build_info.py')

                        try:
                        
                            check_file_validity(build_info_path)

                            folders_on_disk.add(folder)
                            
                            build_class = import_build_info_dynamically(build_info_path)

                            existing_record = db_session.query(data_models.VersionRecord).filter_by(dir_name=folder).first()
                            
                            b_tag = getattr(build_class, 'BUILD_TAG', 'unknown')
                            
                            if not existing_record:
                                new_record = data_models.VersionRecord(
                                    dir_name=folder,
                                    build_tag=b_tag,
                                    build_version=getattr(build_class, 'BUILD_VERSION', 'unknown'),
                                    git_release_hash=getattr(build_class, 'GIT_RELEASE_HASH', 'unknown'),
                                    git_release_tag=getattr(build_class, 'GIT_RELEASE_TAG', 'unknown'),
                                    git_release_datetime=getattr(build_class, 'GIT_RELEASE_DATETIME', 'unknown'),
                                    git_branch=getattr(build_class, 'GIT_BRANCH', 'unknown'),
                                    is_latest=False
                                )
                                db_session.add(new_record)
                                print(f"✅ Added: {folder}")
                                
                            elif existing_record.build_tag != b_tag:
                                existing_record.build_tag = b_tag
                                existing_record.build_version = getattr(build_class, 'BUILD_VERSION', 'unknown')
                                existing_record.git_release_hash = getattr(build_class, 'GIT_RELEASE_HASH', 'unknown')
                                existing_record.git_release_tag = getattr(build_class, 'GIT_RELEASE_TAG', 'unknown')
                                existing_record.git_release_datetime = getattr(build_class, 'GIT_RELEASE_DATETIME', 'unknown')
                                existing_record.git_branch = getattr(build_class, 'GIT_BRANCH', 'unknown')
                                print(f"🔄 Updated: {folder}")
                            
                        except (FileNotFoundError, ValueError, ImportError, AttributeError, RuntimeError) as e:
                            print(f"⚠️ Skip folder {folder}: {e}")

                # --- Mirroring ---
                all_db_records = db_session.query(data_models.VersionRecord).all()
                for record in all_db_records:
                    if record.dir_name not in folders_on_disk:
                        db_session.delete(record)
                        print(f"🗑️ Deleted: {record.dir_name}")
                
                db_session.commit()
                
                    
        time.sleep(config.scan_interval)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run FTP Scanner Worker')
    parser.add_argument(
        '-c', '--config',
        type=str,
        help='Path to the configuration file (e.g. prod_config.ini)',
        default='config.ini'
    )
    args = parser.parse_args()

    app_settings = read_config(args.config)

    main(app_settings)