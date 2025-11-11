#!/usr/bin/env python3
"""
test_evaluation.py - Unit tests for the city evaluation system

Tests the evaluation module functions including scoring, problem analysis,
population classification, and voting simulation.
"""

from unittest.mock import patch

import micropolis.constants
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
        types.total_pop = 0
        types.res_pop = 0
        types.com_pop = 0
        types.ind_pop = 0
        types.road_total = 0
        types.rail_total = 0
        types.police_pop = 0
        types.fire_st_pop = 0
        types.hosp_pop = 0
        types.stadium_pop = 0
        types.port_pop = 0
        types.airport_pop = 0
        types.coal_pop = 0
        types.nuclear_pop = 0
        types.crime_average = 0
        types.pollute_average = 0
        types.lv_average = 0
        types.city_tax = 0
        types.res_cap = False
        types.com_cap = False
        types.ind_cap = False
        types.road_effect = 0
        types.police_effect = 0
        types.fire_effect = 0
        types.r_value = 0
        types.c_value = 0
        types.i_value = 0
        types.un_pwrd_z_cnt = 0
        types.pwrd_z_cnt = 0

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
        types.road_total = 100
        types.rail_total = 50
        types.police_pop = 10
        types.fire_st_pop = 8
        types.hosp_pop = 5
        types.stadium_pop = 2
        types.port_pop = 1
        types.airport_pop = 1
        types.coal_pop = 3
        types.nuclear_pop = 2

        evaluation.GetAssValue()

        # Calculate expected value
        expected = (
            100 * 5
            + 50 * 10
            + 10 * 1000
            + 8 * 1000
            + 5 * 400
            + 2 * 3000
            + 1 * 5000
            + 1 * 10000
            + 3 * 3000
            + 2 * 6000
        ) * 1000
        self.assertEqual(evaluation.CityAssValue, expected)

    def test_do_pop_num_village(self):
        """Test population calculation for village (smallest class)."""
        types.res_pop = 10
        types.com_pop = 5
        types.ind_pop = 3

        evaluation.DoPopNum()

        expected_pop = (10 + 5 * 8 + 3 * 8) * 20
        self.assertEqual(evaluation.CityPop, expected_pop)
        self.assertEqual(evaluation.CityClass, 0)  # Village

    def test_do_pop_num_megalopolis(self):
        """Test population calculation for megalopolis (largest class)."""
        types.res_pop = 50000  # Large residential population
        types.com_pop = 10000
        types.ind_pop = 8000

        evaluation.DoPopNum()

        expected_pop = (50000 + 10000 * 8 + 8000 * 8) * 20
        self.assertEqual(evaluation.CityPop, expected_pop)
        self.assertGreater(evaluation.CityPop, 500000)  # Should be megalopolis
        self.assertEqual(evaluation.CityClass, 5)  # Megalopolis

    def test_do_problems(self):
        """Test problem analysis and voting."""
        # Set up problem values
        types.crime_average = 50
        types.pollute_average = 40
        types.lv_average = 100  # Housing = 70
        types.city_tax = 8  # Taxes = 80
        # Traffic will be calculated
        # Unemployment will be calculated
        types.fire_pop = 10  # Fire = 50

        # Set up population for unemployment calculation (more residents than jobs)
        types.res_pop = 2000  # More residents
        types.com_pop = 100  # Fewer commercial jobs
        types.ind_pop = 100  # Fewer industrial jobs

        # Mock traffic density data
        types.land_value_mem = [
            [100 if i < 10 else 0 for i in range(micropolis.constants.HWLDY)]
            for _ in range(micropolis.constants.HWLDX)
        ]
        types.trf_density = [
            [50 if i < 10 else 0 for i in range(micropolis.constants.HWLDY)]
            for _ in range(micropolis.constants.HWLDX)
        ]

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
        types.total_pop = 1000
        types.res_pop = 500
        types.com_pop = 100
        types.ind_pop = 100

        # Low problems
        types.crime_average = 10
        types.pollute_average = 10
        types.lv_average = 200
        types.city_tax = 5
        types.fire_pop = 5

        # Good infrastructure
        types.road_effect = 100
        types.police_effect = 1500
        types.fire_effect = 1500

        # Positive demand
        types.r_value = 1000
        types.c_value = 1000
        types.i_value = 1000

        # Good power ratio
        types.pwrd_z_cnt = 100
        types.un_pwrd_z_cnt = 10

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
        types.total_pop = 1000
        types.res_pop = 500
        types.com_pop = 100
        types.ind_pop = 100

        # High problems
        types.crime_average = 200
        types.pollute_average = 200
        types.lv_average = 50
        types.city_tax = 15
        types.fire_pop = 50

        # Poor infrastructure
        types.road_effect = 10
        types.police_effect = 500
        types.fire_effect = 500

        # Negative demand
        types.r_value = -2000
        types.c_value = -2000
        types.i_value = -2000

        # Poor power ratio
        types.pwrd_z_cnt = 10
        types.un_pwrd_z_cnt = 100

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
        types.total_pop = 0

        evaluation.CityEvaluation()

        self.assertEqual(evaluation.EvalValid, 1)
        self.assertEqual(evaluation.CityScore, 500)  # Default score

    @patch("src.micropolis.evaluation.GetAssValue")
    @patch("src.micropolis.evaluation.DoPopNum")
    @patch("src.micropolis.evaluation.DoProblems")
    @patch("src.micropolis.evaluation.GetScore")
    @patch("src.micropolis.evaluation.DoVotes")
    @patch("src.micropolis.evaluation.ChangeEval")
    def test_city_evaluation_with_population(
        self,
        mock_change_eval,
        mock_do_votes,
        mock_get_score,
        mock_do_problems,
        mock_do_pop_num,
        mock_get_ass_value,
    ):
        """Test full city evaluation flow with population."""
        types.total_pop = 1000

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
        types.land_value_mem = [
            [100 if i < 10 else 0 for i in range(micropolis.constants.HWLDY)]
            for _ in range(micropolis.constants.HWLDX)
        ]
        types.trf_density = [
            [50 if i < 10 else 0 for i in range(micropolis.constants.HWLDY)]
            for _ in range(micropolis.constants.HWLDX)
        ]

        result = evaluation.AverageTrf()

        # Should calculate average traffic density
        self.assertGreater(result, 0)
        self.assertEqual(evaluation.TrafficAverage, result)

    def test_get_unemployment(self):
        """Test unemployment calculation."""
        types.res_pop = 1000
        types.com_pop = 100
        types.ind_pop = 100

        result = evaluation.GetUnemployment()

        # Should calculate unemployment rate
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, 255)

    def test_get_fire(self):
        """Test fire danger calculation."""
        types.fire_pop = 10

        result = evaluation.GetFire()

        self.assertEqual(result, 50)  # 10 * 5

    def test_get_fire_clamped(self):
        """Test fire danger calculation with clamping."""
        types.fire_pop = 100  # Would be 500, but clamped to 255

        result = evaluation.GetFire()

        self.assertEqual(result, 255)
