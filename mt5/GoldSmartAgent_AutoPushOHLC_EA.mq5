//+------------------------------------------------------------------+
//| Gold Smart Agent - Auto Push OHLCV EA                            |
//| Place in: MQL5/Experts/GoldSmartAgent_AutoPushOHLC_EA.mq5         |
//| Pushes Smart System A and UPAS data every 5 minutes.              |
//+------------------------------------------------------------------+
#property strict

input string InpEndpoint = "https://smart-system-a-agent.onrender.com/api/analyze";
input string InpSymbol = "";            // blank = current chart symbol
input int    InpBarsPerTimeframe = 120;
input int    InpPushIntervalSeconds = 300;
input int    InpTimeoutMs = 15000;
input bool   InpPushOnStart = true;
input bool   InpPingBeforePush = true;

datetime g_last_push_time = 0;
int      g_push_count = 0;
string   g_csv = "";

string EscapeJson(string value)
{
   string escaped = value;
   string backslash = CharToString(92);
   string quote = CharToString(34);

   StringReplace(escaped, backslash, backslash + backslash);
   StringReplace(escaped, quote, backslash + quote);
   StringReplace(escaped, CharToString(13), backslash + "r");
   StringReplace(escaped, CharToString(10), backslash + "n");
   StringReplace(escaped, CharToString(9), backslash + "t");
   return escaped;
}

string TimeframeName(ENUM_TIMEFRAMES timeframe)
{
   if(timeframe == PERIOD_MN1) return "MN1";
   if(timeframe == PERIOD_W1)  return "W1";
   if(timeframe == PERIOD_D1)  return "D1";
   if(timeframe == PERIOD_H4)  return "H4";
   if(timeframe == PERIOD_H1)  return "H1";
   return EnumToString(timeframe);
}

bool AppendRates(string symbol, ENUM_TIMEFRAMES timeframe, int bars)
{
   MqlRates rates[];
   ArraySetAsSeries(rates, false);
   int copied = CopyRates(symbol, timeframe, 0, bars, rates);
   if(copied < 10)
   {
      Print("Gold Smart Agent: not enough candles for ", TimeframeName(timeframe), ". Copied: ", copied);
      return false;
   }

   string tf = TimeframeName(timeframe);
   int digits = _Digits;
   for(int i = 0; i < copied; i++)
   {
      string candle_time = TimeToString(rates[i].time, TIME_DATE) + " " + TimeToString(rates[i].time, TIME_MINUTES);
      string open_price = DoubleToString(rates[i].open, digits);
      string high_price = DoubleToString(rates[i].high, digits);
      string low_price = DoubleToString(rates[i].low, digits);
      string close_price = DoubleToString(rates[i].close, digits);
      string candle_volume = LongToString(rates[i].tick_volume);
      string row = "";
      row = row + tf + ",";
      row = row + candle_time + ",";
      row = row + open_price + ",";
      row = row + high_price + ",";
      row = row + low_price + ",";
      row = row + close_price + ",";
      row = row + candle_volume + CharToString(10);
      g_csv = g_csv + row;
   }
   return true;
}

bool BuildCsv(string symbol, string analysis_system, int bars)
{
   g_csv = "timeframe,timestamp,open,high,low,close,volume" + CharToString(10);
   string system = analysis_system;
   StringToLower(system);

   if(system == "upas")
   {
      if(AppendRates(symbol, PERIOD_MN1, bars) == false)
      {
         return false;
      }
      if(AppendRates(symbol, PERIOD_W1, bars) == false)
      {
         return false;
      }
      if(AppendRates(symbol, PERIOD_D1, bars) == false)
      {
         return false;
      }
      if(AppendRates(symbol, PERIOD_H4, bars) == false)
      {
         return false;
      }
      if(AppendRates(symbol, PERIOD_H1, bars) == false)
      {
         return false;
      }
      return true;
   }

   if(AppendRates(symbol, PERIOD_H4, bars) == false)
   {
      return false;
   }
   if(AppendRates(symbol, PERIOD_H1, bars) == false)
   {
      return false;
   }
   return true;
}

