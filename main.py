from flask import Flask, request, jsonify
import os
import requests
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()
app = Flask(__name__)

# --- FIX: Allow both GET (for browsers) and POST (for Puch AI) requests ---
@app.route('/', methods=['GET', 'POST'])
def home():
    """
    Handles homepage requests.
    - GET: Shows the HTML documentation page.
    - POST: Responds to validation checks from clients like Puch AI.
    """
    if request.method == 'POST':
        # If Puch AI sends a POST to validate, just send back a success message.
        return jsonify({"status": "ok", "message": "POST request successful"})

    # If it's a GET request, show the beautiful documentation page.
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MCP Server Status</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background-color: #eaf2f8; font-family: 'Segoe UI', Roboto, sans-serif; }
            .header-jumbotron { background-color: #fff9e6; }
            .card { border: none; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
            .badge.bg-primary { background-color: #d1c4e9 !important; color: #4527a0; }
            .badge.bg-danger { background-color: #f8bbd0 !important; color: #880e4f; }
            .badge.bg-secondary { background-color: #c8e6c9 !important; color: #1b5e20; }
            .card-title code { color: #5c6bc0; }
        </style>
    </head>
    <body>
        <div class="container my-5">
            <div class="p-5 mb-4 header-jumbotron rounded-3">
                <div class="container-fluid py-4">
                    <h1 class="display-5 fw-bold">✨ SmartDealFinderIndia MCP</h1>
                    <p class="col-md-8 fs-4">A custom tool to find the best product deals in India, built for the Puch AI Hackathon.</p>
                </div>
            </div>
            <h2>Available Tools</h2>
            <div class="row">
                <div class="col-lg-8 mb-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h5 class="card-title"><code>/search</code> <span class="badge bg-primary">GET</span></h5>
                            <p class="card-text">Finds and ranks products from Google Shopping India based on value.</p>
                            <h6>Parameters:</h6>
                            <ul class="list-group list-group-flush">
                                <li class="list-group-item"><code>keyword</code> <span class="badge rounded-pill bg-danger">required</span></li>
                                <li class="list-group-item"><code>max_price</code> <span class="badge rounded-pill bg-danger">required</span></li>
                                <li class="list-group-item"><code>min_price</code> <span class="badge rounded-pill bg-secondary">optional</span></li>
                                <li class="list-group-item"><code>min_rating</code> <span class="badge rounded-pill bg-secondary">optional</span></li>
                            </ul>
                        </div>
                    </div>
                </div>
                <div class="col-lg-4 mb-4">
                    <div class="card h-100">
                        <div class="card-body">
                            <h5 class="card-title"><code>/validate</code> <span class="badge bg-primary">GET</span></h5>
                            <p class="card-text">Validates the server for connection to the Puch AI platform.</p>
                        </div>
                    </div>
                </div>
            </div>
            <footer class="text-center text-muted mt-5"><p>Developed with ❤️ in Hyderabad</p></footer>
        </div>
    </body>
    </html>
    """
    return html_content

# --- Required validation tool for Puch AI ---
@app.route('/validate')
def validate_mcp():
    """Validates the server by returning a phone number."""
    phone_number = {"number": "+919876543210"} # Replace with your number
    return jsonify(phone_number)

# --- Your existing product search tool ---
@app.route('/search')
def search_products():
    """Searches for products using SerpApi with advanced filtering."""
    keyword = request.args.get('keyword')
    max_price_str = request.args.get('max_price')
    min_price_str = request.args.get('min_price', default='0')
    min_rating_str = request.args.get('min_rating', default='0')
    serpapi_key = os.getenv("SERPAPI_KEY")
    if not all([keyword, max_price_str, serpapi_key]):
        return jsonify({"error": "Missing 'keyword', 'max_price', or API key"}), 400
    try:
        max_price, min_price, min_rating = float(max_price_str), float(min_price_str), float(min_rating_str)
    except ValueError:
        return jsonify({"error": "Price/rating must be numbers."}), 400
    params = {"api_key": serpapi_key, "engine": "google_shopping", "q": keyword, "hl": "en", "gl": "in"}
    try:
        response = requests.get("https://serpapi.com/search.json", params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return jsonify({"error": f"API request failed: {e}"}), 502
    clean_results = []
    for item in data.get("shopping_results", []):
        try:
            price, rating = float(item.get("extracted_price", 0)), float(item.get("rating", 0))
            if price == 0 or not (min_price <= price <= max_price) or rating < min_rating: continue
            clean_results.append({
                "name": item.get("title"), "source": item.get("source"), "price": price,
                "rating": rating, "link": item.get("product_link"), "thumbnail": item.get("thumbnail"),
                "value_score": rating / price if price != 0 else 0
            })
        except (TypeError, ValueError): continue
    clean_results.sort(key=lambda x: x["value_score"], reverse=True)
    return jsonify(clean_results)

# --- Run the Flask App ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)