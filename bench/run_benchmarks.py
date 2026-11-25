# -*- coding: utf-8 -*-
import os
import sys
import json
import gzip
import time
import orjson
from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import user_pb2


def _encode_varint(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            break
    return bytes(out)


def encode_pb_repeated_users(users) -> bytes:
    """Encode a list as wire-format `message UserList { repeated UserResponse users = 1; }`."""
    chunks = []
    for u in users:
        payload = user_pb2.UserResponse(id=u["id"], name=u["name"], email=u["email"]).SerializeToString()
        # Field 1, wire type 2 (length-delimited) => tag byte 0x0A + varint(len) + payload
        chunks.append(b"\x0a" + _encode_varint(len(payload)) + payload)
    return b"".join(chunks)


# Jeux de données (Cas Utilisateur 42 + multi-échelle)
user_single = {"id": 42, "name": "Alice Martin", "email": "alice@example.com"}
user_full = {
    "id": 42,
    "name": "Alice Martin",
    "email": "alice@example.com",
    "role": "admin",
    "active": True,
    "createdAt": "2026-01-15T10:30:00Z",
    "ordersCount": 9,
}
users_100 = [{"id": i, "name": f"User {i}", "email": f"user{i}@example.com"} for i in range(1, 101)]
users_10000 = [{"id": i, "name": f"User {i}", "email": f"user{i}@example.com"} for i in range(1, 10001)]

# 1. Tailles de payload
# REST
rest_min_1 = json.dumps(user_single, separators=(",", ":")).encode("utf-8")  # 59 o
rest_full_1 = json.dumps(user_full, separators=(",", ":")).encode("utf-8")   # 139 o (over-fetching simulé)
rest_min_100 = json.dumps(users_100, separators=(",", ":")).encode("utf-8")
rest_min_10000 = json.dumps(users_10000, separators=(",", ":")).encode("utf-8")

# GraphQL
gql_targeted_1 = json.dumps(
    {"data": {"user": {"name": "Alice Martin", "email": "alice@example.com"}}},
    separators=(",", ":"),
).encode("utf-8")  # 69 o (champs ciblés : name, email)
gql_single_eq = {"id": "42", "name": "Alice Martin", "email": "alice@example.com"}
gql_100 = [{"id": str(i), "name": f"User {i}", "email": f"user{i}@example.com"} for i in range(1, 101)]
gql_10000 = [{"id": str(i), "name": f"User {i}", "email": f"user{i}@example.com"} for i in range(1, 10001)]

gql_min_1 = json.dumps({"data": {"user": gql_single_eq}}, separators=(",", ":")).encode("utf-8")  # 79 o
gql_min_100 = json.dumps({"data": {"users": gql_100}}, separators=(",", ":")).encode("utf-8")
gql_min_10000 = json.dumps({"data": {"users": gql_10000}}, separators=(",", ":")).encode("utf-8")

# SOAP 1.1 (trame réellement émise par soap/server.py, contrôlée par verify_payloads.py)
SOAP_HEAD = (
    "<?xml version='1.0' encoding='UTF-8'?>\n"
    '<soap11env:Envelope xmlns:soap11env="http://schemas.xmlsoap.org/soap/envelope/" '
    'xmlns:tns="http://example.com/user"><soap11env:Body>'
)
SOAP_TAIL = "</soap11env:Body></soap11env:Envelope>"


def soap_user(u) -> str:
    return f'<tns:id>{u["id"]}</tns:id><tns:name>{u["name"]}</tns:name><tns:email>{u["email"]}</tns:email>'


def soap_list(users) -> bytes:
    """Liste simulée au même format (le serveur n'expose que GetUser)."""
    items = "".join(f"<tns:UserModel>{soap_user(u)}</tns:UserModel>" for u in users)
    return (
        f"{SOAP_HEAD}<tns:GetUsersResponse><tns:GetUsersResult>{items}"
        f"</tns:GetUsersResult></tns:GetUsersResponse>{SOAP_TAIL}"
    ).encode("utf-8")


soap_xml_1 = (
    f"{SOAP_HEAD}<tns:GetUserResponse><tns:GetUserResult>{soap_user(user_single)}"
    f"</tns:GetUserResult></tns:GetUserResponse>{SOAP_TAIL}"
).encode("utf-8")  # 383 o
soap_xml_100 = soap_list(users_100)
soap_xml_10000 = soap_list(users_10000)

# gRPC Protobuf
grpc_bin_1 = user_pb2.UserResponse(id=42, name="Alice Martin", email="alice@example.com").SerializeToString()  # 35 o
grpc_bin_100 = encode_pb_repeated_users(users_100)
grpc_bin_10000 = encode_pb_repeated_users(users_10000)


# 2. Benchmark Latence CPU (désérialisation client en mémoire, 500 warmup + 5000 mesures)
def bench_fn(fn, iters=5000):
    for _ in range(500):
        fn()
    times = []
    for _ in range(iters):
        t0 = time.perf_counter_ns()
        fn()
        t1 = time.perf_counter_ns()
        times.append(t1 - t0)
    times.sort()
    return times[int(iters * 0.50)] / 1000.0, times[int(iters * 0.95)] / 1000.0


p50_grpc, p95_grpc = bench_fn(lambda: user_pb2.UserResponse.FromString(grpc_bin_1))
p50_rest_std, p95_rest_std = bench_fn(lambda: json.loads(rest_min_1))
p50_rest_orjson, p95_rest_orjson = bench_fn(lambda: orjson.loads(rest_min_1))
p50_gql_std, p95_gql_std = bench_fn(lambda: json.loads(gql_targeted_1))
p50_gql_orjson, p95_gql_orjson = bench_fn(lambda: orjson.loads(gql_targeted_1))
p50_soap, p95_soap = bench_fn(lambda: etree.fromstring(soap_xml_1))

print("=" * 116)
print("BENCHMARK MULTI-ÉCHELLE DE COMMUNICATION DE SERVICES (ENSIIE 2026-2027)")
print("Auteurs : Tony UY, Arthur PINEL, Maxence TOURNAUD")
print("=" * 116)
print(
    f"{'Technologie':<26} | {'1 rec (Brut/Gzip)':<18} | {'Ratio':<6} | {'100 rec (Brut/Gzip)':<19} | "
    f"{'10 000 rec (Brut/Gzip)':<22} | {'CPU p50 / p95'}"
)
print("-" * 116)
print(
    f"{'gRPC Protobuf':<26} | {len(grpc_bin_1):>3} o / {len(gzip.compress(grpc_bin_1)):>3} o      | {'1.0x':<6} | "
    f"{len(grpc_bin_100):>5} o / {len(gzip.compress(grpc_bin_100)):>3} o     | "
    f"{len(grpc_bin_10000)/1000:>6.2f} Ko / {len(gzip.compress(grpc_bin_10000))/1000:>5.2f} Ko   | "
    f"{p50_grpc:.2f} / {p95_grpc:.2f} µs"
)
print(
    f"{'REST JSON (Minifié)':<26} | {len(rest_min_1):>3} o / {len(gzip.compress(rest_min_1)):>3} o      | "
    f"{f'{len(rest_min_1)/len(grpc_bin_1):.1f}x':<6} | "
    f"{len(rest_min_100):>5} o / {len(gzip.compress(rest_min_100)):>3} o     | "
    f"{len(rest_min_10000)/1000:>6.2f} Ko / {len(gzip.compress(rest_min_10000))/1000:>5.2f} Ko   | "
    f"{p50_rest_std:.2f} / {p95_rest_std:.2f} µs (std) | {p50_rest_orjson:.2f} µs (orjson)"
)
print(
    f"{'REST JSON (Profil complet)':<26} | {len(rest_full_1):>3} o / {len(gzip.compress(rest_full_1)):>3} o      | "
    f"{f'{len(rest_full_1)/len(grpc_bin_1):.1f}x':<6} | {'-':<19} | {'-':<22} | -"
)
print(
    f"{'GraphQL (name, email)':<26} | {len(gql_targeted_1):>3} o / {len(gzip.compress(gql_targeted_1)):>3} o      | "
    f"{f'{len(gql_targeted_1)/len(grpc_bin_1):.1f}x':<6} | {'-':<19} | {'-':<22} | "
    f"{p50_gql_std:.2f} / {p95_gql_std:.2f} µs (std) | {p50_gql_orjson:.2f} µs (orjson)"
)
print(
    f"{'GraphQL (id, name, email)':<26} | {len(gql_min_1):>3} o / {len(gzip.compress(gql_min_1)):>3} o      | "
    f"{f'{len(gql_min_1)/len(grpc_bin_1):.1f}x':<6} | "
    f"{len(gql_min_100):>5} o / {len(gzip.compress(gql_min_100)):>3} o     | "
    f"{len(gql_min_10000)/1000:>6.2f} Ko / {len(gzip.compress(gql_min_10000))/1000:>5.2f} Ko   | -"
)
print(
    f"{'SOAP 1.1 (Spyne)':<26} | {len(soap_xml_1):>3} o / {len(gzip.compress(soap_xml_1)):>3} o      | "
    f"{f'{len(soap_xml_1)/len(grpc_bin_1):.1f}x':<6} | "
    f"{len(soap_xml_100):>5} o / {len(gzip.compress(soap_xml_100)):>3} o     | "
    f"{len(soap_xml_10000)/1000:>6.2f} Ko / {len(gzip.compress(soap_xml_10000))/1000:>5.2f} Ko   | "
    f"{p50_soap:.2f} / {p95_soap:.2f} µs (lxml)"
)
print("=" * 116)
