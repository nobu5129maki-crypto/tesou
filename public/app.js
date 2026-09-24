/**
 * 手相解析アプリ - フロントエンド
 */

const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const uploadSection = document.getElementById('uploadSection');
const previewSection = document.getElementById('previewSection');
const previewImage = document.getElementById('previewImage');
const changeImageBtn = document.getElementById('changeImageBtn');
const analyzeBtn = document.getElementById('analyzeBtn');
const loadingSpinner = document.getElementById('loadingSpinner');
const resultsSection = document.getElementById('resultsSection');
const edgesImage = document.getElementById('edgesImage');
const vizImage = document.getElementById('vizImage');
const interpretationsList = document.getElementById('interpretationsList');
const newAnalysisBtn = document.getElementById('newAnalysisBtn');
const cameraBtn = document.getElementById('cameraBtn');
const cameraModal = document.getElementById('cameraModal');
const cameraVideo = document.getElementById('cameraVideo');
const cameraCanvas = document.getElementById('cameraCanvas');
const closeCameraBtn = document.getElementById('closeCameraBtn');
const captureBtn = document.getElementById('captureBtn');

const MAX_FILE_BYTES = 16 * 1024 * 1024;
const MAX_EDGE = 1200;

let currentImageData = null;
let cameraStream = null;
let currentInterpretations = [];
let currentCategories = [];

function setSectionVisible(section, visible) {
    section.classList.toggle('hidden', !visible);
    section.setAttribute('aria-hidden', visible ? 'false' : 'true');
}

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function loadImageElement(source) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = () => reject(new Error('画像を読み込めませんでした'));
        if (source instanceof Blob) {
            const url = URL.createObjectURL(source);
            img.onload = () => {
                URL.revokeObjectURL(url);
                resolve(img);
            };
            img.src = url;
            return;
        }
        img.src = source;
    });
}

async function imageToDataUrl(source) {
    let drawable = source;
    if (!(source instanceof HTMLCanvasElement)) {
        if (typeof createImageBitmap === 'function' && (source instanceof Blob || source instanceof HTMLCanvasElement)) {
            try {
                drawable = await createImageBitmap(source, { imageOrientation: 'from-image' });
            } catch (err) {
                drawable = await loadImageElement(source);
            }
        } else {
            drawable = await loadImageElement(source);
        }
    }
    const srcW = drawable.width || drawable.videoWidth || 0;
    const srcH = drawable.height || drawable.videoHeight || 0;
    const scale = Math.min(1, MAX_EDGE / Math.max(srcW, srcH, 1));
    const width = Math.max(1, Math.round(srcW * scale));
    const height = Math.max(1, Math.round(srcH * scale));
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(drawable, 0, 0, width, height);
    if (drawable.close) drawable.close();
    return canvas.toDataURL('image/jpeg', 0.82);
}

uploadArea.addEventListener('click', () => fileInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length) handleFile(files[0]);
});

fileInput.addEventListener('change', (e) => {
    const files = e.target.files;
    if (files.length) handleFile(files[0]);
});

async function handleFile(file) {
    if (!file || !file.type.startsWith('image/')) {
        alert('画像ファイルを選択してください。');
        return;
    }
    if (file.size > MAX_FILE_BYTES) {
        alert('画像が大きすぎます。16MB以下のJPEG / PNG / WEBPをお使いください。');
        return;
    }
    try {
        currentImageData = await imageToDataUrl(file);
        showPreview(currentImageData);
    } catch (err) {
        alert('画像を読み込めませんでした。別の写真でもう一度お試しください。');
    }
}

function showPreview(dataUrl) {
    previewImage.src = dataUrl;
    setSectionVisible(uploadSection, false);
    setSectionVisible(previewSection, true);
    setSectionVisible(resultsSection, false);
}

function backToUpload() {
    setSectionVisible(uploadSection, true);
    setSectionVisible(previewSection, false);
    setSectionVisible(resultsSection, false);
    fileInput.value = '';
    currentImageData = null;
    previewImage.removeAttribute('src');
}

changeImageBtn.addEventListener('click', backToUpload);

analyzeBtn.addEventListener('click', async () => {
    if (!currentImageData) return;

    const btnText = analyzeBtn.querySelector('.btn-text');
    btnText.classList.add('hidden');
    loadingSpinner.classList.remove('hidden');
    analyzeBtn.disabled = true;

    try {
        const formData = new FormData();
        formData.append('image_data', currentImageData);

        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.error || '解析に失敗しました');
        }
        showResults(data);
    } catch (err) {
        alert(err.message || '解析中にエラーが発生しました。');
    } finally {
        btnText.classList.remove('hidden');
        loadingSpinner.classList.add('hidden');
        analyzeBtn.disabled = false;
    }
});

function filterInterpretations(category) {
    const filtered = category === 'all'
        ? currentInterpretations
        : currentInterpretations.filter((item) => item.category === category);

    interpretationsList.innerHTML = '';
    filtered.forEach((item) => {
        const card = document.createElement('div');
        card.className = 'interpretation-card';
        card.dataset.category = item.category;
        card.innerHTML = `
            <div class="line-name">
                ${escapeHtml(item.line)}
                <span class="line-score" title="画像から検出された手相の線の濃さ。高いほどはっきりと見えていることを示します。">線の明瞭度: ${Math.round(Number(item.score) || 0)}%</span>
            </div>
            <p class="line-reading">${escapeHtml(item.reading)}</p>
        `;
        interpretationsList.appendChild(card);
    });
}

