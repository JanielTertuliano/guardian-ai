import json
from pathlib import Path
import unittest


BASE_DIR = Path(__file__).resolve().parent.parent
CASES_PATH = BASE_DIR / "tests" / "evaluation_cases.json"
PROMPTS_DIR = BASE_DIR / "prompts"


class EvaluationContractTest(unittest.TestCase):
    def test_evaluation_cases_have_required_fields(self):
        cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))

        self.assertTrue(cases, "A lista de casos de avaliacao nao pode estar vazia.")

        required_fields = {
            "id",
            "query",
            "expected_risk",
            "required_terms",
            "expected_tools",
            "success_criteria",
        }

        for case in cases:
            missing = required_fields - set(case)
            self.assertFalse(
                missing,
                f"Caso {case.get('id')} sem campos: {sorted(missing)}",
            )
            self.assertTrue(
                case["required_terms"],
                f"Caso {case['id']} sem termos obrigatorios.",
            )
            self.assertTrue(
                case["expected_tools"],
                f"Caso {case['id']} sem ferramentas esperadas.",
            )

    def test_prompts_are_versioned(self):
        expected_files = [
            "agent_system_v1.md",
            "rag_baseline_system_v1.md",
            "tool_guidance_v1.md",
        ]

        for filename in expected_files:
            path = PROMPTS_DIR / filename
            self.assertTrue(path.exists(), f"Prompt versionado ausente: {filename}")
            content = path.read_text(encoding="utf-8").strip()
            self.assertGreater(
                len(content),
                200,
                f"Prompt {filename} parece incompleto.",
            )

    def test_ethics_and_technical_report_exist(self):
        docs_dir = BASE_DIR / "docs"
        expected_files = [
            "RELATORIO_TECNICO.md",
            "AUDITORIA_ETICA.md",
        ]

        for filename in expected_files:
            path = docs_dir / filename
            self.assertTrue(path.exists(), f"Documento obrigatorio ausente: {filename}")
            content = path.read_text(encoding="utf-8")
            self.assertIn("Guardian AI", content)
            self.assertGreater(len(content), 1000)


if __name__ == "__main__":
    unittest.main()
