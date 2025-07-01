# tests/benchmark_performance.py
"""
Performance benchmarks for PinPoint 2.0 architecture.
Measures performance of key systems to ensure efficiency.
"""

import sys
from pathlib import Path
import time
import tempfile
import json
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import PinPointApplication
from core.events import EventBus
from core.tile_manager import TileManager
from core.tile_registry import get_tile_registry
from core.layout_manager import LayoutManager
from data.json_store import JSONStore
from design.theme import ThemeManager


class PerformanceBenchmark:
    """Performance benchmark suite."""
    
    def __init__(self):
        self.results = []
        
    def measure(self, name: str, func, iterations: int = 1000) -> Dict[str, Any]:
        """
        Measure performance of a function.
        
        Args:
            name: Benchmark name
            func: Function to benchmark
            iterations: Number of iterations
            
        Returns:
            Performance metrics
        """
        times = []
        
        # Warm up
        for _ in range(10):
            func()
            
        # Measure
        for _ in range(iterations):
            start = time.perf_counter()
            func()
            end = time.perf_counter()
            times.append(end - start)
            
        # Calculate metrics
        times.sort()
        result = {
            "name": name,
            "iterations": iterations,
            "total_time": sum(times),
            "average": sum(times) / len(times),
            "min": times[0],
            "max": times[-1],
            "median": times[len(times) // 2],
            "p95": times[int(len(times) * 0.95)],
            "p99": times[int(len(times) * 0.99)]
        }
        
        self.results.append(result)
        return result
        
    def benchmark_event_bus(self):
        """Benchmark event bus performance."""
        print("\n=== Event Bus Benchmarks ===")
        
        bus = EventBus()
        events_received = []
        
        def handler(data):
            events_received.append(data)
            
        # Benchmark: Subscribe
        result = self.measure(
            "EventBus.subscribe",
            lambda: bus.subscribe("test", handler),
            iterations=10000
        )
        print(f"Subscribe: {result['average']*1000:.3f}ms avg")
        
        # Setup for emit benchmark
        bus.clear()
        for i in range(100):
            bus.subscribe(f"test{i}", handler)
            
        # Benchmark: Emit (with 100 subscribers)
        result = self.measure(
            "EventBus.emit (100 subscribers)",
            lambda: bus.emit("test50", {"value": 42}),
            iterations=10000
        )
        print(f"Emit (100 subs): {result['average']*1000:.3f}ms avg")
        
        # Benchmark: Emit (no subscribers)
        result = self.measure(
            "EventBus.emit (no subscribers)",
            lambda: bus.emit("nonexistent", {"value": 42}),
            iterations=10000
        )
        print(f"Emit (no subs): {result['average']*1000:.3f}ms avg")
        
    def benchmark_tile_manager(self):
        """Benchmark tile manager performance."""
        print("\n=== Tile Manager Benchmarks ===")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            store = JSONStore(Path(temp_dir) / "tiles.json")
            manager = TileManager(store)
            
            # Benchmark: Create tile
            tile_count = 0
            def create_tile():
                nonlocal tile_count
                tile_count += 1
                return manager.create_tile("note", {
                    "title": f"Tile {tile_count}",
                    "content": "Benchmark content"
                })
                
            result = self.measure(
                "TileManager.create_tile",
                create_tile,
                iterations=1000
            )
            print(f"Create tile: {result['average']*1000:.3f}ms avg")
            
            # Get a tile ID for testing
            all_tiles = manager.get_all_tiles()
            if all_tiles:
                tile_id = all_tiles[0]["id"]
            else:
                # Create one tile if none exist
                tile = manager.create_tile("note", {"title": "Benchmark"})
                tile_id = tile["id"]
            
            # Benchmark: Get tile
            result = self.measure(
                "TileManager.get_tile",
                lambda: manager.get_tile(tile_id),
                iterations=10000
            )
            print(f"Get tile: {result['average']*1000:.3f}ms avg")
            
            # Benchmark: Update tile
            update_count = 0
            def update_tile():
                nonlocal update_count
                update_count += 1
                return manager.update_tile(tile_id, {
                    "content": f"Updated {update_count}"
                })
                
            result = self.measure(
                "TileManager.update_tile",
                update_tile,
                iterations=1000
            )
            print(f"Update tile: {result['average']*1000:.3f}ms avg")
            
            # Benchmark: Get all tiles (with 1000 tiles)
            result = self.measure(
                "TileManager.get_all_tiles (1000 tiles)",
                lambda: manager.get_all_tiles(),
                iterations=1000
            )
            print(f"Get all tiles (1000): {result['average']*1000:.3f}ms avg")
            
    def benchmark_storage(self):
        """Benchmark storage performance."""
        print("\n=== Storage Benchmarks ===")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            store = JSONStore(Path(temp_dir) / "benchmark.json")
            
            # Create test data
            small_data = {"key": "value"}
            medium_data = {f"key{i}": f"value{i}" for i in range(100)}
            large_data = {f"key{i}": {"nested": list(range(100))} for i in range(100)}
            
            # Benchmark: Save small
            result = self.measure(
                "JSONStore.save (small)",
                lambda: store.save(small_data),
                iterations=1000
            )
            print(f"Save small: {result['average']*1000:.3f}ms avg")
            
            # Benchmark: Save medium
            result = self.measure(
                "JSONStore.save (medium)",
                lambda: store.save(medium_data),
                iterations=100
            )
            print(f"Save medium: {result['average']*1000:.3f}ms avg")
            
            # Benchmark: Save large
            result = self.measure(
                "JSONStore.save (large)",
                lambda: store.save(large_data),
                iterations=100
            )
            print(f"Save large: {result['average']*1000:.3f}ms avg")
            
            # Save large data for load test
            store.save(large_data)
            
            # Benchmark: Load large
            result = self.measure(
                "JSONStore.load (large)",
                lambda: store.load(),
                iterations=100
            )
            print(f"Load large: {result['average']*1000:.3f}ms avg")
            
            # Benchmark: Get/Set operations
            result = self.measure(
                "JSONStore.set",
                lambda: store.set("benchmark_key", "benchmark_value"),
                iterations=10000
            )
            print(f"Set operation: {result['average']*1000:.3f}ms avg")
            
            result = self.measure(
                "JSONStore.get",
                lambda: store.get("benchmark_key"),
                iterations=10000
            )
            print(f"Get operation: {result['average']*1000:.3f}ms avg")
            
    def benchmark_theme_system(self):
        """Benchmark theme system performance."""
        print("\n=== Theme System Benchmarks ===")
        
        from design.theme import get_theme_manager
        from design.components import get_component_registry, ComponentType
        
        theme_manager = get_theme_manager()
        registry = get_component_registry()
        
        # Benchmark: Get theme
        result = self.measure(
            "ThemeManager.get_current_theme",
            lambda: theme_manager.get_current_theme(),
            iterations=10000
        )
        print(f"Get theme: {result['average']*1000:.3f}ms avg")
        
        # Benchmark: Switch theme
        themes = ["dark", "light", "high_contrast"]
        theme_index = 0
        def switch_theme():
            nonlocal theme_index
            theme_manager.set_current_theme(themes[theme_index % 3])
            theme_index += 1
            
        result = self.measure(
            "ThemeManager.set_current_theme",
            switch_theme,
            iterations=100
        )
        print(f"Switch theme: {result['average']*1000:.3f}ms avg")
        
        # Benchmark: Generate style
        result = self.measure(
            "ComponentRegistry.get_style",
            lambda: registry.get_style(ComponentType.BUTTON, variant="primary"),
            iterations=10000
        )
        print(f"Generate style: {result['average']*1000:.3f}ms avg")
        
    def benchmark_application_startup(self):
        """Benchmark application startup time."""
        print("\n=== Application Startup Benchmark ===")
        
        def startup():
            with tempfile.TemporaryDirectory() as temp_dir:
                app = PinPointApplication(config_path=Path(temp_dir))
                app.initialize()
                app.shutdown()
                
        # Measure with fewer iterations due to complexity
        result = self.measure(
            "Application startup/shutdown",
            startup,
            iterations=10
        )
        print(f"Startup/shutdown: {result['average']*1000:.3f}ms avg")
        
    def generate_report(self):
        """Generate performance report."""
        print("\n=== Performance Report ===")
        print(f"{'Operation':<40} {'Avg (ms)':<10} {'Min (ms)':<10} {'P95 (ms)':<10} {'P99 (ms)':<10}")
        print("-" * 80)
        
        for result in self.results:
            print(f"{result['name']:<40} "
                  f"{result['average']*1000:<10.3f} "
                  f"{result['min']*1000:<10.3f} "
                  f"{result['p95']*1000:<10.3f} "
                  f"{result['p99']*1000:<10.3f}")
            
        # Save detailed report
        report_path = Path("performance_report.json")
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\nDetailed report saved to: {report_path}")
        
    def check_performance_targets(self):
        """Check if performance meets targets."""
        print("\n=== Performance Targets ===")
        
        targets = {
            "EventBus.emit (100 subscribers)": 1.0,  # 1ms
            "TileManager.get_tile": 0.1,  # 0.1ms
            "JSONStore.get": 0.1,  # 0.1ms
            "ComponentRegistry.get_style": 0.5,  # 0.5ms
        }
        
        passed = True
        for result in self.results:
            if result['name'] in targets:
                target = targets[result['name']]
                avg_ms = result['average'] * 1000
                status = "✓ PASS" if avg_ms <= target else "✗ FAIL"
                print(f"{result['name']}: {avg_ms:.3f}ms (target: {target}ms) {status}")
                if avg_ms > target:
                    passed = False
                    
        return passed


def main():
    """Run all benchmarks."""
    print("PinPoint 2.0 Performance Benchmarks")
    print("=" * 50)
    
    benchmark = PerformanceBenchmark()
    
    # Run benchmarks
    benchmark.benchmark_event_bus()
    benchmark.benchmark_tile_manager()
    benchmark.benchmark_storage()
    benchmark.benchmark_theme_system()
    benchmark.benchmark_application_startup()
    
    # Generate report
    benchmark.generate_report()
    
    # Check targets
    if benchmark.check_performance_targets():
        print("\n✓ All performance targets met!")
        return 0
    else:
        print("\n✗ Some performance targets not met.")
        return 1


if __name__ == "__main__":
    sys.exit(main())