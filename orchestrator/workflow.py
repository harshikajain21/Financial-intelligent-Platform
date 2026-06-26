"""
Workflow — defines reusable named analysis workflows.

A Workflow is a lightweight DAG of agent execution steps.
Workflows can be composed, serialised, and replayed.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from utils.logger import get_logger

logger = get_logger("Workflow")


@dataclass
class WorkflowStep:
    """A single step in a workflow DAG."""

    name: str
    fn: Callable[..., Any]
    depends_on: list[str] = field(default_factory=list)
    kwargs: dict[str, Any] = field(default_factory=dict)


class Workflow:
    """Lightweight workflow engine for composing agent pipelines.

    Usage::

        wf = Workflow("quick_scan")
        wf.add_step("market", market_agent.run, kwargs={"tickers": ["AAPL"]})
        wf.add_step("technical", tech_agent.run, depends_on=["market"])
        results = wf.execute()
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._steps: dict[str, WorkflowStep] = {}
        self._results: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Building the DAG
    # ------------------------------------------------------------------

    def add_step(
        self,
        name: str,
        fn: Callable[..., Any],
        depends_on: list[str] | None = None,
        **kwargs: Any,
    ) -> "Workflow":
        """Register a workflow step.

        Args:
            name:       Unique step identifier.
            fn:         Callable to execute.
            depends_on: List of step names this step depends on.
            **kwargs:   Static keyword arguments forwarded to fn.
        """
        self._steps[name] = WorkflowStep(
            name=name,
            fn=fn,
            depends_on=depends_on or [],
            kwargs=kwargs,
        )
        return self  # fluent interface

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(self) -> dict[str, Any]:
        """Execute steps in topological order.

        Returns:
            Dict mapping step name → result.
        """
        logger.info("Executing workflow '%s' with %d steps.", self.name, len(self._steps))
        execution_order = self._topological_sort()

        start = time.perf_counter()
        for step_name in execution_order:
            step = self._steps[step_name]
            dep_results = {dep: self._results[dep] for dep in step.depends_on}
            combined_kwargs = {**step.kwargs, **dep_results}

            logger.info("  Running step: %s", step_name)
            step_start = time.perf_counter()
            try:
                self._results[step_name] = step.fn(**combined_kwargs)
            except Exception as exc:  # noqa: BLE001
                logger.error("Step '%s' failed: %s", step_name, exc)
                self._results[step_name] = {"error": str(exc)}
            logger.info(
                "  Step '%s' done in %.3fs.", step_name, time.perf_counter() - step_start
            )

        logger.info(
            "Workflow '%s' complete in %.3fs.", self.name, time.perf_counter() - start
        )
        return dict(self._results)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _topological_sort(self) -> list[str]:
        """Kahn's algorithm for topological sort."""
        in_degree: dict[str, int] = {name: 0 for name in self._steps}
        graph: dict[str, list[str]] = {name: [] for name in self._steps}

        for name, step in self._steps.items():
            for dep in step.depends_on:
                if dep not in self._steps:
                    raise ValueError(f"Step '{name}' depends on unknown step '{dep}'.")
                graph[dep].append(name)
                in_degree[name] += 1

        queue = [n for n, deg in in_degree.items() if deg == 0]
        order: list[str] = []

        while queue:
            node = queue.pop(0)
            order.append(node)
            for neighbour in graph[node]:
                in_degree[neighbour] -= 1
                if in_degree[neighbour] == 0:
                    queue.append(neighbour)

        if len(order) != len(self._steps):
            raise RuntimeError("Cycle detected in workflow DAG.")

        return order

    def __repr__(self) -> str:
        return f"<Workflow name={self.name!r} steps={list(self._steps)}>"
