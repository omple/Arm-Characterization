#!/usr/bin/env python3
"""Path file selector and runner.

Browse CSV files in the paths/ folder and stream them to the Arduino.
"""

import os
import csv
import time
from typing import List, Tuple, Optional


def list_path_files(paths_dir: str = 'paths') -> List[str]:
    """List all CSV files in the paths directory."""
    if not os.path.exists(paths_dir):
        return []
    
    files = []
    for f in os.listdir(paths_dir):
        if f.endswith('.csv'):
            files.append(f)
    
    return sorted(files)


def load_csv_path(filepath: str) -> Optional[List[Tuple[float, float, float]]]:
    """Load a path CSV file and return list of (t_ms, x, y) tuples."""
    samples = []
    
    try:
        with open(filepath, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)  # Skip header
            
            for row in reader:
                if len(row) >= 3:
                    try:
                        t_ms = float(row[0])
                        x = float(row[1])
                        y = float(row[2])
                        samples.append((t_ms, x, y))
                    except ValueError:
                        continue
        
        return samples if samples else None
    
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None


def preview_path(samples: List[Tuple[float, float, float]]) -> None:
    """Show path preview."""
    if not samples:
        print("No samples in path.")
        return
    
    duration = samples[-1][0]
    num_samples = len(samples)
    xs = [s[1] for s in samples]
    ys = [s[2] for s in samples]
    
    print(f"\n{'─'*70}")
    print(f"Path Preview:")
    print(f"{'─'*70}")
    print(f"  Samples: {num_samples}")
    print(f"  Duration: {duration:.1f} ms ({duration/1000:.2f} sec)")
    print(f"  X range: [{min(xs):.6f}, {max(xs):.6f}]")
    print(f"  Y range: [{min(ys):.6f}, {max(ys):.6f}]")
    
    # Check if closed
    first_xy = (samples[0][1], samples[0][2])
    last_xy = (samples[-1][1], samples[-1][2])
    is_closed = abs(first_xy[0] - last_xy[0]) < 0.0001 and abs(first_xy[1] - last_xy[1]) < 0.0001
    
    print(f"  Closed path: {'Yes ✓' if is_closed else 'No'}")
    print(f"{'─'*70}\n")
    
    # Show first few samples
    print(f"First 5 samples:")
    print(f"  {'Idx':<5} {'Time(ms)':<12} {'X':<12} {'Y':<12}")
    for i in range(min(5, len(samples))):
        t, x, y = samples[i]
        print(f"  {i:<5} {t:<12.1f} {x:<12.6f} {y:<12.6f}")
    
    if len(samples) > 10:
        print(f"  ...")
        print(f"Last 5 samples:")
        print(f"  {'Idx':<5} {'Time(ms)':<12} {'X':<12} {'Y':<12}")
        for i in range(max(0, len(samples)-5), len(samples)):
            t, x, y = samples[i]
            print(f"  {i:<5} {t:<12.1f} {x:<12.6f} {y:<12.6f}")
    print()


def stream_path_to_arduino(samples: List[Tuple[float, float, float]], port: str, baudrate: int = 9600, wait_ack: bool = False) -> None:
    """Stream the path samples to Arduino via serial."""
    try:
        from ArmSerialController import ArmController
    except Exception as e:
        print(f"Error importing ArmSerialController: {e}")
        return
    
    print(f"\n{'─'*70}")
    print(f"STREAMING PATH")
    print(f"{'─'*70}")
    print(f"Port: {port}, Baud: {baudrate}")
    print(f"Samples: {len(samples)}, Duration: {samples[-1][0]:.1f} ms")
    print(f"Wait for ACK: {'Yes' if wait_ack else 'No'}")
    print(f"{'─'*70}\n")
    
    try:
        controller = ArmController(port=port, baudrate=baudrate)
    except SystemExit:
        print("Failed to open serial port.")
        return
    
    time.sleep(0.5)
    controller.stream_parametric_path(samples, wait_ack=wait_ack, start_delay=0.5)
    controller.close()
    
    print(f"\n{'─'*70}")
    print("✓ Stream complete")
    print(f"{'─'*70}\n")


