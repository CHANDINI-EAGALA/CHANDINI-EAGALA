import os
import requests
from bs4 import BeautifulSoup
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import QueryParser

# Define a schema for the Whoosh index
schema = Schema(title=TEXT(stored=True), content=TEXT, path=ID(stored=True))

def fetch_html_data(url, headers):
    """
    Fetch HTML data from a GitHub repository's issues or PR page.
    """
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching {url}: {response.text}")
        return None
    return response.text

def parse_issues_html(html_content):
    """
    Parse the HTML content to extract issue titles, bodies, and URLs.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    issues = []
    
    # Find all issue elements (simplified for example purposes)
    for issue_item in soup.find_all('div', class_='js-issue-row'):
        title_tag = issue_item.find('a', class_='h4')
        title = title_tag.text.strip() if title_tag else 'No Title'
        url = "https://github.com" + title_tag['href'] if title_tag else 'No URL'
        body = issue_item.find('p').text.strip() if issue_item.find('p') else 'No Content'
        
        issues.append({'title': title, 'body': body, 'url': url})
    
    return issues

def parse_prs_html(html_content):
    """
    Parse the HTML content to extract PR titles, bodies, and URLs.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    prs = []
    
    # Find all PR elements (simplified for example purposes)
    for pr_item in soup.find_all('div', class_='js-issue-row'):
        title_tag = pr_item.find('a', class_='h4')
        title = title_tag.text.strip() if title_tag else 'No Title'
        url = "https://github.com" + title_tag['href'] if title_tag else 'No URL'
        body = pr_item.find('p').text.strip() if pr_item.find('p') else 'No Content'
        
        prs.append({'title': title, 'body': body, 'url': url})
    
    return prs

def create_index(index_dir="indexdir"):
    """
    Create a Whoosh index to store repository data.
    """
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)
    return create_in(index_dir, schema)

def index_repository(issues_url, prs_url, headers, index_writer):
    """
    Index the issues and PRs from a repository.
    """
    # Fetch and parse issues HTML
    issues_html = fetch_html_data(issues_url, headers)
    if issues_html:
        issues = parse_issues_html(issues_html)
        for issue in issues:
            index_writer.add_document(
                title=issue['title'], content=issue['body'], path=issue['url']
            )
    
    # Fetch and parse PRs HTML
    prs_html = fetch_html_data(prs_url, headers)
    if prs_html:
        prs = parse_prs_html(prs_html)
        for pr in prs:
            index_writer.add_document(
                title=pr['title'], content=pr['body'], path=pr['url']
            )

def search_index(query_string, index_dir="indexdir"):
    """
    Search the Whoosh index for a query string.
    """
    from whoosh.index import open_dir
    ix = open_dir(index_dir)
    with ix.searcher() as searcher:
        query = QueryParser("content", ix.schema).parse(query_string)
        results = searcher.search(query)
        for result in results:
            print(f"Title: {result['title']}, URL: {result['path']}")

# Example usage
if __name__ == "__main__":
    # GitHub headers with authentication
    headers = {
        "Authorization": "Bearer ghp_YOUR_PERSONAL_ACCESS_TOKEN",  # Replace with your token
        "Accept": "text/html"  # Indicating we want HTML responses
    }
    
    # URLs for issues and pull requests (replace with the desired repository URLs)
    issues_url = "https://github.com/langchain-ai/langchain/issues"
    prs_url = "https://github.com/langchain-ai/langchain/pulls"
    
    # Create Whoosh index
    ix = create_index()

    # Index issues and PRs
    with ix.writer() as writer:
        print(f"Indexing issues and PRs from {issues_url} and {prs_url}")
        index_repository(issues_url, prs_url, headers, writer)

    # Search the index
    query = "bug fix"
    print(f"Searching for: {query}")
    search_index(query)
