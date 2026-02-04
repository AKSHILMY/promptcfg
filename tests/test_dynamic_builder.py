import unittest
from promptcfg.builder import PromptBuilder as Builder
from promptcfg.config import PromptConfig, PromptPart

class TestDynamicBuilder(unittest.TestCase):
    def setUp(self):
        self.config = PromptConfig(version="1.0", prompts=[
            PromptPart(id="default_part", text="Default", default=True),
            PromptPart(id="python_part", text="Python", tags=["python"], default=False),
            PromptPart(id="go_part", text="Go", tags=["go"], default=False),
            PromptPart(id="core_part", text="Core", tags=["core"], default=True),
            PromptPart(id="mixed_part", text="Mixed", tags=["python", "extra"], default=False),
        ])
        self.builder = Builder(self.config)

    def test_default_inclusion(self):
        prompt = self.builder.build(tags=[], variables={})
        self.assertIn("Default", prompt)
        self.assertIn("Core", prompt)
        self.assertNotIn("Python", prompt)

    def test_exclude_id_overrides_default(self):
        prompt = self.builder.build(tags=[], variables={}, exclude_ids=["default_part"])
        self.assertNotIn("Default", prompt)
        self.assertIn("Core", prompt) 

    def test_include_id_overrides_default_false(self):
        prompt = self.builder.build(tags=[], variables={}, include_ids=["python_part"])
        self.assertIn("Python", prompt)
        self.assertIn("Default", prompt)

    def test_include_id_overrides_exclude_tag(self):
        
        
        prompt = self.builder.build(
            tags=[], 
            variables={}, 
            include_ids=["python_part"], 
            exclude_tags=["python"]
        )
        self.assertIn("Python", prompt)

    def test_exclude_id_overrides_include_id(self):
        prompt = self.builder.build(
            tags=[], 
            variables={}, 
            include_ids=["default_part"], 
            exclude_ids=["default_part"]
        )
        self.assertNotIn("Default", prompt)

    def test_exclude_tag_overrides_include_tag(self):
        
        
        prompt = self.builder.build(
            tags=["python"], 
            variables={}, 
            exclude_tags=["extra"]
        )
        self.assertNotIn("Mixed", prompt)
        self.assertIn("Python", prompt) 

    def test_exclude_tag_overrides_default(self):
        
        prompt = self.builder.build(
            tags=[], 
            variables={}, 
            exclude_tags=["core"]
        )
        self.assertNotIn("Core", prompt)
        self.assertIn("Default", prompt)

    def test_complex_combination(self):
        
        
        
        
        
        prompt = self.builder.build(
            tags=["go"],
            variables={},
            include_ids=["python_part"],
            exclude_ids=["default_part"],
            exclude_tags=["core"]
        )
        
        self.assertNotIn("Default", prompt)
        self.assertIn("Python", prompt)
        self.assertIn("Go", prompt)
        self.assertNotIn("Core", prompt)

if __name__ == '__main__':
    unittest.main()
