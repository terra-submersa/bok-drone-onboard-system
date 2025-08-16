from typing import Tuple

from bok_drone_onboard_system.positioner import Vector, vector_from_quaternion, Position


def calculate_pole_end_position(
    quaternion: Tuple[float, float, float, float],
    utm_position: Tuple[float, float, float],
    pole_length: float
) -> Tuple[float, float, float]:
    """
    Calculate the position at end B of the pole given the quaternion orientation,
    position at end A, and pole length.
    
    Args:
        quaternion: BNO08x quaternion as (i, j, k, real)
        utm_position: Position at end A of the pole as (x, y, z) in UTM coordinates
        pole_length: Length of the pole in meters
        
    Returns:
        Position at end B of the pole as (x, y, z) in UTM coordinates
    """
    # Create a Position object from the UTM coordinates
    position_a = Position(*utm_position)
    
    # The natural vector (1,0,0) represents the pole's direction in its local frame
    v_nat = Vector(1, 0, 0)
    
    # Apply the quaternion rotation to get the pole's direction in world frame
    direction = vector_from_quaternion(quaternion, v_nat)
    
    # Normalize the direction vector
    direction_np = direction.np
    norm = (direction_np[0]**2 + direction_np[1]**2 + direction_np[2]**2)**0.5
    normalized_direction = Vector(
        direction.x / norm,
        direction.y / norm,
        direction.z / norm
    )
    
    # Scale the direction vector by the pole length
    scaled_direction = Vector(
        normalized_direction.x * pole_length,
        normalized_direction.y * pole_length,
        normalized_direction.z * pole_length
    )
    
    # Calculate position B by adding the scaled direction to position A
    position_b = position_a.plus(scaled_direction)
    
    # Return the result as a tuple
    return (position_b.x, position_b.y, position_b.z)