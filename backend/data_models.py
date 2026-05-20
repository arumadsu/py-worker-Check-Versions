import os
from typing import ClassVar
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base

class AppConfig(BaseModel):
    database_uri: str
    scan_interval: int
    ftp_dir_name: str
    base_dir: ClassVar[str] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    @property
    def ftp_dir_path(self):
        return(os.path.join(self.base_dir, self.ftp_dir_name))


Base = declarative_base()

class VersionRecord(Base):
    __tablename__ = 'versions'
    
    id = Column(Integer, primary_key=True)
    dir_name = Column(String, unique=True)
    
    build_tag = Column(String)
    build_version = Column(String)
    git_release_hash = Column(String)
    git_release_tag = Column(String)
    git_release_datetime = Column(String)
    git_branch = Column(String)
    
    is_latest = Column(Boolean, default=False)

