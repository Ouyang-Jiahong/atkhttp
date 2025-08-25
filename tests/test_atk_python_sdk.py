from unittest.mock import MagicMock, patch
import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from atk_python_sdk import atkConnect


def test_atkConnect_includes_objPath():
    with patch("atk_python_sdk.requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"events": ["ok"]}
        mock_resp.content = b'{"events":["ok"]}'
        mock_post.return_value = mock_resp

        events = atkConnect("http://example", "New", "/", "Scenario Test")

        assert events == ["ok"]
        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        assert kwargs["json"] == {
            "command": "New",
            "objPath": "/",
            "cmdParam": "Scenario Test",
            "waitMs": 10,
        }
