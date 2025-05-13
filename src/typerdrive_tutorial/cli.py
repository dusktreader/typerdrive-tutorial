from enum import StrEnum, auto
from typing import cast

import typer
from loguru import logger
from pydantic import BaseModel
from typerdrive import (
    TyperdriveClient,
    TyperdriveError,
    add_logs_subcommand,
    add_settings_subcommand,
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


app = typer.Typer()
add_logs_subcommand(app)
add_settings_subcommand(app, Settings)


@app.command()
@handle_errors("Failed to access the API", do_except=log_error)
@attach_logging()
@attach_settings(Settings)
@attach_client(api="api_url")
def access(ctx: typer.Context, endpoint: Endpoint, api: TyperdriveClient, settings: Settings):
    logger.debug(f"Attempting to access api {endpoint=} in {settings.env} environment")
    response = cast(
        APIResponse,
        api.get_x(
            endpoint,
            expected_status=200,
            response_model=APIResponse,
        ),
    )
    terminal_message(
        response.message,
        subject="Successfully connected to API",
    )

@app.command()
def login():
    terminal_message("Processing login command")
