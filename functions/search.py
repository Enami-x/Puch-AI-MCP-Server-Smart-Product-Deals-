import json
import os
from urllib.parse import parse_qs, urlparse
import requests
from cloudflare.workers.types import Response

# This function is automatically triggered for requests to /search
def onRequest(context):
    """Searches for products using SerpApi with advanced filtering."""
    # Get environment variable for the API key from Cloudflare settings
    serpapi_key = os.environ.get("SERPAPI_KEY")

    # Get query parameters from the request URL
    query_params = parse_qs(urlparse(context.request.url).query)
    
    keyword = query_params.get('keyword', [None])[0]
    max_price_str = query_params.get('max_price', [None])[0]
    min_price_str = query_params.get('min_price', ['0'])[0]
    min_rating_str = query_params.get('min_rating', ['0'])[0]

    # --- Input Validation ---
    if not all([keyword, max_price_str, serpapi_key]):
        error_response = {"error": "Missing 'keyword', 'max_price', or the SERPAPI_KEY is not set."}
        return Response(json.dumps(error_response), status=400, headers={'Content-Type': 'application/json'})

    try:
        max_price = float(max_price_str)
        min_price = float(min_price_str)
        min_rating = float(min_rating_str)
    except (ValueError, TypeError):
        error_response = {"error": "Price and rating parameters must be valid numbers."}
        return Response(json.dumps(error_response), status=400, headers={'Content-Type': 'application/json'})

    # --- Call the SerpApi service ---
    params = {"api_key": serpapi_key, "engine": "google_shopping", "q": keyword, "hl": "en", "gl": "in"}
    try:
        response = requests.get("https://serpapi.com/search.json", params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        error_response = {"error": f"API request failed: {e}"}
        return Response(json.dumps(error_response), status=502, headers={'Content-Type': 'application/json'})

    # --- Process the results ---
    clean_results = []
    for item in data.get("shopping_results", []):
        try:
            price = float(item.get("extracted_price", 0))
            rating = float(item.get("rating", 0))
            
            if price == 0 or not (min_price <= price <= max_price) or rating < min_rating:
                continue

            clean_results.append({
                "name": item.get("title"),
                "source": item.get("source"),
                "price": price,
                "rating": rating,
                "link": item.get("product_link"),
                "thumbnail": item.get("thumbnail"),
                "value_score": rating / price if price != 0 else 0
            })
        except (TypeError, ValueError):
            continue

    clean_results.sort(key=lambda x: x["value_score"], reverse=True)
    
    # --- Return the final JSON as a Response object ---
    return Response(json.dumps(clean_results), headers={'Content-Type': 'application/json'})
