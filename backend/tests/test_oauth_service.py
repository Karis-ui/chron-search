import asyncio
from urllib.parse import parse_qs, urlsplit

from app.core.oauth_config import OAuthProvider, OAuthProviderConfig, oauth_settings
from app.services.oauth_service import OAuthService


def test_authorization_url_supports_google_and_github_enum_members(monkeypatch):
    configs = {
        OAuthProvider.google: OAuthProviderConfig(
            name="Google",
            client_id="google-client",
            client_secret="google-secret",
            authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            userinfo_url="https://www.googleapis.com/oauth2/v3/userinfo",
            scopes=["openid", "email", "profile"],
            redirect_uri="https://api.example.test/api/v1/oauth/google/callback",
        ),
        OAuthProvider.github: OAuthProviderConfig(
            name="GitHub",
            client_id="github-client",
            client_secret="github-secret",
            authorize_url="https://github.com/login/oauth/authorize",
            token_url="https://github.com/login/oauth/access_token",
            userinfo_url="https://api.github.com/user",
            scopes=["read:user", "user:email"],
            redirect_uri="https://api.example.test/api/v1/oauth/github/callback",
        ),
    }
    monkeypatch.setattr(
        type(oauth_settings),
        "get_provider",
        lambda self, provider: configs[provider],
    )

    async def run_test():
        service = OAuthService(db=None)

        async def create_state(**kwargs):
            return "test-state"

        monkeypatch.setattr(service, "create_state", create_state)

        google_url = await service.get_authorization_url(OAuthProvider.google)
        google_params = parse_qs(urlsplit(google_url).query)
        assert google_params["client_id"] == ["google-client"]
        assert google_params["state"] == ["test-state"]
        assert google_params["access_type"] == ["offline"]

        github_url = await service.get_authorization_url(OAuthProvider.github)
        github_params = parse_qs(urlsplit(github_url).query)
        assert github_params["client_id"] == ["github-client"]
        assert github_params["state"] == ["test-state"]
        assert github_params["allow_signup"] == ["true"]

    asyncio.run(run_test())
