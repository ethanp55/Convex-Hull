# Class representing a node object
# A node contains the point that it represents and pointers to the next and previous nodes.  This allows for a linked
# list instead of keeping track of a circular array
class Node:
    def __init__(self, point, previous_node, next_node):
        # The point that the node represents
        self.point = point
        # The previous node
        self.previous_node = previous_node
        # The next node
        self.next_node = next_node
