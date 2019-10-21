import unittest


class TestUtils(unittest.TestCase):

    def setUp(self):
        self.test = 'Yes'

    def test_simple_conversion(self):
        result = 1
        expect = 1

        self.assertEqual(result, expect)


if __name__ == '__main__':
    unittest.main()
