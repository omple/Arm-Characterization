#!/usr/bin/env python3
"""
Python Serial Controller for 2-Link Planar Arm
Sends (x, y) target positions to Arduino via serial communication
"""

import serial
import time
import sys

class ArmController:
    def __init__(self, port='/dev/ttyACM0', baudrate=9600, timeout=1):
        """
        Initialize serial connection to Arduino

        Args:
            port: Serial port (e.g., 'COM3' on Windows, '/dev/ttyACM0' on Linux)
            baudrate: Communication speed (must match Arduino)
            timeout: Read timeout in seconds
        """
        try:
            self.ser = serial.Serial(port, baudrate, timeout=timeout)
            time.sleep(2)  # Wait for Arduino to reset after serial connection
            print(f"Connected to Arduino on {port}")

            # Read initial messages from Arduino
            time.sleep(0.5)
            while self.ser.in_waiting > 0:
                print(self.ser.readline().decode('utf-8').strip())

        except serial.SerialException as e:
            print(f"Error: Could not open serial port {port}")
            print(f"Details: {e}")
            sys.exit(1)

    def send_position(self, x, y):
        """
        Send target (x, y) position to Arduino

        Args:
            x: X coordinate
            y: Y coordinate
        """
        command = f"{x},{y}\n"
        self.ser.write(command.encode('utf-8'))
        print(f"Sent: ({x}, {y})")

        # Wait and read response from Arduino
        time.sleep(0.1)
        self.read_response()

    def read_response(self, timeout=2.0):
        """Read and print response from Arduino"""
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            if self.ser.in_waiting > 0:
                response = self.ser.readline().decode('utf-8').strip()
                print(f"  Arduino: {response}")
                if "Position reached!" in response or "ERROR" in response:
                    break
            time.sleep(0.05)

    def send_trajectory(self, positions, delay=1.0):
        """
        Send multiple positions in sequence

        Args:
            positions: List of (x, y) tuples
            delay: Delay between positions in seconds
        """
        for x, y in positions:
            self.send_position(x, y)
            time.sleep(delay)

    def interactive_mode(self):
        """Interactive mode for manual position input"""
        print("\n=== Interactive Mode ===")
        print("Enter target positions as 'x,y' (e.g., '15.5,8.2')")
        print("Type 'quit' to exit")

        while True:
            try:
                user_input = input("\nEnter position (x,y): ").strip()

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Exiting...")
                    break

                # Parse input
                parts = user_input.split(',')
                if len(parts) != 2:
                    print("Invalid format. Use: x,y")
                    continue

                x = float(parts[0])
                y = float(parts[1])

                self.send_position(x, y)

            except ValueError:
                print("Invalid numbers. Please enter valid x,y coordinates")
            except KeyboardInterrupt:
                print("\nExiting...")
                break

    def close(self):
        """Close serial connection"""
        if self.ser.is_open:
            self.ser.close()
            print("Serial connection closed")


def demo_trajectory():
    """Demo: Send a predefined trajectory"""
    # Adjust port name based on your system
    # Windows: 'COM3', 'COM4', etc.
    # Linux: '/dev/ttyACM0', '/dev/ttyUSB0', etc.
    # macOS: '/dev/cu.usbmodem14101', etc.

    port = '/dev/ttyACM0'  # Change this to match your system

    controller = ArmController(port=port, baudrate=9600)

    # Define trajectory (adjust based on your link lengths)
    trajectory = [
        (0.9, 0.9),    # Position 1
        (0.9 + 0.1, 0.9),   # Position 2
        (0.9 + 0.1, 0.9 + 0.1),    # Position 3
        (0.9 - 0.1, 0.9 - 0.1),    # Position 4
        (0.9, 0.9 - 0.1),    # Position 5
    ]

    print("\nSending trajectory...")
    controller.send_trajectory(trajectory, delay=2.0)

    controller.close()


def interactive_control():
    """Interactive control mode"""
    port = 'COM4'  # Change this to match your system

    controller = ArmController(port=port, baudrate=9600)
    controller.interactive_mode()
    controller.close()


if __name__ == "__main__":
    print("2-Link Planar Arm - Python Serial Controller")
    print("=" * 50)
    print("\nSelect mode:")
    print("1. Interactive mode (manual position entry)")
    print("2. Demo trajectory")

    try:
        choice = input("\nEnter choice (1 or 2): ").strip()

        if choice == '1':
            interactive_control()
        elif choice == '2':
            demo_trajectory()
        else:
            print("Invalid choice")

    except KeyboardInterrupt:
        print("\nExiting...")
