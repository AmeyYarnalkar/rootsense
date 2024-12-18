import psutil
import pandas as pd
import time
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import logging
import pymongo

# MongoDB setup
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["system_performance_db"]
performance_collection = db["performance_data"]  # Collection for raw performance data
analysis_collection = db["performance_analysis_results"]  # Separate collection for analysis results

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Define thresholds for system metrics
CPU_THRESHOLD = 80
MEMORY_THRESHOLD = 80
DISK_THRESHOLD = 80
NETWORK_THRESHOLD = 100000000  # 100 MB

def collect_system_data():
    """Collects system metrics like CPU, memory, disk, and network usage."""
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    network = psutil.net_io_counters()

    # Prepare the system data
    system_data = {
        "cpu_usage": cpu_usage,
        "memory_percent": memory.percent,
        "disk_percent": disk.percent,
        "network_sent": network.bytes_sent,
        "network_recv": network.bytes_recv
    }

    return system_data

def label_system_health(data):
    """Labels system health based on threshold values."""
    label = "Healthy"

    # Check if system metrics exceed the threshold
    if data["cpu_usage"] > CPU_THRESHOLD or data["memory_percent"] > MEMORY_THRESHOLD or data["disk_percent"] > DISK_THRESHOLD or data["network_sent"] > NETWORK_THRESHOLD or data["network_recv"] > NETWORK_THRESHOLD:
        label = "Warning"

    if data["cpu_usage"] > 90 or data["memory_percent"] > 90 or data["disk_percent"] > 90 or data["network_sent"] > NETWORK_THRESHOLD * 1.5 or data["network_recv"] > NETWORK_THRESHOLD * 1.5:
        label = "Critical"

    return label

def store_data_in_mongodb(data, label):
    """Stores the raw performance data in MongoDB."""
    data["timestamp"] = datetime.now()
    data["label"] = label  # Store the health label (Healthy, Warning, Critical)
    try:
        performance_collection.insert_one(data)
        logging.info(f"Data stored in MongoDB at {data['timestamp']}")
    except Exception as e:
        logging.error(f"Error storing data in MongoDB: {e}")

def store_analysis_results_in_mongodb(prediction_label, model_accuracy):
    """Stores the analysis result in the performance_analysis_results collection."""
    analysis_result = {
        "timestamp": datetime.now(),
        "predicted_health": prediction_label,
        "model_accuracy": model_accuracy
    }

    try:
        analysis_collection.insert_one(analysis_result)
        logging.info(f"Analysis result stored in MongoDB: {analysis_result}")
    except Exception as e:
        logging.error(f"Error storing analysis result in MongoDB: {e}")

def get_data_from_mongodb():
    """Fetch data from MongoDB for training the model."""
    data = pd.DataFrame(list(performance_collection.find()))
    return data

def preprocess_data(data):
    """Preprocess the data for machine learning model."""
    # Drop the '_id' field, as it's not relevant for the ML model
    data = data.drop(columns=['_id', 'timestamp'])

    # Convert labels to numeric values: Healthy=0, Warning=1, Critical=2
    label_mapping = {"Healthy": 0, "Warning": 1, "Critical": 2}
    data["label"] = data["label"].map(label_mapping)

    return data

def train_model():
    """Train the machine learning model on historical data."""
    data = get_data_from_mongodb()
    if len(data) > 0:
        # Preprocess the data
        data = preprocess_data(data)
        
        # Separate features and labels
        X = data.drop(columns=['label'])
        y = data['label']

        # Split data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train the Random Forest model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Evaluate the model
        y_pred = model.predict(X_test)
        print("Model Evaluation:")
        print(classification_report(y_test, y_pred))

        return model
    else:
        logging.warning("No data available to train the model.")
        return None

def predict_system_health(model):
    """Predict the health of the system using the trained model."""
    system_data = collect_system_data()

    # Preprocess data for prediction
    input_data = pd.DataFrame([system_data])
    prediction = model.predict(input_data)
    
    # Convert the numeric prediction to label
    label_mapping = {0: "Healthy", 1: "Warning", 2: "Critical"}
    predicted_label = label_mapping[prediction[0]]

    logging.info(f"Predicted system health: {predicted_label}")
    return predicted_label

def main():
    """Main function to collect data, train the model, and predict system health."""
    model = train_model()  # Train the model using historical data

    while True:
        logging.debug("Collecting system data...")

        # Collect real-time system data and label it
        system_data = collect_system_data()
        label = label_system_health(system_data)

        # Store data and label in MongoDB (performance data collection)
        store_data_in_mongodb(system_data, label)

        if model:
            # Predict system health using the trained model
            predicted_label = predict_system_health(model)
            
            # Store analysis result in MongoDB (performance_analysis_results collection)
            store_analysis_results_in_mongodb(predicted_label, 0.95)  # Assuming model accuracy is 95%

        time.sleep(5)  # Collect data every 5 seconds

if __name__ == "__main__":
    logging.info("Starting system performance analysis with machine learning...")
    main()
