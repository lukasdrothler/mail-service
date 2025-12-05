import socket
import os
import sys

def check_connection(host, port, name):
    print(f"--- Checking {name} connection to {host}:{port} ---")
    try:
        # Resolve IP
        ip = socket.gethostbyname(host)
        print(f"✅ DNS Resolution: {host} -> {ip}")
    except socket.gaierror as e:
        print(f"❌ DNS Resolution Failed: {e}")
        return False

    try:
        # Connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, int(port)))
        if result == 0:
            print(f"✅ TCP Connection: Successfully connected to {host}:{port}")
            sock.close()
            return True
        else:
            error_msg = os.strerror(result)
            print(f"❌ TCP Connection Failed: Error code {result} ({error_msg})")
            sock.close()
            return False
    except Exception as e:
        print(f"❌ TCP Connection Error: {e}")
        return False

def main():
    print("=== Network Connectivity Debugger ===\n")
    
    # Check RabbitMQ
    rmq_host = os.environ.get("RABBITMQ_HOST", "localhost")
    rmq_port = os.environ.get("RABBITMQ_PORT", "5672")
    check_connection(rmq_host, rmq_port, "RabbitMQ")
    print("\n")

    # Check SMTP
    smtp_host = os.environ.get("SMTP_SERVER", "localhost")
    smtp_port = os.environ.get("SMTP_PORT", "587")
    check_connection(smtp_host, smtp_port, "SMTP Server")
    print("\n")

    # Check Internet (Google DNS)
    check_connection("8.8.8.8", 53, "Internet (Google DNS)")

if __name__ == "__main__":
    main()
