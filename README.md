# service-comm-benchmark

> **Suite d'évaluation empirique multi-échelle et implémentations comparatives de communication orientée services (SOAP, REST, GraphQL, gRPC)**  
> **École :** ENSIIE (École Nationale Supérieure d'Informatique pour l'Industrie et l'Entreprise)  
> **Cours :** Architectures logicielles : services, microservices et BPM  
> **Année universitaire :** 2026 – 2027  
> **Auteurs :** Tony UY, Arthur PINEL, Maxence TOURNAUD  
> **Rapport complet (PDF) :** [Consulter le rapport final (12 pages)](docs/Rapport_Technologies_Services_ENSIIE.pdf)

---

## 1. Vue d'ensemble du projet

Ce dépôt contient l'ensemble du code source exécutable, des contrats d'interface, des bancs d'essai de mesure et des schémas d'architecture accompagnant le rapport académique de comparaison des quatre grandes technologies de communication inter-services :
1. **SOAP 1.1 / WSDL 1.1** (Appel procédural formalisé sous enveloppe XML avec sécurité au niveau du message WS-Security)
2. **REST / HTTP** (Manipulation de ressources via verbes HTTP standard, cache ETag / 304, spécification OpenAPI 3.1)
3. **GraphQL** (Langage de requêtage déclaratif, schéma SDL, résolveurs avec DataLoader anti-N+1 et mutations)
4. **gRPC / HTTP/2** (Appels RPC haute performance, sérialisation binaire Protocol Buffers proto3, streaming et deadlines)

Le cas d'usage unifié implémenté par chaque technologie est la **gestion du profil utilisateur 42** (*Alice Martin*, `alice@example.com`).

---

## 2. Structure du dépôt

```text
service-comm-benchmark/
├── README.md               # Documentation complète et guide de lancement
├── requirements.txt        # Dépendances Python nécessaires
├── LICENSE                 # Licence MIT
├── bench/
│   ├── run_benchmarks.py   # Script de benchmark autonome en 1 commande
│   ├── verify_payloads.py  # Contrôle des tailles du rapport sur les vrais serveurs
│   ├── user_pb2.py         # Stubs Protobuf compilés
│   └── user_pb2_grpc.py
├── soap/
│   ├── UserService.wsdl    # Contrat WSDL 1.1 + XSD servi par le serveur (/?wsdl)
│   ├── server.py           # Serveur Spyne WSGI avec levée de soap:Fault
│   └── client.py           # Client Zeep avec capture de SoapFault
├── rest/
│   ├── openapi.yaml        # Spécification OpenAPI 3.1 (GET, POST, PUT)
│   ├── server.py           # Serveur FastAPI avec ETag dynamique et 304
│   └── client.py           # Client Requests avec cycle POST / 304 / PUT
├── graphql/
│   ├── schema.graphql      # Schéma SDL (Query, Mutation, DataLoader)
│   ├── server.py           # Serveur Strawberry + FastAPI (bascule N+1, /stats)
│   └── client.py           # Client Requests (démonstration 101 vs 2 requêtes)
├── grpc/
│   ├── user.proto          # Définition IDL proto3 (Unaire + Streaming)
│   ├── server.py           # Serveur gRPC avec cycle de vie bloquant
│   ├── client.py           # Client gRPC avec streaming et interception deadline
│   ├── user_pb2.py
│   └── user_pb2_grpc.py
└── docs/
    ├── Rapport_Technologies_Services_ENSIIE.pdf   # Rapport PDF final (12 pages)
    ├── Rapport_Technologies_Services_ENSIIE.docx  # Version Word éditable
    └── images/                                    # Schémas et figures du rapport
```

---

## 3. Lancement rapide : Reproduction du Benchmark en 1 seule commande

### Prérequis
- Python 3.10, 3.11 ou 3.12 (CPython 64 bits)

### Installation des dépendances
```bash
pip install -r requirements.txt
```

### Exécution du banc d'essai multi-échelle
```bash
python bench/run_benchmarks.py
```

Ce script autonome mesure, sur des réponses construites en mémoire :
1. Les tailles de charges utiles brutes et compressées gzip à **1, 100 et 10 000 enregistrements**.
2. La latence CPU de désérialisation en mémoire sur **5 000 itérations** (médiane p50 et 95e percentile p95).

### Contrôle des tailles sur les vrais serveurs
```bash
python bench/verify_payloads.py
```

Ce script démarre les quatre serveurs l'un après l'autre (ports 8000 et 50051 libres) et échoue si une taille publiée dans le rapport ne correspond plus à la réponse reçue.

---

## 4. Synthèse des résultats mesurés (Cas Utilisateur 42 — Rapport Section C.5)

| Technologie | Taille 1 rec (Brut) | Ratio vs gRPC | Remarque technique |
| :--- | :---: | :---: | :--- |
| **gRPC Protobuf** | **35 o** | **1,0x (Base)** | Encodage binaire compact (tags d'index + varints). |
| **REST (Minifié)** | **59 o** | **1,7x** | JSON minimal `{"id":42,"name":"...","email":"..."}`. |
| **GraphQL (Champs choisis)** | **69 o** | **2,0x** | Enveloppe `{"data":{"user":...}}` limitée aux champs demandés (`name`, `email`). |
| **GraphQL (id, name, email)** | **79 o** | **2,3x** | Mêmes champs que REST et gRPC, avec l'enveloppe `data`/`user`. |
| **REST (Profil complet, simulé)** | **139 o** | **4,0x** | Illustration de la sur-récupération (*over-fetching*), non renvoyée par `rest/server.py`. |
| **SOAP 1.1 (Réponse Spyne)** | **383 o** | **10,9x** | Déclaration XML, enveloppe, espaces de noms et balises ouvrantes/fermantes. |

*Exécutez `python bench/run_benchmarks.py` pour obtenir également les mesures multi-échelles (100 et 10 000 enregistrements, avec et sans gzip) ainsi que les latences CPU de désérialisation (`json` standard, `orjson`, `lxml`, `protobuf`).*

---

## 5. Exécution des services individuels

Chaque technologie dispose de son serveur et client de test indépendants :

### SOAP / WSDL
```bash
# Terminal 1 : Serveur SOAP Spyne
python soap/server.py

# Terminal 2 : Client Zeep
python soap/client.py
```
*Note Python 3.12 :* Le serveur intègre un pont de compatibilité pour `six.moves.collections_abc` (PEP 451).

### REST (FastAPI)
```bash
# Terminal 1 : Serveur REST
python rest/server.py

# Terminal 2 : Client Requests (POST, ETag 304, PUT, 404)
python rest/client.py
```

### GraphQL (Strawberry + FastAPI)
```bash
# Terminal 1 : Serveur GraphQL
python graphql/server.py

# Terminal 2 : Client Requests (Validation N+1 : 101 requêtes naïf vs 2 requêtes DataLoader)
python graphql/client.py
```

### gRPC (Protocol Buffers v3 + HTTP/2)
```bash
# Compilation du proto (déjà généré dans le dépôt) :
python -m grpc_tools.protoc -Igrpc --python_out=grpc --grpc_python_out=grpc grpc/user.proto

# Terminal 1 : Serveur gRPC
python grpc/server.py

# Terminal 2 : Client gRPC (Unaire, Streaming serveur, Deadline)
python grpc/client.py
```

---

## 6. Schémas et Diagrammes d'Architecture

Tous les schémas techniques haute résolution générés pour le rapport sont consultables dans [`docs/images/`](docs/images/) :
- `soa_triangle.png` : Le triangle fondamental SOA
- `soap_structure.png` : Structure de l'enveloppe SOAP 1.1 et WS-Security
- `richardson_model.png` : Modèle de maturité de Richardson et propriétés HTTP
- `graphql_engine.png` : Moteur d'exécution GraphQL et compilation AST
- `grpc_http2.png` : Multiplexage HTTP/2 et encodage binaire Protobuf
- `benchmark_sizes.png` : Graphique multi-échelle des tailles réseau
- `decision_tree.png` : Arbre de décision pour le choix architectural
- `hybrid_architecture.png` : Architecture hybride d'entreprise avec patron BFF et passerelle d'API

---

## 7. Licence

Ce projet est distribué sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.
