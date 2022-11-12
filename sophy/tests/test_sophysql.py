import unittest


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)  # add assertion here


if __name__ == '__main__':
    unittest.main()

    # functions that isolate and test cases in test_sql_worms.py
    # test cases:
    # microscopy values are matched to the right aphiaID
    # injection avoidance (string params dont delete or modify sql commands (DELETE, DROP, etc))
    # invalid sci_name is handled --> print location of error name
    # empty dataset
    # class requires that tables w/ right schema are made
    # @TODO create small csv with sample data and run operations on that
    # Can you make connection to DB
    # Correctness of structure