# File Writer Service for MT5 Signal Files
# This service runs on your MT5 VPS and writes signal files for the EA to read

from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# MT5 Data Directory - adjust this path for your MT5 installation
MT5_DATA_PATH = "C:/Users/YourUser/AppData/Roaming/MetaQuotes/Terminal/D0E8209F77C8CF37AD8BF550E51FF075/MQL5/Files/"
SIGNAL_FILE = "trading_signals.json"

@app.route('/write-signal-file', methods=['POST'])
def write_signal_file():
    """Receive signal from n8n and write to file for MT5 EA"""
    try:
        signal_data = request.get_json()
        
        # Validate required fields
        required_fields = ['signal_id', 'symbol', 'side', 'entry_price_1', 'entry_price_2', 
                          'entry_price_3', 'stop_loss', 'take_profit']
        
        for field in required_fields:
            if field not in signal_data:
                return jsonify({"success": False, "error": f"Missing field: {field}"}), 400
        
        # Write signal to file that EA can read
        file_path = os.path.join(MT5_DATA_PATH, SIGNAL_FILE)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write JSON data to file
        with open(file_path, 'w') as f:
            json.dump(signal_data, f, indent=2)
        
        print(f"Signal written to file: {file_path}")
        print(f"Signal data: {json.dumps(signal_data, indent=2)}")
        
        return jsonify({
            "success": True, 
            "message": "Signal file created",
            "file_path": file_path,
            "signal_id": signal_data.get('signal_id')
        })
        
    except Exception as e:
        print(f"Error writing signal file: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/check-signal-file', methods=['GET'])
def check_signal_file():
    """Check if signal file exists and return its contents"""
    try:
        file_path = os.path.join(MT5_DATA_PATH, SIGNAL_FILE)
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            return jsonify({
                "success": True,
                "file_exists": True,
                "data": data,
                "file_modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            })
        else:
            return jsonify({
                "success": True,
                "file_exists": False,
                "message": "No signal file found"
            })
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/clear-signal-file', methods=['POST'])
def clear_signal_file():
    """Clear/delete the signal file"""
    try:
        file_path = os.path.join(MT5_DATA_PATH, SIGNAL_FILE)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({"success": True, "message": "Signal file cleared"})
        else:
            return jsonify({"success": True, "message": "No signal file to clear"})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    """Check service status"""
    return jsonify({
        "service": "MT5 Signal File Writer",
        "status": "running",
        "mt5_data_path": MT5_DATA_PATH,
        "signal_file": SIGNAL_FILE,
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    print(f"MT5 Signal File Writer starting...")
    print(f"MT5 Data Path: {MT5_DATA_PATH}")
    print(f"Signal File: {SIGNAL_FILE}")
    print(f"Make sure to update MT5_DATA_PATH for your MT5 installation!")
    
    app.run(host='0.0.0.0', port=8080, debug=False)