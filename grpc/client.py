# -*- coding: utf-8 -*-
import grpc
import user_pb2, user_pb2_grpc

channel = grpc.insecure_channel('localhost:50051')
stub = user_pb2_grpc.UserServiceStub(channel)

print("--- 1. Appel RPC Unaire GetUser(42) ---")
res = stub.GetUser(user_pb2.UserRequest(id=42))
print(f"Réponse reçue : id={res.id}, name='{res.name}', email='{res.email}'")

print("\n--- 2. Appel Streaming Serveur StreamUserActivity(42) ---")
for event in stub.StreamUserActivity(user_pb2.UserRequest(id=42)):
    print(f"Événement de streaming : type={event.event_type}, timestamp={event.timestamp}")

print("\n--- 3. Capture de DEADLINE_EXCEEDED (timeout) ---")
# Le flux dure environ 150 ms côté serveur : une deadline de 80 ms l'interrompt en cours de route
try:
    for event in stub.StreamUserActivity(user_pb2.UserRequest(id=42), timeout=0.08):
        print(f"Événement reçu avant la deadline : type={event.event_type}")
except grpc.RpcError as e:
    print(f"RpcError interceptée : code={e.code().name}, détails={e.details()}")
