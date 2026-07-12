let analyzedRepositories = [];
let currentPreviewIndex = -1;

function switchTab(tabName) {
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));
    
    const links = document.querySelectorAll('.nav-link');
    links.forEach(link => link.classList.remove('active'));
    
    document.getElementById(tabName + '-tab').classList.add('active');
    
    const activeLink = Array.from(links).find(link => 
        link.textContent.toLowerCase() === tabName
    );
    if (activeLink) {
        activeLink.classList.add('active');
    }
    
    if (tabName === 'documentation') {
        renderRepositoryList();
        document.getElementById('doc-preview-view').classList.add('hidden');
        document.getElementById('doc-list-view').classList.add('hidden');
        document.getElementById('doc-empty').classList.add('hidden');
        document.getElementById('pdf-loading').classList.add('hidden');
        
        if (analyzedRepositories.length === 0) {
            document.getElementById('doc-empty').classList.remove('hidden');
        } else {
            document.getElementById('doc-list-view').classList.remove('hidden');
        }
    }
}

async function analyzeRepo() {
    const input = document.getElementById('repoInput');
    const button = document.getElementById('analyzeBtn');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    
    const repoUrl = input.value.trim();
    if (!repoUrl) {
        alert('Please enter a GitHub repository URL');
        return;
    }
    
    button.disabled = true;
    button.innerHTML = 'Analyzing...';
    
    loading.classList.remove('hidden');
    results.classList.add('hidden');
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ repo: repoUrl })
        });
        
        const data = await response.json();
        
        if (data.error) {
            alert('Error: ' + data.error);
            return;
        }
        
        const repoName = data.metadata?.name || 'Unknown';
        
        const existingIndex = analyzedRepositories.findIndex(r => r.name === repoName);
        const analysisData = {
            name: repoName,
            url: repoUrl,
            data: data,
            timestamp: new Date().toLocaleString(),
            language: data.metadata?.language || 'N/A',
            stars: data.metadata?.stargazers_count || 0
        };
        
        if (existingIndex >= 0) {
            analyzedRepositories[existingIndex] = analysisData;
        } else {
            analyzedRepositories.push(analysisData);
        }
        
        renderResults(data);
        results.classList.remove('hidden');
        switchTab('analyzer');
        
    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        button.disabled = false;
        button.innerHTML = 'Analyze';
        loading.classList.add('hidden');
    }
}

function formatOverallAnalysis(text) {
    if (!text) return '';
    
    let formatted = text;
    
    formatted = formatted.replace(/^#+ /gm, '');
    
    formatted = formatted.replace(/\[([^\]]+)\]/g, '<h4 class="analysis-heading">$1</h4>');
    
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    formatted = formatted.replace(/^\* (.*)$/gm, '<li>$1</li>');
    formatted = formatted.replace(/^- (.*)$/gm, '<li>$1</li>');
    
    formatted = formatted.replace(/^(\d+)\. (.*)$/gm, '<li>$1. $2</li>');
    
    if (formatted.includes('<li>')) {
        formatted = formatted.replace(/<li>/g, '<ul class="analysis-list"><li>');
        formatted = formatted.replace(/<\/li>/g, '</li></ul>');
        formatted = formatted.replace(/<\/ul><ul>/g, '');
    }
    
    formatted = formatted.replace(/\n\n/g, '</p><p>');
    formatted = formatted.replace(/\n/g, ' ');
    
    if (!formatted.startsWith('<')) {
        formatted = '<p>' + formatted + '</p>';
    }
    
    return formatted;
}

