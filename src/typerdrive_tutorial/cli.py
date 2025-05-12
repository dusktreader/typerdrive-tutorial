from enum import StrEnum, auto

import httpx
import typer
from loguru import logger
from typerdrive import (
    TyperdriveError,
    add_logs_subcommand,
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


app = typer.Typer()
add_logs_subcommand(app)



@app.command()
@handle_errors("Failed to access the API", do_except=log_error)
@attach_logging()
def access(ctx: typer.Context, endpoint: Endpoint):
    logger.debug(f"Attempting to access api {endpoint=}")
    response = httpx.get(f"http://localhost:8000/{endpoint}")
    logger.debug(f"Got {response.status_code=}")
    TutorialError.require_condition(
        response.status_code == 200,
        f"Expected status code 200, but got {response.status_code}",
    )
    message = response.json()["message"]
    terminal_message(
        message,
        subject="Successfully connected to API",
        footer=f"Status Code: {response.status_code}",
    )

@app.command()
def login():
    terminal_message("Processing login command")
