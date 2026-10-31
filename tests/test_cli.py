import unittest
from unittest.mock import patch

from xingyu_video_tools.cli import analyze_workflow, environment_report, main


class WorkflowTests(unittest.TestCase):
    def test_ui_workflow(self):
        workflow = {"nodes": [{"type": "LoadImage", "widgets_values": ["demo.png"]}, {"type": "SaveVideo"}]}
        report = analyze_workflow(workflow)
        self.assertEqual(report["node_count"], 2)
        self.assertEqual(report["node_types"]["SaveVideo"], 1)
        self.assertEqual(report["privacy_warnings"], [])

    def test_api_workflow(self):
        workflow = {"1": {"class_type": "LoadImage", "inputs": {"image": "demo.png"}}}
        self.assertEqual(analyze_workflow(workflow)["node_count"], 1)

    def test_detects_local_user_path_without_exposing_value(self):
        workflow = {"nodes": [{"type": "LoadImage", "widgets_values": ["/Users/privateperson/image.png"]}]}
        report = analyze_workflow(workflow)
        self.assertEqual(report["privacy_warnings"], ["absolute user path"])
        self.assertNotIn("privateperson", str(report))

    def test_rejects_empty_json(self):
        with self.assertRaises(ValueError):
            analyze_workflow({})

    def test_detects_model_filenames(self):
        workflow = {"nodes": [{"type": "Loader", "widgets_values": ["foo.safetensors"]}]}
        self.assertEqual(analyze_workflow(workflow)["referenced_model_filenames"], ["foo.safetensors"])

    def test_environment_report(self):
        self.assertIn("architecture", environment_report())


if __name__ == "__main__":
    unittest.main()
