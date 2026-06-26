"""
Explainability Agent — generates human-readable explanations for model decisions.

Uses:
  - SHAP values for feature importance
  - LIME for local approximation
  - Textual narrative generation from signal weights
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from agents.base_agent import BaseAgent, AgentError


class ExplainabilityAgent(BaseAgent):
    """Explains model predictions and signal contributions in plain language."""

    agent_name = "ExplainabilityAgent"

    _METHODS = ("shap", "lime", "weights")

    def __init__(self, method: str = "weights", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if method not in self._METHODS:
            raise ValueError(f"method must be one of {self._METHODS}")
        self.method = method

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    def _execute(
        self,
        model: Any,
        X: pd.DataFrame,
        feature_names: list[str] | None = None,
        prediction_index: int = -1,
    ) -> dict[str, Any]:
        """Explain a model's prediction for the given input data.

        Args:
            model:            Fitted sklearn-compatible model.
            X:                Feature matrix (DataFrame).
            feature_names:    Optional list of feature names.
            prediction_index: Row index to explain (-1 → last row).

        Returns:
            Dict with feature importances, explanation text, and method used.
        """
        if X.empty:
            raise AgentError("Feature matrix X is empty.")

        names = feature_names or (list(X.columns) if hasattr(X, "columns") else [f"f{i}" for i in range(X.shape[1])])
        x_explain = X.iloc[[prediction_index]]

        self.logger.info(
            "Generating %s explanation for row %d.", self.method, prediction_index
        )

        if self.method == "shap":
            importances = self._shap_explanation(model, X, x_explain, names)
        elif self.method == "lime":
            importances = self._lime_explanation(model, X, x_explain, names)
        else:
            importances = self._weights_explanation(model, names)

        narrative = self._build_narrative(importances)

        return {
            "method": self.method,
            "feature_importances": importances,
            "narrative": narrative,
            "top_features": sorted(importances.items(), key=lambda x: abs(x[1]), reverse=True)[:5],
        }

    # ------------------------------------------------------------------
    # Explanation back-ends
    # ------------------------------------------------------------------

    def _shap_explanation(
        self, model: Any, X: pd.DataFrame, x_explain: pd.DataFrame, names: list[str]
    ) -> dict[str, float]:
        try:
            import shap  # type: ignore
        except ImportError as exc:
            raise AgentError("shap not installed. Run: pip install shap") from exc

        try:
            explainer = shap.TreeExplainer(model)
        except Exception:
            explainer = shap.KernelExplainer(model.predict, shap.sample(X, 50))

        shap_values = explainer.shap_values(x_explain)
        if isinstance(shap_values, list):
            shap_values = shap_values[0]

        values = shap_values[0] if len(np.array(shap_values).shape) > 1 else shap_values
        return dict(zip(names, [float(v) for v in values]))

    def _lime_explanation(
        self, model: Any, X: pd.DataFrame, x_explain: pd.DataFrame, names: list[str]
    ) -> dict[str, float]:
        try:
            import lime.lime_tabular  # type: ignore
        except ImportError as exc:
            raise AgentError("lime not installed. Run: pip install lime") from exc

        explainer = lime.lime_tabular.LimeTabularExplainer(
            X.values, feature_names=names, mode="regression"
        )
        exp = explainer.explain_instance(x_explain.values[0], model.predict, num_features=len(names))
        return {feat: float(weight) for feat, weight in exp.as_list()}

    @staticmethod
    def _weights_explanation(model: Any, names: list[str]) -> dict[str, float]:
        """Extract feature weights from linear / tree models."""
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
        elif hasattr(model, "coef_"):
            importances = model.coef_.flatten()
        else:
            raise AgentError("Model does not expose feature_importances_ or coef_.")

        return dict(zip(names, [float(v) for v in importances]))

    # ------------------------------------------------------------------
    # Narrative
    # ------------------------------------------------------------------

    @staticmethod
    def _build_narrative(importances: dict[str, float]) -> str:
        sorted_feats = sorted(importances.items(), key=lambda x: abs(x[1]), reverse=True)
        top_pos = [(k, v) for k, v in sorted_feats if v > 0][:3]
        top_neg = [(k, v) for k, v in sorted_feats if v < 0][:3]

        parts = []
        if top_pos:
            pos_str = ", ".join(f"{k} (+{v:.3f})" for k, v in top_pos)
            parts.append(f"Key positive contributors: {pos_str}.")
        if top_neg:
            neg_str = ", ".join(f"{k} ({v:.3f})" for k, v in top_neg)
            parts.append(f"Key negative contributors: {neg_str}.")
        if not parts:
            parts.append("No significant feature contributions identified.")

        return " ".join(parts)
