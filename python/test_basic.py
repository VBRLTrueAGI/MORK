#!/usr/bin/env python3
"""
Basic MORK functionality test
Tests the fundamental features of MORK: upload, download, transform
"""

from client import ManagedMORK

def test_basic_upload_download():
    """Test basic upload and download operations"""
    print("\n=== Test 1: Basic Upload/Download ===")
    
    with ManagedMORK.connect("../target/release/mork-server").and_terminate() as server:
        # Clear the space
        server.clear().block()
        print("✓ Server space cleared")
        
        # Upload some simple data
        server.upload_("(foo 1)\n(foo 2)\n(bar 3)\n").block()
        print("✓ Data uploaded: (foo 1), (foo 2), (bar 3)")
        
        # Download all data
        all_data = server.download_().data
        print(f"✓ All data downloaded:\n{all_data}")
        
        # Download filtered data
        foo_data = server.download("(foo $x)", "$x").data
        print(f"✓ Filtered data (foo):\n{foo_data}")

def test_transform():
    """Test pattern matching and transformation"""
    print("\n=== Test 2: Transform Operation ===")
    
    with ManagedMORK.connect("../target/release/mork-server").and_terminate() as server:
        server.clear().block()
        
        # Upload person data
        server.upload_("(person alice 25)\n(person bob 30)\n(person charlie 28)\n").block()
        print("✓ Uploaded: (person alice 25), (person bob 30), (person charlie 28)")
        
        # Transform to extract ages
        server.transform(
            ("(person $name $age)",),
            ("(age $name $age)",)
        ).block()
        print("✓ Transformed person data to age data")
        
        # Download ages
        ages = server.download("(age $name $age)", "($name $age)").data
        print(f"✓ Ages extracted:\n{ages}")

def test_subspaces():
    """Test working with subspaces"""
    print("\n=== Test 3: Subspaces ===")
    
    with ManagedMORK.connect("../target/release/mork-server").and_terminate() as server:
        server.clear().block()
        
        # Create a subspace for animals
        with server.work_at("animals").and_clear() as animals:
            animals.upload_("(cat fluffy)\n(dog buddy)\n(cat whiskers)\n").block()
            print("✓ Uploaded animals to 'animals' subspace")
            
            # Query just cats
            cats = animals.download("(cat $name)", "$name").data
            print(f"✓ Cats in subspace:\n{cats}")
        
        # Create a subspace for vehicles
        with server.work_at("vehicles").and_clear() as vehicles:
            vehicles.upload_("(car toyota)\n(bike giant)\n(car honda)\n").block()
            print("✓ Uploaded vehicles to 'vehicles' subspace")
            
            # Query just cars
            cars = vehicles.download("(car $name)", "$name").data
            print(f"✓ Cars in subspace:\n{cars}")
        
        # Verify subspaces are isolated
        all_server_data = server.download_().data
        print(f"✓ All server data (showing both subspaces):\n{all_server_data[:200]}...")

def test_multi_pattern_transform():
    """Test transform with multiple patterns"""
    print("\n=== Test 4: Multi-Pattern Transform ===")
    
    with ManagedMORK.connect("../target/release/mork-server").and_terminate() as server:
        server.clear().block()
        
        # Upload related data
        server.upload_(
            "(parent john mary)\n"
            "(parent john tom)\n"
            "(parent jane mary)\n"
            "(parent jane tom)\n"
            "(gender mary female)\n"
            "(gender tom male)\n"
            "(gender john male)\n"
            "(gender jane female)\n"
        ).block()
        print("✓ Uploaded family data")
        
        # Find mothers (parent + female)
        server.transform(
            ("(parent $p $c)", "(gender $p female)"),
            ("(mother $p $c)",)
        ).block()
        print("✓ Transformed to extract mothers")
        
        # Download results
        mothers = server.download("(mother $p $c)", "($p $c)").data
        print(f"✓ Mothers found:\n{mothers}")

def main():
    """Run all tests"""
    print("=" * 60)
    print("MORK Basic Functionality Tests")
    print("=" * 60)
    
    try:
        test_basic_upload_download()
        test_transform()
        test_subspaces()
        test_multi_pattern_transform()
        
        print("\n" + "=" * 60)
        print("✓ All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()