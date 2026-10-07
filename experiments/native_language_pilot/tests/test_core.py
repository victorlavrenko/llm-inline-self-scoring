import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(name, fn):
    import sys
    s = importlib.util.spec_from_file_location(name, ROOT / fn)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m

class CoreTests(unittest.TestCase):
    def test_strip_scores(self):
        g = load("gen", "generate_ru.py")
        clean, scores = g.strip_scores("Привет. <AI SCORE: 12> Мир! <AI SCORE: 77>")
        self.assertEqual(scores, [12, 77])
        self.assertNotIn("AI SCORE", clean)

    def test_parse_verdict(self):
        j = load("judge", "judge_ru.py")
        self.assertEqual(j.parse_verdict("A"), "A")
        self.assertEqual(j.parse_verdict("**B**"), "B")
        self.assertEqual(j.parse_verdict("Объяснение\n\n**TIE**"), "TIE")

    def test_prompts_balanced(self):
        import json, collections
        rows = [json.loads(x) for x in (ROOT / "prompts_ru.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
        self.assertEqual(len(rows), 24)
        c = collections.Counter(r["generator"] for r in rows)
        self.assertEqual(set(c.values()), {6})

if __name__ == "__main__":
    unittest.main()
