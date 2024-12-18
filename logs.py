import psutil
import time
from pymongo import MongoClient
from datetime import datetime
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Replace with your MongoDB URI if needed
db = client["system_info_db"]  # Database name
collection = db["system_stats"]  # Collection for storing system stats
excessive_logs_collection = db["excessive_logs"]  # Collection for storing excessive logs
all_logs_collection = db["all_logs"]  # New collection for storing all logs

# Define thresholds for the system metrics (in appropriate units)
CPU_THRESHOLD = 80  # CPU usage > 80%
MEMORY_THRESHOLD = 80  # Memory usage > 80%
DISK_THRESHOLD = 80  # Disk usage > 80%
NETWORK_THRESHOLD = 100000000  # Network bytes sent/received > 100 MB

def get_system_data():
    try:
        logging.debug("Fetching system data...")

        # Fetch system data
        cpu_usage = psutil.cpu_percent(interval=1)  # CPU usage over 1 second
        logging.debug(f"CPU Usage: {cpu_usage}%")

        memory = psutil.virtual_memory()
        logging.debug(f"Memory - Total: {memory.total}, Used: {memory.used}, Free: {memory.free}, Percent: {memory.percent}%")

        disk = psutil.disk_usage('/')
        logging.debug(f"Disk - Total: {disk.total}, Used: {disk.used}, Free: {disk.free}, Percent: {disk.percent}%")

        network = psutil.net_io_counters()
        logging.debug(f"Network - Sent: {network.bytes_sent}, Received: {network.bytes_recv}")

        # Prepare the data to be stored
        system_data = {
            "timestamp": datetime.now(),  # Record the timestamp
            "cpu_usage": cpu_usage,  # CPU usage percentage
            "memory_total": memory.total,  # Total memory in bytes
            "memory_used": memory.used,  # Used memory in bytes
            "memory_free": memory.free,  # Free memory in bytes
            "memory_percent": memory.percent,  # Memory usage percentage
            "disk_total": disk.total,  # Total disk space in bytes
            "disk_used": disk.used,  # Used disk space in bytes
            "disk_free": disk.free,  # Free disk space in bytes
            "disk_percent": disk.percent,  # Disk usage percentage
            "network_sent": network.bytes_sent,  # Bytes sent over the network
            "network_recv": network.bytes_recv  # Bytes received over the network
        }

        return system_data
    except Exception as e:
        logging.error(f"Error occurred while fetching system data: {e}")
        return None

def store_data_in_mongodb(data):
    try:
        if data:
            logging.debug("Inserting data into MongoDB...")
            # Insert the system data into MongoDB
            collection.insert_one(data)
            logging.info(f"Data inserted at {data['timestamp']}")
        else:
            logging.warning("No data to insert into MongoDB.")
    except Exception as e:
        logging.error(f"Error occurred while inserting data into MongoDB: {e}")

def log_excessive_data(data):
    try:
        logging.debug("Checking for excessive data...")

        excessive_data = {}

        # Check if any value exceeds the thresholds
        if data["cpu_usage"] > CPU_THRESHOLD:
            excessive_data["cpu_usage"] = data["cpu_usage"]
            logging.warning(f"CPU usage exceeded threshold: {data['cpu_usage']}%")

        if data["memory_percent"] > MEMORY_THRESHOLD:
            excessive_data["memory_percent"] = data["memory_percent"]
            logging.warning(f"Memory usage exceeded threshold: {data['memory_percent']}%")

        if data["disk_percent"] > DISK_THRESHOLD:
            excessive_data["disk_percent"] = data["disk_percent"]
            logging.warning(f"Disk usage exceeded threshold: {data['disk_percent']}%")

        if data["network_sent"] > NETWORK_THRESHOLD:
            excessive_data["network_sent"] = data["network_sent"]
            logging.warning(f"Network bytes sent exceeded threshold: {data['network_sent']}")

        if data["network_recv"] > NETWORK_THRESHOLD:
            excessive_data["network_recv"] = data["network_recv"]
            logging.warning(f"Network bytes received exceeded threshold: {data['network_recv']}")

        # Log the data into `all_logs` collection
        data["log_type"] = "normal"
        all_logs_collection.insert_one(data)
        logging.info(f"Normal data logged at {data['timestamp']}")

        # If any threshold is exceeded, log the excessive data
        if excessive_data:
            excessive_data["timestamp"] = data["timestamp"]  # Add timestamp to excessive log
            excessive_logs_collection.insert_one(excessive_data)
            excessive_data["log_type"] = "excessive"
            all_logs_collection.insert_one(excessive_data)
            logging.info(f"Excessive data logged at {data['timestamp']}")
        else:
            logging.debug("All metrics are within normal thresholds. No excessive data logged.")

    except Exception as e:
        logging.error(f"Error occurred while logging excessive data: {e}")

def main():
    while True:
        logging.debug("Starting data collection cycle...")
        # Get system data
        system_data = get_system_data()

        # Store data in MongoDB
        store_data_in_mongodb(system_data)

        # Check and log excessive data
        log_excessive_data(system_data)

        # Wait for 5 seconds before fetching data again
        logging.debug("Sleeping for 5 seconds before next data collection...")
        time.sleep(5)

if __name__ == "__main__":
    logging.info("System monitoring script started.")
    main()
