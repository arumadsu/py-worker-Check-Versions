from flask import Flask, render_template, request
import grpc

import updater_pb2
import updater_pb2_grpc

app = Flask(__name__)

channel = grpc.insecure_channel('localhost:50051')
stub = updater_pb2_grpc.UpdaterAppStub(channel)

@app.route('/')
def index():
    show_all_flag = request.args.get('show_all') == 'true'

    try:
        grpc_request = updater_pb2.GetVersionsRequest(show_all=show_all_flag)
        response = stub.GetAvailableVersions(grpc_request)
        versions = response.versions
    except grpc.RpcError as e:
        print(f"gRPC communication error: {e}")
        versions = []

    return render_template('index.html', versions=versions, showing_all=show_all_flag)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888, debug=True)