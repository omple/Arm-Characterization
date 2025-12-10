"""Path generation utilities for arm characterization.

Provides a PathGenerator class that accepts waypoints and emits a
parametric (time-indexed) list of (t_ms, x, y) samples suitable for
feeding into a serial controller or saving to CSV.

Simple linear interpolation is used between consecutive waypoints.
"""
from typing import List, Tuple, Optional
import csv
import math


class PathGenerator:
    """Build parametric paths (x,y) over a specified duration.

    Usage:
      pg = PathGenerator([(x1,y1),(x2,y2),...], closed=False)
      samples = pg.generate_parametric_path(total_time_ms=2000, rate_hz=100)
      pg.save_to_csv('out.csv', samples)
    """

    def __init__(self, waypoints: Optional[List[Tuple[float, float]]] = None, closed: bool = False):
        self.waypoints: List[Tuple[float, float]] = waypoints[:] if waypoints else []
        self.closed = closed

    def set_waypoints(self, waypoints: List[Tuple[float, float]], closed: Optional[bool] = None) -> None:
        self.waypoints = waypoints[:]
        if closed is not None:
            self.closed = closed

    def add_waypoint(self, x: float, y: float) -> None:
        self.waypoints.append((x, y))

    def generate_parametric_path(self, total_time_ms: float, rate_hz: int = 100) -> List[Tuple[float, float, float]]:
        """Generate (t_ms, x, y) samples for the configured waypoints.

        - `total_time_ms`: total duration of the path in milliseconds.
        - `rate_hz`: sampling frequency in Hz.

        Returns a list of tuples (t_ms, x, y). If fewer than 2 waypoints
        are present the single point (or empty list) is returned repeated
        or empty accordingly.
        """
        pts = self.waypoints
        n = len(pts)
        if n == 0:
            return []
        if n == 1:
            # single point repeated for the duration
            total_samples = max(1, int(total_time_ms * rate_hz / 1000.0))
            return [(i * (1000.0 / rate_hz), pts[0][0], pts[0][1]) for i in range(total_samples)]

        # number of segments depends on closed flag
        seg_count = n if self.closed else (n - 1)
        seg_time = total_time_ms / float(seg_count)
        total_samples = max(1, int(total_time_ms * rate_hz / 1000.0))

        samples: List[Tuple[float, float, float]] = []

        for s in range(total_samples):
            t_ms = s * (1000.0 / rate_hz)
            # clamp final sample to total_time_ms
            if t_ms > total_time_ms:
                t_ms = total_time_ms

            # Normalized time [0, 1] across the entire path
            t_norm = min(1.0, t_ms / total_time_ms) if total_time_ms > 0 else 1.0
            
            # determine which segment we're on
            seg_idx = int(min(seg_count - 1, t_ms // seg_time))
            # local time into the segment [0,1]
            u = (t_ms - seg_idx * seg_time) / seg_time if seg_time > 0 else 0.0

            i0 = seg_idx
            i1 = (seg_idx + 1) % n
            if not self.closed:
                # for open path indices are straightforward
                i0 = seg_idx
                i1 = seg_idx + 1

            x0, y0 = pts[i0]
            x1, y1 = pts[i1]
            x = x0 + u * (x1 - x0)
            y = y0 + u * (y1 - y0)
            samples.append((t_ms, x, y))

        # Ensure final sample is exactly at the last waypoint (for closed paths, that's the start)
        if samples:
            final_idx = 0 if self.closed else (n - 1)
            samples[-1] = (total_time_ms, pts[final_idx][0], pts[final_idx][1])

        return samples

    def save_to_csv(self, filename: str, samples: List[Tuple[float, float, float]]) -> None:
        """Save samples to CSV with header `t_ms,x,y`."""
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['t_ms', 'x', 'y'])
            for t, x, y in samples:
                writer.writerow([f"{t:.3f}", f"{x:.6f}", f"{y:.6f}"])


def square_right_defined(total_time_ms: float, rate_hz: int = 100) -> List[Tuple[float, float, float]]:
    """Generate the same parametric square from the Arduino example.

    Four corners are taken from the Arduino snippet: BR, TR, BL, TL
    and the square is traversed in the same order.
    """
    BR_x, BR_y = .081, 0.081
    TR_x, TR_y = .13, 0.081
    BL_x, BL_y = 0.13, .13
    TL_x, TL_y = 0.081, 0.13

    waypoints = [(BR_x, BR_y), (TR_x, TR_y), (TL_x, TL_y), (BL_x, BL_y)]
    pg = PathGenerator(waypoints=waypoints, closed=True)
    return pg.generate_parametric_path(total_time_ms=total_time_ms, rate_hz=rate_hz)

def circle_path(center_x: float, center_y: float, radius: float, total_time_ms: float, rate_hz: int = 100, start_angle: float = 0.0) -> List[Tuple[float, float, float]]:
    
    total_samples = max(1, int(total_time_ms * rate_hz / 1000.0))
    samples: List[Tuple[float, float, float]] = []
    
    for s in range(total_samples):
        t_ms = s * (1000.0 / rate_hz)
        if t_ms > total_time_ms:
            t_ms = total_time_ms
        
        # Normalized progress around circle [0, 1]
        t_norm = min(1.0, t_ms / total_time_ms) if total_time_ms > 0 else 1.0
        
        # Angle progresses from start_angle to start_angle + 2π
        angle = start_angle + t_norm * 2 * math.pi
        
        # Parametric circle equation
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        
        samples.append((t_ms, x, y))
    
    # Ensure final sample closes the circle (returns to start)
    if samples:
        x_final = center_x + radius * math.cos(start_angle)
        y_final = center_y + radius * math.sin(start_angle)
        samples[-1] = (total_time_ms, x_final, y_final)
    
    return samples


def test_path(samples: List[Tuple[float, float, float]]) -> None:
    """Interactive test/preview of generated path."""
    if not samples:
        print("No samples to test.")
        return
    
    print("\n" + "="*70)
    print("PATH TEST & PREVIEW")
    print("="*70)
    
    # Summary statistics
    duration = samples[-1][0]
    num_samples = len(samples)
    xs = [s[1] for s in samples]
    ys = [s[2] for s in samples]
    
    print(f"\nPath Statistics:")
    print(f"  Total samples: {num_samples}")
    print(f"  Duration: {duration:.1f} ms")
    print(f"  X range: [{min(xs):.6f}, {max(xs):.6f}]")
    print(f"  Y range: [{min(ys):.6f}, {max(ys):.6f}]")
    
    # Check if closed
    first_xy = (samples[0][1], samples[0][2])
    last_xy = (samples[-1][1], samples[-1][2])
    is_closed = abs(first_xy[0] - last_xy[0]) < 0.0001 and abs(first_xy[1] - last_xy[1]) < 0.0001
    
    print(f"\nPath endpoints:")
    print(f"  Start: ({first_xy[0]:.6f}, {first_xy[1]:.6f})")
    print(f"  End:   ({last_xy[0]:.6f}, {last_xy[1]:.6f})")
    print(f"  Closed: {'Yes ✓' if is_closed else 'No'}")
    
    while True:
        print("\n" + "-"*70)
        print("Test Options:")
        print("  1. Show first 10 samples")
        print("  2. Show last 10 samples")
        print("  3. Show all samples (may be long)")
        print("  4. Show sample at specific index")
        print("  5. Check timing intervals")
        print("  6. Save to CSV")
        print("  0. Exit test")
        print("-"*70)
        
        choice = input("Enter choice (0-6): ").strip()
        
        if choice == '0':
            print("\nExiting test mode.")
            break
        
        elif choice == '1':
            print(f"\nFirst 10 samples:")
            print(f"{'Idx':<5} {'Time(ms)':<12} {'X':<12} {'Y':<12}")
            print("-" * 41)
            for i in range(min(10, len(samples))):
                t, x, y = samples[i]
                print(f"{i:<5} {t:<12.1f} {x:<12.6f} {y:<12.6f}")
        
        elif choice == '2':
            print(f"\nLast 10 samples:")
            print(f"{'Idx':<5} {'Time(ms)':<12} {'X':<12} {'Y':<12}")
            print("-" * 41)
            start_idx = max(0, len(samples) - 10)
            for i in range(start_idx, len(samples)):
                t, x, y = samples[i]
                print(f"{i:<5} {t:<12.1f} {x:<12.6f} {y:<12.6f}")
        
        elif choice == '3':
            print(f"\nAll {len(samples)} samples:")
            print(f"{'Idx':<5} {'Time(ms)':<12} {'X':<12} {'Y':<12}")
            print("-" * 41)
            for i, (t, x, y) in enumerate(samples):
                print(f"{i:<5} {t:<12.1f} {x:<12.6f} {y:<12.6f}")
        
        elif choice == '4':
            try:
                idx = int(input(f"Enter index (0-{len(samples)-1}): ").strip())
                if 0 <= idx < len(samples):
                    t, x, y = samples[idx]
                    print(f"\nSample {idx}:")
                    print(f"  Time: {t:.1f} ms")
                    print(f"  X: {x:.6f}")
                    print(f"  Y: {y:.6f}")
                    print(f"  Command: {x},{y}")
                else:
                    print(f"Invalid index. Must be 0-{len(samples)-1}")
            except ValueError:
                print("Invalid input.")
        
        elif choice == '5':
            time_diffs = [samples[i+1][0] - samples[i][0] for i in range(len(samples)-1)]
            unique_diffs = sorted(set([round(d, 1) for d in time_diffs]))
            
            print(f"\nTiming Analysis:")
            print(f"  Min interval: {min(time_diffs):.1f} ms")
            print(f"  Max interval: {max(time_diffs):.1f} ms")
            print(f"  Unique intervals: {unique_diffs}")
            print(f"  Expected rate: ~10 ms (100 Hz)")
        
        elif choice == '6':
            filename = input("Enter CSV filename (default: test_path.csv): ").strip()
            if not filename:
                filename = 'test_path.csv'
            pg = PathGenerator()
            pg.save_to_csv(filename, samples)
            print(f"✓ Saved {len(samples)} samples to {filename}")
        
        else:
            print("Invalid choice.")
    
    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    samples = [(0.08, 0.08), (0.13, 0.08), (0.13, 0.13), (0.08, 0.13)]
    pg = PathGenerator(waypoints=samples, closed=True)
    sample = square_right_defined(total_time_ms=10000.0, rate_hz=20)
    sample2 = circle_path(center_x=0.097897, center_y=0.097897, radius=0.03, total_time_ms=5000.0, rate_hz=20)
    
    try:        
        # Ask if user wants to save to CSV
        filename = f"paths/square_path.csv"
        pg.save_to_csv(filename, sample)
        print(f"✓ Saved square path to {filename}")
        filename = f"paths/circle_path.csv"
        pg.save_to_csv(filename, sample2)
        print(f"✓ Saved circle path to {filename}")
    except EOFError:
        # Handle non-interactive mode
        print("\n(Non-interactive mode - skipping prompts)")