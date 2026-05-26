from __future__ import annotations

from io import TextIOWrapper

from flask import Flask, render_template_string, request

from smart_system_a.agent import SmartSystemAAgent
from smart_system_a.data_loader import DataLoader
from smart_system_a.image_input import ImageInputValidator
from smart_system_a.live_data import LiveXAUUSDFeed
from smart_system_a.models import AccountSettings, AnalysisSnapshot, NoSetupResult, RiskSettings, TradeSetup
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
    body {
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: radial-gradient(circle at top left, #1d2636 0, #070b12 34%, #05070c 100%);
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
    h1 {
      margin: 0;
      font-size: 24px;
      letter-spacing: 0;
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
    }
    form {
      background: var(--paper);
      border-right: 1px solid var(--line);
      padding: 24px;
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
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px 11px;
      font-size: 14px;
      background: #0f1726;
      color: var(--ink);
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
    }
    .result, .panel {
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 20px;
      box-shadow: 0 18px 45px rgba(0, 0, 0, 0.28);
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
      form { border-right: 0; border-bottom: 1px solid var(--line); }
      .grid { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
      .dashboard-grid { grid-template-columns: 1fr; }
      header { align-items: flex-start; flex-direction: column; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Gold Smart Agent</h1>
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
        </select>
        <label for="ohlc_data">OHLC Data <span class="field-help" tabindex="0" data-tip="Accepted CSV columns: timeframe,timestamp,open,high,low,close,volume. For Smart System A include H4 and H1 rows. For UPAS include MN1, W1, D1, H4, and H1 rows. Volume may be blank, but volume-based rules may fail.">!</span></label>
        <input id="ohlc_data" name="ohlc_data" type="file" accept=".csv">
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
      {% elif result %}
        <div class="result">
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
              <div class="panel">
                <h2 class="panel-title">UPAS Decision Summary</h2>
                <p class="summary-text">{{ upas_analysis.payload.summary }}</p>
                <p class="summary-text">{{ upas_analysis.payload.reasoning }}</p>
                {% if upas_analysis.payload.invalidation %}
                  <p class="summary-text"><strong>Invalidation:</strong> {{ upas_analysis.payload.invalidation }}</p>
                {% endif %}
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
          {% if upas_analysis %}
            <details class="raw-output">
              <summary>View raw UPAS JSON</summary>
              <pre>{{ output }}</pre>
            </details>
          {% else %}
            <pre>{{ output }}</pre>
          {% endif %}
        </div>
      {% elif image_result %}
        <div class="result">
          <div class="status no-setup">Image Accepted - No Setup</div>
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
    </section>
  </main>
</body>
</html>
"""


def create_app() -> Flask:
    return app


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
    snapshot = None
    checklist_items = []
    upas_analysis = None

    if request.method == "POST":
        try:
            ohlc_file = request.files.get("ohlc_data")
            chart_image = request.files.get("chart_image")
            has_ohlc = bool(ohlc_file and ohlc_file.filename)
            has_image = bool(chart_image and chart_image.filename)

            risk_percent = float(form["risk_percent"]) if form["risk_percent"] else None
            settings = RiskSettings(
                risk_mode=form["risk_mode"],
                risk_percent=risk_percent or 0.9,
                volume_override=form["volume_override"],
            )

            if form["analysis_system"] == "upas":
                if form["data_source"] == "live":
                    mn1_data, w1_data, d1_data, h4_data, h1_data = LiveXAUUSDFeed().fetch_upas(form["symbol"])
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
                    image_result = ImageInputValidator().validate(chart_image.stream, chart_image.filename)
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
            elif form["data_source"] == "live":
                h4_data, h1_data = LiveXAUUSDFeed().fetch_h4_h1(form["symbol"])
                agent = SmartSystemAAgent()
                snapshot = agent.analyze_with_snapshot(h4_data, h1_data, AccountSettings(float(form["balance"])), settings)
                result = snapshot.result
                output = agent.format_result(result)
                checklist_items = build_checklist_items(snapshot)
                is_trade = isinstance(result, TradeSetup)
                if isinstance(result, NoSetupResult):
                    is_trade = False
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
                is_trade = isinstance(result, TradeSetup)
                if isinstance(result, NoSetupResult):
                    is_trade = False
            elif has_image:
                image_result = ImageInputValidator().validate(chart_image.stream, chart_image.filename)
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
        snapshot=snapshot,
        checklist_items=checklist_items,
        upas_analysis=upas_analysis,
    )


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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False)
