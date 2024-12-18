import threading
import time
from rootsense.osInfo import main as osInfo_main
from rootsense.ticket import main as ticket_main
from rootsense.predictive import main as predictive_main
from rootsense.root import main as root_main
from rootsense.logs import main as logs_main
from rootsense.performance import main as performance_main
from rootsense.report import main as report_main

# Event to stop the threads gracefully after 30 seconds
stop_event = threading.Event()

def run_script(func):
    """Function to run a script's main function"""
    try:
        while not stop_event.is_set():  # Check for the stop event regularly
            func()
            time.sleep(1)  # Sleep to prevent high CPU usage in a busy loop
    except Exception as e:
        print(f"Error running {func.__name__}: {e}")

def main():
    # List of functions to run concurrently
    functions = [
        osInfo_main,
        ticket_main,
        predictive_main,
        root_main,
        logs_main,
        performance_main,
        report_main
    ]
    
    # Create and start a thread for each function
    threads = []
    for func in functions:
        thread = threading.Thread(target=run_script, args=(func,))
        threads.append(thread)
        thread.start()
        print(f"Started thread for {func.__name__}")

    # Wait for 30 seconds or until stop_event is set
    try:
        time.sleep(30)  # Keep the threads running for 30 seconds
    except KeyboardInterrupt:
        print("\nCtrl+C pressed. Stopping all threads...")
    
    # Stop all threads after 30 seconds or Ctrl+C
    print("\nStopping all threads...")
    stop_event.set()  # Set the stop event to signal threads to stop
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()  # Ensure all threads complete before exiting
    print("All threads stopped gracefully.")

if __name__ == "__main__":
    main()
