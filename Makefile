proto:
	python -m grpc_tools.protoc -I ./protobufs --python_out=./frontend --grpc_python_out=./frontend ./protobufs/updater.proto
	python -m grpc_tools.protoc -I ./protobufs --python_out=./backend --grpc_python_out=./backend ./protobufs/updater.proto

clean:
	rm -f frontend/*_pb2*.py
	rm -f backend/*_pb2*.py