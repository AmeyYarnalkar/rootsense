from datetime import datetime
import os
from pymongo import MongoClient

# MongoDB connection setup
client = MongoClient("mongodb://localhost:27017/")
db = client["system_info_db"]
performance_collection = db["performance_data"]
analysis_collection = db["performance_analysis_results"]
excessive_logs_collection = db["all_logs"]
ticket_collection = db["tickets"]

# Function to fetch data from MongoDB
def fetch_performance_data():
    data = list(performance_collection.find().sort("timestamp", -1).limit(5))  # Last 5 entries
    return data

def fetch_analysis_results():
    data = list(analysis_collection.find().sort("timestamp", -1).limit(5))  # Last 5 analysis results
    return data

def fetch_excessive_logs():
    logs = list(excessive_logs_collection.find().sort("timestamp", -1).limit(5))  # Last 5 excessive logs
    return logs

def fetch_ticket_info():
    tickets = list(ticket_collection.find().sort("timestamp", -1).limit(5))  # Last 5 tickets
    return tickets

# Function to generate the HTML report
def generate_html():
    # Specify the report file location in the current directory
    report_filename = os.path.join(os.getcwd(), f"system_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
    
    # HTML template for the report
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>System Performance Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f4f4f9;
                margin: 0;
                padding: 0;
            }}
            .container {{
                width: 80%;
                margin: auto;
                background-color: #fff;
                padding: 20px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }}
            h1 {{
                text-align: center;
                color: #333;
            }}
            .section {{
                margin-top: 20px;
            }}
            .section h2 {{
                color: #333;
                font-size: 18px;
            }}
            .content-item {{
                margin: 10px 0;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>System Performance Report</h1>
            <p><strong>Generated on:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

            <!-- Introduction -->
            <div class="section">
                <h2>Introduction:</h2>
                <p>This report provides an overview of the system's performance, including the following:</p>
                <ul>
                    <li>System health metrics (CPU, Memory, Disk, Network)</li>
                    <li>Root Cause Analysis</li>
                    <li>Predictive Analysis of system trends</li>
                    <li>Machine Learning-based analysis results</li>
                    <li>Log data (Excessive usage and associated tickets)</li>
                </ul>
            </div>

            <!-- Performance Data Section -->
            <div class="section">
                <h2>Performance Data:</h2>
                {generate_performance_data_section()}
            </div>

            <!-- Root Cause Analysis Section -->
            <div class="section">
                <h2>Root Cause Analysis Results:</h2>
                {generate_analysis_results_section()}
            </div>

            <!-- Excessive Logs Section -->
            <div class="section">
                <h2>Excessive Logs:</h2>
                {generate_excessive_logs_section()}
            </div>

            <!-- Ticket Information Section -->
            <div class="section">
                <h2>Ticket Information:</h2>
                {generate_ticket_section()}
            </div>

            <!-- Conclusion -->
            <div class="section">
                <h2>Conclusion and Final Insights:</h2>
                <p>Based on the analysis and predictions, we recommend the following:</p>
                <ul>
                    <li>Ensure timely monitoring of system metrics to avoid performance degradation.</li>
                    <li>Focus on improving CPU and memory usage efficiency.</li>
                    <li>Consider additional resources for network usage if required.</li>
                </ul>
                <p>This report was generated automatically for ongoing system health monitoring.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Write the HTML content to the file
    with open(report_filename, 'w') as file:
        file.write(html_content)

    return report_filename


def generate_performance_data_section():
    performance_data = fetch_performance_data()
    section_content = ""
    
    if not performance_data:
        section_content += "<p>No performance data available.</p>"
    else:
        for data in performance_data:
            section_content += f"""
            <div class="content-item"><strong>Timestamp:</strong> {data.get('timestamp', 'N/A')}</div>
            <div class="content-item"><strong>CPU Usage:</strong> {data.get('cpu_usage', 'N/A')}%</div>
            <div class="content-item"><strong>Memory Usage:</strong> {data.get('memory_percent', 'N/A')}%</div>
            <div class="content-item"><strong>Disk Usage:</strong> {data.get('disk_percent', 'N/A')}%</div>
            <div class="content-item"><strong>Network Sent:</strong> {data.get('network_sent', 'N/A')} bytes</div>
            <div class="content-item"><strong>Network Received:</strong> {data.get('network_recv', 'N/A')} bytes</div>
            """
    return section_content


def generate_analysis_results_section():
    analysis_results = fetch_analysis_results()
    section_content = ""
    
    if not analysis_results:
        section_content += "<p>No analysis results available.</p>"
    else:
        for result in analysis_results:
            section_content += f"""
            <div class="content-item"><strong>Timestamp:</strong> {result.get('timestamp', 'N/A')}</div>
            <div class="content-item"><strong>Predicted Health:</strong> {result.get('predicted_health', 'N/A')}</div>
            <div class="content-item"><strong>Model Accuracy:</strong> {result.get('model_accuracy', 'N/A')}%</div>
            """
    return section_content


def generate_excessive_logs_section():
    excessive_logs = fetch_excessive_logs()
    section_content = ""
    
    if not excessive_logs:
        section_content += "<p>No excessive logs available.</p>"
    else:
        for log in excessive_logs:
            section_content += f"""
            <div class="content-item"><strong>Timestamp:</strong> {log.get('timestamp', 'N/A')}</div>
            <div class="content-item"><strong>CPU Usage:</strong> {log.get('cpu_usage', 'N/A')}%</div>
            <div class="content-item"><strong>Memory Usage:</strong> {log.get('memory_percent', 'N/A')}%</div>
            """
    return section_content


def generate_ticket_section():
    tickets = fetch_ticket_info()
    section_content = ""
    
    if not tickets:
        section_content += "<p>No tickets available.</p>"
    else:
        for ticket in tickets:
            section_content += f"""
            <div class="content-item"><strong>Ticket ID:</strong> {ticket.get('_id', 'N/A')}</div>
            <div class="content-item"><strong>Created:</strong> {ticket.get('timestamp', 'N/A')}</div>
            <div class="content-item"><strong>Status:</strong> {ticket.get('status', 'N/A')}</div>
            """
    return section_content


def main():
    html_report = generate_html()
    print(f"HTML report generated: {os.path.abspath(html_report)}")

if __name__ == "__main__":
    main()