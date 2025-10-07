#!/usr/bin/env python3
"""
Advanced MORK features demonstration
Shows complex pattern matching, chained transformations, and real-world scenarios
"""

from client import ManagedMORK

def test_knowledge_graph():
    """Test building a simple knowledge graph with relationships"""
    print("\n=== Advanced Test 1: Knowledge Graph ===")
    
    with ManagedMORK.connect("../target/release/mork-server").and_terminate() as server:
        server.clear().block()
        
        # Build a small social network
        server.upload_(
            # People
            "(person alice developer)\n"
            "(person bob designer)\n"
            "(person charlie manager)\n"
            "(person diana analyst)\n"
            # Friendships
            "(friend alice bob)\n"
            "(friend bob charlie)\n"
            "(friend charlie diana)\n"
            "(friend alice diana)\n"
            # Skills
            "(skill alice python)\n"
            "(skill alice rust)\n"
            "(skill bob figma)\n"
            "(skill charlie leadership)\n"
            "(skill diana sql)\n"
        ).block()
        print("✓ Built social network with people, friendships, and skills")
        
        # Find friend-of-friend connections
        server.transform(
            ("(friend $a $b)", "(friend $b $c)"),
            ("(friend_of_friend $a $c)",)
        ).block()
        print("✓ Computed friend-of-friend relationships")
        
        # Find people with similar roles who could collaborate
        server.transform(
            ("(person $p1 $role)", "(person $p2 $role)", "(friend $p1 $p2)"),
            ("(collaboration_opportunity $p1 $p2 $role)",)
        ).block()
        print("✓ Identified collaboration opportunities")
        
        # Query results
        fof = server.download("(friend_of_friend $a $c)", "($a $c)").data
        print(f"✓ Friend-of-friend connections:\n{fof}")
        
        collab = server.download("(collaboration_opportunity $p1 $p2 $role)", "($p1 $p2 $role)").data
        print(f"✓ Collaboration opportunities:\n{collab}")

def test_data_pipeline():
    """Test a data processing pipeline with multiple transformation stages"""
    print("\n=== Advanced Test 2: Data Processing Pipeline ===")
    
    with ManagedMORK.connect("../target/release/mork-server").and_terminate() as server:
        server.clear().block()
        
        # Raw sensor data
        server.upload_(
            "(sensor temp1 sensor1 25.5)\n"
            "(sensor temp2 sensor1 26.0)\n"
            "(sensor temp3 sensor1 24.8)\n"
            "(sensor temp1 sensor2 30.1)\n"
            "(sensor temp2 sensor2 31.0)\n"
            "(sensor temp3 sensor2 29.5)\n"
            "(threshold sensor1 normal 20 28)\n"
            "(threshold sensor2 warning 28 32)\n"
        ).block()
        print("✓ Loaded raw sensor data with thresholds")
        
        # Stage 1: Classify readings based on thresholds
        server.transform(
            ("(sensor $reading $sensor_id $temp)", 
             "(threshold $sensor_id $status $min $max)"),
            ("(classified $reading $sensor_id $temp $status)",)
        ).block()
        print("✓ Stage 1: Classified sensor readings by threshold")
        
        # Stage 2: Detect anomalies (readings outside thresholds)
        # Note: This would require numeric comparison in a real system
        # For demonstration, we're just marking warning status
        server.transform(
            ("(classified $reading $sensor_id $temp warning)",),
            ("(alert $sensor_id $reading $temp)",)
        ).block()
        print("✓ Stage 2: Detected potential alerts")
        
        # Query results
        classified = server.download("(classified $r $s $t $st)", "($r $s $t $st)").data
        print(f"✓ Classified readings:\n{classified}")
        
        alerts = server.download("(alert $s $r $t)", "($s $r $t)").data
        if alerts.strip():
            print(f"✓ Alerts generated:\n{alerts}")
        else:
            print("✓ No alerts (all readings normal)")

def test_recursive_relationships():
    """Test finding transitive relationships (like organizational hierarchy)"""
    print("\n=== Advanced Test 3: Organizational Hierarchy ===")
    
    with ManagedMORK.connect("../target/release/mork-server").and_terminate() as server:
        server.clear().block()
        
        # Company hierarchy
        server.upload_(
            "(employee alice ceo)\n"
            "(employee bob vp_eng)\n"
            "(employee charlie eng_manager)\n"
            "(employee diana engineer)\n"
            "(employee eve engineer)\n"
            "(reports_to bob alice)\n"
            "(reports_to charlie bob)\n"
            "(reports_to diana charlie)\n"
            "(reports_to eve charlie)\n"
        ).block()
        print("✓ Loaded organizational structure")
        
        # Direct reports
        direct_reports = server.download("(reports_to $emp $mgr)", "($emp $mgr)").data
        print(f"✓ Direct reporting relationships:\n{direct_reports}")
        
        # Find indirect reports (2 levels)
        server.transform(
            ("(reports_to $emp $mgr1)", "(reports_to $mgr1 $mgr2)"),
            ("(indirect_report $emp $mgr2 2)",)
        ).block()
        print("✓ Computed indirect reporting relationships (2 levels)")
        
        # Find all people who report up to a specific person
        indirect = server.download("(indirect_report $emp $mgr $levels)", "($emp $mgr)").data
        print(f"✓ Indirect reports:\n{indirect}")

def test_pattern_aggregation():
    """Test aggregating patterns to derive new insights"""
    print("\n=== Advanced Test 4: Pattern Aggregation ===")
    
    with ManagedMORK.connect("../target/release/mork-server").and_terminate() as server:
        server.clear().block()
        
        # Product purchase data
        server.upload_(
            "(purchase customer1 laptop electronics)\n"
            "(purchase customer1 mouse electronics)\n"
            "(purchase customer2 laptop electronics)\n"
            "(purchase customer2 book books)\n"
            "(purchase customer3 book books)\n"
            "(purchase customer3 notebook books)\n"
            "(purchase customer1 book books)\n"
        ).block()
        print("✓ Loaded purchase history")
        
        # Find customers who bought from same category
        server.transform(
            ("(purchase $c1 $p1 $cat)", "(purchase $c2 $p2 $cat)"),
            ("(same_interest $c1 $c2 $cat)",)
        ).block()
        print("✓ Identified customers with same interests")
        
        # Find cross-selling opportunities (customers in multiple categories)
        server.transform(
            ("(purchase $c $p1 $cat1)", "(purchase $c $p2 $cat2)"),
            ("(multi_category_customer $c $cat1 $cat2)",)
        ).block()
        print("✓ Identified multi-category customers")
        
        # Query results
        interests = server.download("(same_interest $c1 $c2 $cat)", "($c1 $c2 $cat)").data
        print(f"✓ Shared interests (first 5 lines):\n{chr(10).join(interests.split(chr(10))[:5])}")
        
        multi = server.download("(multi_category_customer $c $cat1 $cat2)", "($c $cat1 $cat2)").data
        print(f"✓ Multi-category customers:\n{multi}")

def main():
    """Run all advanced tests"""
    print("=" * 60)
    print("MORK Advanced Features Demonstration")
    print("=" * 60)
    
    try:
        test_knowledge_graph()
        test_data_pipeline()
        test_recursive_relationships()
        test_pattern_aggregation()
        
        print("\n" + "=" * 60)
        print("✓ All advanced tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()