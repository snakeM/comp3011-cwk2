import typer
import requests
from crawler import crawl
from utils import load_json
from rich import print
from rich.table import Table
from rich import box

app = typer.Typer()

INDEX_PATH = "./inverse_index.json"
PAGES_PATH = "./pages.json"


# Implementation of PageRank algorithm
def page_rank(pages):
    # Damping factor to account for randomness in browsing links
    # This value can be: increased to make browsing more structured
    #                  : decreased to make browsing more random
    DAMPING_FACTOR = 0.85
    # Threshold ensures that the algorithm terminates efficiently
    CONVERGENCE_THRESHOLD = 0.000001

    page_count = len(pages)
    print(f"Total pages indexed: {page_count}")

    # Rank is initially evenly distributed between all pages
    ranks = {}
    for page in pages:
        ranks[page] = 1 / page_count

    # Previous ranks are compared against after each iteration to check for
    # convergence
    previous_ranks = {}
    converged = False
    iteration = 0

    print("Calculating global rank of each page.")

    # Iterate until all page ranks have converged
    while not converged:
        # Store the number of iterations performed
        iteration += 1
        # Calculate ranks for each page
        for key, page in pages.items():
            incoming_links = page["incoming"]
            new_rank = 1 - DAMPING_FACTOR
            for link in incoming_links:
                new_rank += DAMPING_FACTOR * ranks[link] / len(pages[link]["outgoing"])
            previous_ranks[key] = ranks[key]
            ranks[key] = new_rank

        converged = True
        # Check each pages' rank for convergence
        for page, rank in ranks.items():
            rank_diff = abs(rank - previous_ranks[page])
            # If at least one page rank has yet to converge, continue iterating
            if rank_diff > CONVERGENCE_THRESHOLD:
                converged = False
                break

    print(f"Ranking algorithm converged after {iteration} iterations.")

    # Normalise page ranks so they are between 0 and 1
    sum_ranks = 0
    for _, rank in ranks.items():
        sum_ranks += rank
    for key in ranks:
        ranks[key] = ranks[key] / sum_ranks


@app.command()
def build():
    crawl()


@app.command()
def load():
    index = load_json(INDEX_PATH)
    pages = load_json(PAGES_PATH)
    page_rank(pages)
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
