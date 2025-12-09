"""Path generation utilities for arm characterization.

Provides a PathGenerator class that accepts waypoints and emits a
parametric (time-indexed) list of (t_ms, x, y) samples suitable for
feeding into a serial controller or saving to CSV.

Simple linear interpolation is used between consecutive waypoints.
"""
from typing import List, Tuple, Optional
import csv


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
    BR_x, BR_y = 137.0, 100.0
    TR_x, TR_y = 137.0, 126.0
    BL_x, BL_y = 111.0, 100.0
    TL_x, TL_y = 111.0, 126.0

    waypoints = [(BR_x, BR_y), (TR_x, TR_y), (TL_x, TL_y), (BL_x, BL_y)]
    pg = PathGenerator(waypoints=waypoints, closed=True)
    return pg.generate_parametric_path(total_time_ms=total_time_ms, rate_hz=rate_hz)


if __name__ == '__main__':
    # simple demo: generate a 4-second square at 100 Hz and save
    samples = square_right_defined(total_time_ms=4000.0, rate_hz=100)
    pg = PathGenerator(closed=True)
    pg.set_waypoints([(137.0,100.0),(137.0,126.0),(111.0,126.0),(111.0,100.0)], closed=True)
    pg.save_to_csv('paths/square_path.csv', samples)
    print(f"Wrote {len(samples)} samples to paths/square_path.csv")