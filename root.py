import pandas as pd
import numpy as np
import pymongo
import logging
from datetime import datetime
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.preprocessing import StandardScaler

# Set up logging for debugging and tracking
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["system_info_db"]
collection = db["system_stats"]
logs_collection = db["system_logs"]
rca_collection = db["rca_results"]  # New collection for Root Cause Analysis results

# Define thresholds for anomaly detection
CPU_THRESHOLD = 80
MEMORY_THRESHOLD = 80
DISK_THRESHOLD = 80
NETWORK_THRESHOLD = 100000000  # Bytes

# Fetch system data from MongoDB
def fetch_data_from_mongo(limit=100):
    try:
        cursor = collection.find().sort("timestamp", pymongo.ASCENDING).limit(limit)
        data = list(cursor)
        logging.debug(f"Fetched {len(data)} records from MongoDB.")
        return data
    except Exception as e:
        logging.error(f"Error fetching data from MongoDB: {e}")
        return []

# Preprocess the system data for analysis (Feature Engineering)
def preprocess_data(data):
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    # Feature Engineering: Calculate rolling averages for CPU, Memory, Disk, Network
    df['cpu_rolling_avg'] = df['cpu_usage'].rolling(window=5).mean()
    df['memory_rolling_avg'] = df['memory_percent'].rolling(window=5).mean()
    df['disk_rolling_avg'] = df['disk_percent'].rolling(window=5).mean()
    df['network_rolling_avg'] = df['network_sent'].rolling(window=5).mean()
    
    # Drop NA values created by rolling averages
    df.dropna(inplace=True)
    
    logging.debug(f"Data preprocessing completed. Shape: {df.shape}")
    return df

# Identify clusters in the data using KMeans for anomaly detection
def identify_clusters(df):
    features = ['cpu_usage', 'memory_percent', 'disk_percent', 'network_sent']
    X = df[features]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    kmeans = KMeans(n_clusters=2, random_state=42)  # 2 clusters: normal, anomaly
    df['cluster'] = kmeans.fit_predict(X_scaled)
    
    # Anomaly is classified as the larger cluster
    df['is_anomaly'] = df['cluster'].apply(lambda x: 1 if x == 1 else 0)
    
    anomalies = df[df['is_anomaly'] == 1]
    logging.debug(f"Identified {len(anomalies)} anomalies in the system data.")
    return anomalies

# Classify anomalies using Random Forest classifier (supervised model)
def classify_anomalies(df):
    # Assuming 'is_anomaly' is already in the dataframe
    features = ['cpu_usage', 'memory_percent', 'disk_percent', 'network_sent', 'cpu_rolling_avg', 'memory_rolling_avg', 'disk_rolling_avg', 'network_rolling_avg']
    X = df[features]
    y = df['is_anomaly']
    
    # Split into training and test sets
    X_train = X[:int(0.8*len(X))]
    y_train = y[:int(0.8*len(y))]
    X_test = X[int(0.8*len(X)):]
    y_test = y[int(0.8*len(y)):]
    
    # Train RandomForestClassifier
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    
    # Predict on test data
    y_pred = clf.predict(X_test)
    
    # Evaluate model performance
    report = classification_report(y_test, y_pred)
    logging.info(f"Classification report:\n{report}")
    
    return clf, y_pred

# Log anomalies and RCA results into MongoDB
def log_anomalies(anomalies):
    try:
        anomalies_data = anomalies.to_dict("records")
        db["anomalies_logs"].insert_many(anomalies_data)
        logging.info(f"Anomalies logged to MongoDB. Total anomalies: {len(anomalies)}")
    except Exception as e:
        logging.error(f"Error logging anomalies: {e}")

# Save Root Cause Analysis results into MongoDB
def save_rca_to_mongo(final_insight_data):
    try:
        rca_result = {
            "timestamp": datetime.now(),
            "root_cause_analysis": final_insight_data["root_cause_analysis"],
            "total_anomalies": final_insight_data["total_anomalies"],
            "cpu_anomalies": final_insight_data["cpu_anomalies"],
            "memory_anomalies": final_insight_data["memory_anomalies"],
            "disk_anomalies": final_insight_data["disk_anomalies"],
            "network_anomalies": final_insight_data["network_anomalies"],
            "suggested_actions": final_insight_data["suggested_actions"]
        }
        rca_collection.insert_one(rca_result)
        logging.info("Root Cause Analysis results saved to MongoDB.")
    except Exception as e:
        logging.error(f"Error saving Root Cause Analysis to MongoDB: {e}")

