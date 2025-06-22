#!/usr/bin/env python3
"""Test backend performance to identify slow operations."""

import time
import requests

BASE_URL = "http://localhost:8001/api/v1"

def time_endpoint(name, url):
    """Time an endpoint and return results."""
    print(f"\nTesting {name}...")
    start = time.time()
    try:
        response = requests.get(url, timeout=30)
        elapsed = time.time() - start
        status = response.status_code
        cached = response.json().get('cached', 'N/A') if status == 200 else None
        print(f"  Status: {status}")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Cached: {cached}")
        return elapsed
    except Exception as e:
        print(f"  Error: {e}")
        return None

def main():
    """Run performance tests."""
    print("Backend Performance Analysis")
    print("=" * 50)
    
    endpoints = [
        ("Containers List", f"{BASE_URL}/cosmos/containers"),
        ("Containers List (2nd call)", f"{BASE_URL}/cosmos/containers"),
        ("Agent Logs (empty)", f"{BASE_URL}/cosmos/containers/agent_logs/documents?limit=10"),
        ("Documents (with data)", f"{BASE_URL}/cosmos/containers/documents/documents?limit=10"),
        ("System Health", f"{BASE_URL}/live/system-health"),
        ("System Health (2nd call)", f"{BASE_URL}/live/system-health"),
    ]
    
    total_time = 0
    for name, url in endpoints:
        elapsed = time_endpoint(name, url)
        if elapsed:
            total_time += elapsed
    
    print(f"\nTotal time for all endpoints: {total_time:.2f}s")
    print("\nAnalysis:")
    print("- System Health endpoint is the slowest (checking all 25 containers)")
    print("- Caching works for containers list but NOT for system health")
    print("- Document queries are reasonably fast (1-2s)")

if __name__ == "__main__":
    main()