function renderResults(data) {
    const metadata = data.metadata || {};
    
    let description = safeString(metadata.description, 'No description');
    if (description.length > 120) {
        description = description.substring(0, 120) + '...';
    }
    
    document.getElementById('metadata').innerHTML = `
        <h2>Repository Overview</h2>
        <div class="metadata-grid">
            <div class="metadata-item">
                <div class="label">Repository</div>
                <div class="value">${safeString(metadata.name, 'Unknown')}</div>
            </div>
            <div class="metadata-item">
                <div class="label">Stars</div>
                <div class="value">${metadata.stargazers_count || 0}</div>
            </div>
            <div class="metadata-item">
                <div class="label">Language</div>
                <div class="value">${safeString(metadata.language, 'N/A')}</div>
            </div>
            <div class="metadata-item">
                <div class="label">Description</div>
                <div class="value" style="font-size:14px;">${description}</div>
            </div>
        </div>
    `;
    
    const overallAnalysis = data.overall_analysis;
    const overallDiv = document.getElementById('overall-analysis');
    if (overallAnalysis) {
        overallDiv.classList.remove('hidden');
        overallDiv.innerHTML = `
            <h2>AI Overall Analysis</h2>
            <div class="overall-analysis-content">
                ${formatOverallAnalysis(overallAnalysis)}
            </div>
        `;
    } else {
        overallDiv.classList.add('hidden');
    }
    
    const decisions = data.decisions || [];
    let decisionsHtml = '';
    if (decisions.length > 0) {
        decisionsHtml = decisions.map(d => `
            <div class="decision-card">
                <h3>${safeString(d.file, 'Unknown file')}</h3>
                <div class="analysis">${safeString(d.analysis, 'No analysis available')}</div>
                <div class="confidence-badge">Confidence: ${safeString(d.confidence, 'Medium')} | Related Commits: ${d.related_commits || 0}</div>
            </div>
        `).join('');
    } else {
        decisionsHtml = '<p style="color:#8b949e;">No key decisions identified.</p>';
    }
    
    document.getElementById('decisions').innerHTML = `
        <h2>Reconstructed Decisions</h2>
        ${decisionsHtml}
    `;
    
    const commits = data.commit_analysis || [];
    let commitsHtml = '';
    
    if (commits.length > 0) {
        const commitsToShow = commits.slice(0, 10);
        commitsHtml = commitsToShow.map(c => {
            const sha = safeString(c.sha, 'N/A');
            const message = safeString(c.message, 'No message');
            const author = safeString(c.author, 'Unknown');
            const intent = safeString(c.intent, 'maintenance');
            
            return `
                <div class="commit-item">
                    <span class="commit-sha">${sha}</span>
                    <span class="commit-message">${message}</span>
                    <span class="commit-intent">${intent}</span>
                    <span class="commit-author">${author}</span>
                </div>
            `;
        }).join('');
    } else {
        commitsHtml = '<p style="color:#8b949e;">No commits analyzed.</p>';
    }
    
    document.getElementById('commits').innerHTML = `
        <h2>Recent Commits</h2>
        ${commitsHtml}
    `;
}

function renderRepositoryList() {
    const listDiv = document.getElementById('doc-list');
    
    let html = '<div class="repo-grid">';
    analyzedRepositories.forEach((repo, index) => {
        html += `
            <div class="repo-card" onclick="openPreview(${index})">
                <div class="repo-card-header">
                    <span class="repo-name">${safeString(repo.name, 'Unknown')}</span>
                    <span class="repo-status">Ready</span>
                </div>
                <div class="repo-card-body">
                    <div class="repo-meta">
                        <span>Language: ${safeString(repo.language, 'N/A')}</span>
                        <span>Stars: ${repo.stars || 0}</span>
                    </div>
                    <div class="repo-time">${repo.timestamp}</div>
                </div>
                <div class="repo-card-footer">
                    <span class="repo-url">${safeString(repo.url, '')}</span>
                </div>
                <div class="repo-card-action">
                    <button class="preview-btn-small" onclick="event.stopPropagation(); openPreview(${index})">
                        Preview Document
                    </button>
                </div>
            </div>
        `;
    });
    html += '</div>';
    listDiv.innerHTML = html;
}

