import unittest
import yaml
import tempfile
import os
from prompter.config import PromptConfig
class TestConfigValidation(unittest.TestCase):
    def test_valid_ids(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
            yaml.dump({
                "version": "1.0",
                "prompts": [
                    {"id": "core_identity", "text": "foo"},
                    {"id": "user_context", "text": "bar"}
                ]
            }, tmp)
            tmp_path = tmp.name
        
        try:
            config = PromptConfig.load(tmp_path)
            self.assertEqual(len(config.prompts), 2)
        finally:
            os.remove(tmp_path)

if __name__ == '__main__':
    unittest.main()
