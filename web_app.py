from __future__ import annotations

from io import TextIOWrapper

from flask import Flask, render_template_string, request

from smart_system_a.agent import SmartSystemAAgent
from smart_system_a.data_loader import DataLoader
from smart_system_a.image_input import ImageInputValidator
from smart_system_a.models import AccountSettings, NoSetupResult, RiskSettings, TradeSetup


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024


PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Smart System A Agent</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #18202a;
      --muted: #5b6470;
      --line: #d7dde5;
      --panel: #f7f8fa;
      --accent: #0f766e;
      --danger: #b42318;
      --ok: #12643f;
      --paper: #ffffff;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: #eef2f5;
    }
    header {
      background: var(--paper);
      border-bottom: 1px solid var(--line);
      padding: 18px 28px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    h1 {
      margin: 0;
      font-size: 22px;
      letter-spacing: 0;
    }
    .badge {
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 6px 10px;
      color: var(--muted);
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
      background: var(--paper);
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
      color: white;
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
    @media (max-width: 860px) {
      main { grid-template-columns: 1fr; }
      form { border-right: 0; border-bottom: 1px solid var(--line); }
      .grid { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
      header { align-items: flex-start; flex-direction: column; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Smart System A Agent</h1>
    <div class="badge">XAUUSD rule-based analysis only</div>
  </header>
  <main>
    <form method="post" enctype="multipart/form-data">
      <fieldset>
        <legend>Market Data</legend>
        <label for="h4">H4 CSV</label>
        <input id="h4" name="h4" type="file" accept=".csv">
        <label for="h1">H1 CSV</label>
        <input id="h1" name="h1" type="file" accept=".csv">
        <label for="chart_image">Chart Screenshot</label>
        <input id="chart_image" name="chart_image" type="file" accept=".png,.jpg,.jpeg,.webp,image/png,image/jpeg,image/webp">
      </fieldset>
      <fieldset>
        <legend>Risk Settings</legend>
        <label for="balance">Account Balance</label>
        <input id="balance" name="balance" type="number" min="1" step="0.01" value="{{ form.balance }}" required>
        <label for="risk_mode">Risk Mode</label>
        <select id="risk_mode" name="risk_mode">
          <option value="standard" {% if form.risk_mode == "standard" %}selected{% endif %}>Standard</option>
          <option value="high_confidence" {% if form.risk_mode == "high_confidence" %}selected{% endif %}>High Confidence</option>
        </select>
        <label for="risk_percent">Risk Percent</label>
        <input id="risk_percent" name="risk_percent" type="number" min="0.01" max="1.5" step="0.01" value="{{ form.risk_percent }}">
        <label for="symbol">Symbol</label>
        <input id="symbol" name="symbol" value="{{ form.symbol }}">
        <label class="checkline" for="volume_override">
          <input id="volume_override" name="volume_override" type="checkbox" {% if form.volume_override %}checked{% endif %}>
          Allow volume override
        </label>
      </fieldset>
      <button type="submit">Analyze SSA Setup</button>
    </form>
    <section class="workspace">
      {% if error %}
        <div class="result">
          <div class="status no-setup">Input Error</div>
          <pre>{{ error }}</pre>
        </div>
      {% elif result %}
        <div class="result">
          {% if is_trade %}
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
          <pre>{{ output }}</pre>
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
          <strong>Upload H4 and H1 CSV files to run the SSA checklist.</strong>
          <p class="muted">Screenshots are accepted for intake, but trade analysis still requires OHLCV CSV data so volume and structure rules can be mechanically verified.</p>
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
        "symbol": request.form.get("symbol", "XAUUSD"),
        "volume_override": request.form.get("volume_override") == "on",
    }
    result = None
    output = None
    error = None
    is_trade = False
    image_result = None

    if request.method == "POST":
        try:
            h4_file = request.files.get("h4")
            h1_file = request.files.get("h1")
            chart_image = request.files.get("chart_image")
            has_h4 = bool(h4_file and h4_file.filename)
            has_h1 = bool(h1_file and h1_file.filename)
            has_image = bool(chart_image and chart_image.filename)

            if has_h4 and has_h1:
                loader = DataLoader()
                h4_data = loader.load_csv_stream(TextIOWrapper(h4_file.stream, encoding="utf-8"), "H4", form["symbol"])
                h1_data = loader.load_csv_stream(TextIOWrapper(h1_file.stream, encoding="utf-8"), "H1", form["symbol"])
                risk_percent = float(form["risk_percent"]) if form["risk_percent"] else None
                settings = RiskSettings(
                    risk_mode=form["risk_mode"],
                    risk_percent=risk_percent or 0.9,
                    volume_override=form["volume_override"],
                )
                agent = SmartSystemAAgent()
                result = agent.analyze(h4_data, h1_data, AccountSettings(float(form["balance"])), settings)
                output = agent.format_result(result)
                is_trade = isinstance(result, TradeSetup)
                if isinstance(result, NoSetupResult):
                    is_trade = False
            elif has_image:
                image_result = ImageInputValidator().validate(chart_image.stream, chart_image.filename)
            else:
                error = "Upload both H4 and H1 CSV files, or upload a chart screenshot for image intake."
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
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False)
