//+------------------------------------------------------------------+
//| Gold Smart Agent - Auto Push OHLCV EA                            |
//| Place in: MQL5/Experts/GoldSmartAgent_AutoPushOHLC_EA.mq5         |
//| Polls Gold Smart Agent and pushes the selected system on demand.  |
//+------------------------------------------------------------------+
#property strict

input string InpEndpoint = "https://smart-system-a-agent.onrender.com/api/analyze";
input string InpRequestEndpoint = "https://smart-system-a-agent.onrender.com/api/mt5/next-request";
input string InpSymbol = "";            // blank = current chart symbol
input int    InpBarsPerTimeframe = 120;
input int    InpPushIntervalSeconds = 10;
input int    InpTimeoutMs = 15000;
input bool   InpPushOnStart = false;
input bool   InpPingBeforePush = true;

datetime g_last_push_time = 0;
int      g_push_count = 0;

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

bool AppendRates(string symbol, ENUM_TIMEFRAMES timeframe, int bars, string &csv)
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
   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   for(int i = 0; i < copied; i++)
   {
      csv += tf + ",";
      csv += TimeToString(rates[i].time, TIME_DATE | TIME_MINUTES) + ",";
      csv += DoubleToString(rates[i].open, digits) + ",";
      csv += DoubleToString(rates[i].high, digits) + ",";
      csv += DoubleToString(rates[i].low, digits) + ",";
      csv += DoubleToString(rates[i].close, digits) + ",";
      csv += IntegerToString((long)rates[i].tick_volume) + "\n";
   }
   return true;
}

bool BuildCsv(string symbol, string analysis_system, int bars, string &csv)
{
   csv = "timeframe,timestamp,open,high,low,close,volume\n";
   string system = analysis_system;
   StringToLower(system);

   if(system == "upas")
   {
      if(AppendRates(symbol, PERIOD_MN1, bars, csv) == false)
      {
         return false;
      }
      if(AppendRates(symbol, PERIOD_W1, bars, csv) == false)
      {
         return false;
      }
      if(AppendRates(symbol, PERIOD_D1, bars, csv) == false)
      {
         return false;
      }
      if(AppendRates(symbol, PERIOD_H4, bars, csv) == false)
      {
         return false;
      }
      if(AppendRates(symbol, PERIOD_H1, bars, csv) == false)
      {
         return false;
      }
      return true;
   }

   if(AppendRates(symbol, PERIOD_H4, bars, csv) == false)
   {
      return false;
   }
   if(AppendRates(symbol, PERIOD_H1, bars, csv) == false)
   {
      return false;
   }
   return true;
}

bool PushAnalysis(string symbol, string analysis_system)
{
   string csv;
   if(!BuildCsv(symbol, analysis_system, InpBarsPerTimeframe, csv))
   {
      Print("Gold Smart Agent: failed to build ", analysis_system, " OHLCV CSV.");
      return false;
   }

   string quote = CharToString(34);
   string body = "{";
   body += quote + "analysis_system" + quote + ":" + quote + EscapeJson(analysis_system) + quote + ",";
   body += quote + "symbol" + quote + ":" + quote + EscapeJson(symbol) + quote + ",";
   body += quote + "ohlc_csv" + quote + ":" + quote + EscapeJson(csv) + quote;
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

string FetchNextRequest()
{
   char post[];
   char result[];
   string result_headers;
   string headers = "";

   ResetLastError();
   int status = WebRequest("GET", InpRequestEndpoint, headers, InpTimeoutMs, post, result, result_headers);
   if(status == -1)
   {
      Print("Gold Smart Agent: request poll failed. Error: ", GetLastError());
      Print("Allow this URL in MT5: Tools > Options > Expert Advisors > Allow WebRequest: https://smart-system-a-agent.onrender.com");
      return "none";
   }

   string response = CharArrayToString(result, 0, -1, CP_UTF8);
   StringTrimLeft(response);
   StringTrimRight(response);
   StringToLower(response);
   return response;
}

void PollAndPushRequestedSystem()
{
   string requested = FetchNextRequest();
   if(requested == "none" || requested == "")
   {
      Print("Gold Smart Agent: no pending MT5 request.");
      return;
   }

   string symbol = InpSymbol;
   if(symbol == "")
      symbol = _Symbol;

   g_push_count++;
   g_last_push_time = TimeCurrent();
   Print("Gold Smart Agent: request #", g_push_count, " received: ", requested);

   if(InpPingBeforePush)
      PingServer();

   if(requested == "ssa")
   {
      PushAnalysis(symbol, "ssa");
      return;
   }

   if(requested == "upas")
   {
      PushAnalysis(symbol, "upas");
      return;
   }

   Print("Gold Smart Agent: unknown request value: ", requested);
}

int OnInit()
{
   int interval = InpPushIntervalSeconds;
   if(interval < 60)
      interval = 60;

   EventSetTimer(interval);
   Print("Gold Smart Agent On-Demand Push EA started. Poll interval seconds: ", interval);
   Print("Gold Smart Agent Auto Push EA endpoint: ", InpEndpoint);
   Print("Gold Smart Agent Auto Push EA request endpoint: ", InpRequestEndpoint);
   string display_symbol = InpSymbol;
   if(display_symbol == "")
      display_symbol = _Symbol;
   Print("Gold Smart Agent Auto Push EA symbol: ", display_symbol);
   Print("Gold Smart Agent Auto Push EA waits for website requests and pushes only the selected system.");

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
   PollAndPushRequestedSystem();
}
