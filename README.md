# Repository Insight Engine

Uncovering engineering decisions and historical context from GitHub repositories.

---

## Overview

Repository Insight Engine is a tool that analyzes GitHub repositories to reconstruct the engineering decisions, architectural context, and historical reasoning behind code changes. It addresses the common challenge of understanding why code was written in a particular way, particularly in long-lived projects where original context has been lost.

The tool combines GitHub API data with Google Gemini AI to generate comprehensive insights about repository structure, decision-making patterns, and code evolution.

---

## Features

- **Repository Analysis** – Fetches metadata, commit history, and file structure from GitHub repositories.
- **AI-Powered Decision Reconstruction** – Uses Google Gemini AI to explain why files exist and what problems they solve.
- **Overall Repository Analysis** – Provides comprehensive insights into architecture, code quality, and technical decisions.
- **PDF Report Generation** – Creates structured PDF documents of analysis results for sharing and documentation.
- **Documentation Center** – Manages multiple analyzed repositories with preview and download capabilities.
- **Professional User Interface** – Modern dark theme with responsive design for all screen sizes.

---

## Technical Architecture

| Component | Technology |
|-----------|------------|
| Backend Framework | Flask (Python) |
| AI Engine | Google Gemini 2.0 Flash |
| Data Source | GitHub REST API |
| Frontend | HTML5, CSS3, JavaScript |
| PDF Generation | html2pdf.js |
| Typography | Inter |

---

## Installation

### Prerequisites

- Python 3.9 or higher
- Google Gemini API key (free tier available)
- GitHub personal access token

### Setup Instructions

1. Clone the repository:

```bash
git clone https://github.com/yourusername/repository-insight-engine.git
cd repository-insight-engine
```

---

## Usage Guide

### Analyzing a Repository

1. Enter a GitHub repository URL in the search field on the Analyzer tab.
2. Click the Analyze button.
3. Review the generated insights, including:
   - Repository overview (metadata, stars, language)
   - AI-generated overall analysis
   - Reconstructed decisions for key files
   - Recent commit history with intent classification

### Generating PDF Reports

1. Navigate to the Documentation tab.
2. Select a previously analyzed repository from the list.
3. Click the Preview Document button to review the analysis.
4. Click the Download PDF button to generate and save the report.
