from enum import StrEnum, auto

import httpx
import typer
from typerdrive import terminal_message, handle_errors, TyperdriveError


class Endpoint(StrEnum):
    unsecured = auto()
    secured = auto()


class TutorialError(TyperdriveError):
    pass


app = typer.Typer()


@app.command()
@handle_errors("Failed to access the API")
def access(endpoint: Endpoint):
    response = httpx.get(f"http://localhost:8000/{endpoint}")
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
