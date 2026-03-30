from flask import Flask, render_template, jsonify, request
from jugaad_data.nse import NSELive
import threading, time

app = Flask(__name__)
live = NSELive()

cache = {}
lock = threading.Lock()

# -------------------------------
# Fetch NIFTY 500 stock symbols
# -------------------------------
def get_all_symbols():
    try:
        data = live.live_index("NIFTY 500")
        return [s["symbol"] for s in data["data"]]
    except:
        return ["RELIANCE", "TCS", "INFY", "HDFCBANK"]

ALL_SYMBOLS = get_all_symbols()

# -------------------------------
# Background updater
# -------------------------------
def update_stock_data():
    while True:
        for symbol in ALL_SYMBOLS:
            try:
                q = live.stock_quote(symbol)
                pi = q.get("priceInfo", {})

                with lock:
                    cache[symbol] = {
                        "symbol": symbol,
                        "price": pi.get("lastPrice"),
                        "change": pi.get("change"),
                        "pChange": pi.get("pChange"),
                        "timestamp": time.strftime("%H:%M:%S"),
                    }

            except:
                pass

        time.sleep(15)

# -------------------------------
# Home route
# -------------------------------
@app.route("/")
def home():
    return render_template("dash.html")

# -------------------------------
# Stock API
# -------------------------------
@app.route("/api/quotes")
def all_quotes():
    with lock:
        data = list(cache.values())

    search = request.args.get("search", "").upper()
    gainers = request.args.get("gainers")
    losers = request.args.get("losers")

    if search:
        data = [s for s in data if search in s["symbol"]]

    if gainers:
        data = [s for s in data if s["pChange"] and s["pChange"] > 0]
        data = sorted(data, key=lambda x: x["pChange"], reverse=True)

    elif losers:
        data = [s for s in data if s["pChange"] and s["pChange"] < 0]
        data = sorted(data, key=lambda x: x["pChange"])

    else:
        data = sorted(data, key=lambda x: x["symbol"])

    return jsonify(data)

# -------------------------------
# Run app
# -------------------------------
if __name__ == "__main__":
    threading.Thread(target=update_stock_data, daemon=True).start()
    app.run(debug=True, port=5000)