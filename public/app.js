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

let currentImageData = null;
let cameraStream = null;

// ドラッグ＆ドロップ
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

function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        alert('画像ファイルを選択してください。');
        return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
        currentImageData = e.target.result;
        showPreview(currentImageData);
    };
    reader.readAsDataURL(file);
}

function showPreview(dataUrl) {
    previewImage.src = dataUrl;
    uploadSection.classList.add('hidden');
    uploadSection.setAttribute('aria-hidden', 'true');
    previewSection.classList.remove('hidden');
    previewSection.setAttribute('aria-hidden', 'false');
}

changeImageBtn.addEventListener('click', () => {
    uploadSection.classList.remove('hidden');
    uploadSection.setAttribute('aria-hidden', 'false');
    previewSection.classList.add('hidden');
    previewSection.setAttribute('aria-hidden', 'true');
    resultsSection.classList.add('hidden');
    resultsSection.setAttribute('aria-hidden', 'true');
    fileInput.value = '';
});

// 解析実行
analyzeBtn.addEventListener('click', async () => {
    if (!currentImageData) return;
    
    const btnText = analyzeBtn.querySelector('.btn-text');
    btnText.classList.add('hidden');
    loadingSpinner.classList.remove('hidden');
    analyzeBtn.disabled = true;
    
    try {
        const formData = new FormData();
        if (currentImageData.startsWith('data:')) {
            formData.append('image_data', currentImageData);
        } else {
            const blob = await fetch(currentImageData).then(r => r.blob());
            formData.append('image', blob);
        }
        
        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || '解析に失敗しました');
        }
        
        showResults(data);
    } catch (err) {
        alert(err.message || '解析中にエラーが発生しました。');
    } finally {
        btnText.classList.remove('hidden');
        loadingSpinner.classList.remove('hidden');
        analyzeBtn.disabled = false;
    }
});

let currentInterpretations = [];
let currentCategories = [];

function filterInterpretations(category) {
    const filtered = category === 'all' 
        ? currentInterpretations 
        : currentInterpretations.filter(item => item.category === category);
    
    interpretationsList.innerHTML = '';
    filtered.forEach(item => {
        const card = document.createElement('div');
        card.className = 'interpretation-card';
        card.dataset.category = item.category;
        card.innerHTML = `
            <div class="line-name">
                ${item.line}
                <span class="line-score" title="画像から検出された手相の線の濃さ。高いほどはっきりと見えていることを示します。">線の明瞭度: ${Math.round(item.score)}%</span>
            </div>
            <p class="line-reading">${item.reading}</p>
        `;
        interpretationsList.appendChild(card);
    });
}

function showResults(data) {
    edgesImage.src = data.edges_image;
    vizImage.src = data.visualization;
    
    currentInterpretations = data.interpretations || [];
    currentCategories = data.categories || [];
    
    // カテゴリフィルターボタンを生成
    const filtersContainer = document.getElementById('categoryFilters');
    filtersContainer.innerHTML = '<button type="button" class="category-btn active" data-category="all">すべて</button>';
    
    currentCategories.forEach(cat => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'category-btn';
        btn.dataset.category = cat.id;
        btn.textContent = `${cat.icon} ${cat.name}`;
        filtersContainer.appendChild(btn);
    });
    
    // フィルターボタンのイベント
    filtersContainer.querySelectorAll('.category-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            filtersContainer.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterInterpretations(btn.dataset.category);
        });
    });
    
    filterInterpretations('all');
    
    previewSection.classList.add('hidden');
    previewSection.setAttribute('aria-hidden', 'true');
    resultsSection.classList.remove('hidden');
    resultsSection.setAttribute('aria-hidden', 'false');
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

newAnalysisBtn.addEventListener('click', () => {
    resultsSection.classList.add('hidden');
    resultsSection.setAttribute('aria-hidden', 'true');
    uploadSection.classList.remove('hidden');
    uploadSection.setAttribute('aria-hidden', 'false');
    currentImageData = null;
});

// カメラ機能
cameraBtn.addEventListener('click', async () => {
    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({ 
            video: { facingMode: 'environment', width: { ideal: 1280 }, height: { ideal: 720 } } 
        });
        cameraVideo.srcObject = cameraStream;
        cameraModal.classList.add('active');
        cameraModal.setAttribute('aria-hidden', 'false');
    } catch (err) {
        alert('カメラにアクセスできません。' + (err.message || ''));
    }
});

closeCameraBtn.addEventListener('click', () => {
    stopCamera();
    cameraModal.classList.remove('active');
    cameraModal.setAttribute('aria-hidden', 'true');
});

captureBtn.addEventListener('click', () => {
    const ctx = cameraCanvas.getContext('2d');
    cameraCanvas.width = cameraVideo.videoWidth;
    cameraCanvas.height = cameraVideo.videoHeight;
    ctx.drawImage(cameraVideo, 0, 0);
    
    currentImageData = cameraCanvas.toDataURL('image/jpeg', 0.9);
    stopCamera();
    cameraModal.classList.remove('active');
    cameraModal.setAttribute('aria-hidden', 'true');
    showPreview(currentImageData);
});

function stopCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
}

// モーダル外クリックで閉じる
cameraModal.addEventListener('click', (e) => {
    if (e.target === cameraModal) {
        stopCamera();
        cameraModal.classList.remove('active');
        cameraModal.setAttribute('aria-hidden', 'true');
    }
});

// PWA Service Worker 登録
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js', { scope: '/' })
            .then((reg) => console.log('Service Worker 登録完了', reg.scope))
            .catch((err) => console.log('Service Worker 登録失敗', err));
    });
}