const LIGHTING_ICONS = {
    good: '✓',
    ok: '✓',
    dark: '⚠',
    bright: '⚠',
    too_dark: '✕',
    too_bright: '✕',
};

const LIGHTING_LABELS = {
    good: '照明：適切',
    ok: '照明：問題なし',
    dark: '照明：やや暗め',
    bright: '照明：やや明るめ',
    too_dark: '照明：不足',
    too_bright: '照明：明るすぎ',
};

function showResults(data) {
    edgesImage.src = data.edges_image || '';
    vizImage.src = data.visualization || '';

    const lightingEl = document.getElementById('lightingStatus');
    if (lightingEl && data.lighting) {
        const L = data.lighting;
        const status = L.status || 'ok';
        lightingEl.className = `lighting-status ${status}`;
        lightingEl.innerHTML = `
            <span class="lighting-status-icon" aria-hidden="true">${LIGHTING_ICONS[status] || '○'}</span>
            <div class="lighting-status-text">
                <strong>${LIGHTING_LABELS[status] || '照明'}</strong>
                <p>${escapeHtml(L.message || '')}</p>
                <span class="lighting-status-brightness">明るさレベル: ${escapeHtml(L.brightness ?? '—')} / 255</span>
            </div>
        `;
    } else if (lightingEl) {
        lightingEl.className = 'lighting-status ok';
        lightingEl.innerHTML = '';
    }

    const palmEl = document.getElementById('palmStatus');
    if (palmEl) {
        if (data.palm && data.palm.likely_palm === false) {
            palmEl.className = 'palm-status warn';
            palmEl.hidden = false;
            palmEl.textContent = data.palm.message || '手のひらがはっきり写っていない可能性があります。';
        } else {
            palmEl.hidden = true;
            palmEl.textContent = '';
            palmEl.className = 'palm-status';
        }
    }

    currentInterpretations = data.interpretations || [];
    currentCategories = data.categories || [];

    const filtersContainer = document.getElementById('categoryFilters');
    filtersContainer.innerHTML = '<button type="button" class="category-btn active" data-category="all">すべて</button>';

    currentCategories.forEach((cat) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'category-btn';
        btn.dataset.category = cat.id;
        btn.textContent = `${cat.icon} ${cat.name}`;
        filtersContainer.appendChild(btn);
    });

    filtersContainer.querySelectorAll('.category-btn').forEach((btn) => {
        btn.addEventListener('click', () => {
            filtersContainer.querySelectorAll('.category-btn').forEach((b) => b.classList.remove('active'));
            btn.classList.add('active');
            filterInterpretations(btn.dataset.category);
        });
    });

    filterInterpretations('all');
    setSectionVisible(previewSection, false);
    setSectionVisible(resultsSection, true);
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

newAnalysisBtn.addEventListener('click', backToUpload);

async function openCamera() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('このブラウザではカメラを使えません。');
    }
    const attempts = [
        { video: { facingMode: { ideal: 'environment' }, width: { ideal: 1280 }, height: { ideal: 720 } } },
        { video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } } },
        { video: true }
    ];
    let lastError = null;
    for (const constraints of attempts) {
        try {
            return await navigator.mediaDevices.getUserMedia(constraints);
        } catch (err) {
            lastError = err;
        }
    }
    throw lastError || new Error('カメラにアクセスできません。');
}

cameraBtn.addEventListener('click', async () => {
    try {
        cameraStream = await openCamera();
        cameraVideo.srcObject = cameraStream;
        cameraModal.classList.add('active');
        cameraModal.setAttribute('aria-hidden', 'false');
        document.body.classList.add('camera-open');
    } catch (err) {
        alert('カメラにアクセスできません。' + (err && err.message ? err.message : ''));
    }
});

function closeCameraModal() {
    stopCamera();
    cameraModal.classList.remove('active');
    cameraModal.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('camera-open');
}

closeCameraBtn.addEventListener('click', closeCameraModal);

captureBtn.addEventListener('click', async () => {
    if (!cameraVideo.videoWidth || !cameraVideo.videoHeight) {
        alert('カメラ映像の準備ができていません。少し待ってから撮影してください。');
        return;
    }
    const ctx = cameraCanvas.getContext('2d');
    cameraCanvas.width = cameraVideo.videoWidth;
    cameraCanvas.height = cameraVideo.videoHeight;
    ctx.drawImage(cameraVideo, 0, 0);
    closeCameraModal();
    try {
        currentImageData = await imageToDataUrl(cameraCanvas);
        showPreview(currentImageData);
    } catch (err) {
        alert('撮影した画像を読み込めませんでした。');
    }
});

function stopCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach((track) => track.stop());
        cameraStream = null;
    }
    cameraVideo.srcObject = null;
}

cameraModal.addEventListener('click', (e) => {
    if (e.target === cameraModal) closeCameraModal();
});

if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js', { scope: '/' })
            .then((reg) => console.log('Service Worker 登録完了', reg.scope))
            .catch((err) => console.log('Service Worker 登録失敗', err));
    });
}
