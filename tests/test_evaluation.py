#!/usr/bin/env python3
"""
test_evaluation.py - Unit tests for the city evaluation system

Tests the evaluation module functions including scoring, problem analysis,
population classification, and voting simulation.
"""

from unittest.mock import patch

import micropolis.constants
from src.micropolis import evaluation


from tests.assertions import Assertions


class TestEvaluation(Assertions):
    """Test cases for the evaluation system."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Reset evaluation state
        evaluation.eval_valid = 0
        evaluation.city_yes = 0
        evaluation.city_no = 0
        evaluation.problem_table = [0] * micropolis.constants.PROBNUM
        evaluation.problem_taken = [0] * micropolis.constants.PROBNUM
        evaluation.problem_votes = [0] * micropolis.constants.PROBNUM
        evaluation.problem_order = [0] * 4
        evaluation.city_pop = 0
        evaluation.delta_city_pop = 0
        evaluation.city_ass_value = 0
        evaluation.city_class = 0
        evaluation.city_score = 0
        evaluation.delta_city_score = 0
        evaluation.average_city_score = 0
        evaluation.traffic_average = 0

        # Reset global simulation state used by evaluation (AppContext-backed)
        context.total_pop = 0
        context.res_pop = 0
        context.com_pop = 0
        context.ind_pop = 0
        context.road_total = 0
        context.rail_total = 0
        context.police_pop = 0
        context.fire_st_pop = 0
        context.hosp_pop = 0
        context.stadium_pop = 0
        context.port_pop = 0
        context.airport_pop = 0
        context.coal_pop = 0
        context.nuclear_pop = 0
        context.crime_average = 0
        context.pollute_average = 0
        context.lv_average = 0
        context.city_tax = 0
        context.res_cap = False
        context.com_cap = False
        context.ind_cap = False
        context.road_effect = 0
        context.police_effect = 0
        context.fire_effect = 0
        context.r_value = 0
        context.c_value = 0
        context.i_value = 0
        context.un_pwrd_z_cnt = 0
        context.pwrd_z_cnt = 0

    def test_eval_init(self):
        """Test evaluation initialization."""
        # Set some non-zero values first
        evaluation.city_score = 600
        evaluation.city_yes = 50
        evaluation.problem_votes[0] = 10

        evaluation.eval_init(context)

        self.assertEqual(context.city_yes, 0)
        self.assertEqual(context.city_no, 0)
        self.assertEqual(context.city_pop, 0)
        self.assertEqual(context.city_score, 500)  # Should be set to 500
        self.assertEqual(context.eval_valid, 1)
        self.assertEqual(sum(context.problem_votes), 0)
        self.assertEqual(sum(context.problem_order), 0)

    def test_get_ass_value(self):
        """Test assessed value calculation."""
        # Set up infrastructure values
        context.road_total = 100
        context.rail_total = 50
        context.police_pop = 10
        context.fire_st_pop = 8
        context.hosp_pop = 5
        context.stadium_pop = 2
        context.port_pop = 1
        context.airport_pop = 1
        context.coal_pop = 3
        context.nuclear_pop = 2

        evaluation.get_ass_value(context)

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
        self.assertEqual(context.city_ass_value, expected)

    def test_do_pop_num_village(self):
        """Test population calculation for village (smallest class)."""
        context.res_pop = 10
        context.com_pop = 5
        context.ind_pop = 3

        evaluation.do_pop_num(context)

        expected_pop = (10 + 5 * 8 + 3 * 8) * 20
        self.assertEqual(context.city_pop, expected_pop)
        self.assertEqual(context.city_class, 0)  # Village

    def test_do_pop_num_megalopolis(self):
        """Test population calculation for megalopolis (largest class)."""
        context.res_pop = 50000  # Large residential population
        context.com_pop = 10000
        context.ind_pop = 8000

        evaluation.do_pop_num(context)

        expected_pop = (50000 + 10000 * 8 + 8000 * 8) * 20
        self.assertEqual(context.city_pop, expected_pop)
        self.assertGreater(context.city_pop, 500000)  # Should be megalopolis
        self.assertEqual(context.city_class, 5)  # Megalopolis

    def test_do_problems(self):
        """Test problem analysis and voting."""
        # Set up problem values
        context.crime_average = 50
        context.pollute_average = 40
        context.lv_average = 100  # Housing = 70
        context.city_tax = 8  # Taxes = 80
        # Traffic will be calculated
        # Unemployment will be calculated
        context.fire_pop = 10  # Fire = 50

        # Set up population for unemployment calculation (more residents than jobs)
        context.res_pop = 2000  # More residents
        context.com_pop = 100  # Fewer commercial jobs
        context.ind_pop = 100  # Fewer industrial jobs

        # Mock traffic density data
        context.land_value_mem = [
            [100 if i < 10 else 0 for i in range(micropolis.constants.HWLDY)]
            for _ in range(micropolis.constants.HWLDX)
        ]
        context.trf_density = [
            [50 if i < 10 else 0 for i in range(micropolis.constants.HWLDY)]
            for _ in range(micropolis.constants.HWLDX)
        ]

        evaluation.do_pop_num(context)  # Initialize population
        evaluation.do_problems(context)

        # Check that problems were calculated
        self.assertGreater(context.problem_table[0], 0)  # Crime
        self.assertGreater(context.problem_table[1], 0)  # Pollution
        self.assertGreater(context.problem_table[2], 0)  # Housing
        self.assertGreater(context.problem_table[3], 0)  # Taxes
        self.assertGreater(context.problem_table[4], 0)  # Traffic
        self.assertGreater(context.problem_table[5], 0)  # Unemployment
        self.assertGreater(context.problem_table[6], 0)  # Fire

        # Check that top problems were identified
        self.assertTrue(any(x < 7 for x in context.problem_order))

    def test_get_score_perfect_city(self):
        """Test score calculation for a near-perfect city."""
        # Set up a good city scenario
        context.total_pop = 1000
        context.res_pop = 500
        context.com_pop = 100
        context.ind_pop = 100

        # Low problems
        context.crime_average = 10
        context.pollute_average = 10
        context.lv_average = 200
        context.city_tax = 5
        context.fire_pop = 5

        # Good infrastructure
        context.road_effect = 100
        context.police_effect = 1500
        context.fire_effect = 1500

        # Positive demand
        context.r_value = 1000
        context.c_value = 1000
        context.i_value = 1000

        # Good power ratio
        context.pwrd_z_cnt = 100
        context.un_pwrd_z_cnt = 10

        # Initialize and calculate
        evaluation.do_pop_num(context)
        evaluation.do_problems(context)
        evaluation.get_score(context)

        # Score should be positive and reasonable
        self.assertGreater(context.city_score, 0)
        self.assertLessEqual(context.city_score, 1000)

    def test_get_score_poor_city(self):
        """Test score calculation for a poor city."""
        # Set up a bad city scenario
        context.total_pop = 1000
        context.res_pop = 500
        context.com_pop = 100
        context.ind_pop = 100

        # High problems
        context.crime_average = 200
        context.pollute_average = 200
        context.lv_average = 50
        context.city_tax = 15
        context.fire_pop = 50

        # Poor infrastructure
        context.road_effect = 10
        context.police_effect = 500
        context.fire_effect = 500

        # Negative demand
        context.r_value = -2000
        context.c_value = -2000
        context.i_value = -2000

        # Poor power ratio
        context.pwrd_z_cnt = 10
        context.un_pwrd_z_cnt = 100

        # Initialize and calculate
        evaluation.do_pop_num(context)
        evaluation.do_problems(context)
        evaluation.get_score(context)

        # Score should be low
        self.assertLess(context.city_score, 300)
        self.assertGreaterEqual(context.city_score, 0)

    def test_do_votes_high_score(self):
        """Test voting with high city score."""
        context.city_score = 900

        evaluation.do_votes(context)

        total_votes = context.city_yes + context.city_no
        self.assertEqual(total_votes, 100)
        # Should have mostly yes votes
        self.assertGreater(context.city_yes, 80)

    def test_do_votes_low_score(self):
        """Test voting with low city score."""
        context.city_score = 100

        evaluation.do_votes(context)

        total_votes = context.city_yes + context.city_no
        self.assertEqual(total_votes, 100)
        # Should have mostly no votes
        self.assertGreater(context.city_no, 80)

    def test_city_evaluation_no_population(self):
        """Test city evaluation with no population."""
        context.total_pop = 0

        evaluation.city_evaluation(context)

        self.assertEqual(context.eval_valid, 1)
        self.assertEqual(context.city_score, 500)  # Default score

    @patch("src.micropolis.evaluation.get_ass_value")
    @patch("src.micropolis.evaluation.do_pop_num")
    @patch("src.micropolis.evaluation.do_problems")
    @patch("src.micropolis.evaluation.get_score")
    @patch("src.micropolis.evaluation.do_votes")
    @patch("src.micropolis.evaluation.change_eval")
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
        context.total_pop = 1000

        evaluation.city_evaluation(context)

        # Verify all functions were called
        mock_get_ass_value.assert_called_once()
        mock_do_pop_num.assert_called_once()
        mock_do_problems.assert_called_once()
        mock_get_score.assert_called_once()
        mock_do_votes.assert_called_once()
        mock_change_eval.assert_called_once()
        self.assertEqual(context.eval_valid, 1)

    def test_average_trf(self):
        """Test traffic average calculation."""
        # Set up land value and traffic density with proper dimensions
        context.land_value_mem = [
            [100 if i < 10 else 0 for i in range(micropolis.constants.HWLDY)]
            for _ in range(micropolis.constants.HWLDX)
        ]
        context.trf_density = [
            [50 if i < 10 else 0 for i in range(micropolis.constants.HWLDY)]
            for _ in range(micropolis.constants.HWLDX)
        ]

        result = evaluation.average_trf(context)

        # Should calculate average traffic density
        self.assertGreater(result, 0)
        self.assertEqual(context.traffic_average, result)

    def test_get_unemployment(self):
        """Test unemployment calculation."""
        context.res_pop = 1000
        context.com_pop = 100
        context.ind_pop = 100

        result = evaluation.get_unemployment(context)

        # Should calculate unemployment rate
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, 255)

    def test_get_fire(self):
        """Test fire danger calculation."""
        context.fire_pop = 10

        result = evaluation.get_fire(context)

        self.assertEqual(result, 50)  # 10 * 5

    def test_get_fire_clamped(self):
        """Test fire danger calculation with clamping."""
        context.fire_pop = 100  # Would be 500, but clamped to 255

        result = evaluation.get_fire(context)

        self.assertEqual(result, 255)