function openPreview(index) {
    currentPreviewIndex = index;
    const repo = analyzedRepositories[index];
    
    document.getElementById('doc-list-view').classList.add('hidden');
    document.getElementById('doc-empty').classList.add('hidden');
    document.getElementById('doc-preview-view').classList.remove('hidden');
    document.getElementById('pdf-loading').classList.add('hidden');
    
    document.getElementById('preview-repo-name').textContent = repo.name;
    document.getElementById('preview-repo-url').textContent = repo.url;
    
    const contentDiv = document.getElementById('doc-content');
    contentDiv.innerHTML = generatePDFContent(repo.data, repo.url);
}

function closePreview() {
    document.getElementById('doc-preview-view').classList.add('hidden');
    document.getElementById('pdf-loading').classList.add('hidden');
    
    if (analyzedRepositories.length === 0) {
        document.getElementById('doc-empty').classList.remove('hidden');
    } else {
        document.getElementById('doc-list-view').classList.remove('hidden');
    }
}

function generatePDFContent(data, repoUrl) {
    const metadata = data.metadata || {};
    const decisions = data.decisions || [];
    const commits = data.commit_analysis || [];
    const overallAnalysis = data.overall_analysis || '';
    
    let decisionsHtml = '';
    if (decisions.length > 0) {
        decisionsHtml = decisions.map(d => `
            <div class="pdf-decision" style="margin-bottom:8px;padding:12px 16px;background:#f6f8fa;border-radius:6px;border-left:4px solid #d29922;">
                <div class="pdf-decision-title" style="font-size:15px;font-weight:600;color:#0d1117;margin-bottom:4px;">${safeString(d.file, 'Unknown file')}</div>
                <div class="pdf-decision-text" style="font-size:13px;line-height:1.5;color:#24292e;">${safeString(d.analysis, 'No analysis available')}</div>
                <div style="margin-top:4px;font-size:12px;color:#484f58;">Confidence: ${safeString(d.confidence, 'Medium')}</div>
            </div>
        `).join('');
    } else {
        decisionsHtml = '<p style="color:#484f58;margin:8px 0;">No key decisions identified.</p>';
    }
    
    let commitsHtml = '';
    if (commits.length > 0) {
        const commitsToShow = commits.slice(0, 15);
        commitsHtml = commitsToShow.map(c => `
            <div class="pdf-commit" style="display:flex;align-items:center;gap:12px;padding:6px 12px;border-bottom:1px solid #e6edf3;">
                <span class="pdf-commit-sha" style="font-family:'Courier New',monospace;font-size:12px;color:#58a6ff;font-weight:600;min-width:80px;">${safeString(c.sha, 'N/A')}</span>
                <span class="pdf-commit-message" style="flex:1;font-size:13px;color:#24292e;">${safeString(c.message, 'No message')}</span>
                <span class="pdf-commit-intent" style="font-size:11px;color:#484f58;background:#e6edf3;padding:2px 12px;border-radius:12px;">${safeString(c.intent, 'maintenance')}</span>
                <span class="pdf-commit-author" style="font-size:12px;color:#484f58;">${safeString(c.author, 'Unknown')}</span>
            </div>
        `).join('');
    } else {
        commitsHtml = '<p style="color:#484f58;margin:8px 0;">No commits analyzed.</p>';
    }
    
    let overallHtml = '';
    if (overallAnalysis) {
        let formatted = overallAnalysis;
        formatted = formatted.replace(/^#+ /gm, '');
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        formatted = formatted.replace(/\[([^\]]+)\]/g, '<strong>$1</strong>');
        formatted = formatted.replace(/^\* (.*)$/gm, '<li>$1</li>');
        formatted = formatted.replace(/^- (.*)$/gm, '<li>$1</li>');
        
        if (formatted.includes('<li>')) {
            formatted = formatted.replace(/<li>/g, '<ul style="margin:4px 0 8px 0;padding-left:20px;"><li>');
            formatted = formatted.replace(/<\/li>/g, '</li></ul>');
            formatted = formatted.replace(/<\/ul><ul>/g, '');
        }
        
        formatted = formatted.replace(/^(\d+)\. (.*)$/gm, '<li>$1. $2</li>');
        formatted = formatted.replace(/\n\n/g, '<br>');
        formatted = formatted.replace(/\n/g, ' ');
        
        overallHtml = `
            <div class="pdf-section" style="margin-top:12px;">
                <h2 class="pdf-section-title" style="font-size:16px;font-weight:600;color:#0d1117;margin-bottom:6px;padding-bottom:4px;border-bottom:1px solid #e6edf3;">Overall Analysis</h2>
                <div style="font-size:13px;line-height:1.5;color:#24292e;">
                    ${formatted}
                </div>
            </div>
        `;
    }
    
    return `
        <div class="pdf-document" style="font-family:'Inter','Segoe UI',sans-serif;color:#0d1117;background:white;padding:32px;max-width:900px;margin:0 auto;">
            <h1 style="font-size:24px;font-weight:700;color:#0d1117;margin-bottom:4px;">Repository Insight Engine Analysis Report</h1>
            <div style="font-size:14px;color:#484f58;margin-bottom:2px;">Repository: ${safeString(metadata.name, 'Unknown')}</div>
            <div style="font-size:14px;color:#484f58;margin-bottom:2px;">URL: ${repoUrl}</div>
            <div style="font-size:14px;color:#484f58;margin-bottom:16px;">Generated: ${new Date().toLocaleString()}</div>
            
            <div class="pdf-section" style="margin-top:12px;">
                <h2 class="pdf-section-title" style="font-size:16px;font-weight:600;color:#0d1117;margin-bottom:6px;padding-bottom:4px;border-bottom:1px solid #e6edf3;">Repository Overview</h2>
                <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;background:#f6f8fa;padding:12px;border-radius:6px;">
                    <div style="text-align:center;">
                        <div style="font-size:10px;text-transform:uppercase;color:#484f58;font-weight:500;letter-spacing:0.3px;">Repository</div>
                        <div style="font-size:14px;font-weight:600;color:#0d1117;margin-top:2px;">${safeString(metadata.name, 'Unknown')}</div>
                    </div>
                    <div style="text-align:center;">
                        <div style="font-size:10px;text-transform:uppercase;color:#484f58;font-weight:500;letter-spacing:0.3px;">Stars</div>
                        <div style="font-size:14px;font-weight:600;color:#0d1117;margin-top:2px;">${metadata.stargazers_count || 0}</div>
                    </div>
                    <div style="text-align:center;">
                        <div style="font-size:10px;text-transform:uppercase;color:#484f58;font-weight:500;letter-spacing:0.3px;">Language</div>
                        <div style="font-size:14px;font-weight:600;color:#0d1117;margin-top:2px;">${safeString(metadata.language, 'N/A')}</div>
                    </div>
                    <div style="text-align:center;">
                        <div style="font-size:10px;text-transform:uppercase;color:#484f58;font-weight:500;letter-spacing:0.3px;">Description</div>
                        <div style="font-size:13px;font-weight:600;color:#0d1117;margin-top:2px;">${safeString(metadata.description, 'No description')}</div>
                    </div>
                </div>
            </div>
            
            ${overallHtml}
            
            <div class="pdf-section" style="margin-top:12px;">
                <h2 class="pdf-section-title" style="font-size:16px;font-weight:600;color:#0d1117;margin-bottom:6px;padding-bottom:4px;border-bottom:1px solid #e6edf3;">Reconstructed Decisions</h2>
                ${decisionsHtml}
            </div>
            
            <div class="pdf-section" style="margin-top:12px;">
                <h2 class="pdf-section-title" style="font-size:16px;font-weight:600;color:#0d1117;margin-bottom:6px;padding-bottom:4px;border-bottom:1px solid #e6edf3;">Recent Commits</h2>
                ${commitsHtml}
            </div>
            
            <div class="pdf-section" style="margin-top:12px;">
                <h2 class="pdf-section-title" style="font-size:16px;font-weight:600;color:#0d1117;margin-bottom:6px;padding-bottom:4px;border-bottom:1px solid #e6edf3;">Analysis Summary</h2>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                    <div style="background:#f6f8fa;padding:10px 14px;border-radius:6px;">
                        <div style="font-size:11px;color:#484f58;">Total Commits</div>
                        <div style="font-size:15px;font-weight:600;color:#0d1117;">${commits.length}</div>
                    </div>
                    <div style="background:#f6f8fa;padding:10px 14px;border-radius:6px;">
                        <div style="font-size:11px;color:#484f58;">Key Files</div>
                        <div style="font-size:15px;font-weight:600;color:#0d1117;">${decisions.length}</div>
                    </div>
                    <div style="background:#f6f8fa;padding:10px 14px;border-radius:6px;">
                        <div style="font-size:11px;color:#484f58;">Primary Language</div>
                        <div style="font-size:15px;font-weight:600;color:#0d1117;">${safeString(metadata.language, 'N/A')}</div>
                    </div>
                    <div style="background:#f6f8fa;padding:10px 14px;border-radius:6px;">
                        <div style="font-size:11px;color:#484f58;">Analysis Date</div>
                        <div style="font-size:15px;font-weight:600;color:#0d1117;">${new Date().toLocaleDateString()}</div>
                    </div>
                </div>
            </div>
            
            <div style="margin-top:16px;padding-top:10px;border-top:1px solid #e6edf3;font-size:12px;color:#484f58;text-align:center;">
                Generated by Repository Insight Engine
            </div>
        </div>
    `;
}

