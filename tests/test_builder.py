import unittest
from prompter.builder import PromptBuilder as Builder
from prompter.config import PromptConfig, PromptPart

class TestBuilder(unittest.TestCase):
    def setUp(self):
        self.config = PromptConfig(version="1.0", prompts=[
            PromptPart(id="intro", text="Hello {{ name }}", default=True),
            PromptPart(id="python", text="Use Python.", tags=["python"]),
            PromptPart(id="go", text="Use Go.", tags=["go"]),
        ])
        self.builder = Builder(self.config)

    def test_default_only(self):
        prompt = self.builder.build(tags=[], variables={"name": "User"})
        self.assertIn("Hello User", prompt)
        self.assertNotIn("Use Python", prompt)

    def test_with_tags(self):
        prompt = self.builder.build(tags=["python"], variables={"name": "Dev"})
        self.assertIn("Hello Dev", prompt)
        self.assertIn("Use Python", prompt)
        self.assertNotIn("Use Go", prompt)

    def test_missing_variable(self):
        prompt = self.builder.build(tags=[], variables={})
        self.assertIn("Hello ", prompt)

    def test_default_variable_value(self):
        self.config.prompts.append(
            PromptPart(id="default_test", text="Value: {{ val }}", variables=[{"name": "val", "required": False, "default": "DefaultValue"}], tags=["def"])
        )
        prompt = self.builder.build(tags=["def"], variables={})
        self.assertIn("Value: DefaultValue", prompt)

    def test_missing_required_variable_no_default(self):
        self.config.prompts.append(
            PromptPart(id="required_test", text="{{ necessary }}", variables=[{"name": "necessary", "required": True}], tags=["req"])
        )
        with self.assertRaises(ValueError) as cm:
            self.builder.build(tags=["req"], variables={})
        self.assertIn("Missing required variable 'necessary'", str(cm.exception))

if __name__ == '__main__':
    unittest.main()
