// Alternative: Simple file-based signal system
// This version reads signals from a JSON file that n8n writes to

//+------------------------------------------------------------------+
//|                                    SimpleSignalEA.mq5           |
//+------------------------------------------------------------------+
#property copyright "Simple Signal Trading"
#property version "1.00"

#include <Trade\Trade.mqh>

// Input parameters
input string SignalFile = "trading_signals.json"; // File to read signals from
input double DefaultLotSize = 0.01;               // Default position size
input int MagicNumber = 123456;                   // EA magic number
input bool EnableTrading = true;                  // Enable/disable trading
input int CheckIntervalSeconds = 1;               // Check file every N seconds

// Global variables
CTrade trade;
datetime lastCheckTime = 0;
string lastProcessedSignal = "";

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
 Print("Simple Signal EA initialized - watching file: ", SignalFile);
 trade.SetExpertMagicNumber(MagicNumber);
 return (INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
 if (TimeCurrent() >= lastCheckTime + CheckIntervalSeconds)
 {
  CheckSignalFile();
  lastCheckTime = TimeCurrent();
 }
}

//+------------------------------------------------------------------+
//| Check signal file for new trades                                 |
//+------------------------------------------------------------------+
void CheckSignalFile()
{
 if (!EnableTrading)
  return;

 int fileHandle = FileOpen(SignalFile, FILE_READ | FILE_TXT);
 if (fileHandle == INVALID_HANDLE)
 {
  // File doesn't exist yet - that's OK
  return;
 }

 string fileContent = "";
 while (!FileIsEnding(fileHandle))
 {
  fileContent += FileReadString(fileHandle) + "\n";
 }
 FileClose(fileHandle);

 if (StringLen(fileContent) == 0)
  return;

 // Extract signal ID to avoid duplicate processing
 string signalId = ExtractJsonValue(fileContent, "signal_id");
 if (signalId == lastProcessedSignal)
  return; // Already processed

 // Process the signal
 ProcessSignal(fileContent);
 lastProcessedSignal = signalId;

 // Clear the file after processing
 FileDelete(SignalFile);
}

//+------------------------------------------------------------------+
//| Process trading signal                                           |
//+------------------------------------------------------------------+
void ProcessSignal(string signalData)
{
 string symbol = ExtractJsonValue(signalData, "symbol");
 string side = ExtractJsonValue(signalData, "side");
 double entry1 = StringToDouble(ExtractJsonValue(signalData, "entry_price_1"));
 double entry2 = StringToDouble(ExtractJsonValue(signalData, "entry_price_2"));
 double entry3 = StringToDouble(ExtractJsonValue(signalData, "entry_price_3"));
 double stopLoss = StringToDouble(ExtractJsonValue(signalData, "stop_loss"));
 double takeProfit = StringToDouble(ExtractJsonValue(signalData, "take_profit"));
 double volume = StringToDouble(ExtractJsonValue(signalData, "volume"));

 if (volume <= 0)
  volume = DefaultLotSize;

 Print("Processing signal: ", symbol, " ", side, " Entries: ", entry1, "/", entry2, "/", entry3);

 // Get current price
 double currentPrice = GetCurrentPrice(symbol, side);

 // Place orders based on current price vs entry levels
 PlaceOrdersIfNeeded(symbol, side, entry1, entry2, entry3, stopLoss, takeProfit, volume, currentPrice);
}

//+------------------------------------------------------------------+
//| Place orders if price conditions are met                        |
//+------------------------------------------------------------------+
void PlaceOrdersIfNeeded(string symbol, string side, double entry1, double entry2, double entry3,
                         double sl, double tp, double volume, double currentPrice)
{
 bool isBuy = (StringFind(StringToUpper(side), "BUY") >= 0);

 // Check each entry level
 if (ShouldExecuteEntry(isBuy, currentPrice, entry1))
 {
  PlaceOrder(symbol, isBuy ? ORDER_TYPE_BUY : ORDER_TYPE_SELL, volume, sl, tp, "Entry1");
 }

 if (ShouldExecuteEntry(isBuy, currentPrice, entry2))
 {
  PlaceOrder(symbol, isBuy ? ORDER_TYPE_BUY : ORDER_TYPE_SELL, volume, sl, tp, "Entry2");
 }

 if (ShouldExecuteEntry(isBuy, currentPrice, entry3))
 {
  PlaceOrder(symbol, isBuy ? ORDER_TYPE_BUY : ORDER_TYPE_SELL, volume, sl, tp, "Entry3");
 }

 // Place pending orders for levels not yet reached
 if (!ShouldExecuteEntry(isBuy, currentPrice, entry1))
 {
  PlaceOrder(symbol, isBuy ? ORDER_TYPE_BUY_LIMIT : ORDER_TYPE_SELL_LIMIT, volume, sl, tp, "Entry1-Pending", entry1);
 }

 if (!ShouldExecuteEntry(isBuy, currentPrice, entry2))
 {
  PlaceOrder(symbol, isBuy ? ORDER_TYPE_BUY_LIMIT : ORDER_TYPE_SELL_LIMIT, volume, sl, tp, "Entry2-Pending", entry2);
 }

 if (!ShouldExecuteEntry(isBuy, currentPrice, entry3))
 {
  PlaceOrder(symbol, isBuy ? ORDER_TYPE_BUY_LIMIT : ORDER_TYPE_SELL_LIMIT, volume, sl, tp, "Entry3-Pending", entry3);
 }
}

//+------------------------------------------------------------------+
//| Check if we should execute at this entry level                  |
//+------------------------------------------------------------------+
bool ShouldExecuteEntry(bool isBuy, double currentPrice, double entryPrice)
{
 if (isBuy)
  return (currentPrice <= entryPrice); // Buy when price is at or below entry
 else
  return (currentPrice >= entryPrice); // Sell when price is at or above entry
}

//+------------------------------------------------------------------+
//| Place individual order                                           |
//+------------------------------------------------------------------+
void PlaceOrder(string symbol, ENUM_ORDER_TYPE orderType, double volume, double sl, double tp,
                string comment, double price = 0)
{
 bool result = false;

 if (orderType == ORDER_TYPE_BUY)
 {
  result = trade.Buy(volume, symbol, 0, sl, tp, comment);
 }
 else if (orderType == ORDER_TYPE_SELL)
 {
  result = trade.Sell(volume, symbol, 0, sl, tp, comment);
 }
 else
 {
  // Pending order
  result = trade.OrderOpen(symbol, orderType, volume, 0, price, sl, tp, ORDER_TIME_GTC, 0, comment);
 }

 if (result)
 {
  Print("Order placed: ", symbol, " ", comment);
 }
 else
 {
  Print("Order failed: ", trade.ResultComment());
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
  return (StringFind(StringToUpper(side), "BUY") >= 0) ? tick.ask : tick.bid;
 }
 return 0;
}

string ExtractJsonValue(string json, string key)
{
 string searchKey = "\"" + key + "\"";
 int start = StringFind(json, searchKey);
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