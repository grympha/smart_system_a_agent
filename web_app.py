from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from io import BytesIO
from io import StringIO
from io import TextIOWrapper

from flask import Flask, Response, jsonify, render_template_string, request

from history_store import add_history, get_history_item, latest_history, malaysia_now_text, recent_history
from mt5_requests import consume_next_mt5_request, create_mt5_request
from screenshot_store import add_chart_screenshot, get_chart_screenshot, latest_chart_screenshot, screenshot_bytes
from smart_system_a.agent import SmartSystemAAgent
from smart_system_a.data_loader import DataLoader
from smart_system_a.image_input import ImageInputValidator
from smart_system_a.live_data import LiveXAUUSDFeed
from smart_system_a.models import AccountSettings, AnalysisSnapshot, NoSetupResult, RiskSettings, TradeSetup
from templates import ssa_template_csv, upas_template_csv, wave_template_csv
from upas import UPASAgent
from upas.models import UPASAnalysis, UPASInput
from wave_structure import WaveAnalysisInput, WaveAnalysisResult, WaveStructureAnalyst


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


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
          <option value="wave" {% if form.analysis_system == "wave" %}selected{% endif %}>Wave Structure Analyst</option>
        </select>
        <label for="data_source">Data Source</label>
        <select id="data_source" name="data_source">
          <option value="csv" {% if form.data_source == "csv" %}selected{% endif %}>CSV Upload</option>
          <option value="live" {% if form.data_source == "live" %}selected{% endif %}>Live XAUUSD Feed</option>
          <option value="mt5" {% if form.data_source == "mt5" %}selected{% endif %}>MT5 Direct Mode</option>
        </select>
        <div class="csv-only">
          <label for="ohlc_data">OHLC Data <span class="field-help" tabindex="0" data-tip="Accepted CSV columns: timeframe,timestamp,open,high,low,close,volume. Smart System A: H4/H1. UPAS: MN1/W1/D1/H4/H1. Wave Structure Analyst: H4/H1, optional D1/M30/M15.">!</span></label>
          <input id="ohlc_data" name="ohlc_data" type="file" accept=".csv">
          <div class="quick-actions">
            <a href="/templates/ssa.csv">SSA CSV Template</a>
            <a href="/templates/upas.csv">UPAS CSV Template</a>
            <a href="/templates/wave.csv">Wave CSV Template</a>
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
              {% if item.detail and item.detail.market_snapshot %}
                <div class="panel">
                  <h2 class="panel-title">Market Snapshot</h2>
                  <div class="grid">
                    <div class="metric"><span>Current Price</span>{{ item.detail.market_snapshot.current_price }}</div>
                    <div class="metric"><span>Chart Available</span>{{ item.detail.market_snapshot.chart_available }}</div>
                    <div class="metric"><span>Last Chart Update</span>{{ item.detail.market_snapshot.last_chart_update }}</div>
                  </div>
                </div>
              {% endif %}
              {% if item.detail and item.detail.chart_snapshot %}
                <div class="panel">
                  <h2 class="panel-title">Latest Chart Preview</h2>
                  <a href="{{ item.detail.chart_snapshot.image_url }}" target="_blank">
                    <img class="image-preview" src="{{ item.detail.chart_snapshot.image_url }}" alt="Latest chart screenshot preview">
                  </a>
                  <div class="grid">
                    <div class="metric"><span>Symbol</span>{{ item.detail.chart_snapshot.symbol }}</div>
                    <div class="metric"><span>Timeframe</span>{{ item.detail.chart_snapshot.metadata.timeframe or "H1" }}</div>
                    <div class="metric"><span>Timestamp</span>{{ item.detail.chart_snapshot.market_timestamp }}</div>
                  </div>
                </div>
              {% endif %}
              {% if item.detail and item.detail.trade_plan and item.detail.trade_plan.action %}
                <div class="panel">
                  <h2 class="panel-title">Trade Plan</h2>
                  <div class="grid">
                    <div class="metric"><span>Action</span>{{ item.detail.trade_plan.action }}</div>
                    <div class="metric"><span>Entry Point</span>{{ item.detail.trade_plan.entry_point }}</div>
                    <div class="metric"><span>Take Profit</span>{{ item.detail.trade_plan.take_profit }}</div>
                    <div class="metric"><span>Stop Loss</span>{{ item.detail.trade_plan.stop_loss }}</div>
                  </div>
                </div>
              {% elif item.detail and item.detail.trade_plan_display and item.detail.trade_plan_display.action %}
                <div class="panel">
                  <h2 class="panel-title">Trade Plan</h2>
                  <div class="grid">
                    <div class="metric"><span>Action</span>{{ item.detail.trade_plan_display.action }}</div>
                    <div class="metric"><span>Entry Point</span>{{ item.detail.trade_plan_display.entry_point }}</div>
                    <div class="metric"><span>Take Profit</span>{{ item.detail.trade_plan_display.take_profit }}</div>
                    <div class="metric"><span>Stop Loss</span>{{ item.detail.trade_plan_display.stop_loss }}</div>
                  </div>
                </div>
              {% endif %}
              {% if item.system_used == "Wave Structure Analyst" and item.detail %}
                <div class="dashboard">
                  {% if item.detail.timeframe_results %}
                    <div class="panel">
                      <h2 class="panel-title">MT5 Wave Timeframe Results</h2>
                      <div class="grid">
                        {% for tf, wave in item.detail.timeframe_results.items() %}
                          <div class="metric"><span>{{ tf }}</span>{{ wave.status }} - {{ wave.trading_bias }} - {{ wave.wave_score }}/10</div>
                        {% endfor %}
                      </div>
                    </div>
                  {% endif %}
                  <div class="panel">
                    <h2 class="panel-title">MT5 Wave Structure Analyst Result</h2>
                    <div class="grid">
                      <div class="metric"><span>Timeframe</span>{{ item.detail.timeframe }}</div>
                      <div class="metric"><span>Market Phase</span>{{ item.detail.market_phase }}</div>
                      <div class="metric"><span>Primary Scenario</span>{{ item.detail.primary_scenario }}</div>
                      <div class="metric"><span>Direction</span>{{ item.detail.direction }}</div>
                      <div class="metric"><span>Wave Score</span>{{ item.detail.wave_score }}/10</div>
                      <div class="metric"><span>Trading Bias</span>{{ item.detail.trading_bias }}</div>
                    </div>
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
                  {% if item.detail.trade_plan_display %}
                    <div class="panel">
                      <h2 class="panel-title">MT5 UPAS Trade Plan</h2>
                      <div class="grid">
                        {% for key, value in item.detail.trade_plan.items() %}
                          <div class="metric"><span>{{ key.replace('_', ' ').title() }}</span>{{ value if value is not none else "None" }}</div>
                        {% endfor %}
                      </div>
                    </div>
                  {% endif %}
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
          {% if market_snapshot %}
            <div class="panel">
              <h2 class="panel-title">Market Snapshot</h2>
              <div class="grid">
                <div class="metric"><span>Current Price</span>{{ market_snapshot.current_price }}</div>
                <div class="metric"><span>Chart Available</span>{{ market_snapshot.chart_available }}</div>
                <div class="metric"><span>Last Chart Update</span>{{ market_snapshot.last_chart_update }}</div>
              </div>
            </div>
          {% endif %}
          {% if chart_snapshot %}
            <div class="panel">
              <h2 class="panel-title">Latest Chart Preview</h2>
              <a href="{{ chart_snapshot.image_url }}" target="_blank">
                <img class="image-preview" src="{{ chart_snapshot.image_url }}" alt="Latest chart screenshot preview">
              </a>
              <div class="grid">
                <div class="metric"><span>Symbol</span>{{ chart_snapshot.symbol }}</div>
                <div class="metric"><span>Timeframe</span>{{ chart_snapshot.metadata.timeframe or "H1" }}</div>
                <div class="metric"><span>Timestamp</span>{{ chart_snapshot.market_timestamp }}</div>
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
            {% if trade_plan %}
              <div class="panel">
                <h2 class="panel-title">Trade Plan</h2>
                <div class="grid">
                  <div class="metric"><span>Action</span>{{ trade_plan.action }}</div>
                  <div class="metric"><span>Entry Point</span>{{ trade_plan.entry_point }}</div>
                  <div class="metric"><span>Take Profit</span>{{ trade_plan.take_profit }}</div>
                  <div class="metric"><span>Stop Loss</span>{{ trade_plan.stop_loss }}</div>
                </div>
              </div>
            {% endif %}
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
              {% if trade_plan %}
                <div class="panel">
                  <h2 class="panel-title">UPAS Trade Plan</h2>
                  <div class="grid">
                    {% for key, value in upas_analysis.payload.trade_plan.items() %}
                      <div class="metric"><span>{{ key.replace('_', ' ').title() }}</span>{{ value if value is not none else "None" }}</div>
                    {% endfor %}
                  </div>
                </div>
              {% endif %}
            </div>
          {% elif wave_analysis %}
            <div class="status {{ '' if wave_analysis.status == 'WAVE_CONFIRMED' else 'no-setup' }}">{{ wave_analysis.status }}</div>
            <div class="dashboard">
              {% if wave_results %}
                <div class="panel">
                  <h2 class="panel-title">Wave Structure Results</h2>
                  <div class="dashboard-grid">
                    {% for tf, wave in wave_results.items() %}
                      <div class="panel">
                        <h2 class="panel-title">{{ tf }} Result</h2>
                        <div class="grid">
                          <div class="metric"><span>Status</span>{{ wave.status }}</div>
                          <div class="metric"><span>Market Phase</span>{{ wave.market_phase }}</div>
                          <div class="metric"><span>Primary Scenario</span>{{ wave.primary_scenario }}</div>
                          <div class="metric"><span>Direction</span>{{ wave.direction }}</div>
                          <div class="metric"><span>Wave Score</span>{{ wave.wave_score }}/10</div>
                          <div class="metric"><span>Trading Bias</span>{{ wave.trading_bias }}</div>
                          <div class="metric"><span>Pullback Zone</span>{{ wave.entry_zone if wave.entry_zone is not none else "None" }}</div>
                          <div class="metric"><span>Invalidation Level</span>{{ wave.invalidation_level if wave.invalidation_level is not none else "None" }}</div>
                          <div class="metric"><span>Suggested Action</span>{{ wave.suggested_action }}</div>
                        </div>
                      </div>
                    {% endfor %}
                  </div>
                </div>
              {% endif %}
              {% if trade_plan %}
                <div class="panel">
                  <h2 class="panel-title">Trade Plan</h2>
                  <div class="grid">
                    <div class="metric"><span>Action</span>{{ trade_plan.action }}</div>
                    <div class="metric"><span>Entry Point</span>{{ trade_plan.entry_point }}</div>
                    <div class="metric"><span>Take Profit</span>{{ trade_plan.take_profit }}</div>
                    <div class="metric"><span>Stop Loss</span>{{ trade_plan.stop_loss }}</div>
                  </div>
                </div>
              {% endif %}
              <div class="decision-summary">
                <h2>Wave Decision Summary</h2>
                <dl class="summary-list">
                  {% for item in summary_details %}
                    <div class="summary-row">
                      <dt>{{ item.label }}</dt>
                      <dd>{{ item.value }}</dd>
                    </div>
                  {% endfor %}
                </dl>
              </div>
              {% if wave_analysis.failed_rules %}
                <div class="why-panel">
                  <h2>Why Wait?</h2>
                  <ul class="why-list">
                    {% for rule in wave_analysis.failed_rules %}
                      <li>{{ rule }}</li>
                    {% endfor %}
                  </ul>
                </div>
              {% endif %}
            </div>
          {% elif is_trade %}
            <div class="status">Valid SSA Setup</div>
            {% if trade_plan %}
              <div class="panel">
                <h2 class="panel-title">Trade Plan</h2>
                <div class="grid">
                  <div class="metric"><span>Action</span>{{ trade_plan.action }}</div>
                  <div class="metric"><span>Entry Point</span>{{ trade_plan.entry_point }}</div>
                  <div class="metric"><span>Take Profit</span>{{ trade_plan.take_profit }}</div>
                  <div class="metric"><span>Stop Loss</span>{{ trade_plan.stop_loss }}</div>
                </div>
              </div>
            {% endif %}
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
          {% if upas_analysis or snapshot or wave_analysis %}
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
          <p class="muted">Smart System A requires H4 and H1 rows. UPAS requires MN1, W1, D1, H4, and H1 rows. Wave Structure Analyst requires H4 or H1 rows and supports optional D1, M30, and M15 context.</p>
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


