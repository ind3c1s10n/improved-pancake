# baby's first web crawler
# getting hands on experience with building a web crawler
# my silly plan is to start small and widen my scope as i figure out what i'm doing
# not sure what to do yet after that
# i'm using chatgpt for help because i have no idea what i'm doing wheee

import requests # handles html requests
from bs4 import BeautifulSoup # soup for parsing html
from urllib.parse import urljoin # construct absolute url
from urllib.robotparser import RobotFileParser
from io import BytesIO
import gzip
import logging 
import json 
import os

# user-agent header defined globally
HEADERS = {"User-Agent": "BabyCrawlerBot/1.0"}
class JSONLogHandler(logging.Handler):
    def __init__(self, filename, log_dir="logs"):
        super().__init__()
        self.log_dir = log_dir
        self.filename = filename

        # Ensure the log directory exists
        os.makedirs(self.log_dir, exist_ok=True)

        # Combine directory and filename to create the full file path
        self.filepath = os.path.join(self.log_dir, self.filename)

    def emit(self, record):
        # Ensure the formatter is set and use it to format the timestamp
        if self.formatter:
            timestamp = self.formatter.formatTime(record, datefmt="%Y-%m-%d %H:%M:%S")
        else:
            # Fallback in case no formatter is set
            timestamp = record.created

        # Convert log record to dictionary
        log_entry = {
            "timestamp": timestamp,
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
            "function": record.funcName,
        }

        # Serialize as JSON and write to the file
        with open(self.filepath, "a") as file:
            file.write(json.dumps(log_entry) + "\n")


# Configure logging to use the custom JSON handler
json_handler = JSONLogHandler("crawler_logs.json")
formatter = logging.Formatter("%(asctime)s")  # Format the timestamp
json_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[json_handler]
)

# def allowedToCrawl(url, user_agent):
#     # Parse robots.txt
#     parsed_url = requests.utils.urlparse(url)
#     base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
#     rp = RobotFileParser()

#     try:
#         response = requests.get(base_url, headers=HEADERS, timeout=10)
#         logging.warning(f"Response headers for {base_url}: {response.headers}")  # Diagnostic output

#         # Check if response is valid and not a redirect
#         if response.status_code != 200:
#             logging.warning(f"Error: Non-200 status code ({response.status_code}) for {base_url}")
#             return False

#         # Check for valid robots.txt content
#         if 'text/plain' in response.headers.get("Content-Type", ""):
#             # If not GZIP, parse normally
#             rp.parse(response.text.splitlines())
#         elif response.headers.get("Content-Encoding") == "gzip":
#             # If GZIP, decompress and parse
#             try:
#                 decompressed_content = gzip.GzipFile(fileobj=BytesIO(response.content)).read()
#                 rp.parse(decompressed_content.decode("utf-8").splitlines())
#             except OSError as e:
#                 logging.warning(f"Error decompressing robots.txt from {base_url}: {e}")
#                 return False
#         else:
#             logging.warning(f"Unexpected content type for robots.txt from {base_url}: {response.headers.get('Content-Type')}")
#             return False

#     except UnicodeDecodeError as e:
#         logging.warning(f"Error decoding robots.txt from {base_url}: {e}")
#         return False
#     except Exception as e:
#         logging.warning(f"Error fetching robots.txt from {base_url}: {e}")
#         return False

#     # Use can_fetch() method to check if the user-agent is allowed to crawl
#     if rp.can_fetch(user_agent, url):
#         logging.warning(f"robots say yes to crawling {url}")
#         return True
#     else:
#         logging.warning(f"robots say no to crawling {url}")
#         return False

def allowedToCrawl(url, user_agent):
    # Parse robots.txt
    parsed_url = requests.utils.urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    rp = RobotFileParser()

    try:
        response = requests.get(base_url, headers=HEADERS, timeout=10)
        logging.info(f"Attempting to fetch robots.txt from {base_url}.")

        if response.status_code == 404:
            logging.info(f"No robots.txt found at {base_url}. Assuming no restrictions.")
            return True  # Treat absence of robots.txt as no restrictions

        elif response.status_code == 200:
            if 'text/plain' in response.headers.get("Content-Type", ""):
                rp.parse(response.text.splitlines())
                return rp.can_fetch(user_agent, url)
            else:
                logging.warning(f"Unexpected content type for robots.txt: {response.headers.get('Content-Type')}")
                return False

        else:
            logging.warning(f"Error fetching robots.txt (status code: {response.status_code}) from {base_url}")
            return False

    except Exception as e:
        logging.error(f"Error fetching robots.txt from {base_url}: {e}")
        return False

# def babyCrawler(start_url, max_pages, visited=None):
#     if visited is None:
#         visited = set()
#     to_visit = [start_url]

#     # get domain for the starting url to restrict crawling outside of the domain
#     parsed_start_url = requests.utils.urlparse(start_url)
#     base_domain = parsed_start_url.netloc

#     while to_visit and len(visited) < max_pages:
#         url = to_visit.pop(0)
#         if url in visited:
#             continue

#         # check robots.txt before crawling
#         if not allowedToCrawl(url, HEADERS["User-Agent"]):
#             logging.warning(f"robots say to skip {url}")
#             continue

#         try:
#             response = requests.get(url, headers=HEADERS)  
#             if response.status_code != 200:
#                 continue

#             visited.add(url)
#             logging.warning(f"currently crawling: {url}")

#             # soup = BeautifulSoup(response.text, 'html.parser')
#             # for link in soup.find_all('a', href=True):
#             #     full_url = urljoin(url, link['href'])
#             #     if full_url not in visited:
#             #         to_visit.append(full_url)
#             soup = BeautifulSoup(response.text, 'html.parser')
#             for link in soup.find_all('a', href=True):
#                 full_url = urljoin(url, link['href'])  # Construct absolute URL
#                 parsed_full_url = requests.utils.urlparse(full_url)

#                 # Check if the link belongs to the same domain
#                 if parsed_full_url.netloc == base_domain and full_url not in visited:
#                     to_visit.append(full_url)
#                 else:
#                     logging.warning(f"skipped external link {full_url}")
#         except Exception as e:
#             with open("errors.log", "a") as log:
#                 log.write(f"error crawling {url}: {e}\n")

def babyCrawler(start_url, max_pages, visited=None):
    if visited is None:
        visited = set()
    to_visit = [start_url]

    # Get domain for the starting URL
    parsed_start_url = requests.utils.urlparse(start_url)
    base_domain = parsed_start_url.netloc

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue

        # Check robots.txt before crawling
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
                parsed_full_url = requests.utils.urlparse(full_url)

                # Debug logs for domain check
                logging.info(f"Parsed link: {full_url}")
                logging.info(f"Link netloc: {parsed_full_url.netloc}, Base domain: {base_domain}")

                if parsed_full_url.netloc == base_domain and full_url not in visited:
                    logging.info(f"Adding internal link to queue: {full_url}")
                    to_visit.append(full_url)
                else:
                    logging.warning(f"Skipped external link {full_url}")

        except Exception as e:
            with open("errors.log", "a") as log:
                log.write(f"error crawling {url}: {e}\n")


        else:
            logging.warning(f"skipped external link {full_url}")

    return visited

seed_urls = [
   "http://books.toscrape.com/"
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