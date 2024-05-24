import typer
from crawler import crawl, tokenize
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

    print(f"Page ranks converged after {iteration} iterations.")

    # Normalise page ranks so they are between 0 and 1
    sum_ranks = 0
    for _, rank in ranks.items():
        sum_ranks += rank
    for key in ranks:
        ranks[key] = ranks[key] / sum_ranks

    return ranks


def process_query(query_tokens, i_index, pages, page_ranks, output_pages):
    index_entries = {}
    priority_queue = {}
    uniqueness = {}
    for term in query_tokens.keys():
        if term not in i_index:
            print("No results found")
            return {}
        index_entries[term] = i_index[term]

    for term, links in index_entries.items():
        # The number of articles that this term appears in
        term_frequency = len(links)
        page_number = len(pages)
        uniqueness[term] = term_frequency / page_number
        # print(f"Uniqueness of term '{term}': {uniqueness[term]}")

    for page in pages:
        page_score = 0
        page_rank = page_ranks[page]
        page_completeness = 0
        for term, links in index_entries.items():
            # If the current page is featured in the index entry for the current term
            if page in links:
                page_completeness += 1
                term_occurrences = links[page]
                num_occurrences = len(term_occurrences)
                # print(f"{page} features term: {term} {num_occurrences} times.")
                page_word_count = pages[page]["tokens"]
                page_score += (num_occurrences / page_word_count) * uniqueness[term]
        # Heavily weight the score based on whether all terms which were
        # searched for are present
        page_score = page_score * page_rank * (page_completeness**2)
        if page_score > 0 and page_completeness == len(query_tokens):
            priority_queue[page] = page_score

    total_result_num = len(priority_queue)
    print(f"{total_result_num} results found.")
    sum_scores = 0
    for _, score in priority_queue.items():
        sum_scores += score
    for result in priority_queue:
        priority_queue[result] = priority_queue[result] / sum_scores

    # Sort the results in descending order
    sorted_priority_queue = dict(
        sorted(priority_queue.items(), key=lambda x: x[1], reverse=True)
    )

    return sorted_priority_queue


@app.command()
def build():
    crawl()


@app.command()
def load():
    index = load_json(INDEX_PATH)
    pages = load_json(PAGES_PATH)
    ranks = page_rank(pages)
    while True:
        command = typer.prompt("Enter a command (print, find, exit)")

        if command.startswith("print"):
            word = command.replace("print", "").strip()
            result = print_index(word, index)
            print(result)
        elif command.startswith("find"):
            query = command.replace("find", "").strip()
            tokens, _ = tokenize(query)
            results = process_query(tokens, index, pages, ranks, 4)
            print(print_search_results(query, results))
        elif command == "exit":
            break
        else:
            print("Invalid command")


def print_search_results(query, results):
    if len(results) == 0:
        return f"No results for found for query '{query}'."
    table = Table(
        title=f"Results found for [green]'{query}'[/green]:",
        title_justify="left",
        box=box.SIMPLE_HEAD,
    )

    table.add_column("Rank", justify="left")
    table.add_column("Page", justify="left", no_wrap=True)

    # Results are already ordered by their rank
    # This is a counter to number the rows
    row_count = 0
    for page in results.keys():
        row_count += 1
        if row_count == 1:
            table.add_row(str(row_count), page, style="bright_yellow")
        else:
            table.add_row(str(row_count), page, style="cyan")

    return table


def print_index(word, index):
    if word not in index:
        return f"No results for '{word}' found."
    entry = index[word]
    table = Table(
        title=f"Inverted index entry for word [grey]'{word}'[/grey]:",
        title_justify="left",
        box=box.SIMPLE_HEAD,
    )
    table.add_column("Page", justify="left", style="cyan", no_wrap=True)
    table.add_column("Count", justify="left", style="white")
    table.add_column("Location(s)", justify="left", style="yellow")

    for url, count in entry.items():
        table.add_row(url, str(len(count)), str(count))

    return table


def search(query):
    # Implement your search logic here
    print(f"Searching for: {query}")
    process_query()


@app.command()
def hello(name: str):
    print(f"Hello {name}!")


if __name__ == "__main__":
    app()
