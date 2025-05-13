from enum import StrEnum, auto
from time import sleep
from typing import cast

import typer
from loguru import logger
from pydantic import BaseModel
from typerdrive import (
    CacheManager,
    TyperdriveClient,
    TyperdriveError,
    add_cache_subcommand,
    add_logs_subcommand,
    add_settings_subcommand,
    attach_cache,
    attach_client,
    attach_logging,
    attach_settings,
    handle_errors,
    log_error,
    terminal_message,
)


class Endpoint(StrEnum):
    unsecured = auto()
    secured = auto()


class Environment(StrEnum):
    dev = auto()
    prod = auto()


class TutorialError(TyperdriveError):
    pass


class APIResponse(BaseModel):
    message: str


class Settings(BaseModel):
    api_url: str
    env: Environment
    auth_url: str
    client_id: str
    audience: str


app = typer.Typer()
add_logs_subcommand(app)
add_settings_subcommand(app, Settings)
add_cache_subcommand(app)


@app.command()
@handle_errors("Failed to access the API", do_except=log_error)
@attach_logging()
@attach_settings(Settings)
@attach_client(api="api_url")
@attach_cache()
def access(ctx: typer.Context, endpoint: Endpoint, api: TyperdriveClient, settings: Settings, cache: CacheManager):
    logger.debug(f"Attempting to access api {endpoint=} in {settings.env} environment")
    headers = {}
    if endpoint == Endpoint.secured:
        logger.debug("Loading access token from cache")
        access_token = cache.load_text("auth/access.token")
        headers = {"Authorization": f"Bearer {access_token}"}
    response = cast(
        APIResponse,
        api.get_x(
            endpoint,
            expected_status=200,
            response_model=APIResponse,
            headers=headers,
        ),
    )
    terminal_message(
        response.message,
        subject="Successfully connected to API",
    )


class DeviceCodeRequest(BaseModel):
    client_id: str
    grant_type: str
    audience: str


class DeviceCodeResponse(BaseModel):
    device_code: str
    verification_uri_complete: str
    interval: int

class TokenRequest(BaseModel):
    grant_type: str
    device_code: str
    client_id: str




@app.command()
@handle_errors("Login failed")
@attach_logging()
@attach_settings(Settings)
@attach_client(auth="auth_url")
@attach_cache()
def login(ctx: typer.Context, settings: Settings, auth: TyperdriveClient, cache: CacheManager):
    logger.debug("Starting login process")
    logger.debug("Requesting device code from auth provider")
    device_code_data = cast(
        DeviceCodeResponse,
        auth.post_x(
            "/oauth/device/code",
            expected_status=200,
            body_obj=DeviceCodeRequest(
                client_id=settings.client_id,
                grant_type="client_credentials",
                audience=settings.audience,
            ),
            response_model=DeviceCodeResponse,
        ),
    )
    terminal_message(
        f"Open {device_code_data.verification_uri_complete} in a browser to complete login",
        subject="Complete login with browser",
    )
    while True:
        logger.debug("Attempting to retrieve a token")
        response_data = cast(
            dict[str, str],
            auth.post_x(
                "/oauth/token",
                body_obj=TokenRequest(
                    grant_type="urn:ietf:params:oauth:grant-type:device_code",
                    device_code=device_code_data.device_code,
                    client_id=settings.client_id,
                ),
            ),
        )
        if "error" in response_data:
            TutorialError.require_condition(
                response_data["error"] == "authorization_pending",
                f"Failed to fetch a token with device_code {device_code_data.device_code}",
            )
            logger.debug(f"Didn't get a token yet. Trying again in {device_code_data.interval} seconds")
            sleep(device_code_data.interval)
        else:
            with TutorialError.handle_errors("Couldn't extract token from response"):
                access_token = response_data["access_token"]
            logger.debug(f"Received access token {access_token[:32]}...")
            cache.store_text(access_token, "auth/access.token")
            break
    terminal_message("Successfully logged in!", subject="Login successful")