# Final Insight based on RCA results
def final_insight(anomalies):
    final_insight_data = {
        "root_cause_analysis": [],
        "total_anomalies": 0,
        "cpu_anomalies": [],
        "memory_anomalies": [],
        "disk_anomalies": [],
        "network_anomalies": [],
        "suggested_actions": []
    }

    if anomalies.empty:
        logging.info("No anomalies detected. The system is operating within normal parameters.")
        final_insight_data["root_cause_analysis"].append("System is operating normally.")
    else:
        # Summary of most common root causes
        cpu_anomalies = anomalies[anomalies['cpu_usage'] > CPU_THRESHOLD]
        memory_anomalies = anomalies[anomalies['memory_percent'] > MEMORY_THRESHOLD]
        disk_anomalies = anomalies[anomalies['disk_percent'] > DISK_THRESHOLD]
        network_anomalies = anomalies[anomalies['network_sent'] > NETWORK_THRESHOLD]
        
        logging.info("Final Insight: Root Cause Analysis Results")
        final_insight_data["root_cause_analysis"].append("Root cause analysis completed.")

        if not cpu_anomalies.empty:
            final_insight_data["cpu_anomalies"] = cpu_anomalies.to_dict("records")
            logging.info(f"High CPU usage detected in {len(cpu_anomalies)} instances.")
        if not memory_anomalies.empty:
            final_insight_data["memory_anomalies"] = memory_anomalies.to_dict("records")
            logging.info(f"High memory usage detected in {len(memory_anomalies)} instances.")
        if not disk_anomalies.empty:
            final_insight_data["disk_anomalies"] = disk_anomalies.to_dict("records")
            logging.info(f"High disk usage detected in {len(disk_anomalies)} instances.")
        if not network_anomalies.empty:
            final_insight_data["network_anomalies"] = network_anomalies.to_dict("records")
            logging.info(f"High network usage detected in {len(network_anomalies)} instances.")
        
        # Aggregate insights on the overall system performance
        total_anomalies = len(anomalies)
        final_insight_data["total_anomalies"] = total_anomalies
        logging.info(f"Total number of anomalies detected: {total_anomalies}")
        
        if total_anomalies > 0:
            cpu_percent = (len(cpu_anomalies) / total_anomalies) * 100
            memory_percent = (len(memory_anomalies) / total_anomalies) * 100
            disk_percent = (len(disk_anomalies) / total_anomalies) * 100
            network_percent = (len(network_anomalies) / total_anomalies) * 100

            logging.info(f"Breakdown of anomalies detected: \n- CPU: {cpu_percent:.2f}% \n- Memory: {memory_percent:.2f}% \n- Disk: {disk_percent:.2f}% \n- Network: {network_percent:.2f}%")
        
        final_insight_data["suggested_actions"].append("Suggested Actions:") 
        final_insight_data["suggested_actions"].append("1. Investigate the process or application causing high CPU or memory usage.")
        final_insight_data["suggested_actions"].append("2. Check for disk space issues or I/O bottlenecks.")
        final_insight_data["suggested_actions"].append("3. Monitor network traffic for any unusual spikes.")
        final_insight_data["suggested_actions"].append("4. Implement alerting systems for thresholds to prevent future occurrences.")
        
    # Save the final insights to MongoDB
    save_rca_to_mongo(final_insight_data)

# Define main function to encapsulate the execution flow
def main():
    logging.info("RootSense analysis started.")
    data = fetch_data_from_mongo()
    if data:
        processed_data = preprocess_data(data)
        anomalies = identify_clusters(processed_data)
        clf, predictions = classify_anomalies(processed_data)
        log_anomalies(anomalies)
        final_insight(anomalies)

# Run the analysis when script is executed
if __name__ == "__main__":
    main()
