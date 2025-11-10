#!/usr/bin/env python3
"""
test_evaluation.py - Unit tests for the city evaluation system

Tests the evaluation module functions including scoring, problem analysis,
population classification, and voting simulation.
"""

from unittest.mock import patch
from src.micropolis import evaluation, types


from tests.assertions import Assertions

class TestEvaluation(Assertions):
    """Test cases for the evaluation system."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Reset evaluation state
        evaluation.EvalValid = 0
        evaluation.CityYes = 0
        evaluation.CityNo = 0
        evaluation.ProblemTable = [0] * types.PROBNUM
        evaluation.ProblemTaken = [0] * types.PROBNUM
        evaluation.ProblemVotes = [0] * types.PROBNUM
        evaluation.ProblemOrder = [0] * 4
        evaluation.CityPop = 0
        evaluation.deltaCityPop = 0
        evaluation.CityAssValue = 0
        evaluation.CityClass = 0
        evaluation.CityScore = 0
        evaluation.deltaCityScore = 0
        evaluation.AverageCityScore = 0
        evaluation.TrafficAverage = 0

        # Reset global simulation state used by evaluation
        types.TotalPop = 0
        types.ResPop = 0
        types.ComPop = 0
        types.IndPop = 0
        types.RoadTotal = 0
        types.RailTotal = 0
        types.PolicePop = 0
        types.FireStPop = 0
        types.HospPop = 0
        types.StadiumPop = 0
        types.PortPop = 0
        types.APortPop = 0
        types.CoalPop = 0
        types.NuclearPop = 0
        types.CrimeAverage = 0
        types.PolluteAverage = 0
        types.LVAverage = 0
        types.CityTax = 0
        types.ResCap = False
        types.ComCap = False
        types.IndCap = False
        types.RoadEffect = 0
        types.PoliceEffect = 0
        types.FireEffect = 0
        types.RValve = 0
        types.CValve = 0
        types.IValve = 0
        types.unPwrdZCnt = 0
        types.PwrdZCnt = 0

    def test_eval_init(self):
        """Test evaluation initialization."""
        # Set some non-zero values first
        evaluation.CityScore = 600
        evaluation.CityYes = 50
        evaluation.ProblemVotes[0] = 10

        evaluation.EvalInit()

        self.assertEqual(evaluation.CityYes, 0)
        self.assertEqual(evaluation.CityNo, 0)
        self.assertEqual(evaluation.CityPop, 0)
        self.assertEqual(evaluation.CityScore, 500)  # Should be set to 500
        self.assertEqual(evaluation.EvalValid, 1)
        self.assertEqual(sum(evaluation.ProblemVotes), 0)
        self.assertEqual(sum(evaluation.ProblemOrder), 0)

    def test_get_ass_value(self):
        """Test assessed value calculation."""
        # Set up infrastructure values
        types.RoadTotal = 100
        types.RailTotal = 50
        types.PolicePop = 10
        types.FireStPop = 8
        types.HospPop = 5
        types.StadiumPop = 2
        types.PortPop = 1
        types.APortPop = 1
        types.CoalPop = 3
        types.NuclearPop = 2

        evaluation.GetAssValue()

        # Calculate expected value
        expected = (100 * 5 + 50 * 10 + 10 * 1000 + 8 * 1000 + 5 * 400 +
                   2 * 3000 + 1 * 5000 + 1 * 10000 + 3 * 3000 + 2 * 6000) * 1000
        self.assertEqual(evaluation.CityAssValue, expected)

    def test_do_pop_num_village(self):
        """Test population calculation for village (smallest class)."""
        types.ResPop = 10
        types.ComPop = 5
        types.IndPop = 3

        evaluation.DoPopNum()

        expected_pop = (10 + 5 * 8 + 3 * 8) * 20
        self.assertEqual(evaluation.CityPop, expected_pop)
        self.assertEqual(evaluation.CityClass, 0)  # Village

    def test_do_pop_num_megalopolis(self):
        """Test population calculation for megalopolis (largest class)."""
        types.ResPop = 50000  # Large residential population
        types.ComPop = 10000
        types.IndPop = 8000

        evaluation.DoPopNum()

        expected_pop = (50000 + 10000 * 8 + 8000 * 8) * 20
        self.assertEqual(evaluation.CityPop, expected_pop)
        self.assertGreater(evaluation.CityPop, 500000)  # Should be megalopolis
        self.assertEqual(evaluation.CityClass, 5)  # Megalopolis

    def test_do_problems(self):
        """Test problem analysis and voting."""
        # Set up problem values
        types.CrimeAverage = 50
        types.PolluteAverage = 40
        types.LVAverage = 100  # Housing = 70
        types.CityTax = 8       # Taxes = 80
        # Traffic will be calculated
        # Unemployment will be calculated
        types.FirePop = 10      # Fire = 50

        # Set up population for unemployment calculation (more residents than jobs)
        types.ResPop = 2000  # More residents
        types.ComPop = 100   # Fewer commercial jobs
        types.IndPop = 100   # Fewer industrial jobs

        # Mock traffic density data
        types.LandValueMem = [[100 if i < 10 else 0 for i in range(types.HWLDY)]
                             for _ in range(types.HWLDX)]
        types.TrfDensity = [[50 if i < 10 else 0 for i in range(types.HWLDY)]
                           for _ in range(types.HWLDX)]

        evaluation.DoPopNum()  # Initialize population
        evaluation.DoProblems()

        # Check that problems were calculated
        self.assertGreater(evaluation.ProblemTable[0], 0)  # Crime
        self.assertGreater(evaluation.ProblemTable[1], 0)  # Pollution
        self.assertGreater(evaluation.ProblemTable[2], 0)  # Housing
        self.assertGreater(evaluation.ProblemTable[3], 0)  # Taxes
        self.assertGreater(evaluation.ProblemTable[4], 0)  # Traffic
        self.assertGreater(evaluation.ProblemTable[5], 0)  # Unemployment
        self.assertGreater(evaluation.ProblemTable[6], 0)  # Fire

        # Check that top problems were identified
        self.assertTrue(any(x < 7 for x in evaluation.ProblemOrder))

    def test_get_score_perfect_city(self):
        """Test score calculation for a near-perfect city."""
        # Set up a good city scenario
        types.TotalPop = 1000
        types.ResPop = 500
        types.ComPop = 100
        types.IndPop = 100

        # Low problems
        types.CrimeAverage = 10
        types.PolluteAverage = 10
        types.LVAverage = 200
        types.CityTax = 5
        types.FirePop = 5

        # Good infrastructure
        types.RoadEffect = 100
        types.PoliceEffect = 1500
        types.FireEffect = 1500

        # Positive demand
        types.RValve = 1000
        types.CValve = 1000
        types.IValve = 1000

        # Good power ratio
        types.PwrdZCnt = 100
        types.unPwrdZCnt = 10

        # Initialize and calculate
        evaluation.DoPopNum()
        evaluation.DoProblems()
        evaluation.GetScore()

        # Score should be positive and reasonable
        self.assertGreater(evaluation.CityScore, 0)
        self.assertLessEqual(evaluation.CityScore, 1000)

    def test_get_score_poor_city(self):
        """Test score calculation for a poor city."""
        # Set up a bad city scenario
        types.TotalPop = 1000
        types.ResPop = 500
        types.ComPop = 100
        types.IndPop = 100

        # High problems
        types.CrimeAverage = 200
        types.PolluteAverage = 200
        types.LVAverage = 50
        types.CityTax = 15
        types.FirePop = 50

        # Poor infrastructure
        types.RoadEffect = 10
        types.PoliceEffect = 500
        types.FireEffect = 500

        # Negative demand
        types.RValve = -2000
        types.CValve = -2000
        types.IValve = -2000

        # Poor power ratio
        types.PwrdZCnt = 10
        types.unPwrdZCnt = 100

        # Initialize and calculate
        evaluation.DoPopNum()
        evaluation.DoProblems()
        evaluation.GetScore()

        # Score should be low
        self.assertLess(evaluation.CityScore, 300)
        self.assertGreaterEqual(evaluation.CityScore, 0)

    def test_do_votes_high_score(self):
        """Test voting with high city score."""
        evaluation.CityScore = 900

        evaluation.DoVotes()

        total_votes = evaluation.CityYes + evaluation.CityNo
        self.assertEqual(total_votes, 100)
        # Should have mostly yes votes
        self.assertGreater(evaluation.CityYes, 80)

    def test_do_votes_low_score(self):
        """Test voting with low city score."""
        evaluation.CityScore = 100

        evaluation.DoVotes()

        total_votes = evaluation.CityYes + evaluation.CityNo
        self.assertEqual(total_votes, 100)
        # Should have mostly no votes
        self.assertGreater(evaluation.CityNo, 80)

    def test_city_evaluation_no_population(self):
        """Test city evaluation with no population."""
        types.TotalPop = 0

        evaluation.CityEvaluation()

        self.assertEqual(evaluation.EvalValid, 1)
        self.assertEqual(evaluation.CityScore, 500)  # Default score

    @patch('src.micropolis.evaluation.GetAssValue')
    @patch('src.micropolis.evaluation.DoPopNum')
    @patch('src.micropolis.evaluation.DoProblems')
    @patch('src.micropolis.evaluation.GetScore')
    @patch('src.micropolis.evaluation.DoVotes')
    @patch('src.micropolis.evaluation.ChangeEval')
    def test_city_evaluation_with_population(self, mock_change_eval, mock_do_votes,
                                           mock_get_score, mock_do_problems,
                                           mock_do_pop_num, mock_get_ass_value):
        """Test full city evaluation flow with population."""
        types.TotalPop = 1000

        evaluation.CityEvaluation()

        # Verify all functions were called
        mock_get_ass_value.assert_called_once()
        mock_do_pop_num.assert_called_once()
        mock_do_problems.assert_called_once()
        mock_get_score.assert_called_once()
        mock_do_votes.assert_called_once()
        mock_change_eval.assert_called_once()
        self.assertEqual(evaluation.EvalValid, 1)

    def test_average_trf(self):
        """Test traffic average calculation."""
        # Set up land value and traffic density with proper dimensions
        types.LandValueMem = [[100 if i < 10 else 0 for i in range(types.HWLDY)]
                             for _ in range(types.HWLDX)]
        types.TrfDensity = [[50 if i < 10 else 0 for i in range(types.HWLDY)]
                           for _ in range(types.HWLDX)]

        result = evaluation.AverageTrf()

        # Should calculate average traffic density
        self.assertGreater(result, 0)
        self.assertEqual(evaluation.TrafficAverage, result)

    def test_get_unemployment(self):
        """Test unemployment calculation."""
        types.ResPop = 1000
        types.ComPop = 100
        types.IndPop = 100

        result = evaluation.GetUnemployment()

        # Should calculate unemployment rate
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, 255)

    def test_get_fire(self):
        """Test fire danger calculation."""
        types.FirePop = 10

        result = evaluation.GetFire()

        self.assertEqual(result, 50)  # 10 * 5

    def test_get_fire_clamped(self):
        """Test fire danger calculation with clamping."""
        types.FirePop = 100  # Would be 500, but clamped to 255

        result = evaluation.GetFire()

        self.assertEqual(result, 255)

