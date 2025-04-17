from groq import Groq
import pandas as pd
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics
import logging
import os

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Groq client with API key from environment variable
api_key = os.getenv("GROQ_API_KEY", "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")
client = Groq(api_key=api_key)

def process_forecast(product, region=None):
    # Load and preprocess sales data
    try:
        df = pd.read_csv("data/sales_data.csv")
        logger.debug(f"Loaded CSV with shape: {df.shape}")
    except FileNotFoundError:
        raise ValueError("Sales data file not found at data/sales_data.csv")

    df = df[df['Product'] == product]
    
    # Filter by region if specified
    if region:
        df = df[df['Region'] == region]
    
    # Ensure required columns exist
    if df.empty:
        raise ValueError(f"No data found for Product: {product}" + (f" and Region: {region}" if region else ""))
    
    # Prepare data for Prophet
    df = df[['Date', 'Units_Sold']].rename(columns={'Date': 'ds', 'Units_Sold': 'y'})
    df['ds'] = pd.to_datetime(df['ds'])  # Ensure Date is in datetime format
    logger.debug(f"Prepared Prophet data: {df.head()}")

    # Validate data
    if len(df) < 7:  # Minimum data points for a 7-day forecast
        raise ValueError(f"Insufficient data for Product: {product} (need at least 7 days, got {len(df)})")

    # Fit Prophet model with basic seasonality
    model = Prophet(yearly_seasonality=False, weekly_seasonality=True, daily_seasonality=True, seasonality_mode='additive')
    try:
        model.fit(df)
        logger.debug("Prophet model fitted successfully")
    except ValueError as e:
        logger.error(f"Prophet fit failed: {e}")
        raise ValueError(f"Failed to fit Prophet model: {e}")

    # Perform cross-validation to assess accuracy
    try:
        df_cv = cross_validation(model, initial='20 days', period='7 days', horizon='7 days')
        df_p = performance_metrics(df_cv)
        rmse = df_p['rmse'].mean()
        logger.debug(f"Performance Metrics: {df_p.head()}")
        logger.debug(f"Mean RMSE: {rmse}")
    except Exception as e:
        logger.warning(f"Cross-validation failed: {e}, using default RMSE of 0")
        rmse = 0  # Default value if cross-validation fails

    # Make future dataframe for 7 days
    future = model.make_future_dataframe(periods=7)
    forecast = model.predict(future)
    logger.debug(f"Forecast shape: {forecast.shape}, last 7 rows: {forecast[['ds', 'yhat']].tail(7)}")

    # Extract next week's forecast
    next_week = forecast[['ds', 'yhat']].tail(7)
    labels = next_week['ds'].dt.strftime('%b %d').tolist()
    values = next_week['yhat'].round(1).tolist()

    total_demand = sum(values)

    # Get current stock (use the latest stock value for the product/region)
    current_stock_df = pd.read_csv("data/sales_data.csv")
    current_stock_df = current_stock_df[current_stock_df['Product'] == product]
    if region:
        current_stock_df = current_stock_df[current_stock_df['Region'] == region]
    current_stock = int(current_stock_df['Current_Stock'].iloc[-1]) if not current_stock_df.empty else 0

    # Get additional context for the prompt
    most_preferred = current_stock_df['Most_Preferred'].iloc[-1] if not current_stock_df.empty else "No"
    customer_rating = float(current_stock_df['Customer_Rating'].iloc[-1]) if not current_stock_df.empty else 0.0
    discount_offered = float(current_stock_df['Discount_Offered'].iloc[-1]) if not current_stock_df.empty else 0.0
    region_info = region if region else "All Regions"

    # Inventory classification
    if current_stock < total_demand:
        status = "Restock Needed"
    elif current_stock > total_demand * 1.5:
        status = "Overstocked"
    else:
        status = "Optimal"

    # GenAI prompt for Groq with additional context
    prompt = f"""
    Product: {product}
    Region: {region_info}
    Forecasted Demand: {int(total_demand)} units next week
    Current Stock: {current_stock} units
    Most Preferred: {most_preferred}
    Customer Rating: {customer_rating}/5
    Discount Offered: {discount_offered}%
    Suggest a short recommendation for the inventory team in 2 lines, considering demand, stock, customer preferences, and regional factors.
    """

    # Call Groq API for recommendation
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
            max_tokens=80,
            temperature=0.7,
            stream=False,
        )
        ai_message = chat_completion.choices[0].message.content.strip()
        logger.debug(f"AI Message: {ai_message}")
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        ai_message = "Failed to generate recommendation due to API error"

    # Log debug information
    logger.debug(f"Forecast Data: labels={labels}, values={values}, Status: {status}, AI: {ai_message}")

    return {
        "labels": labels,
        "values": values,
        "total_demand": int(total_demand),
        "current_stock": current_stock,
        "rmse": float(rmse)  # Include RMSE in the response for frontend display
    }, status, ai_message