def main():
    """Main interactive file browser and runner."""
    paths_dir = 'paths'
    
    print("\n" + "="*70)
    print("PATH FILE RUNNER - Select and stream paths to Arduino")
    print("="*70)
    
    # List available files
    files = list_path_files(paths_dir)
    
    if not files:
        print(f"\nNo CSV files found in '{paths_dir}/' directory.")
        print("Generate paths using PathGenerator.py first.")
        return
    
    print(f"\nFound {len(files)} path file(s):\n")
    for i, filename in enumerate(files, 1):
        filepath = os.path.join(paths_dir, filename)
        file_size = os.path.getsize(filepath)
        print(f"  {i}. {filename:<30s} ({file_size} bytes)")
    
    # Let user select a file
    print()
    while True:
        try:
            choice = input(f"Select file (1-{len(files)}) or 0 to exit: ").strip()
            
            if choice == '0':
                print("Exiting.")
                return
            
            idx = int(choice) - 1
            if 0 <= idx < len(files):
                break
            else:
                print(f"Invalid choice. Enter 1-{len(files)}")
        except ValueError:
            print("Invalid input.")
    
    selected_file = files[idx]
    filepath = os.path.join(paths_dir, selected_file)
    
    print(f"\nLoading {selected_file}...")
    samples = load_csv_path(filepath)
    
    if not samples:
        print(f"Failed to load path from {filepath}")
        return
    
    print(f"✓ Loaded {len(samples)} samples")
    
    # Show preview
    preview_path(samples)
    
    # Ask user what to do
    while True:
        print("\nOptions:")
        print("  1. Preview detailed view")
        print("  2. Stream to Arduino")
        print("  3. Stream with ACK (safer)")
        print("  4. Save copy with new name")
        print("  5. Select different file")
        print("  0. Exit")
        print()
        
        action = input("Select action (0-5): ").strip()
        
        if action == '0':
            print("Exiting.")
            break
        
        elif action == '1':
            # Detailed preview
            preview_choice = input("\nShow which samples? (f=first 20, l=last 20, a=all, idx=specific): ").strip().lower()
            
            if preview_choice == 'f':
                print(f"\nFirst 20 samples:")
                print(f"{'Idx':<5} {'Time(ms)':<12} {'X':<12} {'Y':<12}")
                for i in range(min(20, len(samples))):
                    t, x, y = samples[i]
                    print(f"{i:<5} {t:<12.1f} {x:<12.6f} {y:<12.6f}")
            
            elif preview_choice == 'l':
                print(f"\nLast 20 samples:")
                print(f"{'Idx':<5} {'Time(ms)':<12} {'X':<12} {'Y':<12}")
                start = max(0, len(samples) - 20)
                for i in range(start, len(samples)):
                    t, x, y = samples[i]
                    print(f"{i:<5} {t:<12.1f} {x:<12.6f} {y:<12.6f}")
            
            elif preview_choice == 'a':
                print(f"\nAll {len(samples)} samples:")
                print(f"{'Idx':<5} {'Time(ms)':<12} {'X':<12} {'Y':<12}")
                for i, (t, x, y) in enumerate(samples):
                    print(f"{i:<5} {t:<12.1f} {x:<12.6f} {y:<12.6f}")
            
            else:
                try:
                    idx_num = int(preview_choice)
                    if 0 <= idx_num < len(samples):
                        t, x, y = samples[idx_num]
                        print(f"\nSample {idx_num}:")
                        print(f"  Time: {t:.1f} ms")
                        print(f"  X: {x:.6f}")
                        print(f"  Y: {y:.6f}")
                    else:
                        print(f"Index out of range (0-{len(samples)-1})")
                except ValueError:
                    print("Invalid input.")
        
        elif action == '2':
            port = input("Enter serial port (default: COM12): ").strip()
            if not port:
                port = 'COM12'
            
            stream_path_to_arduino(samples, port, baudrate=9600, wait_ack=False)
        
        elif action == '3':
            port = input("Enter serial port (default: COM12): ").strip()
            if not port:
                port = 'COM12'
            
            stream_path_to_arduino(samples, port, baudrate=9600, wait_ack=True)
        
        elif action == '4':
            new_name = input("Enter new filename (without extension): ").strip()
            if new_name:
                new_path = os.path.join(paths_dir, f"{new_name}.csv")
                
                if os.path.exists(new_path):
                    overwrite = input(f"{new_name}.csv already exists. Overwrite? (y/n): ").strip().lower()
                    if overwrite != 'y':
                        continue
                
                try:
                    from PathGenerator import PathGenerator
                    pg = PathGenerator()
                    pg.save_to_csv(new_path, samples)
                    print(f"✓ Saved to {new_path}")
                except Exception as e:
                    print(f"Error saving: {e}")
        
        elif action == '5':
            # Go back to file selection
            main()
            return
        
        else:
            print("Invalid choice.")
    
    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
