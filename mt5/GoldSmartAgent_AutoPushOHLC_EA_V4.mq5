//+------------------------------------------------------------------+
//| Gold Smart Agent - Auto Push OHLCV EA V4                         |
//| Place in: MQL5/Experts/Advisors/GoldSmartAgent_AutoPushOHLC_EA_V4.mq5 |
//| Pushes SSA, UPAS, Wave, and Elliot Wave 3 every 5 minutes.        |
//+------------------------------------------------------------------+
#property strict

input string InpEndpoint = "https://smart-system-a-agent.onrender.com/api/analyze";
input string InpSymbol = "";            // blank = current chart symbol
input string InpChartTimeframeLabel = "H1";
input int    InpBarsPerTimeframe = 120;
input int    InpPushIntervalSeconds = 300;
input int    InpTimeoutMs = 15000;
input bool   InpPushOnStart = true;
input bool   InpPingBeforePush = true;

datetime g_last_push_time = 0;
int      g_push_count = 0;
string   g_csv = "";
string   g_chart_image_base64 = "";
string   g_chart_filename = "";
string   g_chart_image_h1_base64 = "";
string   g_chart_image_h4_base64 = "";
string   g_chart_filename_h1 = "";
string   g_chart_filename_h4 = "";
string   g_market_timestamp = "";
double   g_current_price = 0.0;

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
   if(timeframe == PERIOD_M15) return "M15";
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

bool ReadScreenshotBase64(string relative_path, string &image_base64)
{
   image_base64 = "";
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

   image_base64 = CharArrayToString(encoded, 0, encoded_size, CP_UTF8);
   Print("Gold Smart Agent: screenshot encoded: MQL5\\Files\\", relative_path, " bytes=", size);
   return true;
}

bool CaptureTimeframeScreenshot(string symbol, ENUM_TIMEFRAMES timeframe, string &image_base64, string &filename)
{
   image_base64 = "";
   filename = "";

   string folder = "GoldSmartAgent";
   FolderCreate(folder);

   string timeframe_label = TimeframeName(timeframe);
   datetime now = TimeCurrent();
   filename = symbol + "_" + timeframe_label + "_" + CompactTimestamp(now) + ".png";
   string relative_path = folder + "\\" + filename;

   long chart_id = 0;
   bool temporary_chart = false;
   if(_Symbol == symbol && _Period == timeframe)
   {
      chart_id = ChartID();
   }
   else
   {
      ResetLastError();
      chart_id = ChartOpen(symbol, timeframe);
      if(chart_id <= 0)
      {
         Print("Gold Smart Agent: failed to open ", timeframe_label, " chart for screenshot. Error: ", GetLastError());
         return false;
      }
      temporary_chart = true;
      Sleep(1500);
   }

   ChartRedraw(chart_id);
   Sleep(500);
   ResetLastError();
   if(!ChartScreenShot(chart_id, relative_path, 1280, 720, ALIGN_RIGHT))
   {
      Print("Gold Smart Agent: ", timeframe_label, " screenshot capture failed. Error: ", GetLastError());
      if(temporary_chart)
         ChartClose(chart_id);
      return false;
   }

   bool encoded_ok = ReadScreenshotBase64(relative_path, image_base64);
   if(temporary_chart)
      ChartClose(chart_id);

   if(encoded_ok)
      Print("Gold Smart Agent: ", timeframe_label, " screenshot captured: ", filename);
   return encoded_ok;
}

