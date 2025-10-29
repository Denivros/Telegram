# MetaAPI Trade Execution - N8N Curl Commands

## Basic Trade Execution Template

### Market Buy Order

```bash
curl -X POST "https://XXX.com/users/current/accounts/{accountId}/trade" \
  -H "Content-Type: application/json" \
  -H "auth-token: YOUR_AUTH_TOKEN_HERE" \
  -d '{
    "symbol": "EURUSD",
    "actionType": "ORDER_TYPE_BUY",
    "volume": 0.01,
    "stopLoss": 1.0950,
    "takeProfit": 1.1050,
    "stopLossUnits": "ABSOLUTE_PRICE",
    "takeProfitUnits": "ABSOLUTE_PRICE"
  }'
```

### Market Sell Order

```bash
curl -X POST "https://XXX.com/users/current/accounts/{accountId}/trade" \
  -H "Content-Type: application/json" \
  -H "auth-token: YOUR_AUTH_TOKEN_HERE" \
  -d '{
    "symbol": "EURUSD",
    "actionType": "ORDER_TYPE_SELL",
    "volume": 0.01,
    "stopLoss": 1.1050,
    "takeProfit": 1.0950,
    "stopLossUnits": "ABSOLUTE_PRICE",
    "takeProfitUnits": "ABSOLUTE_PRICE"
  }'
```

### Buy Limit Order

```bash
curl -X POST "https://XXX.com/users/current/accounts/{accountId}/trade" \
  -H "Content-Type: application/json" \
  -H "auth-token: YOUR_AUTH_TOKEN_HERE" \
  -d '{
    "symbol": "EURUSD",
    "actionType": "ORDER_TYPE_BUY_LIMIT",
    "volume": 0.01,
    "openPrice": 1.0980,
    "stopLoss": 1.0950,
    "takeProfit": 1.1050,
    "openPriceUnits": "ABSOLUTE_PRICE",
    "stopLossUnits": "ABSOLUTE_PRICE",
    "takeProfitUnits": "ABSOLUTE_PRICE"
  }'
```

### Sell Limit Order

```bash
curl -X POST "https://XXX.com/users/current/accounts/{accountId}/trade" \
  -H "Content-Type: application/json" \
  -H "auth-token: YOUR_AUTH_TOKEN_HERE" \
  -d '{
    "symbol": "EURUSD",
    "actionType": "ORDER_TYPE_SELL_LIMIT",
    "volume": 0.01,
    "openPrice": 1.1020,
    "stopLoss": 1.1050,
    "takeProfit": 1.0950,
    "openPriceUnits": "ABSOLUTE_PRICE",
    "stopLossUnits": "ABSOLUTE_PRICE",
    "takeProfitUnits": "ABSOLUTE_PRICE"
  }'
```

## N8N HTTP Request Node Configuration

### For N8N HTTP Request Node:

**Method:** POST
**URL:** `https://XXX.com/users/current/accounts/{{$json["accountId"]}}/trade`

**Headers:**

```json
{
  "Content-Type": "application/json",
  "auth-token": "{{$json["authToken"]}}"
}
```

**Body (JSON):**

```json
{
  "symbol": "{{$json["symbol"]}}",
  "actionType": "{{$json["actionType"]}}",
  "volume": {{$json["volume"]}},
  "openPrice": {{$json["openPrice"]}},
  "stopLoss": {{$json["stopLoss"]}},
  "takeProfit": {{$json["takeProfit"]}},
  "stopLossUnits": "ABSOLUTE_PRICE",
  "takeProfitUnits": "ABSOLUTE_PRICE",
  "openPriceUnits": "ABSOLUTE_PRICE"
}
```

## Dynamic N8N Template (Using Telegram Signal Data)

### Complete N8N HTTP Node Setup:

**Method:** POST
**URL:** `https://XXX.com/users/current/accounts/{{$json["account_id"]}}/trade`

**Headers:**

```json
{
  "Content-Type": "application/json",
  "auth-token": "{{$json["meta_api_token"]}}"
}
```

