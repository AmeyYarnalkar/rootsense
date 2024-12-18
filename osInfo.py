import psutil
import time
from pymongo import MongoClient
from datetime import datetime

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Replace with your MongoDB URI if needed
db = client["system_info_db"]  # Database name
collection = db["system_stats"]  # Collection name

def get_system_data():
    # Fetch system data
    cpu_usage = psutil.cpu_percent(interval=1)  # CPU usage over 1 second
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    network = psutil.net_io_counters()

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

def store_data_in_mongodb(data):
    # Insert the system data into MongoDB
    collection.insert_one(data)
    print(f"Data inserted at {data['timestamp']}")

def main():
    while True:
        # Get system data
        system_data = get_system_data()
        
        # Store data in MongoDB
        store_data_in_mongodb(system_data)
        
        # Wait for 5 seconds before fetching data again
        time.sleep(5)

if __name__ == "__main__":
    main()
