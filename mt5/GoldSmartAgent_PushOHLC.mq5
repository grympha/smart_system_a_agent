//+------------------------------------------------------------------+
//| Gold Smart Agent - Push OHLCV to Web App                         |
//| Place in: MQL5/Scripts/GoldSmartAgent_PushOHLC.mq5               |
//+------------------------------------------------------------------+
#property script_show_inputs

input string InpEndpoint = "https://smart-system-a-agent.onrender.com/api/analyze";
input string InpAnalysisSystem = "ssa"; // ssa, upas, or wave
input string InpSymbol = "";            // blank = current chart symbol
input int    InpBarsPerTimeframe = 120;
input int    InpTimeoutMs = 15000;

string EscapeJson(string value)
{
   string escaped = "";
   int length = StringLen(value);
   for(int i = 0; i < length; i++)
   {
      ushort ch = StringGetCharacter(value, i);
      if(ch == 34)       // double quote
         escaped += "\\\"";
      else if(ch == 92)  // backslash
         escaped += "\\\\";
      else if(ch == 13)  // carriage return
         escaped += "\\r";
      else if(ch == 10)  // line feed
         escaped += "\\n";
      else if(ch == 9)   // tab
         escaped += "\\t";
      else
         escaped += ShortToString(ch);
   }
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
      Print("Not enough candles for ", TimeframeName(timeframe), ". Copied: ", copied);
      return false;
   }

   string tf = TimeframeName(timeframe);
   for(int i = 0; i < copied; i++)
   {
      csv += tf + ",";
      csv += TimeToString(rates[i].time, TIME_DATE | TIME_MINUTES) + ",";
      csv += DoubleToString(rates[i].open, _Digits) + ",";
      csv += DoubleToString(rates[i].high, _Digits) + ",";
      csv += DoubleToString(rates[i].low, _Digits) + ",";
      csv += DoubleToString(rates[i].close, _Digits) + ",";
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

   if(system == "wave")
   {
      return AppendRates(symbol, PERIOD_D1, bars, csv)
         && AppendRates(symbol, PERIOD_H4, bars, csv)
         && AppendRates(symbol, PERIOD_H1, bars, csv);
   }

   return AppendRates(symbol, PERIOD_H4, bars, csv)
      && AppendRates(symbol, PERIOD_H1, bars, csv);
}

void OnStart()
{
   string symbol = InpSymbol;
   if(symbol == "")
      symbol = _Symbol;

   string csv;
   if(!BuildCsv(symbol, InpAnalysisSystem, InpBarsPerTimeframe, csv))
   {
      Print("Failed to build OHLCV CSV. Check symbol/timeframe history in MT5.");
      return;
   }

   string body = "{";
   body += "\"analysis_system\":\"" + EscapeJson(InpAnalysisSystem) + "\",";
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
      Print("WebRequest failed. Error: ", GetLastError());
      Print("In MT5, allow this URL under Tools > Options > Expert Advisors > Allow WebRequest: ", InpEndpoint);
      return;
   }

   string response = CharArrayToString(result, 0, -1, CP_UTF8);
   Print("Gold Smart Agent HTTP status: ", status);
   Print(response);
}
