"""The live harness must preserve ordinary-interaction packet evidence."""

import ast
from pathlib import Path
import unittest


SCRIPT = (Path(__file__).resolve().parents[2] / "native_bridge" / "research" /
          "run_ck3_12002_mcp_live.py")


class RecordingEndpointTests(unittest.TestCase):
    def test_send_forwards_packet_evidence_to_native_transport(self):
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        server = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                      and node.name == "native_server")
        endpoint = next(node for node in server.body if isinstance(node, ast.ClassDef)
                        and node.name == "RecordingEndpoint")
        calls = []

        class NativeNamedPipeServer:
            def send(self, frame, *, packet_evidence_path=None):
                calls.append(("transport", frame, packet_evidence_path))

        class Wire:
            def write(self, direction, frame):
                calls.append(("wire", direction, frame))

        namespace = {"NativeNamedPipeServer": NativeNamedPipeServer,
                     "Path": Path, "wire": Wire()}
        exec(compile(ast.Module(body=[endpoint], type_ignores=[]), str(SCRIPT), "exec"), namespace)
        frame = {"type": "ordinary_interaction", "recipient_id": 31763}
        evidence = Path("nomination.packet.bin")
        namespace["RecordingEndpoint"]().send(frame, packet_evidence_path=evidence)
        self.assertEqual(calls, [
            ("wire", "python-to-dll", frame), ("transport", frame, evidence)])


if __name__ == "__main__":
    unittest.main()
