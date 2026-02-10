const LOB_DATA = {
    "Connected Home": { client: "RHE", product: "IGN" },
    "Consumer Wireless": { client: "RCS", product: "WLS" },
    "Rogers Business": { client: "RNS", product: "BRA" },
    "Rogers Bank": { client: "RBG", product: "RBK" },
    "Corporate Brand": { client: "RCP", product: "RCB" },
    "Shaw Direct": { client: "RSH", product: "CBL" }
};

const PLATFORM_SIZES = {
    "Meta": ["1x1 Meta", "9x16 Story", "9x16 Reel"],
    "Pinterest": ["2x3 Pinterest", "1x1 Pinterest", "9x16 Pinterest"],
    "Reddit": ["1x1 Reddit", "4x5 Reddit", "16x9 Reddit"],
    "Display": ["300x250", "728x90", "160x600", "300x600", "970x250"]
};

let matrixData = null;

document.addEventListener('DOMContentLoaded', function() {
    initDates();
    updateSizes();
    updateTotalAssets();
    setupEventListeners();
});

function initDates() {
    const today = new Date().toISOString().split('T')[0];
    const endDate = new Date();
    endDate.setMonth(endDate.getMonth() + 2);
    
    document.getElementById('startDate').value = today;
    document.getElementById('endDate').value = endDate.toISOString().split('T')[0];
    document.getElementById('deliveryDate').value = today;
}

function setupEventListeners() {
    document.querySelectorAll('input[name="matrixType"]').forEach(radio => {
        radio.addEventListener('change', handleMatrixTypeChange);
    });
    
    document.getElementById('platforms').addEventListener('change', updateSizes);
    
    document.getElementById('lob').addEventListener('change', handleLobChange);
    
    document.querySelectorAll('#funnels input, #regions input, #languages input, #durations input, #sizes input').forEach(cb => {
        cb.addEventListener('change', updateTotalAssets);
    });
    document.getElementById('addOfferBtn').addEventListener('click', addOfferRow);
    document.getElementById('offersList').addEventListener('click', handleOfferListClick);
    document.getElementById('offersList').addEventListener('input', updateTotalAssets);
    
    document.getElementById('generateBtn').addEventListener('click', generateMatrix);
    document.getElementById('downloadBtn').addEventListener('click', downloadCSV);
    document.getElementById('copyBtn').addEventListener('click', copyToClipboard);
    document.getElementById('clearBtn').addEventListener('click', clearMatrix);
    
    document.getElementById('addDurationBtn').addEventListener('click', addCustomDuration);
    document.getElementById('addSizeBtn').addEventListener('click', addCustomSize);
    
    document.getElementById('customDuration').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addCustomDuration();
    });
    document.getElementById('customSize').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addCustomSize();
    });
}

function addOfferRow() {
    const container = document.getElementById('offersList');
    const row = document.createElement('div');
    row.className = 'offer-row';
    row.innerHTML = `
        <input type="text" class="input offer-name" placeholder="Offer name">
        <input type="text" class="input offer-price" placeholder="Price (e.g. $65)">
        <button type="button" class="btn btn-small btn-remove" title="Remove">×</button>
    `;
    container.appendChild(row);
    updateTotalAssets();
}

function handleOfferListClick(e) {
    if (e.target.classList.contains('btn-remove')) {
        const row = e.target.closest('.offer-row');
        const container = document.getElementById('offersList');
        if (container.children.length > 1) {
            row.remove();
            updateTotalAssets();
        }
    }
}

function getOffers() {
    const rows = document.querySelectorAll('#offersList .offer-row');
    const offers = [];
    rows.forEach(row => {
        const name = row.querySelector('.offer-name').value.trim();
        const price = row.querySelector('.offer-price').value.trim();
        if (name) {
            offers.push({ name, price });
        }
    });
    return offers;
}

function addCustomDuration() {
    const input = document.getElementById('customDuration');
    const value = input.value.trim();
    
    if (!value) return;
    
    const container = document.getElementById('durations');
    const existingValues = Array.from(container.querySelectorAll('input')).map(cb => cb.value.toLowerCase());
    
    if (existingValues.includes(value.toLowerCase())) {
        input.value = '';
        return;
    }
    
    const label = document.createElement('label');
    label.className = 'checkbox-label';
    label.innerHTML = `<input type="checkbox" value="${value}" checked><span>${value}</span>`;
    container.appendChild(label);
    
    label.querySelector('input').addEventListener('change', updateTotalAssets);
    
    input.value = '';
    updateTotalAssets();
}

function addCustomSize() {
    const input = document.getElementById('customSize');
    const value = input.value.trim();
    
    if (!value) return;
    
    const container = document.getElementById('sizes');
    const existingValues = Array.from(container.querySelectorAll('input')).map(cb => cb.value.toLowerCase());
    
    if (existingValues.includes(value.toLowerCase())) {
        input.value = '';
        return;
    }
    
    const label = document.createElement('label');
    label.className = 'checkbox-label';
    label.innerHTML = `<input type="checkbox" value="${value}" checked><span>${value}</span>`;
    container.appendChild(label);
    
    label.querySelector('input').addEventListener('change', updateTotalAssets);
    
    input.value = '';
    updateTotalAssets();
}