function generatePDF() {
    if (currentPreviewIndex < 0 || currentPreviewIndex >= analyzedRepositories.length) {
        alert('No repository selected.');
        return;
    }
    
    const repo = analyzedRepositories[currentPreviewIndex];
    const loadingDiv = document.getElementById('pdf-loading');
    const previewView = document.getElementById('doc-preview-view');
    const downloadBtn = document.getElementById('downloadBtn');
    
    const pdfContent = document.getElementById('pdf-content');
    if (!pdfContent) {
        alert('Error: PDF content not found. Please try again.');
        return;
    }
    
    loadingDiv.classList.remove('hidden');
    previewView.style.opacity = '0.4';
    downloadBtn.disabled = true;
    downloadBtn.innerHTML = 'Generating...';
    
    const opt = {
        margin: [10, 10, 10, 10],
        filename: `repository-insight-engine-${repo.name || 'report'}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { 
            scale: 2,
            useCORS: true,
            letterRendering: true
        },
        jsPDF: { 
            unit: 'mm', 
            format: 'a4', 
            orientation: 'portrait' 
        }
    };
    
    setTimeout(function() {
        html2pdf()
            .set(opt)
            .from(pdfContent)
            .save()
            .then(function() {
                loadingDiv.classList.add('hidden');
                previewView.style.opacity = '1';
                downloadBtn.disabled = false;
                downloadBtn.innerHTML = 'Download PDF';
            })
            .catch(function(error) {
                console.error('PDF generation error:', error);
                alert('Error generating PDF: ' + error.message);
                loadingDiv.classList.add('hidden');
                previewView.style.opacity = '1';
                downloadBtn.disabled = false;
                downloadBtn.innerHTML = 'Download PDF';
            });
    }, 500);
}

function safeString(value, defaultValue) {
    if (value === undefined || value === null) {
        return defaultValue || '';
    }
    return String(value);
}

document.getElementById('repoInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        analyzeRepo();
    }
});

document.addEventListener('DOMContentLoaded', function() {
    console.log('Repository Insight Engine initialized');
});