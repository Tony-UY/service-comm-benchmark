# -*- coding: utf-8 -*-
# Compatibilité Python 3.12+ : le six 1.14 embarqué par Spyne 2.14 repose sur
# find_module(), supprimé en 3.12. On redirige uniquement ses sous-modules moves
# vers le paquet six installé (le reste du six embarqué est spécifique à Spyne).
# En 3.10 / 3.11, Spyne fonctionne tel quel.
import sys
if sys.version_info >= (3, 12):
    import importlib
    for _name in ('six.moves', 'six.moves.collections_abc', 'six.moves.http_cookies',
                  'six.moves.urllib', 'six.moves.urllib.error', 'six.moves.urllib.parse',
                  'six.moves.urllib.request'):
        sys.modules['spyne.util.' + _name] = importlib.import_module(_name)

from spyne import Application, rpc, ServiceBase, Integer, Unicode, ComplexModel, Fault
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from wsgiref.simple_server import make_server
from lxml import etree

class UserModel(ComplexModel):
    id = Integer
    name = Unicode
    email = Unicode

class UserService(ServiceBase):
    @rpc(Integer, _returns=UserModel)
    def GetUser(ctx, id):
        if id == 42:
            return UserModel(id=42, name="Alice Martin", email="alice@example.com")
        detail_elt = etree.Element("{http://example.com/user}UserNotFoundFault")
        etree.SubElement(detail_elt, "message").text = "Utilisateur non trouvé"
        etree.SubElement(detail_elt, "id").text = str(id)
        raise Fault(faultcode="Client", faultstring="Utilisateur non trouvé", detail=detail_elt)

app = Application([UserService], 'http://example.com/user', in_protocol=Soap11(validator='lxml'), out_protocol=Soap11())
wsgi_app = WsgiApplication(app)

if __name__ == '__main__':
    print("Démarrage du serveur SOAP sur http://0.0.0.0:8000/?wsdl ...")
    server = make_server('0.0.0.0', 8000, wsgi_app)
    server.serve_forever()
