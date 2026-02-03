import unittest
import yaml
import tempfile
import os
from prompter.config import PromptConfig
from prompter.ids import PromptID

class TestConfigValidation(unittest.TestCase):
    def test_valid_ids(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
            yaml.dump({
                "version": "1.0",
                "prompts": [
                    {"id": PromptID.CORE_IDENTITY, "text": "foo"},
                    {"id": PromptID.USER_CONTEXT, "text": "bar"}
                ]
            }, tmp)
            tmp_path = tmp.name
        
        try:
            config = PromptConfig.load(tmp_path)
            self.assertEqual(len(config.prompts), 2)
        finally:
            os.remove(tmp_path)

    def test_invalid_id(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp:
            yaml.dump({
                "version": "1.0",
                "prompts": [
                    {"id": "INVALID_ID_XYZ", "text": "foo"}
                ]
            }, tmp)
            tmp_path = tmp.name
        
        try:
            with self.assertRaises(ValueError) as cm:
                PromptConfig.load(tmp_path)
            self.assertIn("Invalid prompt ID", str(cm.exception))
        finally:
            os.remove(tmp_path)

if __name__ == '__main__':
    unittest.main()
