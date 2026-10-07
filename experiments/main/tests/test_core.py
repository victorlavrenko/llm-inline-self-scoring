import importlib.util
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("experiment", ROOT / "experiment.py")
exp = importlib.util.module_from_spec(spec)
sys.modules["experiment"] = exp
spec.loader.exec_module(exp)


class CoreTests(unittest.TestCase):
    def test_strip_scores(self):
        text = "Hello world. <AI SCORE: 22> Another sentence! <AI SCORE: (87)>"
        clean, scores, leak = exp.strip_score_material(text)
        self.assertEqual(scores, [22, 87])
        self.assertFalse(leak)
        self.assertEqual(clean, "Hello world. Another sentence!")

    def test_parse_verdict(self):
        self.assertEqual(exp.parse_verdict("A"), "A")
        self.assertEqual(exp.parse_verdict("TIE\n"), "TIE")
        self.assertEqual(exp.parse_verdict("Verdict: B"), "B")
        self.assertEqual(exp.parse_verdict("Answer A — it is more formulaic."), "A")
        with self.assertRaises(ValueError):
            exp.parse_verdict("T")
        with self.assertRaises(ValueError):
            exp.parse_verdict("Fun art")

    def test_mirrored_resolution(self):
        rows = [
            {"orientation": 0, "canonical_outcome": "baseline_more_slop"},
            {"orientation": 1, "canonical_outcome": "baseline_more_slop"},
        ]
        self.assertEqual(exp.resolve_mirrored(rows, True), "baseline_more_slop")
        rows[1]["canonical_outcome"] = "selfscore_more_slop"
        self.assertEqual(exp.resolve_mirrored(rows, True), "order_sensitive")


    def test_matched_generation_prompts(self):
        task = "Write something."
        b = exp.baseline_messages(task)
        s = exp.selfscore_messages(task)
        self.assertEqual(b[1], s[1])
        self.assertEqual(b[1]["content"], task)
        self.assertIn(exp.COMMON_ANTI_SLOP_INSTRUCTION, b[0]["content"])
        self.assertIn(exp.COMMON_ANTI_SLOP_INSTRUCTION, s[0]["content"])
        self.assertNotIn("AI SCORE", b[0]["content"])
        self.assertIn(exp.AI_SCORE_INSTRUCTION, s[0]["content"])

    def test_summary_direction(self):
        s = exp.summarize_outcomes([
            "baseline_more_slop", "baseline_more_slop", "selfscore_more_slop", "tie"
        ])
        self.assertEqual(s["selfscore_cleaner"], 2)
        self.assertEqual(s["baseline_cleaner"], 1)
        self.assertEqual(s["tie"], 1)
        self.assertAlmostEqual(s["selfscore_cleaner_decisive_rate"], 2/3)

    def test_parse_verbose_final_bold_verdict(self):
        text = "Both answers are close. The difference is marginal.\n\n**B**"
        self.assertEqual(exp.parse_verdict(text), "B")

    def test_runtime_provider_repair(self):
        ds = exp.ModelSpec(alias="deepseek-v4.1-flash", route="deepseek/deepseek-v4.1-flash", provider="deepseek")
        self.assertEqual(exp.effective_provider(ds), "together")
        gpt = exp.ModelSpec(alias="gpt-5.6-sol", route="openai/gpt-5.6-sol", provider="openai")
        self.assertEqual(exp.effective_provider(gpt), "openai")


if __name__ == "__main__":
    unittest.main()
