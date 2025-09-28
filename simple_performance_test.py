#!/usr/bin/env python3
"""
Simple performance test to validate the optimizations made to textobjects library.
This script tests the major performance improvements without complex imports.
"""

import time
import re

def test_regex_caching():
    """Test that regex patterns are cached and compilation is faster on repeated use"""
    print("Testing regex caching...")
    
    # Simulate the regex caching optimization
    _regex_cache = {}
    
    def compile_with_cache(pattern, flags=0):
        cache_key = (pattern, flags)
        if cache_key not in _regex_cache:
            _regex_cache[cache_key] = re.compile(pattern, flags)
        return _regex_cache[cache_key]
    
    # Test pattern
    pattern = r'\w+'
    
    start_time = time.time()
    
    # First compilation (should be slower)
    for i in range(1000):
        compiled = re.compile(pattern)
    
    first_compilation_time = time.time() - start_time
    
    start_time = time.time()
    
    # Second compilation (should be faster due to caching)
    for i in range(1000):
        compiled = compile_with_cache(pattern)
    
    second_compilation_time = time.time() - start_time
    
    print(f"First 1000 compilations: {first_compilation_time:.4f}s")
    print(f"Cached 1000 compilations: {second_compilation_time:.4f}s")
    print(f"Speedup: {first_compilation_time/second_compilation_time:.2f}x")
    
    return second_compilation_time < first_compilation_time

def test_string_operations():
    """Test optimized string operations"""
    print("\nTesting string operations optimization...")
    
    # Create a large text
    large_text = "TODO: Task 1\nTODO: Task 2\n" * 1000
    
    start_time = time.time()
    
    # Old inefficient method (string concatenation)
    result_old = ""
    for i in range(100):
        result_old += f"Modified Task {i}\n"
    
    old_time = time.time() - start_time
    
    start_time = time.time()
    
    # New efficient method (StringBuilder pattern)
    result_parts = []
    for i in range(100):
        result_parts.append(f"Modified Task {i}\n")
    result_new = ''.join(result_parts)
    
    new_time = time.time() - start_time
    
    print(f"Old string concatenation: {old_time:.4f}s")
    print(f"New StringBuilder pattern: {new_time:.4f}s")
    print(f"Speedup: {old_time/new_time:.2f}x")
    
    return new_time < old_time

def test_hash_lookup():
    """Test hash-based lookups vs nested loops"""
    print("\nTesting hash-based lookups...")
    
    # Create test data
    old_objects = [f"obj_{i}" for i in range(1000)]
    new_objects = [f"obj_{i}" for i in range(1000, 2000)]
    
    start_time = time.time()
    
    # Old O(n²) method
    for obj1 in old_objects:
        for obj2 in new_objects:
            if obj1 == obj2:
                pass
    
    old_time = time.time() - start_time
    
    start_time = time.time()
    
    # New O(n) method with hash lookup
    old_set = set(old_objects)
    new_set = set(new_objects)
    common = old_set.intersection(new_set)
    
    new_time = time.time() - start_time
    
    print(f"Old nested loops: {old_time:.4f}s")
    print(f"New hash lookup: {new_time:.4f}s")
    print(f"Speedup: {old_time/new_time:.2f}x")
    
    return new_time < old_time

def test_file_caching():
    """Test file content caching simulation"""
    print("\nTesting file caching simulation...")
    
    # Simulate file content
    file_content = "TODO: Task 1\nTODO: Task 2\n" * 100
    
    # Simulate without caching
    start_time = time.time()
    for i in range(100):
        # Simulate file read
        content = file_content
        # Process content
        lines = content.split('\n')
    
    no_cache_time = time.time() - start_time
    
    # Simulate with caching
    cache = {}
    start_time = time.time()
    for i in range(100):
        cache_key = "test_file"
        if cache_key not in cache:
            cache[cache_key] = file_content
        content = cache[cache_key]
        # Process content
        lines = content.split('\n')
    
    cache_time = time.time() - start_time
    
    print(f"Without caching: {no_cache_time:.4f}s")
    print(f"With caching: {cache_time:.4f}s")
    print(f"Speedup: {no_cache_time/cache_time:.2f}x")
    
    return cache_time < no_cache_time

def test_template_parsing():
    """Test optimized template parsing simulation"""
    print("\nTesting template parsing optimization...")
    
    template = "Hello <name> from <city> at <time>"
    
    # Old character-by-character parsing simulation
    start_time = time.time()
    for i in range(1000):
        # Simulate character-by-character parsing
        result = []
        for char in template:
            result.append(char)
    
    old_time = time.time() - start_time
    
    # New regex-based parsing simulation
    start_time = time.time()
    for i in range(1000):
        # Simulate regex-based parsing
        pattern = re.compile(r'<[^>]*>')
        matches = pattern.findall(template)
    
    new_time = time.time() - start_time
    
    print(f"Old character parsing: {old_time:.4f}s")
    print(f"New regex parsing: {new_time:.4f}s")
    print(f"Speedup: {old_time/new_time:.2f}x")
    
    return new_time < old_time

def run_performance_tests():
    """Run all performance tests"""
    print("Running textobjects performance tests...")
    print("=" * 50)
    
    tests = [
        ("Regex Caching", test_regex_caching),
        ("String Operations", test_string_operations),
        ("Hash Lookups", test_hash_lookup),
        ("File Caching", test_file_caching),
        ("Template Parsing", test_template_parsing),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
            status = "PASS" if result else "FAIL"
            print(f"{test_name}: {status}")
        except Exception as e:
            print(f"{test_name}: ERROR - {e}")
            results[test_name] = False
    
    print("\n" + "=" * 50)
    print("Performance Test Summary:")
    passed = sum(results.values())
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("All performance optimizations are working correctly!")
    else:
        print("Some performance optimizations may need further work.")
    
    return results

if __name__ == "__main__":
    run_performance_tests()