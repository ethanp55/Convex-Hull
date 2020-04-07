from PyQt5.QtCore import QLineF, QPointF, QThread, pyqtSignal

import time
from Node import *
from Hull import *


class ConvexHullSolverThread(QThread):
	def __init__( self, unsorted_points,demo):
		self.points = unsorted_points
		self.pause = demo
		QThread.__init__(self)

	def __del__(self):
		self.wait()

	# These two signals are used for interacting with the GUI.
	show_hull    = pyqtSignal(list,tuple)
	display_text = pyqtSignal(str)

	# Some additional thread signals you can implement and use for debugging,
	# if you like
	show_tangent = pyqtSignal(list,tuple)
	erase_hull = pyqtSignal(list)
	erase_tangent = pyqtSignal(list)


	def set_points( self, unsorted_points, demo):
		self.points = unsorted_points
		self.demo   = demo


	def run(self):
		assert( type(self.points) == list and type(self.points[0]) == QPointF )

		n = len(self.points)
		print( 'Computing Hull for set of {} points'.format(n) )

		t1 = time.time()

		# Sort the points by x-value
		# Assuming that the sorted method uses quick sort, this has a time complexity of O(nlog(n)) and a space
		# complexity of O(n)
		sorted_points = sorted(self.points, key=lambda p: p.x())

		t2 = time.time()
		print('Time Elapsed (Sorting): {:3.3f} sec'.format(t2-t1))

		t3 = time.time()


		# Once we have sorted the points, find the convex hull
		# The find_hull method implements divide and conquer techniques to find the convex hull
		# Time and space and space complexity of O(nlog(n))
		convex_hull = self.find_hull(sorted_points)

		t4 = time.time()

		USE_DUMMY = False
		if USE_DUMMY:
			# This is a dummy polygon of the first 3 unsorted points
			polygon = [QLineF(self.points[i],self.points[(i+1)%3]) for i in range(3)]

			# When passing lines to the display, pass a list of QLineF objects.
			# Each QLineF object can be created with two QPointF objects
			# corresponding to the endpoints
			assert( type(polygon) == list and type(polygon[0]) == QLineF )

			# Send a signal to the GUI thread with the hull and its color
			self.show_hull.emit(polygon,(0,255,0))

		# Time complexity of O(n) because we iterate through all the points on the hull and send them to the GUI
		# Space complexity of O(n) because we store all the points from the hull
		else:
			# Initialize an empty list of points to send to the GUI
			points = []

			# Get the right-most node of the hull
			right_node = convex_hull.right_node
			# Get the node after the right-most node of the hull.  This will be used as an iterator
			current_node = convex_hull.right_node.next_node

			# Add the point corresponding to the right-most node to the list of points
			points.append(right_node.point)

			# Iterate through the nodes of the hull and add their corresponding points to the list
			while current_node != right_node:
				points.append(current_node.point)
				current_node = current_node.next_node

			# Make a list of QLineF points using the list of points we made
			polygon = [QLineF(points[i], points[i + 1]) for i in range(0, len(points) - 1)]
			polygon.append(QLineF(points[0], points[len(points) - 1]))

			# Send the list of QLineF points to the GUI
			self.show_hull.emit(polygon, (255, 0, 0))


		# Send a signal to the GUI thread with the time used to compute the
		# hull
		self.display_text.emit('Time Elapsed (Convex Hull): {:3.3f} sec'.format(t4-t3))
		print('Time Elapsed (Convex Hull): {:3.3f} sec'.format(t4-t3))


	# Divide and conquer method for finding the convex hull
	# Uses a helper function for merging hulls
	# Time and space complexity of O(nlog(n)) (see comments for more details)
	def find_hull(self, points):
		# Get the length of the list of points
		num_points = len(points)

		# Base case
		# If there is only 1 point, make a node for that point, make a hull using that node, and return the hull
		if num_points == 1:
			node = Node(points[0], None, None)
			node.next_node = node
			node.previous_node = node

			hull = Hull(node, node)

			return hull

		# Otherwise, if there is more than 1 point, split the list of points in half and find hulls for the left half
		# and the right half.  Once both hulls have been found, merge them
		# The time complexity is O(nlog(n)) because the points are split in half at each iteration, so there are log(n)
		# recursive calls, and merge_hulls is called at each recursive level, which runs in O(n) time.  So the
		# complexity is O(n) * O(log(n)), or O(nlog(n))
		# The space complexity is also O(nlog(n)), since there are log(n) recursive calls, and merge_hulls is called at
		# each recursive level, which has a space complexity of O(n).  So the complexity is O(n) * O(log(n)), or
		# O(nlog(n))
		else:
			mid = num_points // 2

			left_hull = self.find_hull(points[:mid])
			right_hull = self.find_hull(points[mid:])

			hull = self.merge_hulls(left_hull, right_hull)

			return hull


	# Helper function for merging hulls
	# Uses helper functions for finding the upper and lower tangents
	# O(n) time complexity and O(n) space complexity because the methods find_upper_tangent and find_lower_tangent are
	# called, and they have a time complexity of O(n) and space complexity of O(n).  The other operations in this method
	# have constant time and space complexity
	def merge_hulls(self, left_hull, right_hull):
		# Find the upper and lower tangents (the tangents are tuples containing the 2 nodes the tangent goes through)
		upper_tangent = self.find_upper_tangent(left_hull.right_node, right_hull.left_node)
		lower_tangent = self.find_lower_tangent(left_hull.right_node, right_hull.left_node)

		# Set the upper tangent's left node's next node to the upper tangent's right node.  Then set the upper tangent's
		# right node's previous node to the upper tangent's left node
		upper_tangent[0].next_node = upper_tangent[1]
		upper_tangent[1].previous_node = upper_tangent[0]

		# Set the lower tangent's right node's next node to the lower tangent's left node.  Then set the lower tangent's
		# left node's previous node to the lower tangent's right node
		lower_tangent[1].next_node = lower_tangent[0]
		lower_tangent[0].previous_node = lower_tangent[1]

		# Once the proper node changes have been made, any other unimportant nodes will be garbage collected
		# We can now merge the hulls by creating a new hull that uses the left hull's left node and the right hull's
		# right node
		merged_hull = Hull(left_hull.left_node, right_hull.right_node)

		# Return the merged hull
		return merged_hull


	# Helper function for finding the upper tangent of two hulls
	# O(n) time complexity and O(n) space complexity (see comments within the function for more details)
	def find_upper_tangent(self, left_hull_right_node, right_hull_left_node):
		# Get the left node and the right node
		left_node = left_hull_right_node
		right_node = right_hull_left_node

		# Calculate the initial slope between the left node and the right node
		slope = (left_node.point.y() - right_node.point.y()) / (left_node.point.x() - right_node.point.x())

		# Initialize a boolean flag for changing slope to true
		changed = True

		# As long as the slope keeps changing, keep running the algorithm
		# The time complexity is O(n) because, at most, we will only have to re-check the left and right sides a couple
		# of times, and the 2 other while loops inside of this loop run in O(n) time.  So the time complexity would be
		# O(1) * (O(n) + O(n)), which can be reduced to O(n)
		# The space complexity is O(n) because this loop is executed, at most, only a couple of times, and
		# the 2 while loops inside of this loop have a space complexity of O(1) (constant), so the space complexity
		# would be O(1) * (O(n) + O(n)), which can be reduced to O(n)
		while changed:
			# Set the flag to false.  If the slope changes, it will be reset to true
			changed = False

			# Continuously calculate and update the slope as we move counter-clockwise on the left hull and while the slope
			# continues to decrease
			# The time complexity is O(n) because, in the worst case, we would iterate counter-clockwise halfway on the
			# left hull.  So, in the worst case, the time complexity is O(.5n), which can be reduced to O(n)
			# The space complexity is O(n) because the only things we are storing/changing are the slope,
			# new slope, and left node, but we need access to all the points on the left hull
			while 1:
				new_slope = (left_node.previous_node.point.y() - right_node.point.y()) / (left_node.previous_node.point.x() - right_node.point.x())

				# If the new slope is less than the old slope, update the slope, left node, and boolean flag
				if new_slope < slope:
					slope = new_slope
					left_node = left_node.previous_node
					changed = True

				else:
					break

			# Continuously calculate and update the slope as we move clockwise on the right hull and while the slope
			# continues to increase
			# The time complexity is O(n) because, in the worst case, we would iterate clockwise halfway on the right
			# hull.  So, in the worst case, the time complexity is O(.5n), which can be reduced to O(n)
			# The space complexity is O(n) because the only things we are storing/changing are the slope,
			# new slope, and left node, but we need access to all the points on the right hull
			while 1:
				new_slope = (left_node.point.y() - right_node.next_node.point.y()) / (left_node.point.x() - right_node.next_node.point.x())

				# If the new slope is greater than the old slope, update the slope, right node, and boolean flag
				if new_slope > slope:
					slope = new_slope
					right_node = right_node.next_node
					changed = True

				else:
					break

		# Once we have finished, we have found the left and right nodes corresponding to the upper tangent.  Return
		# them in a tuple
		return left_node, right_node


	# Helper function for finding the lower tangent of two hulls
	# This function is almost identical to find_upper_tangent, except it essentially works in reverse
	# O(n) time complexity and O(n) space complexity (see comments within the function for more details)
	def find_lower_tangent(self, left_hull_right_node, right_hull_left_node):
		# Get the left node and the right node
		left_node = left_hull_right_node
		right_node = right_hull_left_node

		# Calculate the initial slope between the left node and the right node
		slope = (left_node.point.y() - right_node.point.y()) / (left_node.point.x() - right_node.point.x())

		# Initialize a boolean flag for changing slope to true
		changed = True

		# As long as the slope keeps changing, keep running the algorithm
		# The time complexity is O(n) because, at most, we will only have to re-check the left and right sides a couple
		# of times, and the 2 other while loops inside of this loop run in O(n) time.  So the time complexity would be
		# O(1) * (O(n) + O(n)), which can be reduced to O(n)
		# The space complexity is O(n) because this loop is executed, at most, only a couple of times, and
		# the 2 while loops inside of this loop have a space complexity of O(n), so the space complexity
		# would be O(1) * (O(n) + O(n)), which can be reduced to O(n)
		while changed:
			changed = False

			# Continuously calculate and update the slope as we move clockwise on the left hull and while the slope
			# continues to increase
			# The time complexity is O(n) because, in the worst case, we would iterate clockwise halfway on the left
			# hull.  So, in the worst case, the time complexity is O(.5n), which can be reduced to O(n)
			# The space complexity is O(n) because the only things we are storing/changing are the slope,
			# new slope, and left node, but we need access to all the points on the left hull
			while 1:
				new_slope = (left_node.next_node.point.y() - right_node.point.y()) / (left_node.next_node.point.x() - right_node.point.x())

				# If the new slope is greater than the old slope, update the slope, left node, and boolean flag
				if new_slope > slope:
					slope = new_slope
					left_node = left_node.next_node
					changed = True

				else:
					break

			# Continuously calculate and update the slope as we move counter-clockwise on the right hull and while the slope
			# continues to decrease
			# The time complexity is O(n) because, in the worst case, we would iterate counter-clockwise halfway on the
			# right hull.  So, in the worst case, the time complexity is O(.5n), which can be reduced to O(n)
			# The space complexity is O(n) because the only things we are storing/changing are the slope,
			# new slope, and right node, but we need access to all the points on the right hull
			while 1:
				new_slope = (left_node.point.y() - right_node.previous_node.point.y()) / (left_node.point.x() - right_node.previous_node.point.x())

				# If the new slope is less than the old slope, update the slope, right node, and boolean flag
				if new_slope < slope:
					slope = new_slope
					right_node = right_node.previous_node
					changed = True

				else:
					break

		# Once we have finished, we have found the left and right nodes corresponding to the upper tangent.  Return
		# them in a tuple
		return left_node, right_node


