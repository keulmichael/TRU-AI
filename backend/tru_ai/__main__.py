import typer

app = typer.Typer()

@app.command()
def version():
    print("TRU-AI v0.8.5.1")

def main():
    app()

if __name__ == "__main__":
    main()