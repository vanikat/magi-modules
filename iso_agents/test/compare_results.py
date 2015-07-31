import csv
import sys

class CompareResults(object):

    def __init__(self, testfn):
        self.test_filename = testfn

    def test(self):
        loadTestData()
        loadActualDataFromDeter()
        compareResults()

    def compareResults():
        #  - Test each value of power Function at each timestep
        #  - Test pDispatch for each unit, and all other parameters


if __name__ == "__main__":
    if len(sys.argv) == 3:
        cr = CompareResults(sys.argv[1])
        cr.test()
    else:
        print "Usage: compare_results.py testfile"








# Consume testdata file:
#     - For UNIT: 
#         - Test each value (eMin, pForced, etc.) with each step unit history in testdata
#     - For ISO:
#         - Test each value of power Function at each timestep
#         - Test pDispatch for each unit, and all other parameters