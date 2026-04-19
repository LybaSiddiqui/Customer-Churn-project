CSS = """
<style>
  .block-container { padding-top: 2rem; padding-bottom: 2rem; }

  .stTabs { margin-top: 10px; }
  .stTabs [data-baseweb="tab-list"] {
    gap: 4px; background: #1e293b; padding: 6px 8px;
    border-radius: 10px; border: 1px solid #2a3f5f; margin-bottom: 20px;
    flex-wrap: wrap;
  }
  .stTabs [data-baseweb="tab"] {
    color: #94a3b8 !important; background: transparent !important;
    border-radius: 7px !important; padding: 8px 16px !important;
    font-size: 13px !important; font-weight: 500 !important;
    height: auto !important; white-space: nowrap !important;
  }
  .stTabs [aria-selected="true"] {
    color: #ffffff !important; background: #2563eb !important; border-radius: 7px !important;
  }
  .stTabs [data-baseweb="tab"]:hover {
    color: #e2e8f0 !important; background: #334155 !important; border-radius: 7px !important;
  }
  .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display:none !important; }

  .kpi-card {
    background: #1e293b; border: 1px solid #2a3f5f;
    border-radius: 10px; padding: 18px 20px;
  }
  .kpi-label {
    font-size: 10px; color: #8fa3bd; text-transform: uppercase;
    letter-spacing: 0.08em; font-weight: 600; margin-bottom: 10px;
  }
  .kpi-value { font-size: 26px; font-weight: 700; line-height: 1; margin-bottom: 6px; font-family: monospace; }
  .kpi-sub   { font-size: 11px; color: #8fa3bd; }

  .query-badge {
    display:inline-flex; align-items:center; gap:5px; font-size:11px;
    color:#60a5fa; background:#1e3a5f; border:1px solid #2563eb40;
    border-radius:5px; padding:2px 8px; margin-bottom:6px; font-family:monospace;
  }
  .query-meta {
    font-size:12px; color:#8fa3bd; padding:8px 12px;
    background:#1e293b; border-left:3px solid;
    border-radius:0 6px 6px 0; margin-bottom:10px; line-height:1.6;
  }
  .static-note {
    font-size:12px; padding:10px 14px; background:#7c3aed20;
    border:1px solid #7c3aed40; border-radius:8px; color:#c4b5fd; margin-top:10px;
  }
  .section-bar { display:inline-block; width:5px; height:22px; border-radius:3px; margin-right:8px; vertical-align:middle; }

  .profile-card {
    background: #1e293b; border: 1px solid #2a3f5f;
    border-radius: 12px; padding: 24px; margin-bottom: 16px;
  }
  .profile-name { font-size: 22px; font-weight: 700; color: #e2e8f0; margin-bottom: 4px; }
  .profile-sub  { font-size: 13px; color: #8fa3bd; margin-bottom: 16px; }
  .profile-row  { display:flex; gap:24px; flex-wrap:wrap; }
  .profile-item { font-size:13px; }
  .profile-item span { color:#8fa3bd; }

  .alert-card {
    background:#1e293b; border-left:4px solid; border-radius:8px; padding:14px 16px; margin-bottom:10px;
  }
  .insight-card {
    background:#1e2d3d; border:1px solid #2a3f5f; border-radius:10px; padding:16px; margin-bottom:12px;
  }
</style>
"""