# -*- coding: utf-8 -*-
import requests

BASE_URL = "http://localhost:8000"

print("--- 1. POST /users ---")
r_post = requests.post(f"{BASE_URL}/users", json={"name": "Bob Dupont", "email": "bob@example.com"})
print(f"Statut : {r_post.status_code}, Location : {r_post.headers.get('Location')}, Corps : {r_post.json()}")

print("\n--- 2. GET /users/42 (Premier appel) ---")
r1 = requests.get(f"{BASE_URL}/users/42")
etag1 = r1.headers.get("ETag")
print(f"Statut : {r1.status_code}, ETag : {etag1}, Taille : {len(r1.content)} octets, Données : {r1.json()}")

print("\n--- 3. GET /users/42 Conditionnel (If-None-Match) ---")
r2 = requests.get(f"{BASE_URL}/users/42", headers={"If-None-Match": etag1})
print(f"Statut : {r2.status_code} (304 Not Modified -> 0 octet transféré)")

print("\n--- 4. PUT /users/42 (Modification idempotente) ---")
r_put = requests.put(f"{BASE_URL}/users/42", json={"name": "Alice Martin", "email": "alice.m@ensiie.fr"})
print(f"Statut : {r_put.status_code} (204 No Content)")

print("\n--- 5. GET /users/42 après invalidation de cache ---")
r3 = requests.get(f"{BASE_URL}/users/42", headers={"If-None-Match": etag1})
print(f"Statut : {r3.status_code} (200 OK -> nouveau ETag : {r3.headers.get('ETag')})")

print("\n--- 6. GET /users/99 (Erreur 404) ---")
r4 = requests.get(f"{BASE_URL}/users/99")
print(f"Statut : {r4.status_code}, Message : {r4.json()}")
