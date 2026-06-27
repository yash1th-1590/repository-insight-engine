import requests
from config import Config

class GitHubClient:
    def __init__(self):
        self.token = Config.GITHUB_TOKEN
        self.base_url = Config.GITHUB_API_BASE
        self.headers = {}
        if self.token and self.token != 'N/A':
            self.headers = {'Authorization': f'token {self.token}'}
    
    def extract_repo_info(self, repo_url):
        parts = repo_url.rstrip('/').split('/')
        return parts[-2], parts[-1]
    
    def get_repo_metadata(self, owner, repo):
        url = f'{self.base_url}/repos/{owner}/{repo}'
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                return {'name': repo, 'stargazers_count': 0, 'language': 'Unknown', 'description': 'Error fetching data'}
        except Exception:
            return {'name': repo, 'stargazers_count': 0, 'language': 'Unknown', 'description': 'Error fetching data'}
    
    def get_commits(self, owner, repo, limit=20):
        url = f'{self.base_url}/repos/{owner}/{repo}/commits'
        try:
            response = requests.get(url, headers=self.headers, params={'per_page': limit})
            if response.status_code == 200:
                return response.json()
            else:
                return []
        except Exception:
            return []
    
    def get_file_content(self, owner, repo, path):
        url = f'{self.base_url}/repos/{owner}/{repo}/contents/{path}'
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                return {}
        except Exception:
            return {}
    
    def get_file_structure(self, owner, repo):
        url = f'{self.base_url}/repos/{owner}/{repo}/contents'
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                return []
        except Exception:
            return []