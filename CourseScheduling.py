from Graph import CourseGraph
from Course import Course
from Schedule import Schedule
from priodict import priorityDictionary as priodict
from copy import deepcopy


class CourseScheduling:
	def __init__(self, total_quarter_codes=6):
		self.total_quarter_codes = total_quarter_codes

	def get_schedule(self, G: CourseGraph, L: Schedule, R, from_u, to_u):
		best = None
		best_u = None
		for u in range(from_u, to_u + 1):
			G_temp = deepcopy(G)
			L_temp = deepcopy(L)
			R_temp = deepcopy(R)
			schedule = self.get_single_schedule(G_temp, L_temp, R_temp, u)
			if schedule and (not best or len(schedule) > len(best)):
				best = schedule
				best_u = u
		return best, best_u

	def get_single_schedule(self, G: CourseGraph, L: Schedule, R, u: int):
		"""
		:param G: course graph G
		:param L: empty schedule
		:param u: upper bound layer index
		:param R: requirements table
		:return: schedule if schedule is valid, else none
		"""
		PQ = self._init_priodict(G)

		while PQ:
			current = PQ.smallest()
			del PQ[current]
			cur_course = G[current]
			if self._course_satisfy_any_requirements(cur_course, R):  # do not assign this course
				assigned_index = self.find_course_assign_index(cur_course, L, u)
				L.add_course(assigned_index, current, cur_course.units)
				self._expand_queue(G, current, PQ, assigned_index)
				self.tag_requirement(R, cur_course)
		if self.is_valid_schedule(G, L, R, u):
			L.clear_empty()
			return L
		else:
			return None

	def is_valid_schedule(self, G, L, R, u):
		# first check R is all 0
		if any([any(i) for i in R.values()]):
			return False
		if u > len(L): return False
		# check if a upper only class is in lower division
		for clist in L.L[:u]:
			for cid in clist:
				if G[cid].isUpperOnly:
					return False
		return True


	def tag_requirement(self, R, v: Course):
		"""
		after we assign the course v to the schedule, we check what requirements it satisfies
		:param R: requirements table
		:param v: Course
		"""
		for requirement, index in v.requirements:
			R[requirement][index] = max(0, R[requirement][index] - 1)

	def _expand_queue(self, G, cid, PQ: priodict, assigned_index: int):
		"""
		after we assign course v to the schedule, we expand the priority queue with new ready coruses
		at the same time, we also tag prereq in course cid's successors in the corresponding OR set.
		:param G: CourseGraph
		:param cid: course id, the key in G
		:param PQ: Priority queue
		:param assigned_index: where cid is assigned in L.
		"""
		for child, OR_index in G[cid].successors:
			child_course = G[child]
			if not G[child].prereqBool[OR_index]:
				child_course.prereqBool[OR_index] = cid
				child_course.dependentIndex = max(assigned_index, G[child].dependentIndex)

			if all(child_course.prereqBool):
				PQ[child] = child_course.label

	def _course_satisfy_any_requirements(self, v: Course, R):
		"""
		:param v: course
		:param R: Requirements table
		:return: True if v satisfy any requirements in R.
		"""
		for name, index in v.requirements:
			if R[name][index] > 0:
				return True
		return False

	def _init_priodict(self, G: CourseGraph):
		"""
		initialize the priodict with current ready courses
		:param G:
		:return:
		"""
		PQ = priodict()
		for cid, course in G.items():
			if not course.prereq_list():  # course has no prereq
				PQ[cid] = course.label
		return PQ

	def find_course_assign_index(self, v: Course, L: Schedule, u: int):
		"""
		single course assignment
		:param v: course
		:param L: schedule
		:param u: upperBound index
		:return: the index of the layer where v will be assigned
		"""
		step = len(L) - 1
		if (not self.valid(L, step, v)) or v.has_dependent(step):
			L.add_layer()
			i = step + 1
			while not self.valid(L, i, v) and (not v.isUpperOnly or i >= u):
				# add new empty layer L_i above current highest layer
				L.add_layer()
				i += 1

		lastStep = len(L) - 1
		step -= 1
		while (v.isUpperOnly and step >= u) or (not v.isUpperOnly and step >= 0):
			if v.has_dependent(step):
				break
			elif self.valid(L, step, v):
				lastStep = step
			step -= 1

		return lastStep

	def valid(self, L: Schedule, i: int, v: Course):
		"""
		For a course v, we define a layer L_i with
		M_i+v.units < W(L_i) and (i mod 6) in v.quarterCodes
		to be a valid layer of v.

		:param L: current schedule
		:param i: index for layer L_i
		:param v:  course
		:return:   true if valid
		"""
		return L.layer_is_full(i, v.units) and \
		       (i % self.total_quarter_codes) in v.quarterCodes
