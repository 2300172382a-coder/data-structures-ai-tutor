import unittest

from scripts.bootstrap_openwebui import MODEL_ID, configure_model_defaults


class FakeClient:
    def __init__(self):
        self.calls = []

    def request(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        if method == "GET" and path == "/api/v1/configs/models":
            return {
                "DEFAULT_MODELS": None,
                "DEFAULT_PINNED_MODELS": "existing-model",
                "MODEL_ORDER_LIST": ["existing-model"],
                "DEFAULT_MODEL_METADATA": {"capabilities": {"citations": True}},
                "DEFAULT_MODEL_PARAMS": {"temperature": 0.2},
            }
        return {}


class BootstrapModelDefaultsTests(unittest.TestCase):
    def test_sets_course_default_and_disables_hidden_builtin_tools(self):
        client = FakeClient()

        configure_model_defaults(client)

        method, path, kwargs = client.calls[1]
        self.assertEqual((method, path), ("POST", "/api/v1/configs/models"))
        payload = kwargs["json"]
        self.assertEqual(payload["DEFAULT_MODELS"], MODEL_ID)
        self.assertFalse(payload["DEFAULT_MODEL_METADATA"]["capabilities"]["builtin_tools"])
        self.assertTrue(payload["DEFAULT_MODEL_METADATA"]["capabilities"]["citations"])
        self.assertEqual(payload["DEFAULT_PINNED_MODELS"], "existing-model")
        self.assertEqual(payload["DEFAULT_MODEL_PARAMS"], {"temperature": 0.2})
        self.assertEqual(client.calls[2][:2], ("GET", "/api/models?refresh=true"))


if __name__ == "__main__":
    unittest.main()
