import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Badger | Asset Matrix Creator", page_icon="🦡", layout="wide")

with open('styles.css', 'r') as f:
    css = f.read()

with open('script.js', 'r') as f:
    js = f.read()

html_content = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>{css}</style>
</head>
<body>
    <header>
        <h1 class="main-header">🦡 Badger</h1>
        <p class="sub-header">Asset Matrix Creator — Generate naming conventions in seconds</p>
    </header>

    <div class="container">
        <aside class="sidebar">
            <section class="card">
                <h3>🛠️ Step 1: Choose Matrix Type</h3>
                <p class="caption">Select the type of assets you're creating</p>
                
                <div class="radio-group">
                    <label class="radio-label">
                        <input type="radio" name="matrixType" value="Social" checked>
                        <span>Social</span>
                    </label>
                    <label class="radio-label">
                        <input type="radio" name="matrixType" value="Display">
                        <span>Display</span>
                    </label>
                </div>
                
                <div id="platformsContainer">
                    <label class="label">Platforms</label>
                    <div class="checkbox-group" id="platforms">
                        <label class="checkbox-label">
                            <input type="checkbox" value="Meta" checked>
                            <span>Meta</span>
                        </label>
                        <label class="checkbox-label">
                            <input type="checkbox" value="Pinterest" checked>
                            <span>Pinterest</span>
                        </label>
                        <label class="checkbox-label">
                            <input type="checkbox" value="Reddit">
                            <span>Reddit</span>
                        </label>
                    </div>
                </div>
                
                <div id="sizesInfo" class="info-box success"></div>
            </section>

            <section class="card">
                <h3>📋 Step 2: Set Identity</h3>
                <p class="caption">Define the business unit and timing</p>
                
                <label class="label">Line of Business</label>
                <select id="lob" class="select">
                    <option value="Connected Home">Connected Home</option>
                    <option value="Consumer Wireless">Consumer Wireless</option>
                    <option value="Rogers Business">Rogers Business</option>
                    <option value="Rogers Bank">Rogers Bank</option>
                    <option value="Corporate Brand">Corporate Brand</option>
                    <option value="Shaw Direct">Shaw Direct</option>
                </select>
                
                <div class="row">
                    <div class="col">
                        <label class="label">Client Code</label>
                        <input type="text" id="clientCode" class="input" value="RHE">
                    </div>
                    <div class="col">
                        <label class="label">Product Code</label>
                        <select id="productCode" class="select">
                            <option value="IGN" selected>IGN</option>
                            <option value="WLS">WLS</option>
                            <option value="BRA">BRA</option>
                            <option value="RBK">RBK</option>
                            <option value="RCB">RCB</option>
                            <option value="CBL">CBL</option>
                            <option value="TSP">TSP</option>
                            <option value="FIN">FIN</option>
                            <option value="SHM">SHM</option>
                            <option value="CWI">CWI</option>
                            <option value="FWI">FWI</option>
                            <option value="IDV">IDV</option>
                            <option value="RWI">RWI</option>
                            <option value="SOH">SOH</option>
                            <option value="FIB">FIB</option>
                            <option value="IOT">IOT</option>
                        </select>
                    </div>
                </div>
                
                <p class="label" style="margin-top: 1rem;"><strong>Campaign Dates</strong></p>
                <div class="row">
                    <div class="col">
                        <label class="label">Start Date</label>
                        <input type="date" id="startDate" class="input">
                    </div>
                    <div class="col">
                        <label class="label">End Date</label>
                        <input type="date" id="endDate" class="input">
                    </div>
                </div>
                <label class="label">Delivery Date</label>
                <input type="date" id="deliveryDate" class="input">
            </section>

            <section class="card">
                <h3>🏗️ Step 3: Build Campaign</h3>
                <p class="caption">Configure your campaign details</p>
                
                <label class="label">Campaign Title</label>
                <input type="text" id="campaignTitle" class="input" value="Q3 Comwave QC">
                
                <div class="row">
                    <div class="col">
                        <label class="label">Funnel Stage</label>
                        <div class="multi-select" id="funnels">
                            <label class="checkbox-label"><input type="checkbox" value="AWR" checked><span>AWR</span></label>
                            <label class="checkbox-label"><input type="checkbox" value="COV"><span>COV</span></label>
                            <label class="checkbox-label"><input type="checkbox" value="COS"><span>COS</span></label>
                        </div>
                    </div>
                    <div class="col">
                        <label class="label">Region</label>
                        <div class="multi-select" id="regions">
                            <label class="checkbox-label"><input type="checkbox" value="ATL" checked><span>ATL</span></label>
                            <label class="checkbox-label"><input type="checkbox" value="ROC"><span>ROC</span></label>
                            <label class="checkbox-label"><input type="checkbox" value="QC"><span>QC</span></label>
                            <label class="checkbox-label"><input type="checkbox" value="Halifax"><span>Halifax</span></label>
                        </div>
                    </div>
                </div>
                
                <label class="label">Language</label>
                <div class="multi-select" id="languages">
                    <label class="checkbox-label"><input type="checkbox" value="EN" checked><span>EN</span></label>
                    <label class="checkbox-label"><input type="checkbox" value="FR"><span>FR</span></label>
                </div>
                
                <label class="label">Messaging Variants</label>
                <div id="offersList">
                    <div class="offer-row">
                        <input type="text" class="input offer-name" placeholder="Offer name" value="Internet Offer V1">
                        <input type="text" class="input offer-price" placeholder="Price (e.g. $65)">
                        <button type="button" class="btn btn-small btn-remove" title="Remove">×</button>
                    </div>
                </div>
                <button type="button" id="addOfferBtn" class="btn btn-small btn-add-offer">+ Add Offer</button>
            </section>

            <section class="card">
                <h3>🎨 Step 4: Specify Assets</h3>
                <p class="caption">Define durations and sizes</p>
                
                <label class="label">Durations</label>
                <div class="multi-select" id="durations">
                    <label class="checkbox-label"><input type="checkbox" value="6s"><span>6s</span></label>
                    <label class="checkbox-label"><input type="checkbox" value="10s"><span>10s</span></label>
                    <label class="checkbox-label"><input type="checkbox" value="15s" checked><span>15s</span></label>
                    <label class="checkbox-label"><input type="checkbox" value="30s"><span>30s</span></label>
                    <label class="checkbox-label"><input type="checkbox" value="Static"><span>Static</span></label>
                </div>
                <div class="add-custom-row">
                    <input type="text" id="customDuration" class="input input-small" placeholder="e.g. 5s">
                    <button type="button" id="addDurationBtn" class="btn btn-small">+ Add</button>
                </div>
                
                <label class="label">Sizes</label>
                <div class="multi-select" id="sizes"></div>
                <div class="add-custom-row">
                    <input type="text" id="customSize" class="input input-small" placeholder="e.g. 320x50">
                    <button type="button" id="addSizeBtn" class="btn btn-small">+ Add</button>
                </div>
                
                <label class="label">Custom Suffix (Optional)</label>
                <input type="text" id="customSuffix" class="input" placeholder="e.g. V1, Final, Draft">
            </section>

            <div class="divider"></div>
            
            <div id="totalAssets" class="metric">
                <span class="metric-label">📊 Total Assets</span>
                <span class="metric-value">0</span>
            </div>
            <p id="assetBreakdown" class="caption"></p>
            
            <button id="generateBtn" class="btn btn-primary">🚀 Generate Asset Matrix</button>
            
            <div id="warningBox" class="info-box warning" style="display: none;">
                ⚠️ Please select at least one option in each category
            </div>
        </aside>

        <main class="content">
            <div id="welcomePanel">
                <h2>👋 Welcome!</h2>
                <div class="welcome-box">
                    <h4>How to use Badger:</h4>
                    <ol>
                        <li><strong>Choose Matrix Type</strong> — Social or Display</li>
                        <li><strong>Set Identity</strong> — Select your business unit and dates</li>
                        <li><strong>Build Campaign</strong> — Add funnel, regions, languages, and messaging</li>
                        <li><strong>Specify Assets</strong> — Pick durations and sizes</li>
                        <li><strong>Generate!</strong> — Click the button to create your matrix</li>
                    </ol>
                </div>
                <div class="info-box info">
                    👈 Configure the options on the left, then click <strong>Generate Asset Matrix</strong> to create your naming convention spreadsheet.
                </div>
            </div>
            
            <div id="resultPanel" style="display: none;">
                <h2>📊 Your <span id="matrixTypeLabel">Social</span> Asset Matrix</h2>
                
                <div class="metrics-row">
                    <div class="metric-card">
                        <span class="metric-card-value" id="totalRows">0</span>
                        <span class="metric-card-label">Total Rows</span>
                    </div>
                    <div class="metric-card">
                        <span class="metric-card-value" id="sizeColumns">0</span>
                        <span class="metric-card-label">Size Columns</span>
                    </div>
                    <div class="metric-card">
                        <span class="metric-card-value">✓</span>
                        <span class="metric-card-label">Ready to Export</span>
                    </div>
                </div>
                
                <p class="caption">💡 <strong>Tip:</strong> Review the table below. All data is ready for download.</p>
                
                <div class="table-container">
                    <table id="matrixTable">
                        <thead></thead>
                        <tbody></tbody>
                    </table>
                </div>
                
                <div class="divider"></div>
                
                <div class="button-row">
                    <button id="copyBtn" class="btn btn-primary">📋 Copy to Clipboard</button>
                    <button id="downloadBtn" class="btn btn-primary">📥 Download as CSV</button>
                    <button id="clearBtn" class="btn btn-secondary">🗑️ Clear & Start Over</button>
                </div>
            </div>
        </main>
    </div>

    <script>{js}</script>
</body>
</html>
'''

st.markdown("""
<style>
    .stApp > header { display: none; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    iframe { border: none !important; }
</style>
""", unsafe_allow_html=True)

components.html(html_content, height=1200, scrolling=True)
