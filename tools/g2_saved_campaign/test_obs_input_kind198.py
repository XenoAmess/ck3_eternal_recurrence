"""Two source198 pure input-kind regressions; no OBS client, network or worker."""
from dataclasses import dataclass
import importlib.util
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

ROOT = Path(os.environ.get("VIDEO_INPUT_KIND198_ROOT", str(Path(__file__).resolve().parents[2])))
REPOSITORY = Path(os.environ.get("VIDEO_INPUT_KIND198_REPO", str(Path(__file__).resolve().parents[2])))
sys.path.insert(0, str(REPOSITORY))
SPEC = importlib.util.spec_from_file_location("obs_input_kind198_candidate", ROOT / "tools/ck3_obs_capture.py")
capture = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = capture
SPEC.loader.exec_module(capture)


@dataclass(frozen=True)
class InputKindListResponse:
    """Same observable attribute as SDK util.as_dataclass(inputKinds); no ReqClient."""
    input_kinds: object


class FakeClient:
    def __init__(self, response: object = None, error: Exception | None = None) -> None:
        self.get_input_kind_list = Mock(return_value=response, side_effect=error)


class InputKind198Tests(unittest.TestCase):
    def assert_versioned_request_once(self, client: FakeClient) -> None:
        client.get_input_kind_list.assert_called_once_with(unversioned=False)
        self.assertIs(client.get_input_kind_list.call_args.kwargs["unversioned"], False)

    def test_actual_versioned_v3_and_numeric_highest_exact_return(self) -> None:
        # Literal actual32.2.2 input_kinds_versioned, independent of target execution.
        actual = ["image_source", "color_source_v3", "slideshow_v2", "browser_source", "ffmpeg_source",
                  "text_gdiplus_v3", "text_ft2_source_v2", "monitor_capture", "window_capture", "game_capture",
                  "dshow_input", "spout_capture", "wasapi_input_capture", "wasapi_output_capture", "wasapi_process_output_capture"]
        cases = [(actual, "text_gdiplus_v3"),
                 (["text_gdiplus_v2", "text_gdiplus", "text_gdiplus_v10"], "text_gdiplus_v10"),
                 (["text_gdiplus_v10", "text_gdiplus_v2"], "text_gdiplus_v10"),
                 (["text_gdiplus"], "text_gdiplus")]
        for kinds, expected in cases:
            with self.subTest(kinds=kinds):
                client = FakeClient(InputKindListResponse(kinds))
                self.assertEqual(capture._select_gdiplus_input_kind(client), expected)
                self.assert_versioned_request_once(client)

    def test_missing_malformed_family_and_api_errors_have_no_fallback(self) -> None:
        responses = [None, SimpleNamespace(), InputKindListResponse(None), InputKindListResponse(False),
                     InputKindListResponse("text_gdiplus_v3"), InputKindListResponse(("text_gdiplus_v3",)),
                     InputKindListResponse([]), InputKindListResponse(["image_source", "game_capture"]),
                     InputKindListResponse(["text_gdiplus_v3", 123]), InputKindListResponse(["text_gdiplus_v3", True]),
                     InputKindListResponse(["text_gdiplus_v3", ""])]
        malformed = ["text_gdiplus_v0", "text_gdiplus_v01", "text_gdiplus_v", "text_gdiplus_v+1",
                     "text_gdiplus_v-1", "text_gdiplus_v1.0", "text_gdiplus_v١", "text_gdiplus_v３",
                     "text_gdiplus_v3_extra", "extra_text_gdiplus_v3"]
        responses.extend(InputKindListResponse([kind]) for kind in malformed)
        responses.append(InputKindListResponse(["text_gdiplus_v3", "text_gdiplus_v0"]))
        for response in responses:
            with self.subTest(response=response):
                client = FakeClient(response)
                with self.assertRaises(ValueError):
                    capture._select_gdiplus_input_kind(client)
                self.assert_versioned_request_once(client)
        original = RuntimeError("fixture GetInputKindList failure")
        client = FakeClient(error=original)
        with self.assertRaises(RuntimeError) as caught:
            capture._select_gdiplus_input_kind(client)
        self.assertIs(caught.exception, original)
        self.assert_versioned_request_once(client)


if __name__ == "__main__":
    unittest.main(verbosity=2)
