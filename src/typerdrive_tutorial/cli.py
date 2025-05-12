import typer
from typerdrive import terminal_message


app = typer.Typer()


@app.command()
def access():
    terminal_message("Processing access command")


@app.command()
def login():
    terminal_message("Processing login command")
