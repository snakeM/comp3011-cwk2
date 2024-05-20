import requests
from bs4 import BeautifulSoup
import time
from rich import print
from rich.spinner import Spinner
from rich.table import Table
from rich.console import Console
import json
import nltk
from nltk.tokenize import wordpunct_tokenize, WhitespaceTokenizer
from nltk.corpus import stopwords
from datetime import datetime, timedelta
import re

console = Console()

ROOT_URL = "https://quotes.toscrape.com"


def print_urls(urls):
    table = Table(title="Links")
    table.add_column("URL", justify="left", style="cyan", no_wrap=True)
    for u in urls:
        table.add_row(u)
    return table


def tokenize(content):
    # Convert content to lowercase
    content = content.lower()
    # Replace dashes found in compound words with spaces
    # content = re.sub(pattern=r"(?<=[a-z])-(?=[a-z])", repl=" ", string=content)
    # content = re.sub(pattern=r"(?<=[a-z])'(?=[a-z])", repl="", string=content)
    # [^\p{L} ] regexp for anything which isn't a letter (includes accented
    # chars like in André)
    all_tokens = wordpunct_tokenize(content)

    index = {}
    # punctuation_marks = {",", ".", "'", "-", ":", ";", "(", ")", "”", "“"}
    # all_stopwords = set(stopwords.words("english")).union(punctuation_marks)

    all_stopwords = set(stopwords.words("english"))
    for position, token in enumerate(all_tokens):
        # Discard the token if it is a stop word
        if token in all_stopwords:
            continue
        # Check if an entry for this token already exists
        if token in index:
            # Increment index entry for this token
            index[token].append(position)
        else:
            # Create a new index entry for this token
            index[token] = [position]
    return index


def update_index(index, tokens, url):
    print(f"Updating index with page contents.")
    output_index = index
    for token, token_entries in tokens.items():
        if token in output_index:
            index[token][url] = token_entries
        else:
            index[token] = {url: token_entries}
    return output_index


def crawl():
    nltk.download("stopwords")
    nltk.download("punkt")
    urls = [ROOT_URL]
    data = {ROOT_URL: {"visited": False, "content": ""}}
    index = {}
    next_request_time = datetime.now()
    while len(urls) != 0:
        # Remove this URL from the list of unvisited URLs
        current_url = urls.pop()
        console.rule(f"Crawling: {current_url}")
        print(f"Fetching content from: {current_url}")
        response = requests.get(current_url)
        # Find 6 seconds in the future from the time the last request was made
        next_request_time = datetime.now() + timedelta(seconds=6)

        soup = BeautifulSoup(response.content, "html.parser")
        elements = soup.find_all("div", class_=["quote", "author-details"])
        content = ""
        for e in elements:
            content += e.get_text().strip() + "\n"

        tokens = tokenize(content)

        data[current_url]["visited"] = True
        data[current_url]["content"] = tokens
        index = update_index(index, tokens, current_url)

        # Find all link tags
        links = soup.select("a[href]")
        new_urls = []

        for l in links:
            url = l["href"]
            # Basic check for any external links
            if "http" in url:
                continue
            # Construct full url
            full_url = ROOT_URL + url
            if full_url not in data:
                urls.append(full_url)
                new_urls.append(full_url)
                data[full_url] = {"visited": False}
        # Log a message if new links were found on a page
        if len(new_urls) > 0:
            print(f"{len(new_urls)} new pages discovered:")
            print("---")
            for link in new_urls:
                print(f"[green]+{link}[/green]")
            print("---")
        # Log the number of pages still left to scrape
        print(f"[bold]No. URLs remaining: {len(urls)}.[/bold]")

        # Write the inverse index to local storage
        with open("inverse_index.json", "w") as fp:
            json.dump(index, fp)

        # Find the time remaining before another request can be made
        sleep_time = (abs(datetime.now() - next_request_time)).total_seconds()
        with console.status(
            f"[italic]Observing politeness window. Waiting for {sleep_time:.2f} seconds[/italic]...",
            spinner="material",
        ) as status:
            status.start()
            time.sleep(sleep_time)
            status.stop()
