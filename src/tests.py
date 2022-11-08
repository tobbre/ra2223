import unittest
import lpbp


class TestsILP(unittest.TestCase):
    def test_no_triplets(self, num_items=6):
        m = lpbp.lp_runner_complete(num_items=num_items, lp_type="ILP", sol_name="test1")
        obj_value = m.getObjective().getValue()
        self.assertEqual(obj_value, 3)

    def test_1_triplet(self, num_items=6):
        m = lpbp.lp_runner_complete(num_items=num_items, allowed_triplets=[[0, 0, 1, 1, 0, 1]], lp_type="ILP", sol_name="test1")
        obj_value = m.getObjective().getValue()
        self.assertEqual(obj_value, 3)


class TestsLP(unittest.TestCase):
    def test_no_triplets(self, num_items=6):
        m = lpbp.lp_runner_complete(num_items=num_items, lp_type="LP", sol_name="test1")
        obj_value = m.getObjective().getValue()
        self.assertEqual(obj_value, 3)

    def test_1_triplet(self, num_items=6):
        m = lpbp.lp_runner_complete(num_items=num_items, allowed_triplets=[[0, 0, 1, 1, 0, 1]], lp_type="LP", sol_name="test1")
        obj_value = m.getObjective().getValue()
        self.assertEqual(obj_value, 2.5)