function handleMatrixTypeChange() {
    const matrixType = document.querySelector('input[name="matrixType"]:checked').value;
    const platformsContainer = document.getElementById('platformsContainer');
    
    if (matrixType === 'Social') {
        platformsContainer.style.display = 'block';
    } else {
        platformsContainer.style.display = 'none';
    }
    
    updateSizes();
}

function handleLobChange() {
    const lob = document.getElementById('lob').value;
    const data = LOB_DATA[lob];
    
    document.getElementById('clientCode').value = data.client;
    document.getElementById('productCode').value = data.product;
}

function updateSizes() {
    const matrixType = document.querySelector('input[name="matrixType"]:checked').value;
    const sizesContainer = document.getElementById('sizes');
    const sizesInfo = document.getElementById('sizesInfo');
    
    let availableSizes = [];
    
    if (matrixType === 'Social') {
        const selectedPlatforms = getCheckedValues('platforms');
        selectedPlatforms.forEach(platform => {
            availableSizes = availableSizes.concat(PLATFORM_SIZES[platform] || []);
        });
        availableSizes = [...new Set(availableSizes)];
        sizesInfo.textContent = `✓ ${availableSizes.length} sizes available from selected platforms`;
        sizesInfo.className = 'info-box success';
    } else {
        availableSizes = PLATFORM_SIZES['Display'];
        sizesInfo.textContent = `📐 ${availableSizes.length} standard display sizes available`;
        sizesInfo.className = 'info-box info';
    }
    
    availableSizes.push('16x9');
    availableSizes = [...new Set(availableSizes)].sort();
    
    sizesContainer.innerHTML = availableSizes.map(size => `
        <label class="checkbox-label">
            <input type="checkbox" value="${size}" ${matrixType === 'Social' && !size.includes('16x9') ? 'checked' : ''}>
            <span>${size}</span>
        </label>
    `).join('');
    
    sizesContainer.querySelectorAll('input').forEach(cb => {
        cb.addEventListener('change', updateTotalAssets);
    });
    
    updateTotalAssets();
}

function getCheckedValues(containerId) {
    const container = document.getElementById(containerId);
    return Array.from(container.querySelectorAll('input:checked')).map(cb => cb.value);
}

function getMessaging() {
    return getOffers();
}

function updateTotalAssets() {
    const funnels = getCheckedValues('funnels');
    const regions = getCheckedValues('regions');
    const languages = getCheckedValues('languages');
    const durations = getCheckedValues('durations');
    const sizes = getCheckedValues('sizes');
    const messages = getMessaging();
    
    const total = funnels.length * regions.length * languages.length * durations.length * sizes.length * messages.length;
    
    document.querySelector('.metric-value').textContent = total.toLocaleString();
    document.getElementById('assetBreakdown').textContent = 
        `${funnels.length} funnels × ${messages.length} messages × ${regions.length} regions × ${languages.length} languages × ${durations.length} durations × ${sizes.length} sizes`;
    
    const warningBox = document.getElementById('warningBox');
    if (total === 0) {
        warningBox.style.display = 'block';
    } else {
        warningBox.style.display = 'none';
    }
}

function formatDate(dateStr) {
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const d = new Date(dateStr);
    return `${months[d.getMonth()]}.${String(d.getDate()).padStart(2, '0')}.${d.getFullYear()}`;
}

function cleanVal(s) {
    return (s || '').replace(/_/g, ' ').trim();
}

