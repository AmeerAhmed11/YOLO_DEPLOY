// DOM Elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const confSlider = document.getElementById('conf-slider');
const confVal = document.getElementById('conf-val');
const btnInfer = document.getElementById('btn-infer');
const btnSpinner = document.getElementById('btn-spinner');
const btnDownload = document.getElementById('btn-download');

const imagePreview = document.getElementById('image-preview');
const videoPreview = document.getElementById('video-preview');
const resultCanvas = document.getElementById('result-canvas');
const emptyState = document.getElementById('empty-state');
const previewContainer = document.getElementById('preview-container');

const statTotal = document.getElementById('stat-total');
const statLatency = document.getElementById('stat-latency');
const classChipsContainer = document.getElementById('class-chips-container');
const systemStatus = document.getElementById('system-status');
const statusDot = document.querySelector('.status-dot');

const videoProgressOverlay = document.getElementById('video-progress-overlay');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');

// State
let currentFile = null;
let currentFileType = null; // 'image' or 'video'
let currentPredictions = null; // Store for re-rendering
let videoPredictions = null; // Store for video playback

// Configuration
const CLASS_COLORS = {
    'accident': '#EF4444', // Red
    'bus': '#F59E0B',      // Amber
    'car': '#3B82F6',      // Blue
    'truck': '#10B981'     // Green
};
const ALL_CLASSES = ['accident', 'bus', 'car', 'truck'];

// --- Event Listeners ---

// Drag and Drop
dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
        handleFileSelect(e.dataTransfer.files[0]);
    }
});
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
        handleFileSelect(e.target.files[0]);
    }
});

// Confidence Slider
confSlider.addEventListener('input', (e) => {
    confVal.textContent = `${e.target.value}%`;
    if (currentFileType === 'image' && currentPredictions) {
        renderImagePredictions(currentPredictions); // Re-render with new threshold
    }
});

// Inference Button
btnInfer.addEventListener('click', runInference);

// --- Core Functions ---

function showToast(msg, type = 'success') {
    const toastContainer = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = msg;
    toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function handleFileSelect(file) {
    if (file.size > 50 * 1024 * 1024) {
        showToast("File too large. Max 50MB.", "error");
        return;
    }

    currentFile = file;
    currentPredictions = null;
    videoPredictions = null;
    
    emptyState.style.display = 'none';
    btnInfer.disabled = false;
    clearCanvas();
    resetStats();

    if (file.type.startsWith('image/')) {
        currentFileType = 'image';
        videoPreview.style.display = 'none';
        imagePreview.style.display = 'block';
        imagePreview.src = URL.createObjectURL(file);
    } else if (file.type.startsWith('video/')) {
        currentFileType = 'video';
        imagePreview.style.display = 'none';
        videoPreview.style.display = 'block';
        videoPreview.src = URL.createObjectURL(file);
        videoPreview.load();
    } else {
        showToast("Unsupported file type", "error");
        currentFile = null;
        btnInfer.disabled = true;
    }
}

async function runInference() {
    if (!currentFile) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', currentFile);
    
    const startTime = performance.now();
    let endpoint = '/api/predict';
    
    if (currentFileType === 'video') {
        endpoint = '/api/predict/video';
        formData.append('fps_skip', 5); // Process every 5th frame
        videoProgressOverlay.style.display = 'flex';
        progressFill.style.width = '50%'; // Faux progress for now
    }

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || "Inference failed");
        }

        const data = await response.json();
        const latency = performance.now() - startTime;
        statLatency.textContent = `${latency.toFixed(0)} ms`;

        if (currentFileType === 'image') {
            currentPredictions = data.predictions[0];
            renderImagePredictions(currentPredictions);
            showToast("Inference complete");
        } else {
            videoProgressOverlay.style.display = 'none';
            videoPredictions = data.video_predictions;
            setupVideoPlayback();
            showToast("Video processing complete");
        }

        systemStatus.textContent = "Online";
        statusDot.className = "status-dot connected";

    } catch (error) {
        console.error(error);
        showToast(error.message, "error");
        systemStatus.textContent = "Error";
        statusDot.className = "status-dot disconnected";
    } finally {
        setLoading(false);
        if (currentFileType === 'video') videoProgressOverlay.style.display = 'none';
    }
}

function setLoading(isLoading) {
    btnInfer.disabled = isLoading;
    btnSpinner.style.display = isLoading ? 'block' : 'none';
    btnInfer.querySelector('span').style.opacity = isLoading ? '0' : '1';
}

function clearCanvas() {
    const ctx = resultCanvas.getContext('2d');
    ctx.clearRect(0, 0, resultCanvas.width, resultCanvas.height);
}

function resetStats() {
    statTotal.textContent = "0";
    statLatency.textContent = "- ms";
    classChipsContainer.innerHTML = '';
}

