# -*- coding: utf-8 -*-
import requests

URL = "http://localhost:8000/graphql"
STATS_URL = "http://localhost:8000/stats"

print("--- 1. Consultation unitaire de l'utilisateur 42 ---")
q1 = '{ user(id: "42") { id name email } }'
r1 = requests.post(URL, json={"query": q1})
print(f"Statut : {r1.status_code}, Taille : {len(r1.content)} octets")
print(f"Réponse : {r1.json()}")

print("\n--- 2. Résolution naïve N+1 requêtes (useLoader: false) ---")
q_naive = '{ users(limit: 100) { id orders(useLoader: false) { id item } } }'
# Les compteurs du serveur sont cumulatifs : on mesure l'écart avant / après chaque requête
s_start = requests.get(STATS_URL).json()
requests.post(URL, json={"query": q_naive})
s_naive = requests.get(STATS_URL).json()
n_naive = s_naive["sql_naive_count"] - s_start["sql_naive_count"]
print("Compteurs cumulés après cas naïf :", s_naive)
print(f"Résultat : {n_naive} requêtes SQL exécutées vers la BDD !")

print("\n--- 3. Résolution optimisée avec DataLoader (useLoader: true) ---")
q_batch = '{ users(limit: 100) { id orders(useLoader: true) { id item } } }'
requests.post(URL, json={"query": q_batch})
s_batch = requests.get(STATS_URL).json()
n_batch = s_batch["sql_batch_count"] - s_naive["sql_batch_count"]
print("Compteurs cumulés après DataLoader :", s_batch)
print(f"Résultat : seulement {n_batch} requêtes SQL exécutées (1 users + 1 IN batch orders) !")

print("\n--- 4. Mutation de mise à jour d'email ---")
q_mut = 'mutation { updateUserEmail(id: "42", email: "alice.m@ensiie.fr") { id email } }'
r_mut = requests.post(URL, json={"query": q_mut})
print("Réponse mutation :", r_mut.json()["data"]["updateUserEmail"])
