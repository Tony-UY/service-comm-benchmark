# -*- coding: utf-8 -*-
import json, gzip, time, orjson
from lxml import etree
import user_pb2

user_single = {"id": 42, "name": "Alice Martin", "email": "alice@example.com"}
users_100 = [{"id": i, "name": f"User {i}", "email": f"user{i}@example.com"} for i in range(1, 101)]
users_10000 = [{"id": i, "name": f"User {i}", "email": f"user{i}@example.com"} for i in range(1, 10001)]

# 1. Tailles de payload
# REST
rest_min_1 = json.dumps(user_single, separators=(',', ':')).encode('utf-8')
rest_fmt_1 = json.dumps(user_single, indent=2).encode('utf-8')
rest_min_100 = json.dumps(users_100, separators=(',', ':')).encode('utf-8')
rest_min_10000 = json.dumps(users_10000, separators=(',', ':')).encode('utf-8')

# GraphQL (équitable avec ID! string)
gql_single = {"id": "42", "name": "Alice Martin", "email": "alice@example.com"}
gql_100 = [{"id": str(i), "name": f"User {i}", "email": f"user{i}@example.com"} for i in range(1, 101)]
gql_10000 = [{"id": str(i), "name": f"User {i}", "email": f"user{i}@example.com"} for i in range(1, 10001)]

gql_min_1 = json.dumps({"data": {"user": gql_single}}, separators=(',', ':')).encode('utf-8')
gql_min_100 = json.dumps({"data": {"users": gql_100}}, separators=(',', ':')).encode('utf-8')
gql_min_10000 = json.dumps({"data": {"users": gql_10000}}, separators=(',', ':')).encode('utf-8')

# SOAP 1.1
soap_xml_min_1 = '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:u="http://example.com/user"><soapenv:Header/><soapenv:Body><u:GetUserResponse><u:id>42</u:id><u:name>Alice Martin</u:name><u:email>alice@example.com</u:email></u:GetUserResponse></soapenv:Body></soapenv:Envelope>'.encode('utf-8')
soap_xml_fmt_1 = '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:u="http://example.com/user">
  <soap:Header/>
  <soap:Body>
    <u:GetUserResponse><u:id>42</u:id><u:name>Alice Martin</u:name><u:email>alice@example.com</u:email></u:GetUserResponse>
  </soap:Body>
</soap:Envelope>'''.encode('utf-8')

soap_items_100 = "".join([f'<u:user><u:id>{u["id"]}</u:id><u:name>{u["name"]}</u:name><u:email>{u["email"]}</u:email></u:user>' for u in users_100])
soap_xml_100 = f'<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:u="http://example.com/user"><soap:Body><u:GetUsersResponse>{soap_items_100}</u:GetUsersResponse></soap:Body></soap:Envelope>'.encode('utf-8')

soap_items_10000 = "".join([f'<u:user><u:id>{u["id"]}</u:id><u:name>{u["name"]}</u:name><u:email>{u["email"]}</u:email></u:user>' for u in users_10000])
soap_xml_10000 = f'<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:u="http://example.com/user"><soap:Body><u:GetUsersResponse>{soap_items_10000}</u:GetUsersResponse></soap:Body></soap:Envelope>'.encode('utf-8')

# gRPC Protobuf
msg = user_pb2.UserResponse(id=42, name="Alice Martin", email="alice@example.com")
grpc_bin_1 = msg.SerializeToString()

def encode_pb_user(u):
    m = user_pb2.UserResponse(id=u["id"], name=u["name"], email=u["email"])
    return m.SerializeToString()

grpc_bin_100 = b"".join([encode_pb_user(u) for u in users_100])
grpc_bin_10000 = b"".join([encode_pb_user(u) for u in users_10000])

# Benchmark Latence CPU
def bench_fn(fn, iters=5000):
    for _ in range(500): fn()
    times = []
    for _ in range(iters):
        t0 = time.perf_counter_ns()
        fn()
        t1 = time.perf_counter_ns()
        times.append(t1 - t0)
    times.sort()
    return times[int(iters * 0.50)] / 1000.0, times[int(iters * 0.95)] / 1000.0

p50_grpc, p95_grpc = bench_fn(lambda: user_pb2.UserResponse.FromString(grpc_bin_1))
p50_orjson, p95_orjson = bench_fn(lambda: orjson.loads(rest_min_1))
p50_json_std, p95_json_std = bench_fn(lambda: json.loads(rest_min_1))
p50_gql, p95_gql = bench_fn(lambda: orjson.loads(gql_min_1))
p50_soap, p95_soap = bench_fn(lambda: etree.fromstring(soap_xml_min_1))

print("=" * 80)
print("BENCHMARK MULTI-ÉCHELLE DE COMMUNICATION DE SERVICES (ENSIIE 2026-2027)")
print("Auteurs : Tony UY, Arthur PINEL, Maxence TOURNAUD")
print("=" * 80)

print(f"{'Technologie':<22} | {'1 rec (Brut/Gzip)':<20} | {'100 rec':<18} | {'10 000 rec':<20} | {'Latence CPU (p50/p95)':<22}")
print("-" * 110)
print(f"{'gRPC Protobuf':<22} | {len(grpc_bin_1):>3} o / {len(gzip.compress(grpc_bin_1)):>3} o       | {len(grpc_bin_100):>5} o / {len(gzip.compress(grpc_bin_100)):>3} o | {len(grpc_bin_10000)/1000:>6.2f} Ko / {len(gzip.compress(grpc_bin_10000))/1000:>5.2f} Ko | {p50_grpc:>5.2f} µs / {p95_grpc:>5.2f} µs")
print(f"{'REST (Minifié)':<22} | {len(rest_min_1):>3} o / {len(gzip.compress(rest_min_1)):>3} o       | {len(rest_min_100):>5} o / {len(gzip.compress(rest_min_100)):>3} o | {len(rest_min_10000)/1000:>6.2f} Ko / {len(gzip.compress(rest_min_10000))/1000:>5.2f} Ko | {p50_json_std:>5.2f} µs / {p95_json_std:>5.2f} µs (std)")
print(f"{'GraphQL (Équitable)':<22} | {len(gql_min_1):>3} o / {len(gzip.compress(gql_min_1)):>3} o       | {len(gql_min_100):>5} o / {len(gzip.compress(gql_min_100)):>3} o | {len(gql_min_10000)/1000:>6.2f} Ko / {len(gzip.compress(gql_min_10000))/1000:>5.2f} Ko | {p50_gql:>5.2f} µs / {p95_gql:>5.2f} µs")
print(f"{'SOAP 1.1 (Minifié)':<22} | {len(soap_xml_min_1):>3} o / {len(gzip.compress(soap_xml_min_1)):>3} o       | {len(soap_xml_100):>5} o / {len(gzip.compress(soap_xml_100)):>3} o | {len(soap_xml_10000)/1000:>6.2f} Ko / {len(gzip.compress(soap_xml_10000))/1000:>5.2f} Ko | {p50_soap:>5.2f} µs / {p95_soap:>5.2f} µs")
print(f"{'SOAP 1.1 (Formaté)':<22} | {len(soap_xml_fmt_1):>3} o / {len(gzip.compress(soap_xml_fmt_1)):>3} o       | -                  | -                    | -")
print("=" * 110)
