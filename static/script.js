// UI Elements
const loadingOverlay = document.getElementById('loadingOverlay');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const uploadStatus = document.getElementById('uploadStatus');
const questionInput = document.getElementById('questionInput');
const answerDiv = document.getElementById('answer');
const sourcesDiv = document.getElementById('sources');

// File handling
fileInput.addEventListener('change', updateFileList);
fileInput.addEventListener('dragover', (e) => {
    e.preventDefault();
    e.stopPropagation();
});

fileInput.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
    const files = e.dataTransfer.files;
    fileInput.files = files;
    updateFileList();
});

function updateFileList() {
    fileList.innerHTML = '';
    const files = fileInput.files;
    
    for (let file of files) {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <span class="file-name">${file.name}</span>
            <small>(${formatFileSize(file.size)})</small>
        `;
        fileList.appendChild(fileItem);
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showLoading(message = 'Processing...') {
    loadingOverlay.style.display = 'flex';
    loadingOverlay.querySelector('.loading-text').textContent = message;
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
}

function showStatus(message, type) {
    uploadStatus.textContent = message;
    uploadStatus.className = type;
    uploadStatus.style.display = 'block';
    
    if (type !== 'error') {
        setTimeout(() => {
            uploadStatus.style.display = 'none';
        }, 5000);
    }
}

async function uploadFiles() {
    const files = fileInput.files;
    
    if (files.length === 0) {
        showStatus('Please select files to upload', 'error');
        return;
    }

    // Validate file types
    for (let file of files) {
        const extension = file.name.split('.').pop().toLowerCase();
        if (!['pdf', 'txt', 'doc', 'docx', 'md'].includes(extension)) {
            showStatus(`File type .${extension} is not supported. Please use PDF, TXT, DOC, DOCX, or MD files.`, 'error');
            return;
        }
    }

    showLoading('Processing files... This may take a few moments.');
    
    try {
        const formData = new FormData();
        for (let file of files) {
            formData.append('files', file);
        }

        // Set timeout to 2 minutes
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 120000);

        const response = await fetch('/upload', {
            method: 'POST',
            body: formData,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        const result = await response.json();
        
        if (response.ok) {
            showStatus(`Successfully processed ${files.length} files (${result.chunks_created} chunks created)`, 'success');
            fileInput.value = '';
            fileList.innerHTML = '';
        } else {
            let errorMessage = result.detail || result.error || 'Upload failed';
            if (errorMessage.includes('timeout')) {
                errorMessage = 'Processing took too long. Please try with a smaller file or contact support.';
            }
            showStatus(errorMessage, 'error');
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            showStatus('Upload timed out. Please try with a smaller file or contact support.', 'error');
        } else {
            showStatus('Error uploading files: ' + error.message, 'error');
        }
    } finally {
        hideLoading();
    }
}

async function askQuestion() {
    const question = questionInput.value.trim();
    
    if (!question) {
        showStatus('Please enter a question', 'error');
        return;
    }

    showLoading('Analyzing documents and generating answer...');
    answerDiv.textContent = '';
    sourcesDiv.innerHTML = '';
    
    try {
        const formData = new FormData();
        formData.append('question', question);

        // Set timeout to 30 seconds for queries
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);

        const response = await fetch('/query', {
            method: 'POST',
            body: formData,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        const result = await response.json();
        
        if (response.ok) {
            // Display the answer
            answerDiv.textContent = result.answer;
            
            // Display sources with metadata
            sourcesDiv.innerHTML = result.sources.map((source, index) => `
                <div class="source-item">
                    <div class="source-metadata">
                        Source ${index + 1}
                        ${source.metadata.file_name ? `| File: ${source.metadata.file_name}` : ''}
                        ${source.metadata.page_number ? `| Page: ${source.metadata.page_number}` : ''}
                    </div>
                    <div class="source-content">${source.content}</div>
                </div>
            `).join('');
        } else {
            const errorMessage = result.detail || result.error || 'Failed to get answer';
            showStatus(errorMessage, 'error');
        }
    } catch (error) {
        if (error.name === 'AbortError') {
            showStatus('Query timed out. Please try asking a simpler question.', 'error');
        } else {
            showStatus('Error: ' + error.message, 'error');
        }
    } finally {
        hideLoading();
    }
}

// Enter key handler for question input
questionInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        askQuestion();
    }
});
