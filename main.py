"""Main CLI for Arm-Characterization utilities.

Provides two simple modes:
 - `write_csv`: writes a small demo tracking CSV (compat with previous repo example).
 - `stream_square`: generates the Arduino-defined square path and streams it
	to the arm using `ArmSerialController`. Serial modules are imported lazily
	so `write_csv` mode can be used without a serial device attached.

Usage examples:
  python main.py --mode write_csv
  python main.py --mode stream_square --port COM12 --baud 9600 --time_ms 4000 --rate_hz 100 --out square.csv --wait_ack
"""

from typing import List, Dict
import argparse
import time
import csv
import sys


def write_to_csv(file_path: str, data: List[Dict], headers: List[str]) -> None:
	with open(file_path, mode='w', newline='') as file:
		writer = csv.DictWriter(file, fieldnames=headers)
		writer.writeheader()
		for row in data:
			writer.writerow(row)


def demo_write_tracking_csv() -> None:
	sample_data = [
		{'Frame': 1, 'X (px)': 150, 'Y (px)': 200, 'X (m)': 0.5, 'Y (m)': 0.75, 'Area': 3000},
		{'Frame': 2, 'X (px)': 160, 'Y (px)': 210, 'X (m)': 0.53, 'Y (m)': 0.78, 'Area': 3200},
		{'Frame': 3, 'X (px)': 170, 'Y (px)': 220, 'X (m)': 0.57, 'Y (m)': 0.82, 'Area': 3500},
	]
	headers = ['Frame', 'X (px)', 'Y (px)', 'X (m)', 'Y (m)', 'Area']
	write_to_csv('tracking_data.csv', sample_data, headers)
	print("Data written to tracking_data.csv")


def demo_stream_square(port: str = 'COM12', baudrate: int = 9600, total_time_ms: float = 4000.0,
					   rate_hz: int = 100, save_csv: str = '', wait_ack: bool = False) -> None:
	"""Generate the Arduino square path and stream it to the arm controller.

	This function lazily imports `PathGenerator` and `ArmSerialController` so a
	user can run `write_csv` mode without a serial device.
	"""
	# Lazy imports to avoid requiring serial hardware for other modes
	try:
		from PathGenerator import square_right_defined, PathGenerator
	except Exception as e:
		print(f"Error importing PathGenerator: {e}")
		return

	try:
		from ArmSerialController import ArmController
	except Exception as e:
		print(f"Error importing ArmSerialController: {e}")
		return

	samples = square_right_defined(total_time_ms=total_time_ms, rate_hz=rate_hz)

	if save_csv:
		pg = PathGenerator(waypoints=[(.137, 0.100), (0.137, 0.126), (0.111, 0.126), (0.111, 0.100)], closed=True)
		pg.save_to_csv(save_csv, samples)
		print(f"Saved samples to {save_csv}")

	try:
		controller = ArmController(port=port, baudrate=baudrate)
	except SystemExit:
		print("Failed to open serial port. Aborting stream.")
		return

	# small settle delay then start streaming according to sample timestamps
	time.sleep(0.5)
	controller.stream_parametric_path(samples, wait_ack=wait_ack, start_delay=0.5)
	controller.close()


def parse_args():
	p = argparse.ArgumentParser(description='Arm Characterization utilities')
	p.add_argument('--mode', choices=['write_csv', 'stream_square'], default='stream_square')
	p.add_argument('--port', default='COM12', help='Serial port for streaming (e.g., COM3)')
	p.add_argument('--baud', type=int, default=9600, help='Serial baud rate')
	p.add_argument('--time_ms', type=float, default=4000.0, help='Total time for square path in ms')
	p.add_argument('--rate_hz', type=int, default=100, help='Sampling rate in Hz')
	p.add_argument('--out', default='', help='Optional CSV output file for samples')
	p.add_argument('--wait_ack', action='store_true', help='Wait for Arduino ack after each point')
	return p.parse_args()


def main():
	args = parse_args()

	if args.mode == 'write_csv':
		demo_write_tracking_csv()
	elif args.mode == 'stream_square':
		demo_stream_square(port=args.port, baudrate=args.baud, total_time_ms=args.time_ms,
						   rate_hz=args.rate_hz, save_csv=args.out, wait_ack=args.wait_ack)


if __name__ == '__main__':
	main()
