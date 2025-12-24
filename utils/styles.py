import streamlit as st

def apply_dark_theme():
    """Apply dark blue theme globally across all pages"""
    st.markdown("""
    <style>
    /* Main background gradient */
    .main {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* Text colors */
    h1, h2, h3, h4, h5, h6, p, label, span, div, li {
        color: #ffffff !important;
    }
    
    .stMarkdown {
        color: #ffffff !important;
    }
    
    /* Alert boxes - Lembut & Transparan */
    .stAlert {
        background-color: rgba(26, 58, 82, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: #ffffff !important;
        backdrop-filter: blur(10px);
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Metric cards - Lembut & Transparan */
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #cbd5e0 !important;
    }
    
    [data-testid="metric-container"] {
        background-color: rgba(26, 58, 82, 0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px;
        padding: 1rem;
        backdrop-filter: blur(8px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Buttons - Lembut */
    .stButton > button {
        background-color: rgba(26, 58, 82, 0.4) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 10px;
        backdrop-filter: blur(8px);
        transition: all 0.3s ease;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        background-color: rgba(26, 58, 82, 0.6) !important;
        border-color: rgba(255, 255, 255, 0.25) !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    
    /* Inputs - Lembut & Transparan */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {
        background-color: rgba(26, 58, 82, 0.25) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px;
        backdrop-filter: blur(8px);
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        background-color: rgba(26, 58, 82, 0.35) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        box-shadow: 0 0 0 2px rgba(26, 58, 82, 0.2);
    }
    
    /* Dataframes - Lembut & Transparan */
    .dataframe {
        background-color: rgba(26, 58, 82, 0.25) !important;
        color: #ffffff !important;
        border-radius: 10px;
        overflow: hidden;
    }
    
    .dataframe thead tr th {
        background-color: rgba(26, 58, 82, 0.4) !important;
        color: #ffffff !important;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    .dataframe tbody tr {
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    .dataframe tbody tr:hover {
        background-color: rgba(26, 58, 82, 0.35) !important;
    }
    
    [data-testid="stDataFrame"] {
        background-color: rgba(26, 58, 82, 0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px;
        backdrop-filter: blur(8px);
    }
    
    /* Tabs - Lembut */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(26, 58, 82, 0.2);
        border-radius: 10px;
        padding: 0.5rem;
        backdrop-filter: blur(8px);
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #cbd5e0 !important;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(26, 58, 82, 0.3);
        color: #ffffff !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: rgba(26, 58, 82, 0.5) !important;
        color: #ffffff !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Expander - Lembut */
    .streamlit-expanderHeader {
        background-color: rgba(26, 58, 82, 0.25) !important;
        color: #ffffff !important;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(8px);
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: rgba(26, 58, 82, 0.35) !important;
        border-color: rgba(255, 255, 255, 0.15);
    }
    
    .streamlit-expanderContent {
        background-color: rgba(22, 33, 62, 0.2) !important;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-top: none;
        border-radius: 0 0 10px 10px;
        backdrop-filter: blur(8px);
    }
    
    /* Progress bar - Lembut */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, rgba(26, 58, 82, 0.8), rgba(22, 33, 62, 0.9)) !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    /* File Uploader - Lembut */
    [data-testid="stFileUploadDropzone"] {
        background-color: rgba(26, 58, 82, 0.2) !important;
        border: 2px dashed rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px;
        backdrop-filter: blur(8px);
        transition: all 0.3s ease;
    }
    
    [data-testid="stFileUploadDropzone"]:hover {
        background-color: rgba(26, 58, 82, 0.3) !important;
        border-color: rgba(255, 255, 255, 0.25) !important;
    }
    
    /* Columns & Containers - Lembut */
    .element-container {
        color: #ffffff !important;
    }
    
    /* Code blocks - Lembut */
    code {
        background-color: rgba(26, 58, 82, 0.3) !important;
        color: #ffffff !important;
        padding: 3px 8px;
        border-radius: 6px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    pre {
        background-color: rgba(22, 33, 62, 0.3) !important;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 1rem;
        backdrop-filter: blur(8px);
    }
    
    /* Divider - Lembut */
    hr {
        border-color: rgba(255, 255, 255, 0.1) !important;
        opacity: 0.5;
    }
    
    /* Radio & Checkbox - Lembut */
    .stRadio > label, .stCheckbox > label {
        color: #ffffff !important;
    }
    
    /* Scrollbar - Lembut */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(22, 33, 62, 0.3);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(26, 58, 82, 0.5);
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(26, 58, 82, 0.7);
    }
    </style>
    """, unsafe_allow_html=True)


def get_chart_layout_config():
    """Return chart layout config"""
    return {
        'paper_bgcolor': 'rgba(26, 26, 46, 0.5)',
        'plot_bgcolor': 'rgba(22, 33, 62, 0.3)',
        'font_color': '#ffffff'
    }


def get_chart_color_scheme():
    """Return color scheme"""
    return {
        'primary': '#1a3a52',
        'secondary': '#16213e',
        'gradient': [[0, '#1a1a2e'], [0.5, '#16213e'], [1, '#1a3a52']]
    }