function generateMatrix() {
    const matrixType = document.querySelector('input[name="matrixType"]:checked').value;
    const clientCode = document.getElementById('clientCode').value;
    const productCode = document.getElementById('productCode').value;
    const campaignTitle = document.getElementById('campaignTitle').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const deliveryDate = document.getElementById('deliveryDate').value;
    const customSuffix = document.getElementById('customSuffix').value;
    
    const funnels = getCheckedValues('funnels');
    const regions = getCheckedValues('regions');
    const languages = getCheckedValues('languages');
    const durations = getCheckedValues('durations');
    const sizes = getCheckedValues('sizes');
    const messages = getMessaging();
    
    if (funnels.length === 0 || regions.length === 0 || languages.length === 0 || 
        durations.length === 0 || sizes.length === 0 || messages.length === 0) {
        alert('Please select at least one option in each category');
        return;
    }
    
    const flatData = [];
    
    for (const funnel of funnels) {
        for (const offer of messages) {
            for (const region of regions) {
                // FR is only available for QC region
                const regionLanguages = region === 'QC' 
                    ? languages 
                    : languages.filter(l => l === 'EN');
                
                // Skip if no languages available for this region
                if (regionLanguages.length === 0) continue;
                
                for (const lang of regionLanguages) {
                    for (const duration of durations) {
                        for (const size of sizes) {
                            const fullCampaign = `${campaignTitle}-${funnel}-${region}-${lang}`;
                            const sizeCode = size.split(' ')[0];
                            
                            const year = new Date(startDate).getFullYear().toString();
                            let creativeName = [
                                year, clientCode, productCode, lang,
                                cleanVal(fullCampaign), cleanVal(offer.name),
                                sizeCode, formatDate(startDate), cleanVal(duration)
                            ].join('_');
                            
                            if (customSuffix) {
                                creativeName += `_${cleanVal(customSuffix)}`;
                            }
                            
                            if (offer.price) {
                                creativeName += `_${cleanVal(offer.price)}`;
                            }
                            
                            flatData.push({
                                FUNNEL: funnel,
                                MESSAGING: offer.name,
                                REGION: region,
                                LANGUAGE: lang,
                                DURATION: duration,
                                SizeLabel: size,
                                'Creative Name': creativeName
                            });
                        }
                    }
                }
            }
        }
    }
    
    const pivotData = {};
    const allSizes = new Set();
    
    flatData.forEach(row => {
        const key = `${row.FUNNEL}|${row.MESSAGING}|${row.REGION}|${row.LANGUAGE}|${row.DURATION}`;
        if (!pivotData[key]) {
            pivotData[key] = {
                FUNNEL: row.FUNNEL,
                MESSAGING: row.MESSAGING,
                REGION: row.REGION,
                LANGUAGE: row.LANGUAGE,
                DURATION: row.DURATION
            };
        }
        pivotData[key][row.SizeLabel] = row['Creative Name'];
        allSizes.add(row.SizeLabel);
    });
    
    const rows = Object.values(pivotData);
    const sizeColumns = [...allSizes].sort();
    
    rows.forEach(row => {
        row['DELIVERY DATE'] = formatDate(deliveryDate);
        row['START DATE'] = formatDate(startDate);
        row['END DATE'] = formatDate(endDate);
        row['URL'] = '';
    });
    
    matrixData = { rows, sizeColumns };
    
    renderTable(rows, sizeColumns);
    
    document.getElementById('welcomePanel').style.display = 'none';
    document.getElementById('resultPanel').style.display = 'block';
    document.getElementById('matrixTypeLabel').textContent = matrixType;
    document.getElementById('totalRows').textContent = rows.length;
    document.getElementById('sizeColumns').textContent = sizeColumns.length;
}

function renderTable(rows, sizeColumns) {
    const thead = document.querySelector('#matrixTable thead');
    const tbody = document.querySelector('#matrixTable tbody');
    
    const columns = ['FUNNEL', 'MESSAGING', 'REGION', 'LANGUAGE', 'DURATION', ...sizeColumns, 'DELIVERY DATE', 'START DATE', 'END DATE', 'URL'];
    
    thead.innerHTML = '<tr>' + columns.map(col => `<th>${col}</th>`).join('') + '</tr>';
    
    tbody.innerHTML = rows.map(row => {
        return '<tr>' + columns.map(col => `<td title="${row[col] || ''}">${row[col] || ''}</td>`).join('') + '</tr>';
    }).join('');
}

function downloadCSV() {
    if (!matrixData) return;
    
    const { rows, sizeColumns } = matrixData;
    const columns = ['FUNNEL', 'MESSAGING', 'REGION', 'LANGUAGE', 'DURATION', ...sizeColumns, 'DELIVERY DATE', 'START DATE', 'END DATE', 'URL'];
    
    const csvContent = [
        columns.join(','),
        ...rows.map(row => columns.map(col => `"${(row[col] || '').replace(/"/g, '""')}"`).join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    const matrixType = document.querySelector('input[name="matrixType"]:checked').value;
    const lob = document.getElementById('lob').value.replace(/ /g, '_');
    const today = new Date().toISOString().split('T')[0].replace(/-/g, '');
    
    link.setAttribute('href', url);
    link.setAttribute('download', `Asset_Matrix_${lob}_${matrixType}_${today}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function copyToClipboard() {
    if (!matrixData) return;
    
    const { rows, sizeColumns } = matrixData;
    const columns = ['FUNNEL', 'MESSAGING', 'REGION', 'LANGUAGE', 'DURATION', ...sizeColumns, 'DELIVERY DATE', 'START DATE', 'END DATE', 'URL'];
    
    const tsvContent = [
        columns.join('\t'),
        ...rows.map(row => columns.map(col => row[col] || '').join('\t'))
    ].join('\n');
    
    navigator.clipboard.writeText(tsvContent).then(() => {
        const btn = document.getElementById('copyBtn');
        const originalText = btn.textContent;
        btn.textContent = '✓ Copied!';
        btn.style.background = '#28a745';
        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.background = '';
        }, 2000);
    }).catch(err => {
        alert('Failed to copy. Please try again.');
    });
}

function clearMatrix() {
    matrixData = null;
    document.getElementById('welcomePanel').style.display = 'block';
    document.getElementById('resultPanel').style.display = 'none';
    document.querySelector('#matrixTable thead').innerHTML = '';
    document.querySelector('#matrixTable tbody').innerHTML = '';
}
