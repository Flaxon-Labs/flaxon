from __future__ import annotations

import secrets
import urllib.parse
from typing import Any


class OAuth2Provider:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        authorization_endpoint: str,
        token_endpoint: str,
        redirect_uri: str,
        scope: str = "openid profile email",
        state: str | None = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorization_endpoint = authorization_endpoint
        self.token_endpoint = token_endpoint
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.state = state or secrets.token_urlsafe(32)

    def get_authorization_url(self, additional_params: dict[str, Any] | None = None) -> str:
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": self.scope,
            "state": self.state,
            **(additional_params or {}),
        }
        return f"{self.authorization_endpoint}?{urllib.parse.urlencode(params)}"

    async def exchange_code(self, code: str) -> dict[str, Any]:
        import httpx

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_endpoint, data=data)
            response.raise_for_status()
            return response.json()

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        import httpx

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_endpoint, data=data)
            response.raise_for_status()
            return response.json()


class OAuth2Backend:
    def __init__(self, providers: dict[str, OAuth2Provider] | None = None) -> None:
        self.providers = providers or {}

    def register_provider(self, name: str, provider: OAuth2Provider) -> None:
        self.providers[name] = provider

    def get_provider(self, name: str) -> OAuth2Provider | None:
        return self.providers.get(name)

    def get_authorization_url(self, provider_name: str) -> str:
        provider = self.get_provider(provider_name)
        if provider is None:
            raise ValueError(f"Provider '{provider_name}' not found")
        return provider.get_authorization_url()

    async def authenticate(self, provider_name: str, code: str) -> dict[str, Any]:
        provider = self.get_provider(provider_name)
        if provider is None:
            raise ValueError(f"Provider '{provider_name}' not found")
        return await provider.exchange_code(code)
