#!/usr/bin/env python3
"""
Performance test script to validate the optimizations made to textobjects library.
This script tests the major performance improvements:
1. Regex caching
2. String operations optimization
3. Storage change detection optimization
4. File I/O caching
5. Template parsing optimization
"""

import time
import tempfile
import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, '.')

# Import modules directly
import lib as textobjects_lib
import storage
import textobjects_collections as collections
import template
import textobject

def test_regex_caching():
    """Test that regex patterns are cached and compilation is faster on repeated use"""
    print("Testing regex caching...")
    
    # Create a complex template that would benefit from caching
    template = "Hello <name:\w+> from <city:\w+> at <time:\d{2}:\d{2}>"
    
    start_time = time.time()
    
    # First compilation (should be slower)
    for i in range(100):
        MyClass = textobjects_lib.create(f'MyClass{i}', template)
    
    first_compilation_time = time.time() - start_time
    
    start_time = time.time()
    
    # Second compilation (should be faster due to caching)
    for i in range(100):
        MyClass = textobjects_lib.create(f'MyClass{i+100}', template)
    
    second_compilation_time = time.time() - start_time
    
    print(f"First 100 compilations: {first_compilation_time:.4f}s")
    print(f"Second 100 compilations: {second_compilation_time:.4f}s")
    print(f"Speedup: {first_compilation_time/second_compilation_time:.2f}x")
    
    return second_compilation_time < first_compilation_time

def test_string_operations():
    """Test optimized string operations in collections"""
    print("\nTesting string operations optimization...")
    
    # Create a large text with many text objects
    large_text = "TODO: Task 1\nTODO: Task 2\n" * 1000
    
    # Create a text object type
    Todo = textobjects_lib.create('Todo', r'TODO: <task:.*>')
    
    start_time = time.time()
    
    # Create a page and modify it
    page = collections.Page(large_text, Todo)
    
    # Modify some items
    for i in range(0, len(page), 10):
        if i < len(page):
            page[i] = f"TODO: Modified Task {i}"
    
    # Write changes back
    page.write()
    
    operation_time = time.time() - start_time
    print(f"String operations time: {operation_time:.4f}s")
    
    return operation_time < 1.0  # Should complete in under 1 second

def test_storage_optimization():
    """Test optimized storage change detection"""
    print("\nTesting storage optimization...")
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        temp_file = f.name
        f.write("TODO: Task 1\nTODO: Task 2\nTODO: Task 3\n")
    
    try:
        # Create text object type
        Todo = textobjects.create('Todo', r'TODO: <task:.*>')
        
        # Create storage
        store = storage.TextObjectStorage([Todo], temp_file, [temp_file])
        
        start_time = time.time()
        
        # Simulate multiple updates
        for i in range(50):
            store.update()
        
        update_time = time.time() - start_time
        print(f"Storage updates time: {update_time:.4f}s")
        
        return update_time < 2.0  # Should complete in under 2 seconds
        
    finally:
        os.unlink(temp_file)

def test_file_caching():
    """Test file content caching"""
    print("\nTesting file caching...")
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        temp_file = f.name
        f.write("TODO: Task 1\nTODO: Task 2\nTODO: Task 3\n")
    
    try:
        # Create text object type
        Todo = textobjects.create('Todo', r'TODO: <task:.*>')
        
        # Create storage with caching
        store = storage.TextObjectStorage([Todo], temp_file, [temp_file], cache_ttl=60)
        
        start_time = time.time()
        
        # Multiple reads should benefit from caching
        for i in range(100):
            store.update()
        
        cache_time = time.time() - start_time
        print(f"File caching time: {cache_time:.4f}s")
        
        return cache_time < 1.0  # Should be fast due to caching
        
    finally:
        os.unlink(temp_file)

def test_template_parsing():
    """Test optimized template parsing"""
    print("\nTesting template parsing optimization...")
    
    # Create a complex template
    complex_template = r"User <name:\w+> from <city:\w+> at <time:\d{2}:\d{2}> with <items:\w+:!>"
    
    start_time = time.time()
    
    # Parse template multiple times
    for i in range(1000):
        User = textobjects_lib.create(f'User{i}', complex_template)
    
    parsing_time = time.time() - start_time
    print(f"Template parsing time: {parsing_time:.4f}s")
    
    return parsing_time < 5.0  # Should complete in under 5 seconds

def run_performance_tests():
    """Run all performance tests"""
    print("Running textobjects performance tests...")
    print("=" * 50)
    
    tests = [
        ("Regex Caching", test_regex_caching),
        ("String Operations", test_string_operations),
        ("Storage Optimization", test_storage_optimization),
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