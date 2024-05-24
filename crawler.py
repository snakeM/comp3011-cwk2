import requests
from bs4 import BeautifulSoup
import time
from rich import print
from rich.table import Table
from rich.console import Console
import json
import nltk
from nltk.tokenize import wordpunct_tokenize
from nltk.corpus import stopwords
from datetime import datetime, timedelta


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
    num_tokens = len(all_tokens)
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
    return index, num_tokens


def update_index(index, tokens, url):
    print(f"Indexing page content.")
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
    pages = {ROOT_URL: {"visited": False, "content": "", "incoming": []}}
    pages_crawled = 0
    index = {}
    next_request_time = datetime.now()
    while len(urls) != 0:
        pages_crawled += 1
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

        tokens, tokens_count = tokenize(content)

        pages[current_url]["visited"] = True
        pages[current_url]["tokens"] = tokens_count
        index = update_index(index, tokens, current_url)

        # Find all link tags
        links = soup.select("a[href]")
        new_urls = []
        outgoing_urls = set({})

        # for link in links:
        #     url = link["href"]
        #     # Basic check for any external links
        #     if "http" in url:
        #         continue
        #     # Construct full url
        #     full_url = ROOT_URL + url
        #     outgoing_urls.add(full_url)
        # # Get list of URLs as a set
        # all_urls = set(urls)
        # all_urls.add(outgoing_urls)
        # # Find urls which have just been added
        # diff_urls = new_urls - all_urls

        for l in links:
            url = l["href"]
            # Basic check for any external links
            if "http" in url:
                continue
            # Construct full url
            full_url = ROOT_URL + url
            outgoing_urls.add(full_url)
            if full_url not in pages:
                urls.append(full_url)
                new_urls.append(full_url)
                pages[full_url] = {"visited": False, "incoming": [current_url]}
            else:
                existing_incoming = pages[full_url]["incoming"]
                new_incoming = set(existing_incoming)
                new_incoming.add(current_url)
                # print(f"Updating incoming links for {full_url}")
                pages[full_url]["incoming"] = list(new_incoming)
        pages[current_url]["outgoing"] = list(outgoing_urls)
        # Log a message if new links were found on a page
        if len(new_urls) > 0:
            print(f"{len(new_urls)} new pages discovered:")
            print("---")
            for link in new_urls:
                print(f"[green]+{link}[/green]")
            print("---")
        # Log the number of pages still left to scrape
        print(f"[bold]No. URLs remaining: {len(urls)}.[/bold]")
        print(f"[bold]No. pages indexed: {pages_crawled}.[/bold]")

        # Write the inverse index to local storage
        with open("inverse_index.json", "w") as fp:
            json.dump(index, fp)

        # Write pages to local storage
        with open("pages.json", "w") as fp:
            json.dump(pages, fp)

        # Find the time remaining before another request can be made
        sleep_time = (abs(datetime.now() - next_request_time)).total_seconds()

        with console.status(
            f"[italic]Observing politeness window before next request is made...",
            spinner="material",
        ) as status:
            time.sleep(sleep_time)
