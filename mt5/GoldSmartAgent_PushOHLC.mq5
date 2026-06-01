//+------------------------------------------------------------------+
//| Gold Smart Agent - Push OHLCV to Web App                         |
//| Place in: MQL5/Scripts/GoldSmartAgent_PushOHLC.mq5               |
//+------------------------------------------------------------------+
#property script_show_inputs

input string InpEndpoint = "https://smart-system-a-agent.onrender.com/api/analyze";
input string InpAnalysisSystem = "ssa"; // ssa, upas, or wave
input string InpSymbol = "";            // blank = current chart symbol
input string InpChartTimeframeLabel = "H1";
input int    InpBarsPerTimeframe = 120;
input int    InpTimeoutMs = 15000;

string g_chart_image_base64 = "";
string g_chart_filename = "";
string g_market_timestamp = "";
double g_current_price = 0.0;

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

string CompactTimestamp(datetime value)
{
   MqlDateTime dt;
   TimeToStruct(value, dt);
   return StringFormat("%04d%02d%02d_%02d%02d%02d", dt.year, dt.mon, dt.day, dt.hour, dt.min, dt.sec);
}

string IsoTimestamp(datetime value)
{
   MqlDateTime dt;
   TimeToStruct(value, dt);
   return StringFormat("%04d-%02d-%02dT%02d:%02d:%02d", dt.year, dt.mon, dt.day, dt.hour, dt.min, dt.sec);
}

double CaptureCurrentPrice(string symbol)
{
   double bid = 0.0;
   double last = 0.0;
   if(SymbolInfoDouble(symbol, SYMBOL_BID, bid) && bid > 0.0)
   {
      Print("Gold Smart Agent: current price captured from bid: ", DoubleToString(bid, _Digits));
      return bid;
   }
   if(SymbolInfoDouble(symbol, SYMBOL_LAST, last) && last > 0.0)
   {
      Print("Gold Smart Agent: current price captured from last: ", DoubleToString(last, _Digits));
      return last;
   }
   Print("Gold Smart Agent: current price capture failed for ", symbol);
   return 0.0;
}

bool CaptureChartScreenshot(string symbol)
{
   g_chart_image_base64 = "";
   g_chart_filename = "";

   string folder = "GoldSmartAgent";
   FolderCreate(folder);

   string timeframe = InpChartTimeframeLabel;
   datetime now = TimeCurrent();
   g_chart_filename = symbol + "_" + timeframe + "_" + CompactTimestamp(now) + ".png";
   string relative_path = folder + "\\" + g_chart_filename;

   ChartRedraw(0);
   ResetLastError();
   if(!ChartScreenShot(0, relative_path, 1280, 720, ALIGN_RIGHT))
   {
      Print("Gold Smart Agent: screenshot capture failed. Error: ", GetLastError());
      return false;
   }

   int handle = FileOpen(relative_path, FILE_READ | FILE_BIN);
   if(handle == INVALID_HANDLE)
   {
      Print("Gold Smart Agent: screenshot file open failed. Error: ", GetLastError(), " path=", relative_path);
      return false;
   }

   int size = (int)FileSize(handle);
   uchar bytes[];
   ArrayResize(bytes, size);
   FileReadArray(handle, bytes, 0, size);
   FileClose(handle);

   uchar key[];
   uchar encoded[];
   ResetLastError();
   int encoded_size = CryptEncode(CRYPT_BASE64, bytes, key, encoded);
   if(encoded_size <= 0)
   {
      Print("Gold Smart Agent: screenshot base64 encode failed. Error: ", GetLastError());
      return false;
   }

   g_chart_image_base64 = CharArrayToString(encoded, 0, encoded_size, CP_UTF8);
   Print("Gold Smart Agent: screenshot captured: MQL5\\Files\\", relative_path, " bytes=", size);
   return true;
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

   g_market_timestamp = IsoTimestamp(TimeCurrent());
   g_current_price = CaptureCurrentPrice(symbol);
   bool screenshot_ok = CaptureChartScreenshot(symbol);
   Print("Gold Smart Agent: screenshot status: ", screenshot_ok);

   string csv;
   if(!BuildCsv(symbol, InpAnalysisSystem, InpBarsPerTimeframe, csv))
   {
      Print("Failed to build OHLCV CSV. Check symbol/timeframe history in MT5.");
      return;
   }

   string body = "{";
   body += "\"analysis_system\":\"" + EscapeJson(InpAnalysisSystem) + "\",";
   body += "\"symbol\":\"" + EscapeJson(symbol) + "\",";
   body += "\"current_price\":" + DoubleToString(g_current_price, _Digits) + ",";
   body += "\"timestamp\":\"" + EscapeJson(g_market_timestamp) + "\",";
   body += "\"chart_timeframe\":\"" + EscapeJson(InpChartTimeframeLabel) + "\",";
   body += "\"chart_filename\":\"" + EscapeJson(g_chart_filename) + "\",";
   body += "\"chart_mime_type\":\"image/png\",";
   body += "\"chart_image\":\"" + EscapeJson(g_chart_image_base64) + "\",";
   body += "\"ohlc_csv\":\"" + EscapeJson(csv) + "\"";
   body += "}";

   uchar post[];
   StringToCharArray(body, post, 0, WHOLE_ARRAY, CP_UTF8);
   if(ArraySize(post) > 0)
      ArrayResize(post, ArraySize(post) - 1);

   uchar result[];
   string result_headers;
   string headers = "Content-Type: application/json\r\n";

   int status = -1;
   for(int attempt = 1; attempt <= 3; attempt++)
   {
      ArrayResize(result, 0);
      result_headers = "";
      ResetLastError();
      status = WebRequest("POST", InpEndpoint, headers, InpTimeoutMs, post, result, result_headers);
      if(status >= 200 && status < 300)
         break;
      Print("Gold Smart Agent: upload attempt ", attempt, " failed. HTTP status=", status, " error=", GetLastError());
      Sleep(1000);
   }

   string response = CharArrayToString(result, 0, -1, CP_UTF8);
   Print("Gold Smart Agent HTTP status: ", status);
   Print(response);
   if(status == -1)
      Print("In MT5, allow this URL under Tools > Options > Expert Advisors > Allow WebRequest: ", InpEndpoint);
}
