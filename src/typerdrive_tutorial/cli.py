from enum import StrEnum, auto

import httpx
import typer
from typerdrive import terminal_message


class Endpoint(StrEnum):
    unsecured = auto()
    secured = auto()


app = typer.Typer()


@app.command()
def access(endpoint: Endpoint):
    response = httpx.get(f"http://localhost:8000/{endpoint}")
    response.raise_for_status()
    message = response.json()["message"]
    terminal_message(
        message,
        subject="Successfully connected to API",
        footer=f"Status Code: {response.status_code}",
    )


@app.command()
def login():
    terminal_message("Processing login command")