bool CaptureH1H4ChartScreenshots(string symbol)
{
   g_chart_image_h1_base64 = "";
   g_chart_image_h4_base64 = "";
   g_chart_filename_h1 = "";
   g_chart_filename_h4 = "";

   bool h1_ok = CaptureTimeframeScreenshot(symbol, PERIOD_H1, g_chart_image_h1_base64, g_chart_filename_h1);
   bool h4_ok = CaptureTimeframeScreenshot(symbol, PERIOD_H4, g_chart_image_h4_base64, g_chart_filename_h4);

   if(h1_ok)
   {
      g_chart_image_base64 = g_chart_image_h1_base64;
      g_chart_filename = g_chart_filename_h1;
   }
   else if(h4_ok)
   {
      g_chart_image_base64 = g_chart_image_h4_base64;
      g_chart_filename = g_chart_filename_h4;
   }

   Print("Gold Smart Agent: H1/H4 screenshot status. H1=", h1_ok, " H4=", h4_ok);
   return (h1_ok || h4_ok);
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
      string candle_volume = IntegerToString((long)rates[i].tick_volume);
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

   if(system == "wave")
   {
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

   if(system == "elliot_wave3")
   {
      if(AppendRates(symbol, PERIOD_H4, bars) == false)
      {
         return false;
      }
      if(AppendRates(symbol, PERIOD_H1, bars) == false)
      {
         return false;
      }
      if(AppendRates(symbol, PERIOD_M15, bars) == false)
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
   body += quote + "current_price" + quote + ":" + DoubleToString(g_current_price, _Digits) + ",";
   body += quote + "timestamp" + quote + ":" + quote + EscapeJson(g_market_timestamp) + quote + ",";
   body += quote + "chart_timeframe" + quote + ":" + quote + EscapeJson(InpChartTimeframeLabel) + quote + ",";
   body += quote + "chart_filename" + quote + ":" + quote + EscapeJson(g_chart_filename) + quote + ",";
   body += quote + "chart_mime_type" + quote + ":" + quote + "image/png" + quote + ",";
   body += quote + "chart_image" + quote + ":" + quote + EscapeJson(g_chart_image_base64) + quote + ",";
   body += quote + "chart_images" + quote + ":{";
   body += quote + "H1" + quote + ":" + quote + EscapeJson(g_chart_image_h1_base64) + quote + ",";
   body += quote + "H4" + quote + ":" + quote + EscapeJson(g_chart_image_h4_base64) + quote;
   body += "},";
   body += quote + "chart_filenames" + quote + ":{";
   body += quote + "H1" + quote + ":" + quote + EscapeJson(g_chart_filename_h1) + quote + ",";
   body += quote + "H4" + quote + ":" + quote + EscapeJson(g_chart_filename_h4) + quote;
   body += "},";
   body += quote + "ohlc_csv" + quote + ":" + quote + EscapeJson(g_csv) + quote;
   body += "}";

   char post[];
   StringToCharArray(body, post, 0, WHOLE_ARRAY, CP_UTF8);
   if(ArraySize(post) > 0)
      ArrayResize(post, ArraySize(post) - 1);

   char result[];
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
      Print("Gold Smart Agent: upload attempt ", attempt, " failed for ", analysis_system, ". HTTP status=", status, " error=", GetLastError());
      Sleep(1000);
   }

   string response = CharArrayToString(result, 0, -1, CP_UTF8);
   Print("Gold Smart Agent: ", analysis_system, " push HTTP status: ", status);
   Print(response);
   if(status == -1)
      Print("Allow this URL in MT5: Tools > Options > Expert Advisors > Allow WebRequest: https://smart-system-a-agent.onrender.com");
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
   Print("Gold Smart Agent: pushing SSA, UPAS, Wave, and Elliot Wave 3 for ", symbol, ". Interval seconds: ", InpPushIntervalSeconds);

   g_market_timestamp = IsoTimestamp(TimeCurrent());
   g_current_price = CaptureCurrentPrice(symbol);
   bool screenshot_ok = CaptureH1H4ChartScreenshots(symbol);
   if(!screenshot_ok)
      screenshot_ok = CaptureChartScreenshot(symbol);
   Print("Gold Smart Agent: batch H1/H4 screenshot status: ", screenshot_ok);

   if(InpPingBeforePush)
      PingServer();

   bool ssa_ok = PushAnalysis(symbol, "ssa");
   bool upas_ok = PushAnalysis(symbol, "upas");
   bool wave_ok = PushAnalysis(symbol, "wave");
   bool ew3_ok = PushAnalysis(symbol, "elliot_wave3");
   Print("Gold Smart Agent: push cycle complete. SSA=", ssa_ok, " UPAS=", upas_ok, " WAVE=", wave_ok, " EW3=", ew3_ok);
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
   Print("Gold Smart Agent Auto Push EA V4 pushes SSA, UPAS, Wave, and Elliot Wave 3 every 5 minutes.");

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
