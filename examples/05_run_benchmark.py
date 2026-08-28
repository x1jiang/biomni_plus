"""
05_run_benchmark.py: Run the standardized comparative benchmark suite
"""

import subprocess
import sys
from pathlib import Path

def main():
    bench_script = Path(__file__).resolve().parent.parent / "benchmark_biomni_vs_claw.py"
    if not bench_script.exists():
        print(f"Error: {bench_script} not found.")
        sys.exit(1)

    print("Launching Biomni-Plus Comparative Benchmark...")
    subprocess.run([sys.executable, str(bench_script)], check=True)

if __name__ == "__main__":
    main()
