import typer
import requests
from crawler import crawl
from utils import load_json
from rich import print
from rich.table import Table
from rich import box

app = typer.Typer()

INDEX_PATH = "./inverse_index.json"


@app.command()
def build():
    crawl()


@app.command()
def load():
    index = load_json(INDEX_PATH)
    while True:
        command = typer.prompt("Enter a command (print, find, exit)")

        if command.startswith("print"):
            word = command.replace("print", "").strip()
            result = print_index(word, index)
            print(result)
        elif command.startswith("find"):
            query = command.replace("find", "").strip()
            find_text(query)
        elif command == "exit":
            break
        else:
            print("Invalid command")


def print_index(word, index):
    if word not in index:
        return f"No results for '{word}' found."
    entry = index[word]
    table = Table(
        title=f"Inverted index entry for word [grey]'{word}'[/grey]:",
        title_justify="left",
        box=box.SIMPLE_HEAD,
    )
    table.add_column("URL", justify="left", style="cyan", no_wrap=True)
    table.add_column("Count", justify="left", style="yellow")

    for url, count in entry.items():
        table.add_row(url, str(count))

    return table


def find_text(query):
    # Implement your search logic here
    print(f"Searching for: {query}")


@app.command()
def hello(name: str):
    print(f"Hello {name}!")


if __name__ == "__main__":
    app()
