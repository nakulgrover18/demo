import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Replace with your GitHub personal access token
GITHUB_TOKEN = 'your_github_admin_token'

# GitHub API base URL
GITHUB_API_URL = 'https://api.github.com'

# Headers with the authentication token
headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.mercy-preview+json'  # Necessary to work with topics
}

def fetch_repos_page(org_name, topic, page):
    """
    Fetch a specific page of repositories that have a specific topic.
    """
    url = f'{GITHUB_API_URL}/search/repositories?q=org:{org_name}+topic:{topic}&page={page}&per_page=100'
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json().get('items', [])
    except requests.exceptions.RequestException as e:
        print(f'Error fetching page {page}: {e}')
        return []

def fetch_all_repos_concurrently(org_name, topic, total_pages):
    """
    Fetch all repository pages concurrently.
    """
    repos_with_topic = []
    with ThreadPoolExecutor(max_workers=20) as executor:  # Adjust max_workers for concurrency
        futures = {executor.submit(fetch_repos_page, org_name, topic, page): page for page in range(1, total_pages + 1)}

        for future in as_completed(futures):
            page_repos = future.result()
            repos_with_topic.extend(page_repos)
            print(f'Fetched page {futures[future]} with {len(page_repos)} repos.')

    return repos_with_topic

def add_topic_to_repo(repo_full_name, new_topic):
    """
    Add a new topic to a specific repository.
    """
    topics_url = f'{GITHUB_API_URL}/repos/{repo_full_name}/topics'

    try:
        response = requests.get(topics_url, headers=headers, timeout=10)
        response.raise_for_status()
        current_topics = response.json().get('names', [])

        if new_topic not in current_topics:
            current_topics.append(new_topic)

            update_response = requests.put(topics_url, headers=headers, json={'names': current_topics}, timeout=10)
            if update_response.status_code == 200:
                print(f'Successfully added topic "{new_topic}" to repo: {repo_full_name}')
            else:
                print(f'Failed to add topic "{new_topic}" to repo: {repo_full_name}, Status Code: {update_response.status_code}, Response: {update_response.text}')
        else:
            print(f'Topic "{new_topic}" already exists in repo: {repo_full_name}')
    except requests.exceptions.RequestException as e:
        print(f'Error updating topics for {repo_full_name}: {e}')

def main():
    # The organization name
    org_name = 'your_organization_name'

    # The topic to search for (input from the user)
    search_topic = input("Enter the topic name to search for: ").strip()

    # The new topic to add
    new_topic = 'legacy'

    # Estimate the total number of pages (based on 100 results per page)
    total_repos = 32000  # Total repos with the topic
    repos_per_page = 100
    total_pages = (total_repos // repos_per_page) + (1 if total_repos % repos_per_page != 0 else 0)

    # Fetch all repos with the specified topic concurrently
    repos = fetch_all_repos_concurrently(org_name, search_topic, total_pages)
    print(f'Repositories in organization "{org_name}" with topic "{search_topic}": {repos}')

    # Add the "legacy" topic to those repos
    for repo in repos:
        add_topic_to_repo(repo['full_name'], new_topic)

if __name__ == "__main__":
    main()
