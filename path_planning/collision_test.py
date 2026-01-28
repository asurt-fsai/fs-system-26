"""
Test suite for the collision detection module.
"""

import numpy as np
from modules.collision import is_collision, build_obstacle_tree


def test_no_collision():
    """Test case: Path that doesn't collide with any cones."""
    cone_data = [(5, 5, 'y'), (15, 5, 'y')]
    obstacle_tree = build_obstacle_tree(cone_data)
    
    # Path from (0, 0) to (20, 0) - should not collide with cones at (5, 5) and (15, 5)
    result = is_collision(0, 0, 20, 0, robot_radius=1.5, obstacle_tree=obstacle_tree)
    assert result == False, "Expected no collision for clear path"
    print("✓ Test passed: No collision on clear path")


def test_direct_collision():
    """Test case: Path that directly hits a cone."""
    cone_data = [(10, 0, 'y')]
    obstacle_tree = build_obstacle_tree(cone_data)
    
    # Path from (0, 0) to (20, 0) passes through cone at (10, 0)
    result = is_collision(0, 0, 20, 0, robot_radius=1.5, obstacle_tree=obstacle_tree)
    assert result == True, "Expected collision when path hits cone"
    print("✓ Test passed: Collision detected on direct path")


def test_close_collision():
    """Test case: Path that comes close to a cone (within robot radius)."""
    cone_data = [(10, 1.0, 'y')]  # Cone very close to the path
    obstacle_tree = build_obstacle_tree(cone_data)
    
    # Path from (0, 0) to (20, 0) with robot_radius=1.5
    result = is_collision(0, 0, 20, 0, robot_radius=1.5, obstacle_tree=obstacle_tree)
    assert result == True, "Expected collision when cone is within robot radius"
    print("✓ Test passed: Collision detected when cone within robot radius")


def test_safe_distance():
    """Test case: Path that stays safely away from cones."""
    cone_data = [(10, 3.0, 'y')]  # Cone far enough away
    obstacle_tree = build_obstacle_tree(cone_data)
    
    # Path from (0, 0) to (20, 0) with robot_radius=1.5
    result = is_collision(0, 0, 20, 0, robot_radius=1.5, obstacle_tree=obstacle_tree)
    assert result == False, "Expected no collision when cone is far enough"
    print("✓ Test passed: No collision when cone at safe distance")


def test_max_edge_length():
    """Test case: Edge that exceeds max_edge_len is considered invalid."""
    cone_data = []  # No cones, so collision would be False if not for edge length
    obstacle_tree = build_obstacle_tree(cone_data) if cone_data else None
    
    # Create dummy tree for testing
    cone_data = [(100, 100, 'y')]
    obstacle_tree = build_obstacle_tree(cone_data)
    
    # Very long path (distance > 30)
    result = is_collision(0, 0, 50, 0, robot_radius=1.5, obstacle_tree=obstacle_tree, max_edge_len=30.0)
    assert result == True, "Expected collision due to exceeding max_edge_len"
    print("✓ Test passed: Edge exceeding max_edge_len rejected")


def test_multiple_cones():
    """Test case: Multiple cones with a safe path between them."""
    cone_data = [
        (5, -2, 'y'),   # Left side
        (15, 2, 'b')    # Right side
    ]
    obstacle_tree = build_obstacle_tree(cone_data)
    
    # Path from (0, 0) to (20, 0) should fit between cones
    result = is_collision(0, 0, 20, 0, robot_radius=1.0, obstacle_tree=obstacle_tree)
    assert result == False, "Expected no collision with path between cones"
    print("✓ Test passed: Safe path found between multiple cones")


def test_obstacle_tree_building():
    """Test case: Verify KDTree is built correctly."""
    cone_data = [(0, 0, 'y'), (5, 5, 'b'), (10, 0, 'y')]
    obstacle_tree = build_obstacle_tree(cone_data)
    
    # Query a point at a cone location
    dist, idx = obstacle_tree.query([0, 0])
    assert dist < 0.01, "Expected to find cone at (0, 0)"
    assert idx == 0, "Expected correct cone index"
    
    dist, idx = obstacle_tree.query([5, 5])
    assert dist < 0.01, "Expected to find cone at (5, 5)"
    assert idx == 1, "Expected correct cone index"
    
    print("✓ Test passed: KDTree built and queried correctly")


def run_all_tests():
    """Run all collision detection tests."""
    print("\n=== Running Collision Detection Tests ===\n")
    
    test_no_collision()
    test_direct_collision()
    test_close_collision()
    test_safe_distance()
    test_max_edge_length()
    test_multiple_cones()
    test_obstacle_tree_building()
    
    print("\n=== All tests passed! ===\n")


if __name__ == "__main__":
    run_all_tests()
