//+------------------------------------------------------------------+
//| Gold Smart Agent - Auto Push OHLCV EA                            |
//| Place in: MQL5/Experts/GoldSmartAgent_AutoPushOHLC_EA.mq5         |
//| Pushes both Smart System A and UPAS data every 5 minutes.         |
//+------------------------------------------------------------------+
#property strict

input string InpEndpoint = "https://smart-system-a-agent.onrender.com/api/analyze";
input string InpSymbol = "";            // blank = current chart symbol
input int    InpBarsPerTimeframe = 120;
input int    InpPushIntervalSeconds = 300;
input int    InpTimeoutMs = 15000;
input bool   InpPushOnStart = true;

string EscapeJson(string value)
{
   StringReplace(value, "\\", "\\\\");
   StringReplace(value, "\"", "\\\"");
   StringReplace(value, "\r", "\\r");
   StringReplace(value, "\n", "\\n");
   StringReplace(value, "\t", "\\t");
   return value;
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
      return AppendRates(symbol, PERIOD_MN1, bars, csv)
         && AppendRates(symbol, PERIOD_W1, bars, csv)
         && AppendRates(symbol, PERIOD_D1, bars, csv)
         && AppendRates(symbol, PERIOD_H4, bars, csv)
         && AppendRates(symbol, PERIOD_H1, bars, csv);
   }

   return AppendRates(symbol, PERIOD_H4, bars, csv)
      && AppendRates(symbol, PERIOD_H1, bars, csv);
}

bool PushAnalysis(string symbol, string analysis_system)
{
   string csv;
   if(!BuildCsv(symbol, analysis_system, InpBarsPerTimeframe, csv))
   {
      Print("Gold Smart Agent: failed to build ", analysis_system, " OHLCV CSV.");
      return false;
   }

   string body = "{";
   body += "\"analysis_system\":\"" + EscapeJson(analysis_system) + "\",";
   body += "\"symbol\":\"" + EscapeJson(symbol) + "\",";
   body += "\"ohlc_csv\":\"" + EscapeJson(csv) + "\"";
   body += "}";

   uchar post[];
   StringToCharArray(body, post, 0, WHOLE_ARRAY, CP_UTF8);
   if(ArraySize(post) > 0)
      ArrayResize(post, ArraySize(post) - 1);

   uchar result[];
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
   return status >= 200 && status < 300;
}

void PushBothSystems()
{
   string symbol = InpSymbol;
   if(symbol == "")
      symbol = _Symbol;

   Print("Gold Smart Agent: pushing SSA and UPAS for ", symbol);
   PushAnalysis(symbol, "ssa");
   PushAnalysis(symbol, "upas");
}

int OnInit()
{
   int interval = InpPushIntervalSeconds;
   if(interval < 60)
      interval = 60;

   EventSetTimer(interval);
   Print("Gold Smart Agent Auto Push EA started. Interval seconds: ", interval);

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
