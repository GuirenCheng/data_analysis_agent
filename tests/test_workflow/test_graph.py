"""LangGraph 工作流测试。"""

import pytest

from daa.workflow.edges import route_by_action, should_continue_analysis, should_retry
from daa.workflow.state import AnalysisState


class TestRouteByAction:
    def test_generate_code_routes_to_execute(self):
        state: AnalysisState = {"action": "generate_code", "user_query": "test"}
        assert route_by_action(state) == "execute_code"

    def test_collect_figures_routes_to_collect(self):
        state: AnalysisState = {"action": "collect_figures", "user_query": "test"}
        assert route_by_action(state) == "collect_figures"

    def test_analysis_complete_routes_to_report(self):
        state: AnalysisState = {"action": "analysis_complete", "user_query": "test"}
        assert route_by_action(state) == "generate_report"

    def test_unknown_routes_to_error(self):
        state: AnalysisState = {"action": "unknown", "user_query": "test"}
        assert route_by_action(state) == "error_handler"


class TestShouldContinue:
    def test_analysis_complete_stops(self):
        state: AnalysisState = {
            "action": "analysis_complete",
            "current_round": 5,
            "max_rounds": 20,
            "user_query": "test",
        }
        assert should_continue_analysis(state) == "stop"

    def test_max_rounds_stops(self):
        state: AnalysisState = {
            "action": "generate_code",
            "current_round": 20,
            "max_rounds": 20,
            "user_query": "test",
            "error_count": 0,
        }
        assert should_continue_analysis(state) == "stop"

    def test_too_many_errors_stops(self):
        state: AnalysisState = {
            "action": "generate_code",
            "current_round": 5,
            "max_rounds": 20,
            "user_query": "test",
            "error_count": 3,
        }
        assert should_continue_analysis(state) == "stop"

    def test_normal_continues(self):
        state: AnalysisState = {
            "action": "generate_code",
            "current_round": 5,
            "max_rounds": 20,
            "user_query": "test",
            "error_count": 0,
        }
        assert should_continue_analysis(state) == "continue"


class TestShouldRetry:
    def test_few_errors_retries(self):
        state: AnalysisState = {
            "error_count": 1,
            "user_query": "test",
        }
        assert should_retry(state) == "retry"

    def test_many_errors_aborts(self):
        state: AnalysisState = {
            "error_count": 3,
            "user_query": "test",
        }
        assert should_retry(state) == "abort"
