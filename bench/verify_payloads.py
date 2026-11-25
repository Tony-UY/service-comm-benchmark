# -*- coding: utf-8 -*-
"""Démarre les quatre serveurs l'un après l'autre et mesure les réponses réellement reçues.

Les tailles attendues sont celles publiées dans le rapport (section C.5) : le script
échoue (code 1) si le code et le rapport ne concordent plus.
"""
import os
import socket
import subprocess
import sys
import time

import requests

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOAP_REQUEST = (
    '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:usr="http://example.com/user">'
    "<soapenv:Body><usr:GetUser><usr:id>42</usr:id></usr:GetUser></soapenv:Body></soapenv:Envelope>"
)
HTTP = "http://localhost:8000"


def port_open(port):
    try:
        with socket.create_connection(("localhost", port), timeout=1):
            return True
    except OSError:
        return False


class Server:
    def __init__(self, name, port):
        self.name, self.port = name, port

    def __enter__(self):
        if port_open(self.port):
            sys.exit(f"Le port {self.port} est déjà occupé : arrêtez l'autre serveur avant de lancer ce script.")
        self.proc = subprocess.Popen(
            [sys.executable, os.path.join(ROOT, self.name, "server.py")],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        for _ in range(60):
            if port_open(self.port):
                return self
            if self.proc.poll() is not None:
                sys.exit(f"Le serveur {self.name} s'est arrêté au démarrage.")
            time.sleep(0.25)
        self.proc.terminate()
        sys.exit(f"Le serveur {self.name} ne répond pas.")

    def __exit__(self, *exc):
        self.proc.terminate()
        self.proc.wait()
        while port_open(self.port):
            time.sleep(0.1)


def graphql(query):
    return requests.post(f"{HTTP}/graphql", json={"query": query})


results = []  # (libellé, mesuré, attendu)

with Server("soap", 8000):
    r = requests.post(f"{HTTP}/", data=SOAP_REQUEST, headers={"Content-Type": "text/xml; charset=utf-8"})
    assert r.status_code == 200, r.text
    soap_body = r.text
    results.append(("SOAP 1.1 (réponse Spyne)", len(r.content), 383))

with Server("rest", 8000):
    r = requests.get(f"{HTTP}/users/42")
    results.append(("REST (id, name, email)", len(r.content), 59))
    r304 = requests.get(f"{HTTP}/users/42", headers={"If-None-Match": r.headers["ETag"]})
    assert r304.status_code == 304
    results.append(("REST (304, corps)", len(r304.content), 0))

with Server("graphql", 8000):
    results.append(("GraphQL (name, email)", len(graphql("{ user(id: 42) { name email } }").content), 69))
    results.append(("GraphQL (id, name, email)", len(graphql("{ user(id: 42) { id name email } }").content), 79))
    for use_loader, key, expected in (("false", "sql_naive_count", 101), ("true", "sql_batch_count", 2)):
        before = requests.get(f"{HTTP}/stats").json()[key]
        graphql("{ users(limit: 100) { id orders(useLoader: %s) { id } } }" % use_loader)
        after = requests.get(f"{HTTP}/stats").json()[key]
        results.append((f"GraphQL accès données (useLoader: {use_loader})", after - before, expected))

with Server("grpc", 50051):
    import grpc
    sys.path.insert(0, os.path.join(ROOT, "grpc"))
    import user_pb2
    import user_pb2_grpc
    with grpc.insecure_channel("localhost:50051") as channel:
        user = user_pb2_grpc.UserServiceStub(channel).GetUser(user_pb2.UserRequest(id=42), timeout=5)
    results.append(("gRPC (message Protobuf)", user.ByteSize(), 35))

ok = True
for label, measured, expected in results:
    same = measured == expected
    ok &= same
    print(f"{'OK   ' if same else 'ÉCART'} | {label:<44} | mesuré {measured:>4} | rapport {expected:>4}")
print("\nRéponse SOAP reçue :\n" + soap_body)
sys.exit(0 if ok else 1)
