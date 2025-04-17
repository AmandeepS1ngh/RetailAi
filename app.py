from flask import Flask, render_template, request, jsonify
from forecast import process_forecast
import os
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Ensure the data directory exists
os.makedirs("data", exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/products')
def products():
    return render_template('products.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file and file.filename.endswith('.csv'):
        filepath = "data/sales_data.csv"
        file.save(filepath)
        logger.debug(f"File saved to {filepath}")  # Debug
        return jsonify({"message": "File uploaded successfully"}), 200
    logger.debug(f"Failed to save file: {file}")  # Debug
    return jsonify({"error": "Invalid file. Please upload a CSV file."}), 400

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    product = data.get('product')
    region = data.get('region')  # Optional

    if not product:
        return jsonify({"error": "Product name is required"}), 400

    try:
        forecast_data, status, ai_message = process_forecast(product, region)
        logger.debug(f"Forecast data: {forecast_data}, Status: {status}, AI: {ai_message}")
        response = {
            "labels": forecast_data["labels"],
            "values": forecast_data["values"],
            "total_demand": forecast_data["total_demand"],
            "current_stock": forecast_data["current_stock"],
            "status": status,
            "ai": ai_message
        }
        return jsonify(response)
    except ValueError as e:
        logger.error(f"ValueError in analyze: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error in analyze: {e}", exc_info=True)
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)