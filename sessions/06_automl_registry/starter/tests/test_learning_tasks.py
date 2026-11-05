"""Run these tests after implementing the three student functions."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
from lab06_worker.learning_tasks import comparison_options, log_validation_metrics
from highrev.lab06.learning_tasks import gate_reasons


class LearningTasks(unittest.TestCase):
    def test_options_and_invalid_budget(self):
        options = comparison_options(["lr", "dt"], 120)
        self.assertEqual(options, {"include": ["lr", "dt"], "sort": "AUC", "budget_time": 2,
                                   "n_select": 1, "errors": "raise"})
        with self.assertRaises(ValueError):
            comparison_options([], 120)
        with self.assertRaises(ValueError):
            comparison_options(["lr"], 0)

    def test_log_validation_metrics(self):
        metrics = {"validation_roc_auc": .75, "validation_f1": .4}
        with patch("mlflow.log_metrics") as log:
            log_validation_metrics(metrics)
            log.assert_called_once_with(metrics)

    def test_gate_thresholds_and_regression(self):
        policy = {"min_validation_roc_auc": .7, "max_auc_drop": .02,
                  "max_artifact_bytes": 1000, "max_predict_p95_ms": 20}
        candidate = {"metrics": {"validation_roc_auc": .75, "predict_p95_ms": 10}, "artifact_bytes": 500}
        self.assertEqual(gate_reasons(candidate, None, policy), [])
        self.assertTrue(gate_reasons(candidate, {"metrics": {"validation_roc_auc": .8}}, policy))
        self.assertTrue(gate_reasons({**candidate, "artifact_bytes": 1001}, None, policy))
        self.assertTrue(gate_reasons({**candidate, "metrics": {"validation_roc_auc": .69, "predict_p95_ms": 21}}, None, policy))


if __name__ == "__main__":
    unittest.main()
