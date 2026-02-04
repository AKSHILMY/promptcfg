import unittest
import os
import yaml
from promptcfg.config import PromptConfig

class TestCustomConfig(unittest.TestCase):
    def test_custom_ids_allowed(self):
        
        
        config_data = {
            "version": "1.0",
            "prompts": [
                {
                    "id": "my_super_custom_id",
                    "text": "Hello Custom World",
                    "default": True
                },
                {
                    "id": "another_random_id",
                    "text": "More Text",
                    "tags": ["custom"]
                }
            ]
        }
        
        
        filename = "temp_custom_config.yaml"
        with open(filename, "w") as f:
            yaml.dump(config_data, f)
            
        try:
            
            config = PromptConfig.load(filename)
            
            
            self.assertEqual(len(config.prompts), 2)
            self.assertEqual(config.prompts[0].id, "my_super_custom_id")
            self.assertEqual(config.prompts[1].id, "another_random_id")
            
        finally:
            
            if os.path.exists(filename):
                os.remove(filename)

    def test_duplicate_ids_rejected(self):
        config_data = {
            "version": "1.0",
            "prompts": [
                {"id": "duplicate_id", "text": "First"},
                {"id": "duplicate_id", "text": "Second"}
            ]
        }
        
        filename = "temp_duplicate_config.yaml"
        with open(filename, "w") as f:
            yaml.dump(config_data, f)
            
        try:
            with self.assertRaises(ValueError) as cm:
                PromptConfig.load(filename)
            self.assertIn("Duplicate prompt ID", str(cm.exception))
        finally:
            if os.path.exists(filename):
                os.remove(filename)

if __name__ == '__main__':
    unittest.main()
