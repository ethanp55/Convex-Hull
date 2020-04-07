# Class representing a hull object
# The left node and right node attributes are used when finding the upper and lower tangents
class Hull:
    def __init__(self, left_node, right_node):
        # Left-most node of the hull
        self.left_node = left_node
        # Right-most node of the hull
        self.right_node = right_node
