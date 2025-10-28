//+------------------------------------------------------------------+
//|                                        TelegramSignalEA.mq5     |
//|                        Copyright 2024, Telegram Signal Trading  |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "Telegram Signal Trading"
#property link "https://www.mql5.com"
#property version "2.00"
#property description "EA that fetches trading signals from N8N and executes trades"

#include <Trade\Trade.mqh>

// Input parameters
input string N8N_GET_URL = "https://n8n.srv881084.hstgr.cloud/webhook/get-pending-signals";     // N8N Get Signals API
input string N8N_UPDATE_URL = "https://n8n.srv881084.hstgr.cloud/webhook/update-signal-status"; // Update signal status
input double DefaultLotSize = 0.01;                                                             // Default position size
input int MagicNumber = 123456;                                                                 // EA magic number
input bool EnableTrading = true;                                                                // Enable/disable trading
input int CheckIntervalSeconds = 5;                                                             // How often to check for signals (seconds)
input int MaxOrdersPerSymbol = 3;                                                               // Max orders per symbol (for 3 entry points)

// Global variables
CTrade trade;
datetime lastCheckTime = 0;
string signals[];
int totalSignals = 0;

struct TradingSignal
{
 string signal_id;
 string symbol;
 string side;
 double entry_price_1;
 double entry_price_2;
 double entry_price_3;
 double stop_loss;
 double take_profit;
 double volume;
 string status;
 datetime created_at;
};

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
 Print("Telegram Signal EA initialized");
 Print("N8N API URL: ", N8N_API_URL);

 trade.SetExpertMagicNumber(MagicNumber);
 trade.SetMarginMode();
 trade.SetTypeFillingBySymbol(Symbol());

 return (INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
 Print("Telegram Signal EA deinitialized. Reason: ", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
 // Check for new signals periodically
 if (TimeCurrent() >= lastCheckTime + CheckIntervalSeconds)
 {
  CheckForNewSignals();
  CheckExistingOrders();
  lastCheckTime = TimeCurrent();
 }
}

//+------------------------------------------------------------------+
//| Check for new trading signals from N8N                          |
//+------------------------------------------------------------------+
void CheckForNewSignals()
{
 if (!EnableTrading)
 {
  return;
 }

 string headers = "Content-Type: application/json\r\n";
 char post_data[];
 char result_data[];
 string result_headers;

 // Make GET request to N8N API to fetch pending signals
 int res = WebRequest(
     "GET",
     N8N_GET_URL,
     headers,
     10000, // 10 second timeout
     post_data,
     result_data,
     result_headers);

 if (res == 200)
 {
  string response = CharArrayToString(result_data);
  Print("Received signals response from N8N");

  // Parse JSON response and process signals
  ProcessSignalResponse(response);
 }
 else if (res == -1)
 {
  Print("WebRequest error: ", GetLastError());
  Print("Make sure the URL is added to allowed URLs in Tools -> Options -> Expert Advisors");
  Print("URL: ", N8N_GET_URL);
 }
 else
 {
  Print("HTTP Error: ", res, " - Response: ", CharArrayToString(result_data));
 }
}

//+------------------------------------------------------------------+
//| Process signal response from N8N API                            |
//+------------------------------------------------------------------+
void ProcessSignalResponse(string response)
{
 // Check if we have signals in the response
 if (StringFind(response, "\"success\":true") == -1)
 {
  Print("No success in response or no pending signals");
  return;
 }

 // Extract signals array - look for signals in the response
 int signals_start = StringFind(response, "\"signals\":[");
 if (signals_start == -1)
 {
  Print("No signals array found in response");
  return;
 }

 // Find the signals array content
 signals_start = StringFind(response, "[", signals_start);
 int signals_end = StringFind(response, "]", signals_start);

 if (signals_end == -1)
 {
  Print("Could not parse signals array");
  return;
 }

 string signals_json = StringSubstr(response, signals_start + 1, signals_end - signals_start - 1);

 // Process each signal (simplified - assumes one signal per response for now)
 if (StringLen(signals_json) > 10) // Has actual signal content
 {
  TradingSignal signal;

  // Extract signal data
  signal.signal_id = ExtractJsonValue(signals_json, "signal_id");
  signal.symbol = ExtractJsonValue(signals_json, "symbol");
  signal.side = ExtractJsonValue(signals_json, "side");
  signal.entry_price_1 = StringToDouble(ExtractJsonValue(signals_json, "entry_price_1"));
  signal.entry_price_2 = StringToDouble(ExtractJsonValue(signals_json, "entry_price_2"));
  signal.entry_price_3 = StringToDouble(ExtractJsonValue(signals_json, "entry_price_3"));
  signal.stop_loss = StringToDouble(ExtractJsonValue(signals_json, "stop_loss"));
  signal.take_profit = StringToDouble(ExtractJsonValue(signals_json, "take_profit"));
  signal.volume = StringToDouble(ExtractJsonValue(signals_json, "volume"));
  signal.status = ExtractJsonValue(signals_json, "status");

  if (signal.symbol != "" && signal.signal_id != "")
  {
   Print("Processing signal: ", signal.signal_id, " for ", signal.symbol);
   ExecuteSignal(signal);
  }
 }
 else
 {
  Print("No pending signals to process");
 }
}

//+------------------------------------------------------------------+
//| Execute trading signal                                           |
//+------------------------------------------------------------------+
void ExecuteSignal(TradingSignal &signal)
{
 Print("Processing signal for ", signal.symbol, " - ", signal.side);

 // Check if we already have orders for this signal
 if (HasOrdersForSignal(signal.signal_id))
 {
  Print("Orders already placed for signal: ", signal.signal_id);
  return;
 }

 // Determine order type based on current price vs entry prices
 double current_price = GetCurrentPrice(signal.symbol, signal.side);

 if (current_price <= 0)
 {
  Print("Unable to get current price for ", signal.symbol);
  return;
 }

 // Place orders for all 3 entry points
 PlaceEntryOrders(signal, current_price);

 // Update signal status in N8N
 UpdateSignalStatus(signal.signal_id, "processing");
}

//+------------------------------------------------------------------+
//| Place entry orders for the 3 price levels                       |
//+------------------------------------------------------------------+
void PlaceEntryOrders(TradingSignal &signal, double current_price)
{
 double entry_prices[3];
 entry_prices[0] = signal.entry_price_1;
 entry_prices[1] = signal.entry_price_2;
 entry_prices[2] = signal.entry_price_3;

 for (int i = 0; i < 3; i++)
 {
  bool is_buy = (StringToLower(signal.side) == "buy");
  ENUM_ORDER_TYPE order_type;

  // Determine if we need market order or pending order
  bool should_place_market = false;
  if (is_buy && current_price <= entry_prices[i])
   should_place_market = true;
  else if (!is_buy && current_price >= entry_prices[i])
   should_place_market = true;

  if (should_place_market)
  {
   // Place market order
   order_type = is_buy ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
   PlaceMarketOrder(signal, order_type, i + 1);
  }
  else
  {
   // Place pending order
   order_type = is_buy ? ORDER_TYPE_BUY_LIMIT : ORDER_TYPE_SELL_LIMIT;
   PlacePendingOrder(signal, order_type, entry_prices[i], i + 1);
  }
 }
}

//+------------------------------------------------------------------+
//| Place market order                                               |
//+------------------------------------------------------------------+
void PlaceMarketOrder(TradingSignal &signal, ENUM_ORDER_TYPE order_type, int entry_number)
{
 string comment = "Signal-" + signal.signal_id + "-Entry" + IntegerToString(entry_number);

 bool result = trade.Buy(signal.volume, signal.symbol, 0, signal.stop_loss, signal.take_profit, comment);
 if (order_type == ORDER_TYPE_SELL)
  result = trade.Sell(signal.volume, signal.symbol, 0, signal.stop_loss, signal.take_profit, comment);

 if (result)
 {
  Print("Market order placed: ", signal.symbol, " Entry ", entry_number);
 }
 else
 {
  Print("Market order failed: ", trade.ResultComment());
 }
}

//+------------------------------------------------------------------+
//| Place pending order                                              |
//+------------------------------------------------------------------+
void PlacePendingOrder(TradingSignal &signal, ENUM_ORDER_TYPE order_type, double price, int entry_number)
{
 string comment = "Signal-" + signal.signal_id + "-Entry" + IntegerToString(entry_number);

 bool result = trade.OrderOpen(
     signal.symbol,
     order_type,
     signal.volume,
     0,     // limit price (0 for market)
     price, // stop price
     signal.stop_loss,
     signal.take_profit,
     ORDER_TIME_GTC,
     0,
     comment);

 if (result)
 {
  Print("Pending order placed: ", signal.symbol, " Entry ", entry_number, " @ ", price);
 }
 else
 {
  Print("Pending order failed: ", trade.ResultComment());
 }
}

//+------------------------------------------------------------------+
//| Check existing orders and update status if needed               |
//+------------------------------------------------------------------+
void CheckExistingOrders()
{
 // Check for filled orders and update N8N accordingly
 int total_orders = OrdersTotal();

 for (int i = 0; i < total_orders; i++)
 {
  if (OrderSelect(i, SELECT_BY_POS))
  {
   string comment = OrderComment();
   if (StringFind(comment, "Signal-") == 0)
   {
    // This is one of our signal orders
    // You could update the status in N8N here if needed
   }
  }
 }
}

//+------------------------------------------------------------------+
//| Utility functions                                                |
//+------------------------------------------------------------------+
double GetCurrentPrice(string symbol, string side)
{
 MqlTick tick;
 if (SymbolInfoTick(symbol, tick))
 {
  return StringToLower(side) == "buy" ? tick.ask : tick.bid;
 }
 return 0;
}

bool HasOrdersForSignal(string signal_id)
{
 int total = OrdersTotal();
 for (int i = 0; i < total; i++)
 {
  if (OrderSelect(i, SELECT_BY_POS))
  {
   if (StringFind(OrderComment(), "Signal-" + signal_id) >= 0)
    return true;
  }
 }
 return false;
}

void UpdateSignalStatus(string signal_id, string status)
{
 string headers = "Content-Type: application/json\r\n";
 datetime now = TimeCurrent();

 string json_data = StringFormat(
     "{\"signal_id\":\"%s\",\"status\":\"%s\",\"updated_at\":\"%s\",\"processed_at\":\"%s\",\"ea_comments\":\"Processed by EA at %s\"}",
     signal_id,
     status,
     TimeToString(now, TIME_DATE | TIME_SECONDS),
     TimeToString(now, TIME_DATE | TIME_SECONDS),
     TimeToString(now, TIME_DATE | TIME_SECONDS));

 char post_data[];
 char result_data[];
 string result_headers;

 StringToCharArray(json_data, post_data, 0, StringLen(json_data));

 int res = WebRequest(
     "POST",
     N8N_UPDATE_URL,
     headers,
     5000,
     post_data,
     result_data,
     result_headers);

 if (res == 200)
 {
  Print("Signal status updated successfully: ", signal_id, " -> ", status);
 }
 else
 {
  Print("Failed to update signal status: ", res, " - ", CharArrayToString(result_data));
 }
}

string ExtractJsonValue(string json, string key)
{
 string search_key = "\"" + key + "\"";
 int start = StringFind(json, search_key);
 if (start == -1)
  return "";

 start = StringFind(json, ":", start) + 1;
 int end = StringFind(json, ",", start);
 if (end == -1)
  end = StringFind(json, "}", start);

 string value = StringSubstr(json, start, end - start);
 StringReplace(value, "\"", "");
 StringReplace(value, " ", "");

 return value;
}

string StringToLower(string str)
{
 string result = "";
 for (int i = 0; i < StringLen(str); i++)
 {
  int char_code = StringGetCharacter(str, i);
  if (char_code >= 65 && char_code <= 90)
   char_code += 32;
  result += CharToString(char_code);
 }
 return result;
}