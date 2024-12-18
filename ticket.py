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
ticket_collection = db["tickets"]  # Collection for storing tickets

# Define thresholds for the system metrics (in appropriate units)
CPU_THRESHOLD = 40  # CPU usage > 80%
MEMORY_THRESHOLD = 60  # Memory usage > 80%
DISK_THRESHOLD = 30  # Disk usage > 80%
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

def create_ticket(issue_type, metric, current_value, threshold):
    try:
        logging.debug(f"Creating ticket for {issue_type}...")

        # Create a new ticket document
        ticket = {
            "timestamp": datetime.now(),
            "issue_type": issue_type,
            "metric": metric,
            "current_value": current_value,
            "threshold": threshold,
            "status": "open",  # Ticket is open initially
            "description": f"{metric} exceeded threshold. Current value: {current_value}, Threshold: {threshold}",
        }

        # Insert the ticket into the MongoDB collection
        ticket_collection.insert_one(ticket)
        logging.info(f"Ticket created for {issue_type} with {metric} exceeding threshold.")
        return ticket
    except Exception as e:
        logging.error(f"Error occurred while creating ticket: {e}")
        return None

def monitor_system():
    while True:
        logging.debug("Starting data collection cycle...")
        # Get system data
        system_data = get_system_data()

        if system_data:
            # Check if any value exceeds the thresholds and create a ticket if necessary
            if system_data["cpu_usage"] > CPU_THRESHOLD:
                create_ticket("CPU Usage Exceeded", "CPU Usage", system_data["cpu_usage"], CPU_THRESHOLD)

            if system_data["memory_percent"] > MEMORY_THRESHOLD:
                create_ticket("Memory Usage Exceeded", "Memory Usage", system_data["memory_percent"], MEMORY_THRESHOLD)

            if system_data["disk_percent"] > DISK_THRESHOLD:
                create_ticket("Disk Usage Exceeded", "Disk Usage", system_data["disk_percent"], DISK_THRESHOLD)

            if system_data["network_sent"] > NETWORK_THRESHOLD:
                create_ticket("Network Sent Exceeded", "Network Sent", system_data["network_sent"], NETWORK_THRESHOLD)

            if system_data["network_recv"] > NETWORK_THRESHOLD:
                create_ticket("Network Received Exceeded", "Network Received", system_data["network_recv"], NETWORK_THRESHOLD)

        # Wait for 5 seconds before fetching data again
        logging.debug("Sleeping for 5 seconds before next data collection...")
        time.sleep(5)

# Added main function to start the monitoring
def main():
    logging.info("Ticket monitoring script started.")
    monitor_system()

if __name__ == "__main__":
    main()
