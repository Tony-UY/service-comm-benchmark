# -*- coding: utf-8 -*-
from zeep import Client
from zeep.exceptions import Fault as SoapFault

client = Client('http://localhost:8000/?wsdl')

# 1. Cas nominal (200 OK)
try:
    user = client.service.GetUser(42)
    print(f"[SOAP SUCCÈS] Utilisateur reçu : {user.name} ({user.email})")
except SoapFault as fault:
    print(f"[SOAP ERREUR] : {fault.message}")

# 2. Cas d'erreur (soap:Fault 500)
try:
    user_err = client.service.GetUser(99)
except SoapFault as fault:
    print(f"[SOAP FAULT INTERCEPTÉE] Code: {fault.code}, Message: {fault.message}")
