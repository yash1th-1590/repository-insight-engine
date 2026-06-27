import os
from config import Config
from github_client import GitHubClient
import time
import requests
import json

class CodeArchaeologist:
    def __init__(self):
        self.gemini_available = False
        self.groq_available = False
        
        if Config.GEMINI_API_KEY and Config.GEMINI_API_KEY != '':
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=Config.GEMINI_API_KEY)
                
                models_to_try = [
                    'gemini-2.0-flash',
                    'gemini-2.0-flash-lite'
                ]
                
                for model_name in models_to_try:
                    try:
                        test_response = self.gemini_client.models.generate_content(
                            model=model_name,
                            contents="test"
                        )
                        self.gemini_model = model_name
                        self.gemini_available = True
                        print(f"Using Gemini model: {model_name}")
                        break
                    except Exception as e:
                        if '429' in str(e):
                            print(f"Gemini model {model_name} quota exhausted")
                        else:
                            print(f"Gemini model {model_name} failed: {e}")
                        continue
                
                if not self.gemini_available:
                    print("No Gemini models available. Falling back to Groq.")
                    
            except Exception as e:
                print(f"Gemini initialization failed: {e}")
        
        if not self.gemini_available and Config.GROQ_API_KEY and Config.GROQ_API_KEY != '':
            try:
                self.groq_api_key = Config.GROQ_API_KEY
                self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
                self.groq_headers = {
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                }
                self.groq_model = "llama-3.1-8b-instant"
                self.groq_available = True
                print(f"Using Groq model: {self.groq_model}")
            except Exception as e:
                print(f"Groq initialization failed: {e}")
        
        if not self.gemini_available and not self.groq_available:
            print("WARNING: No AI models available. Please check your API keys.")
        
        self.github = GitHubClient()
    
    def _call_gemini(self, prompt, max_retries=3):
        if not self.gemini_available:
            return None
        
        for attempt in range(max_retries):
            try:
                response = self.gemini_client.models.generate_content(
                    model=self.gemini_model,
                    contents=prompt
                )
                return response.text
            except Exception as e:
                if '429' in str(e):
                    wait_time = (2 ** attempt) * 5
                    print(f"Gemini rate limit, waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    return None
        
        return None
    
    def _call_groq(self, prompt, max_retries=3):
        if not self.groq_available:
            return None
        
        payload = {
            "model": self.groq_model,
            "messages": [
                {"role": "system", "content": "You are a senior software engineer analyzing code. Provide professional, technical analysis."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 800,
            "top_p": 0.95
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.groq_url, 
                    headers=self.groq_headers, 
                    json=payload, 
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    if content:
                        print(f"Groq response received (attempt {attempt+1})")
                        return content
                    return "Groq returned empty response."
                elif response.status_code == 429:
                    wait_time = (2 ** attempt) * 3
                    print(f"Groq rate limit, waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"Groq error: {response.status_code}")
                    print(f"Response: {response.text[:200]}")
                    return f"Groq API error: {response.status_code}"
            except requests.exceptions.Timeout:
                print(f"Groq timeout, retrying...")
                time.sleep(3)
            except Exception as e:
                print(f"Groq exception: {str(e)[:100]}")
                time.sleep(2)
        
        return None
    
    def _generate(self, prompt):
        result = self._call_gemini(prompt)
        if result:
            return result
        
        result = self._call_groq(prompt)
        if result:
            return result
        
        return "AI analysis unavailable. Please check your API keys or try again later."
    
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
                
                analysis = self._ask_ai_about_file(file_name, file_path, related_commits, metadata)
                
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
You are a senior software engineer analyzing a repository. Provide a comprehensive analysis with the following structure:

[Purpose]
What problem does this repository solve?

[Architecture]
What architectural patterns are used?

[Code Quality]
What patterns are evident in the code?

[Technical Decisions]
What key technical choices were made?

[Recommendations]
What improvements could be made?

Repository: {repo_name}
Description: {description}
Primary Language: {language}
Stars: {stars}
Forks: {forks}

Recent Commits:
{commit_summary}

Key Files:
{file_summary}

Provide a detailed, professional analysis. Use clear section headings.
"""
            
            return self._generate(prompt)
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
You are analyzing a code file. Provide a concise summary in 4-5 lines.

File: {file_name}
Path: {file_path}
Repository: {metadata.get('name', 'Unknown')}
Related commit history:
{commit_summary}

Provide a brief summary covering:
- What this file does
- Its role in the project
- Any important patterns or decisions

Keep it short, professional, and technical. Maximum 4-5 sentences. Do not use asterisks or markdown formatting.
"""
            
            return self._generate(prompt)
        except Exception as e:
            return f"Analysis failed: {str(e)}"