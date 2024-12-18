import pandas as pd
import numpy as np
import logging
import time
from pymongo import MongoClient
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from statsmodels.tsa.arima.model import ARIMA
from prophet import Prophet  # Prophet is good for time-series forecasting

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Replace with your MongoDB URI if needed
db = client["system_info_db"]  # Database name
stats_collection = db["system_stats"]  # Collection for storing system data
predictive_analysis_collection = db["predictive_analysis"]  # Collection for storing predictions

# Function to fetch historical data from MongoDB
def fetch_historical_data():
    try:
        logging.debug("Fetching historical data from MongoDB...")

        # Fetch system data for CPU, memory, disk, and network from the past data
        data = list(stats_collection.find().sort("timestamp", 1))  # Sort by timestamp (ascending)

        if not data:
            logging.warning("No historical data found in MongoDB.")
            return None
        
        # Convert the data to a pandas DataFrame
        df = pd.DataFrame(data)

        # Select relevant features for prediction (e.g., CPU, Memory, Disk)
        df['timestamp'] = pd.to_datetime(df['timestamp'])  # Ensure timestamp is in datetime format
        df.set_index('timestamp', inplace=True)  # Set timestamp as index

        # You can add more features or choose specific columns for prediction
        features = ["cpu_usage", "memory_percent", "disk_percent", "network_sent", "network_recv"]

        # Prepare data for prediction
        return df[features]
    except Exception as e:
        logging.error(f"Error occurred while fetching historical data: {e}")
        return None

# Function to perform in-depth predictive analysis using ARIMA (for time-series prediction)
def perform_arima_forecast(df, feature):
    try:
        logging.debug(f"Performing ARIMA predictive analysis for {feature}...")

        # Prepare the feature data for prediction
        df_feature = df[feature].dropna()  # Drop missing values

        # Fit ARIMA model
        model = ARIMA(df_feature, order=(5,1,0))  # ARIMA(p,d,q) - (5,1,0) for simplicity
        model_fit = model.fit()

        # Predict the next value (next time step)
        forecast = model_fit.forecast(steps=1)
        prediction = forecast[0]

        logging.info(f"ARIMA prediction for {feature}: {prediction}")
        return prediction
    except Exception as e:
        logging.error(f"Error occurred while performing ARIMA prediction for {feature}: {e}")
        return None

# Function to perform in-depth predictive analysis using Prophet (for time-series forecasting)
def perform_prophet_forecast(df, feature):
    try:
        logging.debug(f"Performing Prophet predictive analysis for {feature}...")

        # Prepare the data for Prophet
        prophet_data = df.reset_index()[['timestamp', feature]]
        prophet_data.columns = ['ds', 'y']  # Prophet expects 'ds' for datetime and 'y' for the value

        # Fit Prophet model
        model = Prophet()
        model.fit(prophet_data)

        # Make a forecast for the next time step (future date)
        future = model.make_future_dataframe(prophet_data, periods=1)
        forecast = model.predict(future)

        prediction = forecast['yhat'].iloc[-1]
        logging.info(f"Prophet prediction for {feature}: {prediction}")
        return prediction
    except Exception as e:
        logging.error(f"Error occurred while performing Prophet prediction for {feature}: {e}")
        return None

# Function to perform multiple linear regression (if predicting multiple features)
def perform_multiple_regression(df):
    try:
        logging.debug("Performing Multiple Linear Regression analysis...")

        # Prepare data for multiple regression (e.g., predicting CPU based on other features)
        df_features = df.dropna()  # Drop missing values
        X = df_features[['memory_percent', 'disk_percent', 'network_sent', 'network_recv']]
        y = df_features['cpu_usage']

        # Fit the model
        model = LinearRegression()
        model.fit(X, y)

        # Predict future CPU usage
        prediction = model.predict([[
            df['memory_percent'].iloc[-1], 
            df['disk_percent'].iloc[-1], 
            df['network_sent'].iloc[-1], 
            df['network_recv'].iloc[-1]
        ]])

        logging.info(f"Multiple Regression prediction for CPU usage: {prediction[0]}")
        return prediction[0]
    except Exception as e:
        logging.error(f"Error occurred while performing multiple regression: {e}")
        return None

# Function to evaluate model performance (using MSE, MAE, R-squared)
def evaluate_model(y_true, y_pred):
    try:
        mse = mean_squared_error(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)

        logging.info(f"Model Evaluation: MSE: {mse}, MAE: {mae}, R-squared: {r2}")
        return mse, mae, r2
    except Exception as e:
        logging.error(f"Error occurred while evaluating model: {e}")
        return None, None, None

# Function to store predictive analysis result in MongoDB
def store_prediction_result(prediction, feature, model_type):
    try:
        logging.debug(f"Storing prediction result for {feature}...")

        # Prepare the prediction result document
        prediction_result = {
            "timestamp": datetime.now(),  # Current timestamp for prediction
            "feature": feature,
            "predicted_value": prediction,
            "model_type": model_type,
            "status": "pending",  # Status can be "pending" or "resolved"
            "description": f"Predicted value for {feature} based on {model_type} model"
        }

        # Insert the prediction result into the MongoDB collection
        predictive_analysis_collection.insert_one(prediction_result)
        logging.info(f"Prediction result for {feature} stored successfully.")
    except Exception as e:
        logging.error(f"Error occurred while storing prediction result for {feature}: {e}")

# Main function to perform in-depth predictive analysis
def main():
    while True:
        logging.debug("Starting predictive analysis cycle...")
        # Fetch historical data from MongoDB
        df = fetch_historical_data()

        if df is not None:
            # Perform ARIMA or Prophet forecasting for each feature
            for feature in ["cpu_usage", "memory_percent", "disk_percent", "network_sent", "network_recv"]:
                # Choose ARIMA or Prophet depending on the feature or use case
                prediction = perform_arima_forecast(df, feature)
                if prediction is not None:
                    store_prediction_result(prediction, feature, "ARIMA")

                prediction = perform_prophet_forecast(df, feature)
                if prediction is not None:
                    store_prediction_result(prediction, feature, "Prophet")

            # Perform multiple regression for overall prediction (e.g., predicting CPU usage based on other metrics)
            prediction = perform_multiple_regression(df)
            if prediction is not None:
                store_prediction_result(prediction, "cpu_usage", "Multiple Regression")

        # Wait for 10 seconds before performing the next cycle of analysis
        logging.debug("Sleeping for 10 seconds before the next predictive analysis cycle...")
        time.sleep(10)

if __name__ == "__main__":
    logging.info("In-depth predictive analysis script started.")
    main()
