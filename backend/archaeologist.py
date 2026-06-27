from google import genai
from config import Config
from github_client import GitHubClient
import time

class CodeArchaeologist:
    def __init__(self):
        self.gemini_available = False
        if Config.GEMINI_API_KEY and Config.GEMINI_API_KEY != '':
            try:
                self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
                
                models_to_try = [
                    'gemini-1.5-flash',
                    'gemini-1.5-pro',
                    'gemini-2.0-flash-lite',
                    'gemini-2.0-flash'
                ]
                
                for model_name in models_to_try:
                    try:
                        test_response = self.client.models.generate_content(
                            model=model_name,
                            contents="test"
                        )
                        self.model = model_name
                        self.gemini_available = True
                        print(f"Gemini initialized with model: {model_name}")
                        break
                    except Exception as e:
                        if '429' in str(e):
                            print(f"Model {model_name} quota exhausted, trying next...")
                        else:
                            print(f"Model {model_name} failed: {e}")
                        continue
                
                if not self.gemini_available:
                    print("No Gemini models with available quota found.")
                    
            except Exception as e:
                print(f"Gemini client initialization failed: {e}")
        
        self.github = GitHubClient()
    
    def _call_with_retry(self, prompt, max_retries=3):
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                if '429' in str(e):
                    wait_time = (2 ** attempt) * 5
                    print(f"Rate limit hit, waiting {wait_time}s... (attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                else:
                    return f"Analysis failed: {str(e)}"
        
        return "Analysis failed: All retry attempts exhausted due to rate limits."
    
    def analyze_repository(self, repo_url):
        owner, repo = self.github.extract_repo_info(repo_url)
        
        metadata = self.github.get_repo_metadata(owner, repo)
        commits = self.github.get_commits(owner, repo)
        files = self.github.get_file_structure(owner, repo)
        
        commit_analysis = self._analyze_commits(commits)
        key_files = self._identify_key_files(files)
        decisions = self._reconstruct_decisions(key_files, commit_analysis, metadata)
        
        overall_analysis = self._generate_overall_analysis(metadata, decisions, commit_analysis)
        
        return {
            'metadata': metadata,
            'decisions': decisions,
            'commit_analysis': commit_analysis,
            'overall_analysis': overall_analysis,
            'key_files': key_files
        }
    
    def _analyze_commits(self, commits):
        intent_patterns = []
        if not commits:
            return intent_patterns
            
        for commit in commits[:20]:
            try:
                message = commit.get('commit', {}).get('message', 'No message')
                author = commit.get('commit', {}).get('author', {}).get('name', 'Unknown')
                intent = self._classify_commit_intent(message)
                
                sha = commit.get('sha', 'N/A')
                if sha and sha != 'N/A':
                    sha = str(sha)[:8]
                
                intent_patterns.append({
                    'sha': sha,
                    'message': message[:100],
                    'author': author,
                    'intent': intent
                })
            except Exception:
                continue
                
        return intent_patterns
    
    def _classify_commit_intent(self, message):
        if not message:
            return 'maintenance'
            
        lower = message.lower()
        if any(word in lower for word in ['fix', 'bug', 'issue']):
            return 'bug_fix'
        elif any(word in lower for word in ['add', 'feature', 'feat']):
            return 'new_feature'
        elif any(word in lower for word in ['refactor', 'clean', 'optimize']):
            return 'refactor'
        elif any(word in lower for word in ['test', 'spec', 'unit']):
            return 'testing'
        elif any(word in lower for word in ['docs', 'documentation', 'readme']):
            return 'docs'
        else:
            return 'maintenance'
    
    def _identify_key_files(self, files):
        key_files = []
        if not files:
            return key_files
            
        for file in files:
            try:
                name = file.get('name', '').lower()
                if any(pattern in name for pattern in 
                       ['main', 'app', 'server', 'controller', 'service', 'auth', 'config', 'route', 'index']):
                    key_files.append(file)
            except Exception:
                continue
                
        return key_files[:5]
    
    def _reconstruct_decisions(self, key_files, commit_analysis, metadata):
        decisions = []
        
        for file in key_files:
            try:
                file_name = file.get('name', 'Unknown')
                file_path = file.get('path', '')
                file_type = file.get('type', 'file')
                file_size = file.get('size', 0)
                
                related_commits = []
                for commit in commit_analysis:
                    if file_name.lower() in commit.get('message', '').lower():
                        related_commits.append(commit)
                
                if self.gemini_available:
                    analysis = self._ask_ai_about_file(file_name, file_path, related_commits, metadata)
                else:
                    analysis = "AI analysis unavailable. Please check your GEMINI_API_KEY in .env file."
                
                decisions.append({
                    'file': file_name,
                    'path': file_path,
                    'type': file_type,
                    'size': file_size,
                    'analysis': analysis,
                    'confidence': 'High' if related_commits else 'Medium',
                    'related_commits': len(related_commits)
                })
            except Exception as e:
                decisions.append({
                    'file': file_name if 'file_name' in locals() else 'Unknown',
                    'path': file_path if 'file_path' in locals() else 'Unknown',
                    'analysis': f"Error: {str(e)}",
                    'confidence': 'Low',
                    'related_commits': 0
                })
                continue
                
        return decisions
    
    def _generate_overall_analysis(self, metadata, decisions, commit_analysis):
        if not self.gemini_available:
            return "AI analysis unavailable. Please check your GEMINI_API_KEY in .env file."
        
        try:
            repo_name = metadata.get('name', 'Unknown')
            description = metadata.get('description', 'No description')
            language = metadata.get('language', 'Unknown')
            stars = metadata.get('stargazers_count', 0)
            forks = metadata.get('forks_count', 0)
            
            commit_summary = ""
            for commit in commit_analysis[:10]:
                commit_summary += f"- {commit.get('message')} ({commit.get('intent')})\n"
            
            file_summary = ""
            for decision in decisions[:3]:
                file_summary += f"- {decision.get('file')}\n"
            
            prompt = f"""
            You are a senior software engineer analyzing a repository. Provide a comprehensive analysis.

            Repository: {repo_name}
            Description: {description}
            Primary Language: {language}
            Stars: {stars}
            Forks: {forks}

            Recent Commits:
            {commit_summary}

            Key Files:
            {file_summary}

            Please provide a structured analysis covering:

            1. Purpose: What problem does this repository solve?
            2. Architecture: What architectural patterns are used?
            3. Code Quality: What patterns are evident in the code?
            4. Technical Decisions: What key technical choices were made?
            5. Recommendations: What improvements could be made?

            Keep it concise, professional, and technical.
            """
            
            return self._call_with_retry(prompt)
        except Exception as e:
            return f"Overall analysis failed: {str(e)}"
    
    def _ask_ai_about_file(self, file_name, file_path, commit_history, metadata):
        try:
            commit_summary = ""
            for commit in commit_history[:5]:
                commit_summary += f"- {commit.get('message')} (by {commit.get('author')})\n"
            
            if not commit_summary:
                commit_summary = "No direct commit history found for this file."
            
            prompt = f"""
            You are analyzing a code file to understand WHY it exists and what decisions led to it.
            
            Repository: {metadata.get('name', 'Unknown')}
            File: {file_name}
            Path: {file_path}
            Related commit history:
            {commit_summary}
            
            Provide a detailed analysis covering:
            
            1. Purpose: What problem does this file solve?
            2. Architecture: What role does it play in the overall system?
            3. Decision Context: Why was this approach chosen?
            4. Trade-offs: What alternatives were likely considered?
            5. Dependencies: What does this file depend on?
            
            Keep it concise, professional, and technical.
            """
            
            return self._call_with_retry(prompt)
        except Exception as e:
            return f"Analysis failed: {str(e)}"