@app.get("/templates/wave.csv")
def download_wave_template() -> Response:
    return Response(
        wave_template_csv(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=wave_structure_ohlc_template.csv"},
    )


@app.get("/screenshots/<int:screenshot_id>")
def chart_screenshot(screenshot_id: int) -> Response:
    item = get_chart_screenshot(screenshot_id)
    if not item:
        return Response("Screenshot not found.", status=404, mimetype="text/plain")
    return Response(
        screenshot_bytes(item),
        mimetype=item["mime_type"],
        headers={"Content-Disposition": f"inline; filename={item['filename']}"},
    )


def intake_market_context(payload: dict[str, object], analysis_system: str, symbol: str) -> tuple[dict[str, object], dict[str, object] | None]:
    current_price = payload.get("current_price")
    timestamp = str(payload.get("timestamp") or malaysia_now_text())
    chart_image = str(payload.get("chart_image") or "")
    chart_snapshot = None
    if chart_image:
        chart_snapshot = add_chart_screenshot(
            symbol=symbol,
            analysis_system=display_system_name(analysis_system),
            market_timestamp=timestamp,
            current_price=current_price,
            filename=str(payload.get("chart_filename") or f"{symbol}_{analysis_system}_chart.png"),
            image_base64=chart_image,
            mime_type=str(payload.get("chart_mime_type") or "image/png"),
            image_source="mt5_api",
            metadata={
                "timeframe": payload.get("chart_timeframe") or "H1",
                "future_ai_ready": {
                    "elliott_wave_recognition": False,
                    "snr_detection": False,
                    "trendline_detection": False,
                    "breakout_detection": False,
                    "candlestick_pattern_detection": False,
                    "price_action_validation": False,
                },
            },
        )
    market_snapshot = build_market_snapshot(current_price, timestamp, chart_snapshot)
    return market_snapshot, chart_snapshot


def parse_optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@app.post("/api/analyze")
def api_analyze() -> Response:
    payload = request.get_json(silent=True) or {}
    analysis_system = (payload.get("analysis_system") or "ssa").lower()
    symbol = payload.get("symbol") or "XAUUSD"
    ohlc_csv = payload.get("ohlc_csv") or ""
    if not ohlc_csv:
        return jsonify({"status": "ERROR", "message": "ohlc_csv is required."}), 400

    try:
        market_snapshot, chart_snapshot = intake_market_context(payload, analysis_system, symbol)
        multi = DataLoader().load_multi_timeframe_csv_stream(StringIO(ohlc_csv), symbol)
        if analysis_system == "wave":
            wave_results = analyze_wave_results_from_multi(multi, current_price=parse_optional_float(payload.get("current_price")))
            wave = primary_wave_result(wave_results)
            trade_plan = build_wave_trade_plan(wave, multi[wave.timeframe].candles[-1].close)
            trade_plans = build_wave_trade_plans(wave_results, multi)
            save_wave_history(wave, source="mt5", mt5_data_status=build_mt5_data_status([data for tf, data in multi.items() if tf in {"H4", "H1"}]), trade_plan=trade_plan, related_results=wave_results, market_snapshot=market_snapshot, chart_snapshot=chart_snapshot)
            return jsonify(
                {
                    "ok": True,
                    "analysis_system": "Wave Structure Analyst",
                    "market_snapshot": market_snapshot,
                    "chart_snapshot": chart_snapshot,
                    "status": wave.status,
                    "result": wave.__dict__,
                    "results": {timeframe: result.__dict__ for timeframe, result in wave_results.items()},
                    "primary_timeframe": wave.timeframe,
                    "trade_plan": trade_plan,
                    "trade_plans": trade_plans,
                    "output": format_wave_result(wave),
                    "summary": build_wave_summary(wave, trade_plan),
                }
            )
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
            trade_plan = build_upas_trade_plan(upas_analysis)
            mt5_status = build_mt5_data_status([multi["MN1"], multi["W1"], multi["D1"], multi["H4"], multi["H1"]])
            save_upas_history(upas_analysis, source="mt5", mt5_data_status=mt5_status, market_snapshot=market_snapshot, chart_snapshot=chart_snapshot)
            return jsonify(
                {
                    "ok": True,
                    "analysis_system": "UPAS Trade Assistant",
                    "market_snapshot": market_snapshot,
                    "chart_snapshot": chart_snapshot,
                    "result": upas_analysis.payload,
                    "trade_plan": trade_plan,
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
        trade_plan = build_ssa_trade_plan(snapshot)
        save_ssa_history(snapshot, source="mt5", mt5_data_status=mt5_status, market_snapshot=market_snapshot, chart_snapshot=chart_snapshot)
        return jsonify(
            {
                "ok": True,
                "analysis_system": "Smart System A",
                "market_snapshot": market_snapshot,
                "chart_snapshot": chart_snapshot,
                "status": "VALID_TRADE" if isinstance(snapshot.result, TradeSetup) else "NO_TRADE",
                "trade_plan": trade_plan,
                "output": agent.format_result(snapshot.result),
                "summary": build_ssa_summary(snapshot, trade_plan),
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
    wave_analysis = None
    wave_results = {}
    trade_plan = None
    summary_details = []
    why_no_trade = []
    live_status = None
    market_snapshot = None
    chart_snapshot = None
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
                if has_ohlc:
                    chart_snapshot = add_chart_screenshot(
                        symbol=form["symbol"],
                        analysis_system=display_system_name(form["analysis_system"]),
                        market_timestamp=malaysia_now_text(),
                        current_price=None,
                        filename=chart_image.filename,
                        image_base64=base64.b64encode(image_bytes).decode("ascii"),
                        mime_type=chart_image.mimetype or "image/png",
                        image_source="web_upload",
                        metadata={"timeframe": "uploaded"},
                    )
                    market_snapshot = build_market_snapshot(None, None, chart_snapshot)

            risk_percent = float(form["risk_percent"]) if form["risk_percent"] else None
            settings = RiskSettings(
                risk_mode=form["risk_mode"],
                risk_percent=risk_percent or 0.9,
                volume_override=form["volume_override"],
            )

            if form["data_source"] == "mt5":
                selected_system = display_system_name(form["analysis_system"])
                requested_mt5_system = selected_system
                if mt5_bridge_configured():
                    bridge_timeframes = ["MN1", "W1", "D1", "H4", "H1"] if form["analysis_system"] == "upas" else (["D1", "H4", "H1"] if form["analysis_system"] == "wave" else ["H4", "H1"])
                    multi = fetch_mt5_bridge_data(bridge_timeframes)
                    market_snapshot, chart_snapshot = build_mt5_direct_market_context(multi, form["analysis_system"], form["symbol"])
                    if form["analysis_system"] == "upas":
                        upas_input = UPASInput(
                            mn1=multi["MN1"],
                            w1=multi["W1"],
                            d1=multi["D1"],
                            h4=multi["H4"],
                            h1=multi["H1"],
                            account_balance=float(form["balance"]),
                        )
                        upas_analysis = UPASAgent().analyze(upas_input)
                        result = upas_analysis.payload
                        output = upas_analysis.summary
                        trade_plan = build_upas_trade_plan(upas_analysis)
                        summary_details = build_upas_summary(upas_analysis, trade_plan)
                        why_no_trade = build_upas_why_no_trade(upas_analysis)
                        save_upas_history(upas_analysis, source="mt5", mt5_data_status=build_mt5_data_status([multi["MN1"], multi["W1"], multi["D1"], multi["H4"], multi["H1"]]), market_snapshot=market_snapshot, chart_snapshot=chart_snapshot)
                    elif form["analysis_system"] == "wave":
                        wave_results = analyze_wave_results_from_multi(multi)
                        wave_analysis = primary_wave_result(wave_results)
                        result = wave_analysis
                        output = format_wave_result(wave_analysis)
                        trade_plan = build_wave_trade_plan(wave_analysis, multi[wave_analysis.timeframe].candles[-1].close)
                        summary_details = build_wave_summary(wave_analysis, trade_plan)
                        save_wave_history(wave_analysis, source="mt5", mt5_data_status=build_mt5_data_status([multi["H4"], multi["H1"]]), trade_plan=trade_plan, related_results=wave_results, market_snapshot=market_snapshot, chart_snapshot=chart_snapshot)
                    else:
                        agent = SmartSystemAAgent()
                        snapshot = agent.analyze_with_snapshot(
                            multi["H4"],
                            multi["H1"],
                            AccountSettings(balance=float(form["balance"])),
                            settings,
                        )
                        result = snapshot.result
                        output = agent.format_result(result)
                        is_trade = isinstance(result, TradeSetup)
                        checklist_items = build_checklist_items(snapshot)
                        trade_plan = build_ssa_trade_plan(snapshot)
                        summary_details = build_ssa_summary(snapshot, trade_plan)
                        why_no_trade = build_ssa_why_no_trade(snapshot)
                        save_ssa_history(snapshot, source="mt5", mt5_data_status=build_mt5_data_status([multi["H4"], multi["H1"]]), market_snapshot=market_snapshot, chart_snapshot=chart_snapshot)
                else:
                    mt5_waiting = True
                    create_mt5_request(form["analysis_system"])
                    latest = latest_history("mt5", selected_system)
                    latest_mt5_results = [latest] if latest else []
            elif form["analysis_system"] == "wave":
                if form["data_source"] == "live":
                    h4_data, h1_data = LiveXAUUSDFeed().fetch_h4_h1(form["symbol"])
                    live_status = build_live_status([h4_data, h1_data])
                    multi = {"H4": h4_data, "H1": h1_data}
                elif has_ohlc:
                    multi = DataLoader().load_multi_timeframe_csv_stream(TextIOWrapper(ohlc_file.stream, encoding="utf-8"), form["symbol"])
                elif has_image:
                    image_result = ImageInputValidator().validate(BytesIO(image_bytes or b""), chart_image.filename)
                    multi = {}
                else:
                    error = "Wave Structure Analyst requires one OHLC CSV containing H4 or H1 rows, or live data mode."
                    multi = {}
                if multi:
                    wave_results = analyze_wave_results_from_multi(multi)
                    wave_analysis = primary_wave_result(wave_results)
                    result = wave_analysis
                    output = format_wave_result(wave_analysis)
                    trade_plan = build_wave_trade_plan(wave_analysis, multi[wave_analysis.timeframe].candles[-1].close)
                    summary_details = build_wave_summary(wave_analysis, trade_plan)
                    save_wave_history(wave_analysis, trade_plan=trade_plan, related_results=wave_results)
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
                    trade_plan = build_upas_trade_plan(upas_analysis)
                    summary_details = build_upas_summary(upas_analysis, trade_plan)
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
                trade_plan = build_ssa_trade_plan(snapshot)
                summary_details = build_ssa_summary(snapshot, trade_plan)
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
                trade_plan = build_ssa_trade_plan(snapshot)
                summary_details = build_ssa_summary(snapshot, trade_plan)
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
        wave_analysis=wave_analysis,
        wave_results=wave_results,
        trade_plan=trade_plan,
        summary_details=summary_details,
        why_no_trade=why_no_trade,
        live_status=live_status,
        market_snapshot=market_snapshot,
        chart_snapshot=chart_snapshot,
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
                <div class="status {{ '' if item.status in ['VALID_TRADE', 'WAVE_CONFIRMED'] else 'no-setup' }}">{{ item.status }}</div>
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
                    {% if item.detail.market_snapshot %}
                      <div class="panel">
                        <h2 class="panel-title">Market Snapshot</h2>
                        <div class="grid">
                          <div class="metric"><span>Current Price</span>{{ item.detail.market_snapshot.current_price }}</div>
                          <div class="metric"><span>Chart Available</span>{{ item.detail.market_snapshot.chart_available }}</div>
                          <div class="metric"><span>Last Chart Update</span>{{ item.detail.market_snapshot.last_chart_update }}</div>
                        </div>
                      </div>
                    {% endif %}
                    {% if item.detail.chart_snapshot %}
                      <div class="panel">
                        <h2 class="panel-title">Latest Chart Preview</h2>
                        <a href="{{ item.detail.chart_snapshot.image_url }}" target="_blank">
                          <img class="image-preview" src="{{ item.detail.chart_snapshot.image_url }}" alt="Latest chart screenshot preview">
                        </a>
                      </div>
                    {% endif %}
                    {% if item.detail.trade_plan and item.detail.trade_plan.action %}
                      <div class="panel">
                        <h2 class="panel-title">Trade Plan</h2>
                        <div class="grid">
                          <div class="metric"><span>Action</span>{{ item.detail.trade_plan.action }}</div>
                          <div class="metric"><span>Entry Point</span>{{ item.detail.trade_plan.entry_point }}</div>
                          <div class="metric"><span>Take Profit</span>{{ item.detail.trade_plan.take_profit }}</div>
                          <div class="metric"><span>Stop Loss</span>{{ item.detail.trade_plan.stop_loss }}</div>
                        </div>
                      </div>
                    {% endif %}
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
                    {% if item.detail.market_snapshot %}
                      <div class="panel">
                        <h2 class="panel-title">Market Snapshot</h2>
                        <div class="grid">
                          <div class="metric"><span>Current Price</span>{{ item.detail.market_snapshot.current_price }}</div>
                          <div class="metric"><span>Chart Available</span>{{ item.detail.market_snapshot.chart_available }}</div>
                          <div class="metric"><span>Last Chart Update</span>{{ item.detail.market_snapshot.last_chart_update }}</div>
                        </div>
                      </div>
                    {% endif %}
                    {% if item.detail.chart_snapshot %}
                      <div class="panel">
                        <h2 class="panel-title">Latest Chart Preview</h2>
                        <a href="{{ item.detail.chart_snapshot.image_url }}" target="_blank">
                          <img class="image-preview" src="{{ item.detail.chart_snapshot.image_url }}" alt="Latest chart screenshot preview">
                        </a>
                      </div>
                    {% endif %}
                    {% if item.detail.trade_plan_display %}
                      <div class="panel">
                        <h2 class="panel-title">Trade Plan</h2>
                        <div class="grid">
                          <div class="metric"><span>Action</span>{{ item.detail.trade_plan_display.action }}</div>
                          <div class="metric"><span>Entry Point</span>{{ item.detail.trade_plan_display.entry_point }}</div>
                          <div class="metric"><span>Take Profit</span>{{ item.detail.trade_plan_display.take_profit }}</div>
                          <div class="metric"><span>Stop Loss</span>{{ item.detail.trade_plan_display.stop_loss }}</div>
                        </div>
                      </div>
                    {% endif %}
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
                    {% if item.detail.trade_plan_display %}
                      <div class="panel">
                        <h2 class="panel-title">UPAS Trade Plan</h2>
                        <div class="grid">
                          {% for key, value in item.detail.trade_plan.items() %}
                            <div class="metric"><span>{{ key.replace('_', ' ').title() }}</span>{{ value if value is not none else "None" }}</div>
                          {% endfor %}
                        </div>
                      </div>
                    {% endif %}
                  </div>
                {% elif item.system_used == "Wave Structure Analyst" and item.detail %}
                  <div class="dashboard">
                    {% if item.detail.market_snapshot %}
                      <div class="panel">
                        <h2 class="panel-title">Market Snapshot</h2>
                        <div class="grid">
                          <div class="metric"><span>Current Price</span>{{ item.detail.market_snapshot.current_price }}</div>
                          <div class="metric"><span>Chart Available</span>{{ item.detail.market_snapshot.chart_available }}</div>
                          <div class="metric"><span>Last Chart Update</span>{{ item.detail.market_snapshot.last_chart_update }}</div>
                        </div>
                      </div>
                    {% endif %}
                    {% if item.detail.chart_snapshot %}
                      <div class="panel">
                        <h2 class="panel-title">Latest Chart Preview</h2>
                        <a href="{{ item.detail.chart_snapshot.image_url }}" target="_blank">
                          <img class="image-preview" src="{{ item.detail.chart_snapshot.image_url }}" alt="Latest chart screenshot preview">
                        </a>
                      </div>
                    {% endif %}
                    {% if item.detail.timeframe_results %}
                      <div class="panel">
                        <h2 class="panel-title">Wave Timeframe Results</h2>
                        <div class="grid">
                          {% for tf, wave in item.detail.timeframe_results.items() %}
                            <div class="metric"><span>{{ tf }}</span>{{ wave.status }} - {{ wave.trading_bias }} - {{ wave.wave_score }}/10</div>
                          {% endfor %}
                        </div>
                      </div>
                    {% endif %}
                    {% if item.detail.trade_plan and item.detail.trade_plan.action %}
                      <div class="panel">
                        <h2 class="panel-title">Trade Plan</h2>
                        <div class="grid">
                          <div class="metric"><span>Action</span>{{ item.detail.trade_plan.action }}</div>
                          <div class="metric"><span>Entry Point</span>{{ item.detail.trade_plan.entry_point }}</div>
                          <div class="metric"><span>Take Profit</span>{{ item.detail.trade_plan.take_profit }}</div>
                          <div class="metric"><span>Stop Loss</span>{{ item.detail.trade_plan.stop_loss }}</div>
                        </div>
                      </div>
                    {% endif %}
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
                    <div class="panel">
                      <h2 class="panel-title">Wave Structure Analyst Result</h2>
                      <div class="grid">
                        <div class="metric"><span>Symbol</span>{{ item.detail.symbol }}</div>
                        <div class="metric"><span>Timeframe</span>{{ item.detail.timeframe }}</div>
                        <div class="metric"><span>Market Phase</span>{{ item.detail.market_phase }}</div>
                        <div class="metric"><span>Primary Scenario</span>{{ item.detail.primary_scenario }}</div>
                        <div class="metric"><span>Alternative Scenario</span>{{ item.detail.alternative_scenario }}</div>
                        <div class="metric"><span>Direction</span>{{ item.detail.direction }}</div>
                        <div class="metric"><span>Wave Score</span>{{ item.detail.wave_score }}/10</div>
                        <div class="metric"><span>Confidence</span>{{ item.detail.confidence }}%</div>
                        <div class="metric"><span>Risk Level</span>{{ item.detail.risk_level }}</div>
                        <div class="metric"><span>Trading Bias</span>{{ item.detail.trading_bias }}</div>
                        <div class="metric"><span>Pullback Zone</span>{{ item.detail.entry_zone if item.detail.entry_zone is not none else "None" }}</div>
                        <div class="metric"><span>Invalidation Level</span>{{ item.detail.invalidation_level if item.detail.invalidation_level is not none else "None" }}</div>
                        <div class="metric"><span>Safety</span>Analysis only</div>
                      </div>
                    </div>
                    <div class="decision-summary">
                      <h2>Wave Decision Summary</h2>
                      <dl class="summary-list">
                        {% for row in item.detail.decision_summary %}
                          <div class="summary-row"><dt>{{ row.label }}</dt><dd>{{ row.value }}</dd></div>
                        {% endfor %}
                      </dl>
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


def build_ssa_trade_plan(snapshot: AnalysisSnapshot) -> dict[str, object] | None:
    result = snapshot.result
    if isinstance(result, TradeSetup):
        return {
            "action": f"ENTER {result.setup_type}",
            "entry_point": result.entry,
            "take_profit": f"TP1 {result.tp1}, TP2 {result.tp2}",
            "stop_loss": result.sl,
        }
    return None


def build_upas_trade_plan(upas_analysis: UPASAnalysis) -> dict[str, object] | None:
    payload = upas_analysis.payload
    if payload["status"] != "VALID_TRADE":
        return None
    plan = payload["trade_plan"]
    direction = payload["setup"]["direction"]
    action = f"ENTER {direction}" if direction in {"BUY", "SELL"} else "ENTER"
    return {
        "action": action,
        "entry_point": plan["entry"],
        "take_profit": plan["take_profit"],
        "stop_loss": plan["stop_loss"],
    }


def build_wave_trade_plan(wave: WaveAnalysisResult, current_price: float | None = None) -> dict[str, object] | None:
    direction = wave.trading_bias
    entry = wave.entry_zone
    stop = wave.invalidation_level
    if wave.status != "WAVE_CONFIRMED" or direction not in {"BUY", "SELL"} or stop is None or entry is None:
        return None
    risk = abs(entry - stop)
    if risk <= 0:
        return None
    target = entry + 2 * risk if direction == "BUY" else entry - 2 * risk
    return {
        "action": f"ENTER {direction}",
        "entry_point": round(entry, 3),
        "take_profit": round(target, 3),
        "stop_loss": round(stop, 3),
    }


def build_wave_trade_plans(
    wave_results: dict[str, WaveAnalysisResult],
    multi: dict[str, object],
) -> dict[str, dict[str, object]]:
    plans = {}
    for timeframe, wave in wave_results.items():
        if timeframe in multi:
            plan = build_wave_trade_plan(wave, multi[timeframe].candles[-1].close)
            if plan:
                plans[timeframe] = plan
    return plans


def build_ssa_summary(snapshot: AnalysisSnapshot, trade_plan: dict[str, object] | None = None) -> list[dict[str, object]]:
    result = snapshot.result
    if isinstance(result, NoSetupResult):
        details = [
            {"label": "Decision", "value": "No setup"},
            {"label": "Failed Rules", "value": "; ".join(result.failed_rules)},
            {"label": "H4 Wave Position", "value": result.h4_wave_position},
            {"label": "Active Wave", "value": result.active_wave if result.active_wave is not None else "Unidentifiable"},
            {"label": "Market State", "value": result.market_state.value},
            {"label": "Next Requirement", "value": result.what_next},
            {"label": "Reasoning", "value": result.reasoning_summary},
        ]
        return details
    return [
        {"label": "Decision", "value": "Valid setup"},
        {"label": "Setup Type", "value": result.setup_type},
        {"label": "Entry Point", "value": trade_plan["entry_point"] if trade_plan else result.entry},
        {"label": "Take Profit", "value": trade_plan["take_profit"] if trade_plan else f"TP1 {result.tp1}, TP2 {result.tp2}"},
        {"label": "Stop Loss", "value": trade_plan["stop_loss"] if trade_plan else result.sl},
        {"label": "Risk And Lot", "value": f"{result.risk_percent}% risk, {result.lot_size} lots"},
        {"label": "Confidence", "value": result.confidence_level},
        {"label": "Reasoning", "value": result.reasoning_summary},
    ]


def build_upas_summary(upas_analysis: UPASAnalysis, trade_plan: dict[str, object] | None = None) -> list[dict[str, object]]:
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


def analyze_wave_results_from_multi(
    multi: dict[str, object],
    current_price: float | None = None,
) -> dict[str, WaveAnalysisResult]:
    results = {}
    for timeframe in ["H4", "H1"]:
        if timeframe in multi:
            results[timeframe] = analyze_wave_timeframe(multi, timeframe, current_price=current_price)
    if not results:
        raise ValueError("Wave Structure Analyst requires H4 or H1 OHLC rows.")
    return results


def primary_wave_result(results: dict[str, WaveAnalysisResult]) -> WaveAnalysisResult:
    for timeframe in ["H4", "H1"]:
        wave = results.get(timeframe)
        if wave and wave.status == "WAVE_CONFIRMED":
            return wave
    if "H4" in results:
        return results["H4"]
    return next(iter(results.values()))


def analyze_wave_from_multi(multi: dict[str, object], form: dict[str, object]) -> WaveAnalysisResult:
    return primary_wave_result(analyze_wave_results_from_multi(multi))


def analyze_wave_timeframe(
    multi: dict[str, object],
    timeframe: str,
    current_price: float | None = None,
) -> WaveAnalysisResult:
    if timeframe not in multi:
        raise ValueError("Wave Structure Analyst requires H4 or H1 OHLC rows.")
    primary_data = multi[timeframe]
    current_price = current_price if current_price is not None else primary_data.candles[-1].close
    swing_highs, swing_lows = derive_swings(primary_data.candles)
    trend_direction = infer_wave_trend(primary_data.candles)
    breakout_level = swing_highs[-2] if trend_direction == "bullish" and len(swing_highs) >= 2 else None
    if trend_direction == "bearish" and len(swing_lows) >= 2:
        breakout_level = swing_lows[-2]
    retest_level = breakout_level
    request_data = WaveAnalysisInput(
        symbol="XAUUSD",
        timeframe=timeframe,
        primary_data=primary_data,
        h4=multi.get("H4"),
        h1=multi.get("H1"),
        d1=multi.get("D1"),
        m30=multi.get("M30"),
        m15=multi.get("M15"),
        current_price=current_price,
        swing_highs=swing_highs,
        swing_lows=swing_lows,
        breakout_level=breakout_level,
        retest_level=retest_level,
        trend_direction=trend_direction,
    )
    return WaveStructureAnalyst().analyze(request_data)


def derive_swings(candles: list[object]) -> tuple[list[float], list[float]]:
    swing_highs = []
    swing_lows = []
    for index in range(1, len(candles) - 1):
        previous = candles[index - 1]
        current = candles[index]
        following = candles[index + 1]
        if current.high >= previous.high and current.high >= following.high:
            swing_highs.append(current.high)
        if current.low <= previous.low and current.low <= following.low:
            swing_lows.append(current.low)
    if not swing_highs:
        swing_highs = [max(c.high for c in candles)]
    if not swing_lows:
        swing_lows = [min(c.low for c in candles)]
    return swing_highs, swing_lows


def infer_wave_trend(candles: list[object]) -> str:
    if len(candles) < 6:
        return "neutral"
    first = candles[0].close
    last = candles[-1].close
    recent_high = max(c.high for c in candles[-5:])
    prior_high = max(c.high for c in candles[:5])
    recent_low = min(c.low for c in candles[-5:])
    prior_low = min(c.low for c in candles[:5])
    if last > first and recent_high > prior_high and recent_low > prior_low:
        return "bullish"
    if last < first and recent_low < prior_low and recent_high < prior_high:
        return "bearish"
    return "neutral"


def build_wave_summary(wave: WaveAnalysisResult, trade_plan: dict[str, object] | None = None) -> list[dict[str, object]]:
    details = [
        {"label": "Decision", "value": wave.status},
        {"label": "Market Phase", "value": wave.market_phase},
        {"label": "Primary Scenario", "value": wave.primary_scenario},
        {"label": "Alternative Scenario", "value": wave.alternative_scenario},
        {"label": "Direction", "value": wave.direction},
        {"label": "Wave Score", "value": f"{wave.wave_score}/10"},
        {"label": "Confidence", "value": f"{wave.confidence}%"},
        {"label": "Trading Bias", "value": wave.trading_bias},
        {"label": "Pullback Zone", "value": wave.entry_zone if wave.entry_zone is not None else "None"},
        {"label": "Suggested Action", "value": wave.suggested_action},
        {"label": "Invalidation Level", "value": wave.invalidation_level if wave.invalidation_level is not None else "None"},
        {"label": "Reason", "value": wave.reason},
    ]
    if trade_plan:
        details[1:1] = [
            {"label": "Entry Point", "value": trade_plan["entry_point"]},
            {"label": "Take Profit", "value": trade_plan["take_profit"]},
            {"label": "Stop Loss", "value": trade_plan["stop_loss"]},
        ]
    return details


def format_wave_result(wave: WaveAnalysisResult) -> str:
    invalidation = wave.invalidation_level if wave.invalidation_level is not None else "None"
    return (
        "Wave Structure Analyst Result\n\n"
        f"Symbol:\n{wave.symbol}\n\n"
        f"Timeframe:\n{wave.timeframe}\n\n"
        f"Market Phase:\n{wave.market_phase}\n\n"
        f"Primary Scenario:\n{wave.primary_scenario}\n\n"
        f"Alternative Scenario:\n{wave.alternative_scenario}\n\n"
        f"Direction:\n{wave.direction}\n\n"
        f"Wave Score:\n{wave.wave_score}/10\n\n"
        f"Confidence:\n{wave.confidence}%\n\n"
        f"Risk Level:\n{wave.risk_level}\n\n"
        f"Trading Bias:\n{wave.trading_bias}\n\n"
        f"Pullback Zone:\n{wave.entry_zone if wave.entry_zone is not None else 'None'}\n\n"
        f"Suggested Action:\n{wave.suggested_action}\n\n"
        f"Invalidation Level:\n{invalidation}\n\n"
        f"Reason:\n{wave.reason}"
    )


def save_wave_history(
    wave: WaveAnalysisResult,
    source: str = "web",
    mt5_data_status: dict[str, object] | None = None,
    trade_plan: dict[str, object] | None = None,
    related_results: dict[str, WaveAnalysisResult] | None = None,
    market_snapshot: dict[str, object] | None = None,
    chart_snapshot: dict[str, object] | None = None,
) -> None:
    trade_plan = trade_plan or build_wave_trade_plan(wave)
    detail = {
        "symbol": wave.symbol,
        "timeframe": wave.timeframe,
        "market_phase": wave.market_phase,
        "primary_scenario": wave.primary_scenario,
        "alternative_scenario": wave.alternative_scenario,
        "direction": wave.direction,
        "wave_score": wave.wave_score,
        "confidence": wave.confidence,
        "risk_level": wave.risk_level,
        "trading_bias": wave.trading_bias,
        "entry_zone": wave.entry_zone,
        "suggested_action": wave.suggested_action,
        "invalidation_level": wave.invalidation_level,
        "reason": wave.reason,
        "failed_rules": wave.failed_rules,
        "trade_plan": trade_plan,
        "decision_summary": build_wave_summary(wave, trade_plan),
        "timeframe_results": {
            timeframe: {
                "status": result.status,
                "market_phase": result.market_phase,
                "primary_scenario": result.primary_scenario,
                "direction": result.direction,
                "wave_score": result.wave_score,
                "confidence": result.confidence,
                "trading_bias": result.trading_bias,
                "entry_zone": result.entry_zone,
                "invalidation_level": result.invalidation_level,
            }
            for timeframe, result in (related_results or {}).items()
        },
    }
    if mt5_data_status:
        detail["mt5_data_status"] = mt5_data_status
    if market_snapshot:
        detail["market_snapshot"] = market_snapshot
    if chart_snapshot:
        detail["chart_snapshot"] = chart_snapshot
    add_history(
        "Wave Structure Analyst",
        wave.status,
        wave.primary_scenario,
        f"{wave.wave_score}/10",
        wave.reason,
        source=source,
        detail=detail,
        raw_output=format_wave_result(wave),
    )


def display_system_name(value: str) -> str:
    if value == "upas":
        return "UPAS Trade Assistant"
    if value == "wave":
        return "Wave Structure Analyst"
    return "Smart System A"


def build_image_preview(image_bytes: bytes, mimetype: str) -> dict[str, str]:
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return {"data_url": f"data:{mimetype};base64,{encoded}"}


def build_market_snapshot(
    current_price: object | None,
    timestamp: str | None,
    chart_snapshot: dict[str, object] | None,
) -> dict[str, object]:
    has_price = current_price is not None and current_price != ""
    return {
        "current_price": current_price if has_price else "n/a",
        "timestamp": timestamp or malaysia_now_text(),
        "chart_available": "Yes" if chart_snapshot else "No",
        "last_chart_update": chart_snapshot["market_timestamp"] if chart_snapshot else (timestamp or "n/a"),
        "chart_url": chart_snapshot.get("image_url") if chart_snapshot else None,
        "chart_symbol": chart_snapshot.get("symbol") if chart_snapshot else None,
        "chart_timeframe": (chart_snapshot.get("metadata") or {}).get("timeframe") if chart_snapshot else None,
        "chart_filename": chart_snapshot.get("filename") if chart_snapshot else None,
    }


def build_mt5_direct_market_context(
    multi: dict[str, object],
    analysis_system: str,
    symbol: str,
) -> tuple[dict[str, object], dict[str, object] | None]:
    bridge_snapshot = fetch_mt5_bridge_snapshot()
    current_price = bridge_snapshot.get("current_price")
    timestamp = bridge_snapshot.get("timestamp")
    if current_price is None or not timestamp:
        latest_candle = latest_candle_from_multi(multi)
        if latest_candle:
            current_price = latest_candle.close
            timestamp = latest_candle.timestamp

    display_name = display_system_name(analysis_system)
    chart_snapshot = latest_chart_screenshot(symbol, display_name)
    normalized_symbol = normalize_symbol(symbol)
    if not chart_snapshot and normalized_symbol != symbol:
        chart_snapshot = latest_chart_screenshot(normalized_symbol, display_name)
    if chart_snapshot:
        chart_snapshot.pop("image_base64", None)
        chart_snapshot["image_url"] = f"/screenshots/{chart_snapshot['id']}"
    return build_market_snapshot(current_price, str(timestamp or malaysia_now_text()), chart_snapshot), chart_snapshot


def latest_candle_from_multi(multi: dict[str, object]) -> object | None:
    preferred = multi.get("H1") or next(iter(multi.values()), None)
    candles = getattr(preferred, "candles", []) if preferred else []
    return candles[-1] if candles else None


def normalize_symbol(symbol: str) -> str:
    return symbol.replace("/", "").replace(" ", "").upper()


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
    market_snapshot: dict[str, object] | None = None,
    chart_snapshot: dict[str, object] | None = None,
) -> None:
    result = snapshot.result
    trade_plan = build_ssa_trade_plan(snapshot)
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
        "trade_plan": trade_plan,
        "decision_summary": build_ssa_summary(snapshot, trade_plan),
        "why_no_trade": build_ssa_why_no_trade(snapshot),
    }
    if mt5_data_status:
        detail["mt5_data_status"] = mt5_data_status
    if market_snapshot:
        detail["market_snapshot"] = market_snapshot
    if chart_snapshot:
        detail["chart_snapshot"] = chart_snapshot
    add_history("Smart System A", status, setup_name, score, summary, source=source, detail=detail, raw_output=raw_output)


def save_upas_history(
    upas_analysis: UPASAnalysis,
    source: str = "web",
    mt5_data_status: dict[str, object] | None = None,
    market_snapshot: dict[str, object] | None = None,
    chart_snapshot: dict[str, object] | None = None,
) -> None:
    payload = upas_analysis.payload
    detail = dict(payload)
    detail["trade_plan_display"] = build_upas_trade_plan(upas_analysis)
    if mt5_data_status:
        detail["mt5_data_status"] = mt5_data_status
    if market_snapshot:
        detail["market_snapshot"] = market_snapshot
    if chart_snapshot:
        detail["chart_snapshot"] = chart_snapshot
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


def mt5_bridge_configured() -> bool:
    return bool(os.getenv("MT5_BRIDGE_URL") and os.getenv("MT5_BRIDGE_API_KEY"))


def fetch_mt5_bridge_data(timeframes: list[str], limit: int = 200) -> dict[str, object]:
    base_url = (os.getenv("MT5_BRIDGE_URL") or "").rstrip("/")
    api_key = os.getenv("MT5_BRIDGE_API_KEY") or ""
    if not base_url or not api_key:
        raise ValueError("MT5 Bridge is not configured. Set MT5_BRIDGE_URL and MT5_BRIDGE_API_KEY.")

    csv_parts = ["timeframe,timestamp,open,high,low,close,volume"]
    for timeframe in timeframes:
        url = f"{base_url}/api/mt5/xauusd/candles?timeframe={timeframe}&limit={limit}"
        payload = fetch_mt5_bridge_json(url, api_key)
        if not payload.get("ok"):
            raise ValueError(str(payload.get("error") or f"MT5 Bridge failed for {timeframe}."))
        ohlcv_csv = str(payload.get("ohlcv_csv") or "")
        lines = [line for line in ohlcv_csv.splitlines() if line.strip()]
        if len(lines) < 2:
            raise ValueError(f"MT5 Bridge returned no candle rows for {timeframe}.")
        csv_parts.extend(lines[1:])
    combined_csv = "\n".join(csv_parts) + "\n"
    return DataLoader().load_multi_timeframe_csv_stream(StringIO(combined_csv), "XAUUSD")


def fetch_mt5_bridge_snapshot() -> dict[str, object]:
    base_url = (os.getenv("MT5_BRIDGE_URL") or "").rstrip("/")
    api_key = os.getenv("MT5_BRIDGE_API_KEY") or ""
    if not base_url or not api_key:
        return {}
    try:
        payload = fetch_mt5_bridge_json(f"{base_url}/api/mt5/xauusd/snapshot", api_key)
    except ValueError:
        return {}
    if not payload.get("ok"):
        return {}
    return payload


def fetch_mt5_bridge_json(url: str, api_key: str) -> dict[str, object]:
    req = urllib.request.Request(url, headers={"X-API-Key": api_key, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            message = payload.get("error") or payload.get("message") or str(exc)
        except Exception:
            message = str(exc)
        raise ValueError(f"MT5 Bridge error: {message}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"Cannot reach MT5 Bridge. Check that the local bridge is running and publicly reachable. Details: {exc.reason}") from exc


def extract_page_styles() -> str:
    start = PAGE.find("<style>")
    end = PAGE.find("</style>")
    if start == -1 or end == -1:
        return ""
    return PAGE[start + len("<style>"):end]


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False)
