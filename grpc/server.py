# -*- coding: utf-8 -*-
import grpc, time
from concurrent import futures
import user_pb2, user_pb2_grpc

class UserServicer(user_pb2_grpc.UserServiceServicer):
    def GetUser(self, request, context):
        if request.id == 42:
            return user_pb2.UserResponse(id=42, name="Alice Martin", email="alice@example.com")
        context.abort(grpc.StatusCode.NOT_FOUND, f"Utilisateur ID {request.id} introuvable")

    def StreamUserActivity(self, request, context):
        events = [("LOGIN", 1700000000), ("VIEW_PAGE", 1700000010), ("LOGOUT", 1700000060)]
        for ev, ts in events:
            yield user_pb2.ActivityEvent(event_type=ev, timestamp=ts)
            time.sleep(0.05)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Serveur gRPC démarré sur le port 50051...")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
