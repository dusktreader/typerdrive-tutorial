from enum import StrEnum, auto
from typing import cast

import typer
from loguru import logger
from pydantic import BaseModel
from typerdrive import (
    TyperdriveClient,
    TyperdriveError,
    add_logs_subcommand,
    attach_client,
    attach_logging,
    handle_errors,
    log_error,
    terminal_message,
)


class Endpoint(StrEnum):
    unsecured = auto()
    secured = auto()


class TutorialError(TyperdriveError):
    pass


class APIResponse(BaseModel):
    message: str


app = typer.Typer()
add_logs_subcommand(app)


@app.command()
@handle_errors("Failed to access the API", do_except=log_error)
@attach_logging()
@attach_client(api="http://localhost:8000")
def access(ctx: typer.Context, endpoint: Endpoint, api: TyperdriveClient):
    logger.debug(f"Attempting to access api {endpoint=}")
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
