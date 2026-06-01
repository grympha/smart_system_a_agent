from __future__ import annotations

import base64
import json
from io import BytesIO
from io import StringIO
from io import TextIOWrapper

from flask import Flask, Response, jsonify, render_template_string, request

from history_store import add_history, get_history_item, latest_history, malaysia_now_text, recent_history
from mt5_requests import consume_next_mt5_request, create_mt5_request
from smart_system_a.agent import SmartSystemAAgent
from smart_system_a.data_loader import DataLoader
from smart_system_a.image_input import ImageInputValidator
from smart_system_a.live_data import LiveXAUUSDFeed
from smart_system_a.models import AccountSettings, AnalysisSnapshot, NoSetupResult, RiskSettings, TradeSetup
from templates import ssa_template_csv, upas_template_csv
from upas import UPASAgent
from upas.models import UPASAnalysis, UPASInput


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024


PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Gold Smart Agent</title>
  <style>
    :root {
      color-scheme: dark;
      --ink: #f5f7fb;
      --muted: #9aa5b5;
      --line: #253244;
      --panel: #111827;
      --accent: #d4af37;
      --accent-ink: #15120a;
      --danger: #ff8a80;
      --ok: #76e4a6;
      --paper: #0b1220;
      --shell: #070b12;
    }
    * { box-sizing: border-box; }
    html {
      width: 100%;
      overflow-x: hidden;
    }
    body {
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: radial-gradient(circle at top left, #1d2636 0, #070b12 34%, #05070c 100%);
      width: 100%;
      overflow-x: hidden;
    }
    header {
      background: var(--paper);
      border-bottom: 1px solid var(--line);
      padding: 22px 30px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    .brand-block {
      display: grid;
      gap: 4px;
    }
    h1 {
      margin: 0;
      font-size: 24px;
      letter-spacing: 0;
    }
    .brand-subtitle {
      margin: 0;
      color: var(--muted);
      font-size: 13px;
    }
    .badge {
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 6px 10px;
      color: var(--accent);
      font-size: 13px;
      white-space: nowrap;
    }
    main {
      display: grid;
      grid-template-columns: minmax(320px, 420px) minmax(0, 1fr);
      min-height: calc(100vh - 67px);
      width: 100%;
      min-width: 0;
    }
    form {
      background: var(--paper);
      border-right: 1px solid var(--line);
      padding: 24px;
      min-width: 0;
    }
    fieldset {
      border: 0;
      padding: 0;
      margin: 0 0 22px;
    }
    legend {
      font-weight: 700;
      margin-bottom: 12px;
    }
    label {
      display: block;
      color: var(--muted);
      font-size: 13px;
      margin: 14px 0 6px;
    }
    input, select {
      width: 100%;
      max-width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px 11px;
      font-size: 14px;
      background: #0f1726;
      color: var(--ink);
    }
    input[type="file"] {
      min-width: 0;
      font-size: 13px;
      overflow: hidden;
    }
    input[type="checkbox"] {
      width: auto;
      margin-right: 8px;
    }
    .checkline {
      display: flex;
      align-items: center;
      color: var(--ink);
      margin-top: 14px;
    }
    button {
      width: 100%;
      border: 0;
      border-radius: 6px;
      padding: 12px 14px;
      background: var(--accent);
      color: var(--accent-ink);
      font-weight: 700;
      cursor: pointer;
    }
    .workspace {
      padding: 24px;
      display: grid;
      gap: 18px;
      align-content: start;
      min-width: 0;
    }
    .result, .panel {
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 20px;
      box-shadow: 0 18px 45px rgba(0, 0, 0, 0.28);
      min-width: 0;
    }
    .status {
      font-weight: 700;
      margin-bottom: 14px;
      color: var(--ok);
    }
    .status.no-setup { color: var(--danger); }
    .grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(120px, 1fr));
      gap: 10px;
      margin-bottom: 18px;
    }
    .metric {
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
      min-height: 68px;
      background: var(--panel);
      overflow-wrap: anywhere;
    }
    .metric span {
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 6px;
    }
    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      line-height: 1.45;
      font-family: Consolas, Monaco, monospace;
      font-size: 13px;
    }
    .muted { color: var(--muted); }
    .field-help {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 18px;
      height: 18px;
      margin-left: 6px;
      border: 1px solid var(--line);
      border-radius: 50%;
      color: var(--accent);
      font-size: 12px;
      cursor: help;
      position: relative;
    }
    .field-help:hover::after,
    .field-help:focus::after {
      content: attr(data-tip);
      position: absolute;
      left: 24px;
      top: -8px;
      z-index: 10;
      width: 310px;
      padding: 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #111827;
      color: var(--ink);
      line-height: 1.45;
      box-shadow: 0 14px 35px rgba(0, 0, 0, 0.35);
    }
    .dashboard {
      display: grid;
      gap: 14px;
    }
    .panel-title {
      margin: 0 0 10px;
      font-size: 15px;
    }
    .dashboard-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(220px, 1fr));
      gap: 14px;
    }
    .checklist {
      display: grid;
      gap: 8px;
      margin: 0;
      padding: 0;
      list-style: none;
    }
    .checklist li {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 9px 10px;
      background: var(--panel);
      min-width: 0;
    }
    .pill {
      border-radius: 999px;
      padding: 4px 8px;
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }
    .pill.pass { background: #dcfce7; color: var(--ok); }
    .pill.fail { background: #fee4e2; color: var(--danger); }
    .reasons {
      margin: 8px 0 0;
      padding-left: 18px;
      color: var(--muted);
      line-height: 1.45;
      font-size: 13px;
    }
    .summary-text {
      margin: 12px 0 0;
      line-height: 1.5;
      color: var(--ink);
    }
    .decision-summary {
      margin-top: 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px 20px;
      background: #0f1726;
    }
    .decision-summary h2 {
      margin: 0 0 14px;
      font-size: 15px;
    }
    .summary-list {
      display: grid;
      gap: 10px;
      margin: 0;
    }
    .summary-row {
      display: grid;
      grid-template-columns: 190px minmax(0, 1fr);
      gap: 14px;
      align-items: start;
      line-height: 1.45;
    }
    .summary-row dt {
      color: var(--muted);
      font-size: 13px;
    }
    .summary-row dd {
      margin: 0;
      overflow-wrap: anywhere;
    }
    .quick-actions {
      display: grid;
      gap: 8px;
      grid-template-columns: 1fr 1fr;
      margin-top: 12px;
    }
    .quick-actions a {
      display: block;
      text-align: center;
      text-decoration: none;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 9px 10px;
      color: var(--accent);
      background: #0f1726;
      font-size: 13px;
    }
    .why-panel {
      margin-top: 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px 20px;
      background: #111827;
    }
    .why-panel h2 {
      margin: 0 0 12px;
      font-size: 15px;
    }
    .why-list {
      display: grid;
      gap: 8px;
      margin: 0;
      padding: 0;
      list-style: none;
    }
    .why-list li {
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px;
      background: #0f1726;
      line-height: 1.45;
    }
    .image-preview {
      width: 100%;
      max-height: 360px;
      object-fit: contain;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #05070c;
    }
    .history-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    .history-table th,
    .history-table td {
      border-bottom: 1px solid var(--line);
      padding: 10px 8px;
      text-align: left;
      vertical-align: top;
      overflow-wrap: anywhere;
    }
    .history-table th {
      color: var(--muted);
      font-weight: 700;
    }
    footer {
      grid-column: 1 / -1;
      border-top: 1px solid var(--line);
      background: var(--paper);
      color: var(--muted);
      padding: 14px 30px;
      font-size: 13px;
    }
    .history-link {
      color: var(--accent);
      text-decoration: none;
      font-weight: 700;
    }
    .history-link:hover {
      text-decoration: underline;
    }
    body[data-source="live"] .csv-only {
      display: none;
    }
    details.raw-output {
      margin-top: 14px;
      border-top: 1px solid var(--line);
      padding-top: 12px;
    }
    details.raw-output summary {
      cursor: pointer;
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 10px;
    }
    @media (max-width: 860px) {
      main { grid-template-columns: 1fr; }
      form { border-right: 0; border-bottom: 1px solid var(--line); padding: 18px; }
      .workspace { padding: 16px; }
      .grid { grid-template-columns: 1fr; }
      .dashboard-grid { grid-template-columns: 1fr; }
      .summary-row { grid-template-columns: 1fr; gap: 4px; }
      .quick-actions { grid-template-columns: 1fr; }
      header { align-items: flex-start; flex-direction: column; }
    }
    @media (max-width: 640px) {
      header {
        padding: 18px 20px;
        gap: 10px;
      }
      h1 {
        font-size: 22px;
      }
      .badge {
        white-space: normal;
        line-height: 1.35;
      }
      form {
        padding: 16px 14px;
      }
      fieldset {
        margin-bottom: 18px;
      }
      label {
        margin-top: 12px;
      }
      input, select, button {
        min-height: 44px;
        font-size: 16px;
      }
      input[type="file"] {
        padding: 9px;
        font-size: 14px;
      }
      button {
        margin-top: 6px;
      }
      .workspace {
        padding: 14px;
        gap: 14px;
      }
      .result, .panel, .decision-summary, .why-panel {
        padding: 16px;
        border-radius: 8px;
      }
      .quick-actions {
        grid-template-columns: 1fr;
      }
      .quick-actions a {
        min-height: 42px;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      .field-help:hover::after,
      .field-help:focus::after {
        left: auto;
        right: -8px;
        top: 24px;
        width: min(280px, calc(100vw - 42px));
      }
      .checklist li {
        align-items: flex-start;
        flex-direction: column;
      }
      .pill {
        align-self: flex-start;
      }
      .history-table,
      .history-table thead,
      .history-table tbody,
      .history-table tr,
      .history-table td {
        display: block;
        width: 100%;
      }
      .history-table thead {
        display: none;
      }
      .history-table tr {
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--panel);
        margin-bottom: 12px;
        padding: 10px;
      }
      .history-table td {
        border: 0;
        padding: 8px 0;
      }
      .history-table td::before {
        content: attr(data-label);
        display: block;
        color: var(--muted);
        font-size: 12px;
        font-weight: 700;
        margin-bottom: 4px;
      }
      .history-table td:last-child {
        line-height: 1.45;
      }
      footer {
        padding: 14px 20px;
      }
    }
  </style>
</head>
<body>
  <header>
    <div class="brand-block">
      <h1>Gold Smart Agent</h1>
      <p class="brand-subtitle">Developed by Grympha</p>
    </div>
    <div class="badge">XAUUSD rule-based analysis only</div>
  </header>
  <main>
    <form method="post" enctype="multipart/form-data">
      <fieldset>
        <legend>Market Data</legend>
        <label for="analysis_system">Analysis System</label>
        <select id="analysis_system" name="analysis_system">
          <option value="ssa" {% if form.analysis_system == "ssa" %}selected{% endif %}>Smart System A</option>
          <option value="upas" {% if form.analysis_system == "upas" %}selected{% endif %}>UPAS Trade Assistant</option>
        </select>
        <label for="data_source">Data Source</label>
        <select id="data_source" name="data_source">
          <option value="csv" {% if form.data_source == "csv" %}selected{% endif %}>CSV Upload</option>
          <option value="live" {% if form.data_source == "live" %}selected{% endif %}>Live XAUUSD Feed</option>
          <option value="mt5" {% if form.data_source == "mt5" %}selected{% endif %}>MT5 Direct Mode</option>
        </select>
        <div class="csv-only">
          <label for="ohlc_data">OHLC Data <span class="field-help" tabindex="0" data-tip="Accepted CSV columns: timeframe,timestamp,open,high,low,close,volume. For Smart System A include H4 and H1 rows. For UPAS include MN1, W1, D1, H4, and H1 rows. Volume may be blank, but volume-based rules may fail.">!</span></label>
          <input id="ohlc_data" name="ohlc_data" type="file" accept=".csv">
          <div class="quick-actions">
            <a href="/templates/ssa.csv">SSA CSV Template</a>
            <a href="/templates/upas.csv">UPAS CSV Template</a>
          </div>
        </div>
        <label for="chart_image">Chart Screenshot</label>
        <input id="chart_image" name="chart_image" type="file" accept=".png,.jpg,.jpeg,.webp,image/png,image/jpeg,image/webp">
      </fieldset>
      <button type="submit">Run Analysis</button>
    </form>
    <section class="workspace">
      {% if error %}
        <div class="result">
          <div class="status no-setup">Input Error</div>
          <pre>{{ error }}</pre>
        </div>
      {% elif mt5_waiting %}
        <div class="result">
          {% if latest_mt5_results %}
            <div class="status">Latest MT5 Analysis</div>
            {% for item in latest_mt5_results %}
              <div class="decision-summary">
                <h2>Latest MT5 Result - {{ item.system_used }}</h2>
                <dl class="summary-list">
                  <div class="summary-row"><dt>Date / Time</dt><dd>{{ item.created_at }}</dd></div>
                  <div class="summary-row"><dt>Status</dt><dd>{{ item.status }}</dd></div>
                  <div class="summary-row"><dt>Setup</dt><dd>{{ item.setup_name }}</dd></div>
                  <div class="summary-row"><dt>Score</dt><dd>{{ item.score }}</dd></div>
                  <div class="summary-row"><dt>Summary</dt><dd>{{ item.summary }}</dd></div>
                </dl>
                <p><a class="history-link" href="/history/{{ item.id }}">Open full {{ item.system_used }} result</a></p>
              </div>
              {% if item.detail and item.detail.mt5_data_status %}
                <div class="panel">
                  <h2 class="panel-title">MT5 Data Status</h2>
                  <div class="grid">
                    <div class="metric"><span>Provider</span>{{ item.detail.mt5_data_status.provider }}</div>
                    <div class="metric"><span>Status</span>{{ item.detail.mt5_data_status.status }}</div>
                    <div class="metric"><span>Total Candle</span>{{ item.detail.mt5_data_status.total_candles }}</div>
                    <div class="metric"><span>Volume Data</span>{{ item.detail.mt5_data_status.volume_data }}</div>
                  </div>
                </div>
              {% endif %}
              {% if item.system_used == "Smart System A" and item.detail %}
                <div class="dashboard">
                  <div class="dashboard-grid">
                    <div class="panel">
                      <h2 class="panel-title">MT5 SSA H4 Trend And Wave</h2>
                      <div class="grid">
                        <div class="metric"><span>Trend</span>{{ item.detail.h4.trend }}</div>
                        <div class="metric"><span>Wave</span>{{ item.detail.h4.wave_context }}</div>
                        <div class="metric"><span>Active Wave</span>{{ item.detail.h4.active_wave or "Unclear" }}</div>
                        <div class="metric"><span>State</span>{{ item.detail.h4.market_state }}</div>
                      </div>
                    </div>
                    <div class="panel">
                      <h2 class="panel-title">MT5 SSA H1 Structure And Entry</h2>
                      <div class="grid">
                        <div class="metric"><span>BOS</span>{{ item.detail.h1.bos_direction }}</div>
                        <div class="metric"><span>BOS Level</span>{{ item.detail.h1.bos_level or "None" }}</div>
                        <div class="metric"><span>Breakout</span>{{ item.detail.h1.breakout_strength }}</div>
                        <div class="metric"><span>Entry Zone</span>{{ item.detail.h1.entry_zone or "Invalid" }}</div>
                      </div>
                    </div>
                  </div>
                  <div class="panel">
                    <h2 class="panel-title">MT5 SSA Checklist</h2>
                    <ul class="checklist">
                      <li><span>H4 trend aligned</span><span class="pill {{ 'pass' if item.detail.checklist.condition_1_h4_trend_aligned else 'fail' }}">{{ 'PASS' if item.detail.checklist.condition_1_h4_trend_aligned else 'FAIL' }}</span></li>
                      <li><span>Correct Elliott Wave position</span><span class="pill {{ 'pass' if item.detail.checklist.condition_2_wave_position_correct else 'fail' }}">{{ 'PASS' if item.detail.checklist.condition_2_wave_position_correct else 'FAIL' }}</span></li>
                      <li><span>Clean H1 breakout structure</span><span class="pill {{ 'pass' if item.detail.checklist.condition_3_clean_breakout else 'fail' }}">{{ 'PASS' if item.detail.checklist.condition_3_clean_breakout else 'FAIL' }}</span></li>
                      <li><span>Pullback reaches the correct SSA zone</span><span class="pill {{ 'pass' if item.detail.checklist.condition_4_pullback_reaches_zone else 'fail' }}">{{ 'PASS' if item.detail.checklist.condition_4_pullback_reaches_zone else 'FAIL' }}</span></li>
                      <li><span>Valid candle confirmation or rejection behavior</span><span class="pill {{ 'pass' if item.detail.checklist.condition_5_valid_candle_behavior else 'fail' }}">{{ 'PASS' if item.detail.checklist.condition_5_valid_candle_behavior else 'FAIL' }}</span></li>
                      <li><span>Volume supports direction</span><span class="pill {{ 'pass' if item.detail.checklist.condition_6_volume_supports_direction else 'fail' }}">{{ 'PASS' if item.detail.checklist.condition_6_volume_supports_direction else 'FAIL' }}</span></li>
                    </ul>
                  </div>
                </div>
              {% elif item.system_used == "UPAS Trade Assistant" and item.detail %}
                <div class="dashboard">
                  <div class="dashboard-grid">
                    <div class="panel">
                      <h2 class="panel-title">MT5 UPAS Market Bias</h2>
                      <div class="grid">
                        {% for tf, bias in item.detail.market_bias.items() %}
                          <div class="metric"><span>{{ tf }}</span>{{ bias or "n/a" }}</div>
                        {% endfor %}
                      </div>
                    </div>
                    <div class="panel">
                      <h2 class="panel-title">MT5 UPAS Setup</h2>
                      <div class="grid">
                        <div class="metric"><span>Name</span>{{ item.detail.setup.name }}</div>
                        <div class="metric"><span>Direction</span>{{ item.detail.setup.direction }}</div>
                        <div class="metric"><span>Score</span>{{ item.detail.setup.confluence_score }}/5</div>
                        <div class="metric"><span>Status</span>{{ item.detail.status }}</div>
                      </div>
                    </div>
                  </div>
                  <div class="panel">
                    <h2 class="panel-title">MT5 UPAS Confluence Checklist</h2>
                    <ul class="checklist">
                      {% for key, check in item.detail.setup.checklist.items() %}
                        <li>
                          <span>{{ key.replace('_', ' ').title() }} - {{ check.reason }}</span>
                          <span class="pill {{ 'pass' if check.passed else 'fail' }}">{{ 'PASS' if check.passed else 'FAIL' }}</span>
                        </li>
                      {% endfor %}
                    </ul>
                  </div>
                  <div class="panel">
                    <h2 class="panel-title">MT5 UPAS Trade Plan</h2>
                    <div class="grid">
                      {% for key, value in item.detail.trade_plan.items() %}
                        <div class="metric"><span>{{ key.replace('_', ' ').title() }}</span>{{ value if value is not none else "None" }}</div>
                      {% endfor %}
                    </div>
                  </div>
                </div>
              {% endif %}
            {% endfor %}
          {% else %}
            <div class="status">Waiting for MT5 data</div>
            <p class="muted">No MT5 push has been received yet.</p>
          {% endif %}
        </div>
      {% elif result %}
        <div class="result">
          {% if live_status %}
            <div class="panel">
              <h2 class="panel-title">Live Data Status</h2>
              <div class="grid">
                <div class="metric"><span>Provider</span>{{ live_status.provider }}</div>
                <div class="metric"><span>Status</span>{{ live_status.status }}</div>
                <div class="metric"><span>Last Candle</span>{{ live_status.last_candle_time }}</div>
                <div class="metric"><span>Total Candles</span>{{ live_status.total_candles }}</div>
                <div class="metric"><span>Volume Data</span>{{ live_status.volume_status }}</div>
              </div>
            </div>
          {% endif %}
          {% if image_preview %}
            <div class="panel">
              <h2 class="panel-title">Chart Screenshot Preview</h2>
              <img class="image-preview" src="{{ image_preview.data_url }}" alt="Uploaded chart screenshot preview">
            </div>
          {% endif %}
          {% if upas_analysis %}
            <div class="status {{ '' if upas_analysis.payload.status == 'VALID_TRADE' else 'no-setup' }}">{{ upas_analysis.payload.status }}</div>
            <div class="dashboard">
              <div class="dashboard-grid">
                <div class="panel">
                  <h2 class="panel-title">UPAS Market Bias</h2>
                  <div class="grid">
                    {% for tf, bias in upas_analysis.payload.market_bias.items() %}
                      <div class="metric"><span>{{ tf }}</span>{{ bias or "n/a" }}</div>
                    {% endfor %}
                  </div>
                </div>
                <div class="panel">
                  <h2 class="panel-title">UPAS Setup</h2>
                  <div class="grid">
                    <div class="metric"><span>Name</span>{{ upas_analysis.payload.setup.name }}</div>
                    <div class="metric"><span>Direction</span>{{ upas_analysis.payload.setup.direction }}</div>
                    <div class="metric"><span>Score</span>{{ upas_analysis.payload.setup.confluence_score }}/5</div>
                    <div class="metric"><span>Module</span>{{ upas_analysis.payload.module }}</div>
                  </div>
                </div>
              </div>
              <div class="panel">
                <h2 class="panel-title">UPAS Confluence Checklist</h2>
                <ul class="checklist">
                  {% for key, item in upas_analysis.payload.setup.checklist.items() %}
                    <li>
                      <span>{{ key.replace('_', ' ').title() }} - {{ item.reason }}</span>
                      <span class="pill {{ 'pass' if item.passed else 'fail' }}">{{ 'PASS' if item.passed else 'FAIL' }}</span>
                    </li>
                  {% endfor %}
                </ul>
              </div>
              <div class="panel">
                <h2 class="panel-title">UPAS Trade Plan</h2>
                <div class="grid">
                  {% for key, value in upas_analysis.payload.trade_plan.items() %}
                    <div class="metric"><span>{{ key.replace('_', ' ').title() }}</span>{{ value if value is not none else "None" }}</div>
                  {% endfor %}
                </div>
              </div>
            </div>
          {% elif is_trade %}
            <div class="status">Valid SSA Setup</div>
            <div class="grid">
              <div class="metric"><span>Setup</span>{{ result.setup_type }}</div>
              <div class="metric"><span>Entry</span>{{ result.entry }}</div>
              <div class="metric"><span>SL</span>{{ result.sl }}</div>
              <div class="metric"><span>Lot Size</span>{{ result.lot_size }}</div>
              <div class="metric"><span>TP1</span>{{ result.tp1 }}</div>
              <div class="metric"><span>TP2</span>{{ result.tp2 }}</div>
              <div class="metric"><span>Risk</span>{{ result.risk_percent }}%</div>
              <div class="metric"><span>Confidence</span>{{ result.confidence_level }}</div>
            </div>
          {% else %}
            <div class="status no-setup">No Setup</div>
          {% endif %}
          {% if snapshot %}
            <div class="dashboard">
              <div class="dashboard-grid">
                <div class="panel">
                  <h2 class="panel-title">H4 Trend And Wave</h2>
                  <div class="grid">
                    <div class="metric"><span>Trend</span>{{ snapshot.h4.trend.value }}</div>
                    <div class="metric"><span>Wave</span>{{ snapshot.h4.wave_context }}</div>
                    <div class="metric"><span>Active Wave</span>{{ snapshot.h4.active_wave or "Unclear" }}</div>
                    <div class="metric"><span>State</span>{{ snapshot.h4.market_state.value }}</div>
                  </div>
                  <ul class="reasons">
                    {% for reason in snapshot.h4.reasons %}
                      <li>{{ reason }}</li>
                    {% endfor %}
                  </ul>
                </div>
                <div class="panel">
                  <h2 class="panel-title">H1 Structure And Entry</h2>
                  <div class="grid">
                    <div class="metric"><span>BOS</span>{{ snapshot.h1.bos_direction.value }}</div>
                    <div class="metric"><span>BOS Level</span>{{ snapshot.h1.bos_level or "None" }}</div>
                    <div class="metric"><span>Breakout</span>{{ snapshot.h1.breakout_strength }}</div>
                    <div class="metric"><span>Entry Zone</span>{{ snapshot.h1.entry_zone or "Invalid" }}</div>
                  </div>
                  <ul class="reasons">
                    {% for reason in snapshot.h1.reasons %}
                      <li>{{ reason }}</li>
                    {% endfor %}
                    {% if not snapshot.h1.reasons %}
                      <li>H1 structure, pullback, candle behavior, and volume are aligned.</li>
                    {% endif %}
                  </ul>
                </div>
              </div>
              <div class="panel">
                <h2 class="panel-title">Six-Condition SSA Checklist</h2>
                <ul class="checklist">
                  {% for item in checklist_items %}
                    <li>
                      <span>{{ item.label }}</span>
                      <span class="pill {{ 'pass' if item.passed else 'fail' }}">{{ 'PASS' if item.passed else 'FAIL' }}</span>
                    </li>
                  {% endfor %}
                </ul>
              </div>
            </div>
          {% endif %}
          {% if summary_details %}
            <div class="decision-summary">
              <h2>Decision Summary</h2>
              <dl class="summary-list">
                {% for item in summary_details %}
                  <div class="summary-row">
                    <dt>{{ item.label }}</dt>
                    <dd>{{ item.value }}</dd>
                  </div>
                {% endfor %}
              </dl>
            </div>
          {% endif %}
          {% if why_no_trade %}
            <div class="why-panel">
              <h2>Why No Trade?</h2>
              <ul class="why-list">
                {% for item in why_no_trade %}
                  <li><strong>{{ item.title }}</strong><br>{{ item.detail }}</li>
                {% endfor %}
              </ul>
            </div>
          {% endif %}
          {% if upas_analysis or snapshot %}
            <details class="raw-output">
              <summary>View raw analysis output</summary>
              <pre>{{ output }}</pre>
            </details>
          {% else %}
            <pre>{{ output }}</pre>
          {% endif %}
        </div>
      {% elif image_result %}
        <div class="result">
          <div class="status no-setup">Image Accepted - No Setup</div>
          {% if image_preview %}
            <div class="panel">
              <h2 class="panel-title">Chart Screenshot Preview</h2>
              <img class="image-preview" src="{{ image_preview.data_url }}" alt="Uploaded chart screenshot preview">
            </div>
          {% endif %}
          <div class="grid">
            <div class="metric"><span>File</span>{{ image_result.filename }}</div>
            <div class="metric"><span>Format</span>{{ image_result.image_format }}</div>
            <div class="metric"><span>Width</span>{{ image_result.width }}</div>
            <div class="metric"><span>Height</span>{{ image_result.height }}</div>
          </div>
          <pre>{{ image_result.message }}</pre>
        </div>
      {% else %}
        <div class="panel">
          <strong>Choose an analysis system, then upload one OHLC CSV or use the live XAUUSD feed.</strong>
          <p class="muted">Smart System A requires H4 and H1 rows. UPAS requires MN1, W1, D1, H4, and H1 rows. Screenshots are accepted for intake only.</p>
        </div>
      {% endif %}
      {% if history %}
        <div class="panel">
          <h2 class="panel-title">Recent Analysis History</h2>
          <table class="history-table">
            <thead>
              <tr>
                <th>Date / Time</th>
                <th>System</th>
                <th>Status</th>
                <th>Setup</th>
                <th>Score</th>
                <th>Summary</th>
              </tr>
            </thead>
            <tbody>
              {% for row in history %}
                <tr>
                  <td data-label="Date / Time">{{ row.created_at }}</td>
                  <td data-label="System"><a class="history-link" href="/history/{{ row.id }}">{{ row.system_used }}</a></td>
                  <td data-label="Status">{{ row.status }}</td>
                  <td data-label="Setup">{{ row.setup_name }}</td>
                  <td data-label="Score">{{ row.score }}</td>
                  <td data-label="Summary">{{ row.summary }}</td>
                </tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      {% endif %}
    </section>
    <footer>© 2026 Grympha.</footer>
  </main>
  <script>
    const dataSource = document.getElementById("data_source");
    const syncSource = () => document.body.dataset.source = dataSource.value;
    dataSource.addEventListener("change", syncSource);
    syncSource();
  </script>
</body>
</html>
"""


def create_app() -> Flask:
    return app


@app.get("/templates/ssa.csv")
def download_ssa_template() -> Response:
    return Response(
        ssa_template_csv(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=ssa_ohlc_template.csv"},
    )


@app.get("/templates/upas.csv")
def download_upas_template() -> Response:
    return Response(
        upas_template_csv(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=upas_ohlc_template.csv"},
    )


@app.post("/api/analyze")
def api_analyze() -> Response:
    payload = request.get_json(silent=True) or {}
    analysis_system = (payload.get("analysis_system") or "ssa").lower()
    symbol = payload.get("symbol") or "XAUUSD"
    ohlc_csv = payload.get("ohlc_csv") or ""
    if not ohlc_csv:
        return jsonify({"status": "ERROR", "message": "ohlc_csv is required."}), 400

    try:
        multi = DataLoader().load_multi_timeframe_csv_stream(StringIO(ohlc_csv), symbol)
        if analysis_system == "upas":
            missing = [tf for tf in ["MN1", "W1", "D1", "H4", "H1"] if tf not in multi]
            if missing:
                raise ValueError(f"UPAS OHLC data missing timeframe rows: {', '.join(missing)}")
            upas_input = UPASInput(
                mn1=multi["MN1"],
                w1=multi["W1"],
                d1=multi["D1"],
                h4=multi["H4"],
                h1=multi["H1"],
            )
            upas_analysis = UPASAgent().analyze(upas_input)
            mt5_status = build_mt5_data_status([multi["MN1"], multi["W1"], multi["D1"], multi["H4"], multi["H1"]])
            save_upas_history(upas_analysis, source="mt5", mt5_data_status=mt5_status)
            return jsonify(
                {
                    "ok": True,
                    "analysis_system": "UPAS Trade Assistant",
                    "result": upas_analysis.payload,
                    "output": upas_analysis.summary,
                }
            )

        missing = [tf for tf in ["H4", "H1"] if tf not in multi]
        if missing:
            raise ValueError(f"Smart System A OHLC data missing timeframe rows: {', '.join(missing)}")
        agent = SmartSystemAAgent()
        snapshot = agent.analyze_with_snapshot(
            multi["H4"],
            multi["H1"],
            AccountSettings(balance=100000),
            RiskSettings(),
        )
        mt5_status = build_mt5_data_status([multi["H4"], multi["H1"]])
        save_ssa_history(snapshot, source="mt5", mt5_data_status=mt5_status)
        return jsonify(
            {
                "ok": True,
                "analysis_system": "Smart System A",
                "status": "VALID_TRADE" if isinstance(snapshot.result, TradeSetup) else "NO_TRADE",
                "output": agent.format_result(snapshot.result),
                "summary": build_ssa_summary(snapshot),
                "why_no_trade": build_ssa_why_no_trade(snapshot),
            }
        )
    except Exception as exc:
        return jsonify({"ok": False, "status": "ERROR", "message": str(exc)}), 400


@app.get("/api/ping")
def api_ping() -> Response:
    return jsonify({"ok": True, "status": "READY", "service": "Gold Smart Agent"})


@app.route("/", methods=["GET", "POST"])
def index():
    form = {
        "balance": request.form.get("balance", "100000"),
        "risk_mode": request.form.get("risk_mode", "standard"),
        "risk_percent": request.form.get("risk_percent", ""),
        "symbol": request.form.get("symbol", "XAU/USD"),
        "analysis_system": request.form.get("analysis_system", "ssa"),
        "data_source": request.form.get("data_source", "csv"),
        "volume_override": request.form.get("volume_override") == "on",
    }
    result = None
    output = None
    error = None
    is_trade = False
    image_result = None
    image_preview = None
    snapshot = None
    checklist_items = []
    upas_analysis = None
    summary_details = []
    why_no_trade = []
    live_status = None
    mt5_waiting = False
    latest_mt5_results = []
    requested_mt5_system = None

    if request.method == "POST":
        try:
            ohlc_file = request.files.get("ohlc_data")
            chart_image = request.files.get("chart_image")
            has_ohlc = bool(ohlc_file and ohlc_file.filename)
            has_image = bool(chart_image and chart_image.filename)
            image_bytes = None
            if has_image:
                image_bytes = chart_image.read()
                image_preview = build_image_preview(image_bytes, chart_image.mimetype or "image/png")

            risk_percent = float(form["risk_percent"]) if form["risk_percent"] else None
            settings = RiskSettings(
                risk_mode=form["risk_mode"],
                risk_percent=risk_percent or 0.9,
                volume_override=form["volume_override"],
            )

            if form["data_source"] == "mt5":
                mt5_waiting = True
                selected_system = "UPAS Trade Assistant" if form["analysis_system"] == "upas" else "Smart System A"
                requested_mt5_system = selected_system
                create_mt5_request(form["analysis_system"])
                latest = latest_history("mt5", selected_system)
                latest_mt5_results = [latest] if latest else []
            elif form["analysis_system"] == "upas":
                if form["data_source"] == "live":
                    mn1_data, w1_data, d1_data, h4_data, h1_data = LiveXAUUSDFeed().fetch_upas(form["symbol"])
                    live_status = build_live_status([mn1_data, w1_data, d1_data, h4_data, h1_data])
                elif has_ohlc:
                    loader = DataLoader()
                    multi = loader.load_multi_timeframe_csv_stream(TextIOWrapper(ohlc_file.stream, encoding="utf-8"), form["symbol"])
                    missing = [tf for tf in ["MN1", "W1", "D1", "H4", "H1"] if tf not in multi]
                    if missing:
                        raise ValueError(f"UPAS OHLC data missing timeframe rows: {', '.join(missing)}")
                    mn1_data = multi["MN1"]
                    w1_data = multi["W1"]
                    d1_data = multi["D1"]
                    h4_data = multi["H4"]
                    h1_data = multi["H1"]
                elif has_image:
                    image_result = ImageInputValidator().validate(BytesIO(image_bytes or b""), chart_image.filename)
                    mn1_data = w1_data = d1_data = h4_data = h1_data = None
                else:
                    error = "UPAS requires one OHLC CSV containing MN1, W1, D1, H4, and H1 rows, or live data mode."
                    mn1_data = w1_data = d1_data = h4_data = h1_data = None

                if all([mn1_data, w1_data, d1_data, h4_data, h1_data]):
                    upas_input = UPASInput(
                        mn1=mn1_data,
                        w1=w1_data,
                        d1=d1_data,
                        h4=h4_data,
                        h1=h1_data,
                        account_balance=float(form["balance"]),
                    )
                    upas_analysis = UPASAgent().analyze(upas_input)
                    result = upas_analysis.payload
                    output = upas_analysis.summary
                    summary_details = build_upas_summary(upas_analysis)
                    why_no_trade = build_upas_why_no_trade(upas_analysis)
                    save_upas_history(upas_analysis)
            elif form["data_source"] == "live":
                h4_data, h1_data = LiveXAUUSDFeed().fetch_h4_h1(form["symbol"])
                live_status = build_live_status([h4_data, h1_data])
                agent = SmartSystemAAgent()
                snapshot = agent.analyze_with_snapshot(h4_data, h1_data, AccountSettings(float(form["balance"])), settings)
                result = snapshot.result
                output = agent.format_result(result)
                checklist_items = build_checklist_items(snapshot)
                summary_details = build_ssa_summary(snapshot)
                why_no_trade = build_ssa_why_no_trade(snapshot)
                is_trade = isinstance(result, TradeSetup)
                if isinstance(result, NoSetupResult):
                    is_trade = False
                save_ssa_history(snapshot)
            elif has_ohlc:
                loader = DataLoader()
                multi = loader.load_multi_timeframe_csv_stream(TextIOWrapper(ohlc_file.stream, encoding="utf-8"), form["symbol"])
                missing = [tf for tf in ["H4", "H1"] if tf not in multi]
                if missing:
                    raise ValueError(f"Smart System A OHLC data missing timeframe rows: {', '.join(missing)}")
                h4_data = multi["H4"]
                h1_data = multi["H1"]
                agent = SmartSystemAAgent()
                snapshot = agent.analyze_with_snapshot(h4_data, h1_data, AccountSettings(float(form["balance"])), settings)
                result = snapshot.result
                output = agent.format_result(result)
                checklist_items = build_checklist_items(snapshot)
                summary_details = build_ssa_summary(snapshot)
                why_no_trade = build_ssa_why_no_trade(snapshot)
                is_trade = isinstance(result, TradeSetup)
                if isinstance(result, NoSetupResult):
                    is_trade = False
                save_ssa_history(snapshot)
            elif has_image:
                image_result = ImageInputValidator().validate(BytesIO(image_bytes or b""), chart_image.filename)
            else:
                error = "Upload one OHLC CSV file, use live data mode, or upload a chart screenshot for image intake."
        except Exception as exc:
            error = str(exc)

    return render_template_string(
        PAGE,
        form=form,
        result=result,
        output=output,
        error=error,
        is_trade=is_trade,
        image_result=image_result,
        image_preview=image_preview,
        snapshot=snapshot,
        checklist_items=checklist_items,
        upas_analysis=upas_analysis,
        summary_details=summary_details,
        why_no_trade=why_no_trade,
        live_status=live_status,
        history=recent_history(),
        mt5_waiting=mt5_waiting,
        latest_mt5_results=latest_mt5_results,
        requested_mt5_system=requested_mt5_system,
    )


@app.get("/history/<int:item_id>")
def history_detail(item_id: int) -> Response:
    item = get_history_item(item_id)
    if not item:
        return Response("History item not found.", status=404, mimetype="text/plain")
    return render_template_string(
        """
        <!doctype html>
        <html lang="en">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>Gold Smart Agent History</title>
          <style>{{ styles }}</style>
        </head>
        <body>
          <header>
            <h1>Gold Smart Agent</h1>
            <a class="badge" href="/">Back to dashboard</a>
          </header>
          <main style="display:block; min-height:calc(100vh - 67px);">
            <section class="workspace">
              <div class="result">
                <div class="status {{ '' if item.status == 'VALID_TRADE' else 'no-setup' }}">{{ item.status }}</div>
                <div class="decision-summary">
                  <h2>Analysis History Detail</h2>
                  <dl class="summary-list">
                    <div class="summary-row"><dt>Date / Time</dt><dd>{{ item.created_at }}</dd></div>
                    <div class="summary-row"><dt>System</dt><dd>{{ item.system_used }}</dd></div>
                    <div class="summary-row"><dt>Source</dt><dd>{{ item.source }}</dd></div>
                    <div class="summary-row"><dt>Setup</dt><dd>{{ item.setup_name }}</dd></div>
                    <div class="summary-row"><dt>Score</dt><dd>{{ item.score }}</dd></div>
                    <div class="summary-row"><dt>Summary</dt><dd>{{ item.summary }}</dd></div>
                  </dl>
                </div>
                {% if item.system_used == "Smart System A" and item.detail %}
                  <div class="dashboard">
                    <div class="dashboard-grid">
                      <div class="panel">
                        <h2 class="panel-title">H4 Trend And Wave</h2>
                        <div class="grid">
                          <div class="metric"><span>Trend</span>{{ item.detail.h4.trend }}</div>
                          <div class="metric"><span>Wave</span>{{ item.detail.h4.wave_context }}</div>
                          <div class="metric"><span>Active Wave</span>{{ item.detail.h4.active_wave or "Unclear" }}</div>
                          <div class="metric"><span>State</span>{{ item.detail.h4.market_state }}</div>
                        </div>
                      </div>
                      <div class="panel">
                        <h2 class="panel-title">H1 Structure And Entry</h2>
                        <div class="grid">
                          <div class="metric"><span>BOS</span>{{ item.detail.h1.bos_direction }}</div>
                          <div class="metric"><span>BOS Level</span>{{ item.detail.h1.bos_level or "None" }}</div>
                          <div class="metric"><span>Breakout</span>{{ item.detail.h1.breakout_strength }}</div>
                          <div class="metric"><span>Entry Zone</span>{{ item.detail.h1.entry_zone or "Invalid" }}</div>
                        </div>
                      </div>
                    </div>
                    <div class="panel">
                      <h2 class="panel-title">Six-Condition SSA Checklist</h2>
                      <ul class="checklist">
                        <li><span>H4 trend aligned</span><span class="pill {{ 'pass' if item.detail.checklist.condition_1_h4_trend_aligned else 'fail' }}">{{ 'PASS' if item.detail.checklist.condition_1_h4_trend_aligned else 'FAIL' }}</span></li>
                        <li><span>Correct Elliott Wave position</span><span class="pill {{ 'pass' if item.detail.checklist.condition_2_wave_position_correct else 'fail' }}">{{ 'PASS' if item.detail.checklist.condition_2_wave_position_correct else 'FAIL' }}</span></li>
                        <li><span>Clean H1 breakout structure</span><span class="pill {{ 'pass' if item.detail.checklist.condition_3_clean_breakout else 'fail' }}">{{ 'PASS' if item.detail.checklist.condition_3_clean_breakout else 'FAIL' }}</span></li>
                        <li><span>Pullback reaches the correct SSA zone</span><span class="pill {{ 'pass' if item.detail.checklist.condition_4_pullback_reaches_zone else 'fail' }}">{{ 'PASS' if item.detail.checklist.condition_4_pullback_reaches_zone else 'FAIL' }}</span></li>
                        <li><span>Valid candle confirmation or rejection behavior</span><span class="pill {{ 'pass' if item.detail.checklist.condition_5_valid_candle_behavior else 'fail' }}">{{ 'PASS' if item.detail.checklist.condition_5_valid_candle_behavior else 'FAIL' }}</span></li>
                        <li><span>Volume supports direction</span><span class="pill {{ 'pass' if item.detail.checklist.condition_6_volume_supports_direction else 'fail' }}">{{ 'PASS' if item.detail.checklist.condition_6_volume_supports_direction else 'FAIL' }}</span></li>
                      </ul>
                    </div>
                  </div>
                {% elif item.system_used == "UPAS Trade Assistant" and item.detail %}
                  <div class="dashboard">
                    {% if item.detail.mt5_data_status %}
                      <div class="panel">
                        <h2 class="panel-title">MT5 Data Status</h2>
                        <div class="grid">
                          <div class="metric"><span>Provider</span>{{ item.detail.mt5_data_status.provider }}</div>
                          <div class="metric"><span>Status</span>{{ item.detail.mt5_data_status.status }}</div>
                          <div class="metric"><span>Total Candle</span>{{ item.detail.mt5_data_status.total_candles }}</div>
                          <div class="metric"><span>Volume Data</span>{{ item.detail.mt5_data_status.volume_data }}</div>
                        </div>
                      </div>
                    {% endif %}
                    <div class="dashboard-grid">
                      <div class="panel">
                        <h2 class="panel-title">UPAS Market Bias</h2>
                        <div class="grid">
                          {% for tf, bias in item.detail.market_bias.items() %}
                            <div class="metric"><span>{{ tf }}</span>{{ bias or "n/a" }}</div>
                          {% endfor %}
                        </div>
                      </div>
                      <div class="panel">
                        <h2 class="panel-title">UPAS Setup</h2>
                        <div class="grid">
                          <div class="metric"><span>Name</span>{{ item.detail.setup.name }}</div>
                          <div class="metric"><span>Direction</span>{{ item.detail.setup.direction }}</div>
                          <div class="metric"><span>Score</span>{{ item.detail.setup.confluence_score }}/5</div>
                          <div class="metric"><span>Status</span>{{ item.detail.status }}</div>
                        </div>
                      </div>
                    </div>
                    <div class="panel">
                      <h2 class="panel-title">UPAS Confluence Checklist</h2>
                      <ul class="checklist">
                        {% for key, check in item.detail.setup.checklist.items() %}
                          <li>
                            <span>{{ key.replace('_', ' ').title() }} - {{ check.reason }}</span>
                            <span class="pill {{ 'pass' if check.passed else 'fail' }}">{{ 'PASS' if check.passed else 'FAIL' }}</span>
                          </li>
                        {% endfor %}
                      </ul>
                    </div>
                    <div class="panel">
                      <h2 class="panel-title">UPAS Trade Plan</h2>
                      <div class="grid">
                        {% for key, value in item.detail.trade_plan.items() %}
                          <div class="metric"><span>{{ key.replace('_', ' ').title() }}</span>{{ value if value is not none else "None" }}</div>
                        {% endfor %}
                      </div>
                    </div>
                  </div>
                {% endif %}
                {% if item.detail %}
                  <details class="raw-output">
                    <summary>Stored raw analysis detail</summary>
                    <pre>{{ detail_json }}</pre>
                  </details>
                {% endif %}
                {% if item.raw_output %}
                  <details class="raw-output">
                    <summary>Raw analysis output</summary>
                    <pre>{{ item.raw_output }}</pre>
                  </details>
                {% endif %}
              </div>
            </section>
          </main>
        </body>
        </html>
        """,
        styles=extract_page_styles(),
        item=item,
        detail_json=json.dumps(item["detail"], indent=2),
    )


@app.get("/api/mt5/next-request")
def api_mt5_next_request() -> Response:
    request_item = consume_next_mt5_request()
    if not request_item:
        return Response("none", mimetype="text/plain")
    return Response(str(request_item["analysis_system"]), mimetype="text/plain")


def build_checklist_items(snapshot: AnalysisSnapshot) -> list[dict[str, object]]:
    checklist = snapshot.checklist
    return [
        {"label": "H4 trend aligned", "passed": checklist.condition_1_h4_trend_aligned},
        {"label": "Correct Elliott Wave position", "passed": checklist.condition_2_wave_position_correct},
        {"label": "Clean H1 breakout structure", "passed": checklist.condition_3_clean_breakout},
        {"label": "Pullback reaches the correct SSA zone", "passed": checklist.condition_4_pullback_reaches_zone},
        {"label": "Valid candle confirmation or rejection behavior", "passed": checklist.condition_5_valid_candle_behavior},
        {"label": "Volume supports direction", "passed": checklist.condition_6_volume_supports_direction},
    ]


def build_ssa_summary(snapshot: AnalysisSnapshot) -> list[dict[str, object]]:
    result = snapshot.result
    if isinstance(result, NoSetupResult):
        return [
            {"label": "Decision", "value": "No setup"},
            {"label": "Failed Rules", "value": "; ".join(result.failed_rules)},
            {"label": "H4 Wave Position", "value": result.h4_wave_position},
            {"label": "Active Wave", "value": result.active_wave if result.active_wave is not None else "Unidentifiable"},
            {"label": "Market State", "value": result.market_state.value},
            {"label": "Next Requirement", "value": result.what_next},
            {"label": "Reasoning", "value": result.reasoning_summary},
        ]
    return [
        {"label": "Decision", "value": "Valid setup"},
        {"label": "Setup Type", "value": result.setup_type},
        {"label": "Entry / SL / TP", "value": f"{result.entry} / {result.sl} / {result.tp1}, {result.tp2}"},
        {"label": "Risk And Lot", "value": f"{result.risk_percent}% risk, {result.lot_size} lots"},
        {"label": "Confidence", "value": result.confidence_level},
        {"label": "Reasoning", "value": result.reasoning_summary},
    ]


def build_upas_summary(upas_analysis: UPASAnalysis) -> list[dict[str, object]]:
    payload = upas_analysis.payload
    failed = [
        key.replace("_", " ").title()
        for key, item in payload["setup"]["checklist"].items()
        if not item["passed"]
    ]
    details = [
        {"label": "Decision", "value": payload["status"]},
        {"label": "Setup", "value": f"{payload['setup']['name']} {payload['setup']['direction']}"},
        {"label": "Confluence Score", "value": f"{payload['setup']['confluence_score']}/5"},
        {"label": "Failed Conditions", "value": "; ".join(failed) if failed else "None"},
        {"label": "Reasoning", "value": payload["reasoning"]},
        {"label": "Summary", "value": payload["summary"]},
    ]
    if payload["invalidation"]:
        details.append({"label": "Invalidation", "value": payload["invalidation"]})
    return details


def build_ssa_why_no_trade(snapshot: AnalysisSnapshot) -> list[dict[str, str]]:
    if isinstance(snapshot.result, TradeSetup):
        return []
    failed = set(snapshot.result.failed_rules)
    details = []
    rule_guidance = {
        "H4 trend aligned": "Wait for H4 trend and H1 BOS to point in the same direction.",
        "Correct Elliott Wave position, preferably Wave 3 or Wave 5 continuation": "Wait for a clearer H4 Wave 3 or Wave 5 continuation context.",
        "Clean H1 breakout structure": "Wait for a clean H1 close beyond structure with displacement and limited wick rejection.",
        "Pullback reaches the correct SSA zone": "Wait for price to retest broken structure and hold the valid SSA zone.",
        "Valid candle confirmation or rejection behavior": "Wait for a rejection or confirmation candle from the retest zone.",
        "Volume supports direction": "Use OHLCV data with volume expansion, or wait for impulse volume to exceed pullback volume.",
    }
    for rule in failed:
        details.append({"title": rule, "detail": rule_guidance.get(rule, "Wait for this SSA condition to pass.")})
    return details


def build_upas_why_no_trade(upas_analysis: UPASAnalysis) -> list[dict[str, str]]:
    payload = upas_analysis.payload
    if payload["status"] == "VALID_TRADE":
        return []
    details = []
    for key, item in payload["setup"]["checklist"].items():
        if not item["passed"]:
            title = key.replace("_", " ").title()
            details.append({"title": title, "detail": item["reason"]})
    if payload["reasoning"]:
        details.append({"title": "Next Requirement", "detail": payload["reasoning"]})
    return details


def build_image_preview(image_bytes: bytes, mimetype: str) -> dict[str, str]:
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return {"data_url": f"data:{mimetype};base64,{encoded}"}


def build_live_status(datasets: list[object]) -> dict[str, object]:
    candles = [candle for data in datasets for candle in data.candles]
    last_candle_time = candles[-1].timestamp if candles else "n/a"
    volume_present = bool(candles) and all(candle.volume is not None for candle in candles)
    timeframe_counts = ", ".join(f"{data.timeframe}: {len(data.candles)}" for data in datasets)
    return {
        "provider": "Twelve Data",
        "status": "Loaded",
        "last_candle_time": last_candle_time,
        "total_candles": f"{len(candles)} ({timeframe_counts})",
        "volume_status": "Present" if volume_present else "Missing or partial",
    }


def save_ssa_history(
    snapshot: AnalysisSnapshot,
    source: str = "web",
    mt5_data_status: dict[str, object] | None = None,
) -> None:
    result = snapshot.result
    if isinstance(result, TradeSetup):
        status = "VALID_TRADE"
        setup_name = result.setup_type
        score = "6/6"
        summary = result.reasoning_summary
        raw_output = SmartSystemAAgent().format_result(result)
    else:
        status = "NO_TRADE"
        setup_name = "None"
        score = f"{6 - len(result.failed_rules)}/6"
        summary = result.reasoning_summary
        raw_output = SmartSystemAAgent().format_result(result)
    detail = {
        "h4": snapshot.h4.__dict__,
        "h1": snapshot.h1.__dict__,
        "checklist": snapshot.checklist.__dict__,
        "decision_summary": build_ssa_summary(snapshot),
        "why_no_trade": build_ssa_why_no_trade(snapshot),
    }
    if mt5_data_status:
        detail["mt5_data_status"] = mt5_data_status
    add_history("Smart System A", status, setup_name, score, summary, source=source, detail=detail, raw_output=raw_output)


def save_upas_history(
    upas_analysis: UPASAnalysis,
    source: str = "web",
    mt5_data_status: dict[str, object] | None = None,
) -> None:
    payload = upas_analysis.payload
    detail = dict(payload)
    if mt5_data_status:
        detail["mt5_data_status"] = mt5_data_status
    add_history(
        "UPAS Trade Assistant",
        payload["status"],
        payload["setup"]["name"],
        f"{payload['setup']['confluence_score']}/5",
        payload["summary"],
        source=source,
        detail=detail,
        raw_output=upas_analysis.summary,
    )


def build_mt5_data_status(datasets: list[object]) -> dict[str, object]:
    candles = [candle for data in datasets for candle in data.candles]
    timeframe_counts = ", ".join(f"{data.timeframe}: {len(data.candles)}" for data in datasets)
    volume_present = bool(candles) and all(candle.volume is not None for candle in candles)
    return {
        "provider": "Roboforex",
        "status": malaysia_now_text(),
        "total_candles": f"{len(candles)} ({timeframe_counts})",
        "volume_data": "Present" if volume_present else "Missing or partial",
    }


def extract_page_styles() -> str:
    start = PAGE.find("<style>")
    end = PAGE.find("</style>")
    if start == -1 or end == -1:
        return ""
    return PAGE[start + len("<style>"):end]


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False)