**Body for Buy Signal:**

```json
{
  "symbol": "{{$json["symbol"]}}",
  "actionType": "ORDER_TYPE_BUY",
  "volume": {{$json["volume"] || 0.01}},
  "stopLoss": {{$json["stop_loss"]}},
  "takeProfit": {{$json["take_profit"]}},
  "stopLossUnits": "ABSOLUTE_PRICE",
  "takeProfitUnits": "ABSOLUTE_PRICE"
}
```

**Body for Sell Signal:**

```json
{
  "symbol": "{{$json["symbol"]}}",
  "actionType": "ORDER_TYPE_SELL",
  "volume": {{$json["volume"] || 0.01}},
  "stopLoss": {{$json["stop_loss"]}},
  "takeProfit": {{$json["take_profit"]}},
  "stopLossUnits": "ABSOLUTE_PRICE",
  "takeProfitUnits": "ABSOLUTE_PRICE"
}
```

## All Available Action Types

```javascript
// Market Orders
"ORDER_TYPE_BUY"; // Market buy
"ORDER_TYPE_SELL"; // Market sell

// Pending Orders
"ORDER_TYPE_BUY_LIMIT"; // Buy limit order
"ORDER_TYPE_SELL_LIMIT"; // Sell limit order
"ORDER_TYPE_BUY_STOP"; // Buy stop order
"ORDER_TYPE_SELL_STOP"; // Sell stop order
"ORDER_TYPE_BUY_STOP_LIMIT"; // Buy stop limit
"ORDER_TYPE_SELL_STOP_LIMIT"; // Sell stop limit

// Position Management
"POSITION_MODIFY"; // Modify existing position
"POSITION_PARTIAL"; // Partially close position
"POSITION_CLOSE_ID"; // Close specific position
"POSITIONS_CLOSE_SYMBOL"; // Close all positions for symbol
"POSITION_CLOSE_BY"; // Close position by opposite position

// Order Management
"ORDER_MODIFY"; // Modify pending order
"ORDER_CANCEL"; // Cancel pending order
```

## Price Units Options

```javascript
// For openPrice, stopLoss, takeProfit fields
"ABSOLUTE_PRICE"; // Exact price value
"RELATIVE_PRICE"; // Relative to base price
"RELATIVE_POINTS"; // In points
"RELATIVE_PIPS"; // In pips
"RELATIVE_CURRENCY"; // In account currency
"RELATIVE_BALANCE_PERCENTAGE"; // Percentage of balance
```

## Stop Price Base Options

```javascript
"CURRENT_PRICE"; // Relative to current market price
"OPEN_PRICE"; // Relative to position open price (default)
"STOP_PRICE"; // Relative to previous SL/TP value
```

## Example Success Response

```json
{
  "numericCode": 0,
  "stringCode": "TRADE_RETCODE_DONE",
  "message": "Trade executed successfully",
  "orderId": "12345678",
  "positionId": "87654321"
}
```

## Error Handling in N8N

Add error handling in your N8N workflow:

**Continue on Fail:** Enable
**Ignore SSL Issues:** Disable
**Response Format:** JSON

**Error Response Example:**

```json
{
  "numericCode": 10004,
  "stringCode": "TRADE_RETCODE_INVALID_VOLUME",
  "message": "Invalid volume specified"
}
```

## Integration with Your Telegram Monitor

Your Telegram signal data can be mapped like this:

```javascript
// From your telegram_monitor.py signal output:
{
  "symbol": "EURUSD",           // Maps to symbol
  "signal_type": "buy",         // Maps to actionType (ORDER_TYPE_BUY/SELL)
  "entry_price": 1.1000,        // Maps to openPrice (if limit order)
  "stop_loss": 1.0950,          // Maps to stopLoss
  "take_profit": 1.1050,        // Maps to takeProfit
  "chat_title": "Trading Signals",
  "timestamp": "2025-10-28T15:30:00"
}
```
