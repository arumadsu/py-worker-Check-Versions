import grpc
from concurrent import futures
import configparser
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import updater_pb2
import updater_pb2_grpc

import data_models

config = configparser.ConfigParser()
config.read('config.ini')
db_name = config.get('Settings', 'db_name', fallback='app.db')
base_dir = os.path.dirname(os.path.abspath(__file__))
DATABASE_URI = f"sqlite:///{os.path.join(base_dir, db_name)}"

engine = create_engine(DATABASE_URI, echo=False)
SessionLocal = sessionmaker(bind=engine)

class UpdaterAppServicer(updater_pb2_grpc.UpdaterAppServicer):
    def GetAvailableVersions(self, request, context):
        print(f"Request received from Flask! show_all = {request.show_all}")

        with SessionLocal() as session:
            if request.show_all:
                records = session.query(data_models.VersionRecord)\
                                    .order_by(data_models.VersionRecord.git_release_datetime.desc())\
                                    .all()
            else:
                officials = session.query(data_models.VersionRecord)\
                    .filter(data_models.VersionRecord.build_tag != 'unknown')\
                    .order_by(data_models.VersionRecord.git_release_datetime.desc())\
                    .limit(3).all()
                if officials:
                    threshold_date = officials[-1].git_release_datetime
                else:
                    threshold_date = "0000-00-00 00:00:00"
                
                tests = session.query(data_models.VersionRecord)\
                    .filter(data_models.VersionRecord.build_tag == 'unknown')\
                    .filter(data_models.VersionRecord.git_release_datetime >= threshold_date)\
                    .all()
                
                records = officials + tests
                records.sort(key=lambda x: x.git_release_datetime, reverse=True)

            proto_versions = []
            for r in records:
                v = updater_pb2.VersionInfo(
                    dir_name=r.dir_name or "",
                    build_tag=r.build_tag or "",
                    build_version=r.build_version or "",
                    git_release_hash=r.git_release_hash or "",
                    git_release_tag=r.git_release_tag or "",
                    git_release_datetime=r.git_release_datetime or "",
                    git_branch=r.git_branch or "",
                    is_latest=not request.show_all
                )
                proto_versions.append(v)

            print(f"Sending {len(proto_versions)} versions...")
            return updater_pb2.GetVersionsResponse(versions=proto_versions)
        
        def PerformUpdate(self, request, context):
            yield updater_pb2.UpdateLog(log_message="Preparing for update...", is_completed=False)
            yield updater_pb2.UpdateLog(log_message="The update has not yet been implemented", is_completed=True)

        
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    updater_pb2_grpc.add_UpdaterAppServicer_to_server(UpdaterAppServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC Server is running on port 50051 and is ready to work!")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()