import asyncio
import time
import psutil
import httpx
import statistics
from concurrent.futures import ThreadPoolExecutor
import resource
import json

async def measure_single_request(client, payload):
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    try:
        response = await client.post(
            "http://localhost:8000/api/exercise/generate",
            json=payload,
            timeout=60.0  # 60 second timeout
        )
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        return {
            "response_time": end_time - start_time,
            "memory_delta": end_memory - start_memory,
            "response_size": len(response.content) / 1024 / 1024,  # MB
            "status_code": response.status_code
        }
    except httpx.TimeoutException:
        print(f"Request timed out after 60 seconds")
        return {
            "response_time": 60.0,
            "memory_delta": 0,
            "response_size": 0,
            "status_code": 408  # Request Timeout
        }
    except Exception as e:
        print(f"Request failed: {str(e)}")
        return {
            "response_time": time.time() - start_time,
            "memory_delta": 0,
            "response_size": 0,
            "status_code": 500  # Internal Server Error
        }
    
    response_size = len(response.content) / 1024 / 1024  # MB
    
    return {
        "response_time": end_time - start_time,
        "memory_delta": end_memory - start_memory,
        "response_size": response_size,
        "status_code": response.status_code
    }

async def run_load_test(concurrent_requests=10, total_requests=20):
    # Sample exercise generation payload matching API spec
    payload = {
        "concept_id": "python_basics",
        "student_id": "test_student",
        "student_interests": ["programming", "technology"],
        "life_category": "career",
        "difficulty": "basic"
    }
    
    metrics = []
    
    async with httpx.AsyncClient() as client:
        tasks = [measure_single_request(client, payload) for _ in range(total_requests)]
        # Run requests in batches of concurrent_requests
        for i in range(0, len(tasks), concurrent_requests):
            batch = tasks[i:i + concurrent_requests]
            batch_results = await asyncio.gather(*batch)
            metrics.extend(batch_results)
    
    return metrics

def analyze_metrics(metrics):
    response_times = [m["response_time"] for m in metrics]
    memory_deltas = [m["memory_delta"] for m in metrics]
    response_sizes = [m["response_size"] for m in metrics]
    
    return {
        "response_time": {
            "avg": statistics.mean(response_times),
            "p95": statistics.quantiles(response_times, n=20)[18],  # 95th percentile
            "max": max(response_times)
        },
        "memory_usage": {
            "avg": statistics.mean(memory_deltas),
            "p95": statistics.quantiles(memory_deltas, n=20)[18],
            "max": max(memory_deltas)
        },
        "response_size": {
            "avg": statistics.mean(response_sizes),
            "p95": statistics.quantiles(response_sizes, n=20)[18],
            "max": max(response_sizes)
        },
        "total_requests": len(metrics),
        "failed_requests": len([m for m in metrics if m["status_code"] != 200])
    }

async def main():
    # Note: Running without memory limits for preliminary testing
    print("Note: Running without memory limits for preliminary testing...")
    
    print("Starting performance test...")
    print("Testing with different concurrency levels...")
    
    concurrency_levels = [1, 2, 5]
    results = {}
    
    for concurrency in concurrency_levels:
        print(f"\nTesting with {concurrency} concurrent requests...")
        metrics = await run_load_test(concurrent_requests=concurrency)
        results[f"concurrency_{concurrency}"] = analyze_metrics(metrics)
    
    print("\nTest Results:")
    print(json.dumps(results, indent=2))
    
    # Check if any metrics exceed Supabase limits
    for concurrency, metrics in results.items():
        print(f"\nValidating {concurrency} against Supabase limits:")
        if metrics["response_time"]["max"] > 60:
            print(f"⚠️ WARNING: Max response time ({metrics['response_time']['max']:.2f}s) exceeds Supabase 60s limit")
        if metrics["memory_usage"]["max"] > 1500:
            print(f"⚠️ WARNING: Max memory usage ({metrics['memory_usage']['max']:.2f}MB) exceeds Supabase 1.5GB limit")
        if metrics["response_size"]["max"] > 6:
            print(f"⚠️ WARNING: Max response size ({metrics['response_size']['max']:.2f}MB) exceeds Supabase 6MB limit")

if __name__ == "__main__":
    asyncio.run(main())