function renderImagePredictions(predictionData) {
    if (!predictionData) return;
    
    // Make sure image is fully loaded to get dimensions
    if (imagePreview.naturalWidth === 0) {
        imagePreview.onload = () => renderImagePredictions(predictionData);
        return;
    }

    const imgWidth = predictionData.image_width || imagePreview.naturalWidth;
    const imgHeight = predictionData.image_height || imagePreview.naturalHeight;
    
    // Set canvas dimensions to match the DISPLAYED size of the image, not natural size
    // to ensure overlay matches CSS scaling. We use getBoundingClientRect for actual render size.
    const rect = imagePreview.getBoundingClientRect();
    resultCanvas.width = rect.width;
    resultCanvas.height = rect.height;
    
    const scaleX = rect.width / imgWidth;
    const scaleY = rect.height / imgHeight;

    const ctx = resultCanvas.getContext('2d');
    ctx.clearRect(0, 0, resultCanvas.width, resultCanvas.height);

    const threshold = parseInt(confSlider.value) / 100.0;
    
    let totalDetections = 0;
    const classCounts = {};
    ALL_CLASSES.forEach(c => classCounts[c] = 0);

    const boxes = predictionData.boxes || [];
    const labels = predictionData.labels || [];
    const scores = predictionData.scores || [];

    for (let i = 0; i < boxes.length; i++) {
        if (scores[i] < threshold) continue;

        totalDetections++;
        const label = labels[i];
        classCounts[label] = (classCounts[label] || 0) + 1;

        const [x1, y1, x2, y2] = boxes[i];
        
        // Scale coordinates
        const sx1 = x1 * scaleX;
        const sy1 = y1 * scaleY;
        const width = (x2 - x1) * scaleX;
        const height = (y2 - y1) * scaleY;

        const color = CLASS_COLORS[label] || '#FFFFFF';

        // Draw box fill
        ctx.fillStyle = color + '20'; // 20 hex = ~12% opacity
        ctx.fillRect(sx1, sy1, width, height);
        
        // Draw box border
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.strokeRect(sx1, sy1, width, height);

        // Draw Label Background
        const labelText = `${label} ${(scores[i]*100).toFixed(0)}%`;
        ctx.font = "12px Inter, sans-serif";
        const textMetrics = ctx.measureText(labelText);
        const textWidth = textMetrics.width;
        
        ctx.fillStyle = color;
        ctx.fillRect(sx1, sy1 - 20, textWidth + 10, 20);

        // Draw Label Text
        ctx.fillStyle = '#FFFFFF';
        ctx.fillText(labelText, sx1 + 5, sy1 - 6);
    }

    updateStatsPanel(totalDetections, classCounts);
}

function updateStatsPanel(total, classCounts) {
    statTotal.textContent = total;
    classChipsContainer.innerHTML = '';
    
    for (const [cls, count] of Object.entries(classCounts)) {
        if (count > 0) {
            const chip = document.createElement('div');
            chip.className = `chip chip-${cls}`;
            chip.innerHTML = `<span class="dot"></span> ${cls}: ${count}`;
            classChipsContainer.appendChild(chip);
        }
    }
}

// --- Video Playback Logic ---

function setupVideoPlayback() {
    if (!videoPredictions) return;
    
    videoPreview.addEventListener('play', renderVideoFrame);
    // Trigger initial render
    renderVideoFrame();
}

function renderVideoFrame() {
    if (videoPreview.paused && !videoPreview.seeking) return;
    
    const currentTime = videoPreview.currentTime;
    // Assuming approx 30fps and we processed every 5th frame
    // We need to find the closest frame index
    const fps = 30; 
    const currentFrameIdx = Math.floor(currentTime * fps);
    
    // Find closest prediction
    // (In a real app, you'd interpolate or hold the last prediction)
    let closestPred = null;
    let minDiff = Infinity;
    
    for (const vp of videoPredictions) {
        const diff = Math.abs(vp.frame_index - currentFrameIdx);
        if (diff < minDiff) {
            minDiff = diff;
            closestPred = vp.predictions;
        }
    }
    
    if (closestPred && minDiff < 10) { // Only render if we have a prediction close enough
        // We temporarily trick the renderImagePredictions to use video dimensions
        const rect = videoPreview.getBoundingClientRect();
        
        // Override video sizing for canvas logic
        const dummyData = {
            ...closestPred,
            image_width: videoPreview.videoWidth,
            image_height: videoPreview.videoHeight
        };
        
        // Setup canvas to match video element
        resultCanvas.width = rect.width;
        resultCanvas.height = rect.height;
        
        const scaleX = rect.width / dummyData.image_width;
        const scaleY = rect.height / dummyData.image_height;
        
        const ctx = resultCanvas.getContext('2d');
        ctx.clearRect(0, 0, resultCanvas.width, resultCanvas.height);
        
        const threshold = parseInt(confSlider.value) / 100.0;
        
        const boxes = dummyData.boxes || [];
        const labels = dummyData.labels || [];
        const scores = dummyData.scores || [];
        
        let totalDetections = 0;
        
        for (let i = 0; i < boxes.length; i++) {
            if (scores[i] < threshold) continue;
            totalDetections++;
            
            const label = labels[i];
            const [x1, y1, x2, y2] = boxes[i];
            const sx1 = x1 * scaleX;
            const sy1 = y1 * scaleY;
            const width = (x2 - x1) * scaleX;
            const height = (y2 - y1) * scaleY;
            
            const color = CLASS_COLORS[label] || '#FFFFFF';
            
            ctx.strokeStyle = color;
            ctx.lineWidth = 2;
            ctx.strokeRect(sx1, sy1, width, height);
            
            ctx.fillStyle = color;
            ctx.fillRect(sx1, sy1 - 20, 80, 20);
            ctx.fillStyle = '#FFFFFF';
            ctx.font = "12px sans-serif";
            ctx.fillText(`${label} ${(scores[i]*100).toFixed(0)}%`, sx1 + 5, sy1 - 6);
        }
        
        // Optional: Update stats in real-time
        // statTotal.textContent = totalDetections;
    } else {
        clearCanvas();
    }
    
    // Request next frame
    requestAnimationFrame(renderVideoFrame);
}

// Ensure canvas matches image on window resize
window.addEventListener('resize', () => {
    if (currentFileType === 'image' && currentPredictions) {
        renderImagePredictions(currentPredictions);
    }
});
