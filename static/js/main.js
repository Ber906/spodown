document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('downloadForm');
    const urlInput = document.getElementById('urlInput');
    const progressBar = document.getElementById('progressBar');
    const outputText = document.getElementById('outputText');
    const downloadBtn = document.getElementById('downloadBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    const trackListBtn = document.getElementById('trackListBtn');

    let sessionId = null;
    let progressInterval = null;

    const showNotification = (title, text, icon) => {
        Swal.fire({
            title,
            text,
            icon,
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true
        });
    };

    const startProgressTracking = () => {
        if (progressInterval) clearInterval(progressInterval);
        
        progressInterval = setInterval(async () => {
            try {
                const response = await fetch(`/download-progress?session_id=${sessionId}`);
                const data = await response.json();
                
                if (response.ok) {
                    progressBar.style.width = `${data.percentage}%`;
                    progressBar.textContent = `${data.percentage}%`;
                    
                    if (data.download_complete) {
                        clearInterval(progressInterval);
                        showNotification('Success', 'Download completed!', 'success');
                        downloadBtn.classList.remove('d-none');
                        cancelBtn.classList.add('d-none');
                        form.reset();
                    }
                }
            } catch (error) {
                console.error('Progress tracking error:', error);
                clearInterval(progressInterval);
            }
        }, 1000);
    };

    const updateOutput = async () => {
        try {
            const response = await fetch(`/output?session_id=${sessionId}`);
            if (response.ok) {
                const text = await response.text();
                outputText.textContent = text;
                outputText.scrollTop = outputText.scrollHeight;
            }
        } catch (error) {
            console.error('Output update error:', error);
        }
    };

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const url = urlInput.value.trim();
        if (!url) {
            showNotification('Error', 'Please enter a Spotify URL', 'error');
            return;
        }

        if (!url.startsWith('https://open.spotify.com/')) {
            showNotification('Error', 'Invalid Spotify URL', 'error');
            return;
        }

        try {
            const response = await fetch('/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url })
            });

            const data = await response.json();
            
            if (response.ok) {
                sessionId = data.session_id;
                showNotification('Success', 'Download started', 'success');
                startProgressTracking();
                cancelBtn.classList.remove('d-none');
                downloadBtn.classList.add('d-none');
                setInterval(updateOutput, 1000);
            } else {
                showNotification('Error', data.error || 'Download failed', 'error');
            }
        } catch (error) {
            showNotification('Error', 'Server error occurred', 'error');
            console.error('Download error:', error);
        }
    });

    cancelBtn.addEventListener('click', async () => {
        try {
            const response = await fetch(`/cancel-download?session_id=${sessionId}`);
            const data = await response.json();
            
            if (data.success) {
                showNotification('Success', 'Download cancelled', 'info');
                clearInterval(progressInterval);
                progressBar.style.width = '0%';
                progressBar.textContent = '0%';
                cancelBtn.classList.add('d-none');
                form.reset();
            }
        } catch (error) {
            showNotification('Error', 'Failed to cancel download', 'error');
        }
    });

    downloadBtn.addEventListener('click', () => {
        if (sessionId) {
            window.location.href = `/download/${sessionId}`;
        }
    });

    trackListBtn.addEventListener('click', async () => {
        try {
            const response = await fetch(`/tracks?session_id=${sessionId}`);
            const tracks = await response.json();
            
            if (response.ok) {
                const trackList = tracks.map(track => 
                    `<div class="track-item">
                        <span>${track}</span>
                        <button class="btn btn-sm btn-spotify" 
                                onclick="window.location.href='/download-track/${sessionId}/${encodeURIComponent(track)}'">
                            Download
                        </button>
                    </div>`
                ).join('');

                Swal.fire({
                    title: 'Available Tracks',
                    html: `<div class="track-list">${trackList}</div>`,
                    width: 600,
                    showConfirmButton: false,
                    showCloseButton: true,
                    background: '#282828',
                    color: '#FFFFFF'
                });
            }
        } catch (error) {
            showNotification('Error', 'Failed to fetch track list', 'error');
        }
    });
});
