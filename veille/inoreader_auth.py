"""Obtention unique du refresh_token Inoreader (à lancer sur votre machine).

1. Créer une application sur https://www.inoreader.com/developers/ (onglet
   « Developer apps »), avec l'URL de redirection http://localhost:8765/
   et la portée « read ».
2. export INOREADER_APP_ID=... INOREADER_APP_KEY=...
3. python -m veille.inoreader_auth
4. Copier le refresh_token affiché dans le secret GitHub INOREADER_REFRESH_TOKEN.
"""
from __future__ import annotations

import os
import secrets
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import requests

REDIRECTION = "http://localhost:8765/"
etat = secrets.token_urlsafe(16)
code: dict = {}


class Retour(BaseHTTPRequestHandler):
    def do_GET(self):
        q = parse_qs(urlparse(self.path).query)
        if q.get("state", [""])[0] == etat and "code" in q:
            code["valeur"] = q["code"][0]
            message = "Autorisation reçue, vous pouvez fermer cet onglet."
        else:
            message = "Réponse inattendue (state invalide)."
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(message.encode())

    def log_message(self, *_):
        pass


def main():
    app_id, app_key = os.environ["INOREADER_APP_ID"], os.environ["INOREADER_APP_KEY"]
    url = "https://www.inoreader.com/oauth2/auth?" + urlencode({
        "client_id": app_id, "redirect_uri": REDIRECTION, "response_type": "code",
        "scope": "read", "state": etat,
    })
    print(f"Ouverture du navigateur : {url}")
    webbrowser.open(url)
    serveur = HTTPServer(("localhost", 8765), Retour)
    while "valeur" not in code:
        serveur.handle_request()
    r = requests.post("https://www.inoreader.com/oauth2/token", timeout=30, data={
        "code": code["valeur"], "redirect_uri": REDIRECTION, "client_id": app_id,
        "client_secret": app_key, "scope": "", "grant_type": "authorization_code",
    })
    r.raise_for_status()
    print("\nrefresh_token à stocker dans le secret INOREADER_REFRESH_TOKEN :")
    print(r.json()["refresh_token"])


if __name__ == "__main__":
    main()
