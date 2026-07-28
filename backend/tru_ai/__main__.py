import typer

from tru_ai import __version__

app = typer.Typer()


@app.command()
def version():
    print(f"TRU-AI v{__version__}")


def main():
    app()


if __name__ == "__main__":
    main()