bool PushAnalysis(string symbol, string analysis_system)
{
   if(BuildCsv(symbol, analysis_system, InpBarsPerTimeframe) == false)
   {
      Print("Gold Smart Agent: failed to build ", analysis_system, " OHLCV CSV.");
      return false;
   }

   string quote = CharToString(34);
   string body = "{";
   body += quote + "analysis_system" + quote + ":" + quote + EscapeJson(analysis_system) + quote + ",";
   body += quote + "symbol" + quote + ":" + quote + EscapeJson(symbol) + quote + ",";
   body += quote + "ohlc_csv" + quote + ":" + quote + EscapeJson(g_csv) + quote;
   body += "}";

   char post[];
   StringToCharArray(body, post, 0, WHOLE_ARRAY, CP_UTF8);
   if(ArraySize(post) > 0)
      ArrayResize(post, ArraySize(post) - 1);

   char result[];
   string result_headers;
   string headers = "Content-Type: application/json\r\n";

   ResetLastError();
   int status = WebRequest("POST", InpEndpoint, headers, InpTimeoutMs, post, result, result_headers);
   if(status == -1)
   {
      Print("Gold Smart Agent: WebRequest failed for ", analysis_system, ". Error: ", GetLastError());
      Print("Allow this URL in MT5: Tools > Options > Expert Advisors > Allow WebRequest: https://smart-system-a-agent.onrender.com");
      return false;
   }

   string response = CharArrayToString(result, 0, -1, CP_UTF8);
   Print("Gold Smart Agent: ", analysis_system, " push HTTP status: ", status);
   Print(response);
   return (status >= 200 && status < 300);
}

bool PingServer()
{
   string ping_url = "https://smart-system-a-agent.onrender.com/api/ping";
   char post[];
   char result[];
   string result_headers;
   string headers = "";

   ResetLastError();
   int status = WebRequest("GET", ping_url, headers, InpTimeoutMs, post, result, result_headers);
   if(status == -1)
   {
      Print("Gold Smart Agent: ping failed. Error: ", GetLastError());
      Print("Allow this URL in MT5: Tools > Options > Expert Advisors > Allow WebRequest: https://smart-system-a-agent.onrender.com");
      return false;
   }

   string response = CharArrayToString(result, 0, -1, CP_UTF8);
   Print("Gold Smart Agent: ping HTTP status: ", status, " response: ", response);
   return (status >= 200 && status < 300);
}

void PushBothSystems()
{
   string symbol = InpSymbol;
   if(symbol == "")
      symbol = _Symbol;

   g_push_count++;
   g_last_push_time = TimeCurrent();

   Print("Gold Smart Agent: push cycle #", g_push_count, " at ", TimeToString(g_last_push_time, TIME_DATE | TIME_SECONDS));
   Print("Gold Smart Agent: pushing SSA and UPAS for ", symbol, ". Interval seconds: ", InpPushIntervalSeconds);

   if(InpPingBeforePush)
      PingServer();

   bool ssa_ok = PushAnalysis(symbol, "ssa");
   bool upas_ok = PushAnalysis(symbol, "upas");
   Print("Gold Smart Agent: push cycle complete. SSA=", ssa_ok, " UPAS=", upas_ok);
}

int OnInit()
{
   int interval = InpPushIntervalSeconds;
   if(interval < 300)
      interval = 300;

   EventSetTimer(interval);
   Print("Gold Smart Agent Auto Push EA started. Push interval seconds: ", interval);
   Print("Gold Smart Agent Auto Push EA endpoint: ", InpEndpoint);
   string display_symbol = InpSymbol;
   if(display_symbol == "")
      display_symbol = _Symbol;
   Print("Gold Smart Agent Auto Push EA symbol: ", display_symbol);
   Print("Gold Smart Agent Auto Push EA pushes both SSA and UPAS every 5 minutes.");

   if(InpPushOnStart)
      PushBothSystems();

   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   EventKillTimer();
   Print("Gold Smart Agent Auto Push EA stopped.");
}

void OnTimer()
{
   PushBothSystems();
}
