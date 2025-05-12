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
    terminal_message,
)


class DemoError(TyperdriveError):
    pass


class Settings(BaseModel):
    api_url: str
    auth_url: str
    client_id: str
    audience: str


class LoginRequestData(BaseModel):
    client_id: str
    grant_type: str
    audience: str


class TokenRequestData(BaseModel):
    grant_type: str
    device_code: str
    client_id: str


class DeviceCodeData(BaseModel):
    device_code: str
    verification_uri_complete: str
    interval: int


class APIResponseData(BaseModel):
    message: str


class Endpoint(StrEnum):
    unsecured = auto()
    secured = auto()


app = typer.Typer()
add_cache_subcommand(app)
add_logs_subcommand(app)
add_settings_subcommand(app, Settings)


@app.command()
@handle_errors("Couldn't access API")
@attach_logging()
@attach_cache()
@attach_settings(Settings)
@attach_client(api="api_url")
def access(
    ctx: typer.Context,  # pyright: ignore[reportUnusedParameter]
    api: TyperdriveClient,
    cache_manager: CacheManager,
    endpoint: Endpoint,
):
    logger.debug(f"Attempting to access api {endpoint=}")
    headers = {}
    if endpoint == Endpoint.secured:
        logger.debug("Loading access token from cache")
        access_token: str = cache_manager.load_text("auth/access.token")
        headers = {"Authorization": f"Bearer {access_token}"}
    response = cast(
        APIResponseData,
        api.get_x(
            endpoint,
            expected_status=200,
            response_model=APIResponseData,
            headers=headers,
        ),
    )
    terminal_message(f"API response message: {response.message}", subject="Successfully connected to API")


@app.command()
@handle_errors("Login failed")
@attach_logging()
@attach_settings(Settings)
@attach_cache()
@attach_client(auth="auth_url")
def login(ctx: typer.Context, settings: Settings, auth: TyperdriveClient, cache_manager: CacheManager):  # pyright: ignore[reportUnusedParameter]
    logger.debug("Starting login process")
    logger.debug("Requesting device code from auth provider")
    device_code_data = cast(
        DeviceCodeData,
        auth.post_x(
            "/oauth/device/code",
            expected_status=200,
            body_obj=LoginRequestData(
                client_id=settings.client_id,
                grant_type="client_credentials",
                audience=settings.audience,
            ),
            response_model=DeviceCodeData,
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
                body_obj=TokenRequestData(
                    grant_type="urn:ietf:params:oauth:grant-type:device_code",
                    device_code=device_code_data.device_code,
                    client_id=settings.client_id,
                ),
            ),
        )
        if "error" in response_data:
            DemoError.require_condition(
                response_data["error"] == "authorization_pending",
                f"Failed to fetch a token with device_code {device_code_data.device_code}",
            )
            logger.debug(f"Didn't get a token yet. Trying again in {device_code_data.interval} seconds")
            sleep(device_code_data.interval)
        else:
            with DemoError.handle_errors("Couldn't extract token from response"):
                access_token = response_data["access_token"]
            logger.debug(f"Received access token {access_token[:32]}...")

            cache_manager.store_text(access_token, "auth/access.token")
            break
    terminal_message("Successfully logged in!", subject="Login successful")
