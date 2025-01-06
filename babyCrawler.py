# baby's first web crawler
# getting hands on experience with building a web crawler
# my silly plan is to start small and widen my scope as i figure out what i'm doing
# gonna feed the crawler the homepages for the top x amount of ai commpanies in the states and send it down a link-clicking rabbit hole.
# not sure what to do yet after that
# i'm using chatgpt for help because i have no idea what i'm doing wheee

import requests # handles html requests
from bs4 import BeautifulSoup # soup for parsing html
from urllib.parse import urljoin # construct absolute url
from urllib.robotparser import RobotFileParser
from io import BytesIO
import gzip
import logging 

# user-agent header defined globally
HEADERS = {"User-Agent": "BabyCrawlerBot/1.0"}

logging.basicConfig(
    level=logging.WARNING, # INFO shows levels INFO, WARNING, ERROR, and CRITICAL. DEBUG will be ignored
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
    logging.FileHandler("crawler.log", mode='w'), # log is overwritten each run
    #logging.StreamHandler(), #StreamHandler disabled to stop output in terminal - it's gonna look like it hangs, it's aight
    ]
)

def allowedToCrawl(url, user_agent):
    # Parse robots.txt
    parsed_url = requests.utils.urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    rp = RobotFileParser()

    try:
        response = requests.get(base_url, headers=HEADERS, timeout=10)
        logging.warning(f"Response headers for {base_url}: {response.headers}")  # Diagnostic output

        # Check if response is valid and not a redirect
        if response.status_code != 200:
            logging.warning(f"Error: Non-200 status code ({response.status_code}) for {base_url}")
            return False

        # Check for valid robots.txt content
        if 'text/plain' in response.headers.get("Content-Type", ""):
            # If not GZIP, parse normally
            rp.parse(response.text.splitlines())
        elif response.headers.get("Content-Encoding") == "gzip":
            # If GZIP, decompress and parse
            try:
                decompressed_content = gzip.GzipFile(fileobj=BytesIO(response.content)).read()
                rp.parse(decompressed_content.decode("utf-8").splitlines())
            except OSError as e:
                logging.warning(f"Error decompressing robots.txt from {base_url}: {e}")
                return False
        else:
            logging.warning(f"Unexpected content type for robots.txt from {base_url}: {response.headers.get('Content-Type')}")
            return False

    except UnicodeDecodeError as e:
        logging.warning(f"Error decoding robots.txt from {base_url}: {e}")
        return False
    except Exception as e:
        logging.warning(f"Error fetching robots.txt from {base_url}: {e}")
        return False

    # Use can_fetch() method to check if the user-agent is allowed to crawl
    if rp.can_fetch(user_agent, url):
        logging.warning(f"robots say yes to crawling {url}")
        return True
    else:
        logging.warning(f"robots say no to crawling {url}")
        return False

def babyCrawler(start_url, max_pages, visited=None):
    if visited is None:
        visited = set()
    to_visit = [start_url]

    # get domain for the starting url to restrict crawling outside of the domain
    parsed_start_url = requests.utils.urlparse(start_url)
    base_domain = parsed_start_url.netloc

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue

        # check robots.txt before crawling
        if not allowedToCrawl(url, HEADERS["User-Agent"]):
            logging.warning(f"robots say to skip {url}")
            continue

        try:
            response = requests.get(url, headers=HEADERS)  
            if response.status_code != 200:
                continue

            visited.add(url)
            logging.warning(f"currently crawling: {url}")

            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                full_url = urljoin(url, link['href'])
                if full_url not in visited:
                    to_visit.append(full_url)
        except Exception as e:
            with open("errors.log", "a") as log:
                log.write(f"error crawling {url}: {e}\n")

        else:
            logging.warning(f"skipped external link {full_url}")

    return visited

seed_urls = [
    #"https://www.openai.com",
    "https://www.anthropic.com/"
    #"https://deepmind.google/"
]
# crawl all seed urls
visited_pages = set()
for url in seed_urls:
    logging.warning(f"seed url: {url}")
    visited_pages = babyCrawler(url,max_pages=50, visited=visited_pages)
    logging.warning(f"crawled {len(visited_pages)} unique pages so far")

# Write all visited URLs to a text file
with open("visitedpages.txt", "w") as file:  # Open file in write mode
    for url in visited_pages:  # Iterate through the set of visited URLs
        file.write(f"{url}\n")  # Write each URL on a new line