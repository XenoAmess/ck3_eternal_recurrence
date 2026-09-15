from __future__ import annotations

import base64
import hashlib
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.coat_of_arms_source_probe_contract import (  # noqa: E402
    COAT_OF_ARMS_SOURCE_V2_MAX_BYTES,
    encode_coat_of_arms_source_v1,
    encode_coat_of_arms_source_transport_v2,
)
from xar_autoplayer.bridge.coat_of_arms_source_upload_v2 import (  # noqa: E402
    COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_BUFFERED_BYTES,
    COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_CHUNK_BYTES,
    COAT_OF_ARMS_SOURCE_UPLOAD_V2_TTL_SECONDS,
    CoatOfArmsSourceUploadManagerV2,
)


GAME_VERSION = "1.19.0.6"
EXE_SHA256 = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
BINDING = {
    "mode": "frontend",
    "revision": 0,
    "connection_generation": 7,
    "bridge_pid": 4242,
}


class _Harness:
    def __init__(self) -> None:
        self.now = [100.0]
        self.tokens = iter(
            [
                "00000000000000000000000000000001",
                "00000000000000000000000000000002",
                "00000000000000000000000000000003",
                "00000000000000000000000000000004",
            ]
        )
        self.manager = CoatOfArmsSourceUploadManagerV2(
            clock=lambda: self.now[0],
            token_factory=lambda: next(self.tokens),
        )

    @staticmethod
    def digest(payload: bytes) -> str:
        return hashlib.sha256(payload).hexdigest()

    def begin(
        self,
        payload: bytes,
        *,
        chunk_count: int | None = None,
        expected_revision: int = 0,
        apply: bool = True,
    ) -> dict[str, object]:
        count = chunk_count or (
            (len(payload) + COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_CHUNK_BYTES - 1)
            // COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_CHUNK_BYTES
        )
        return self.manager.begin(
            total_bytes=len(payload),
            source_sha256=self.digest(payload),
            chunk_count=count,
            chunk_encoding="base64",
            expected_revision=expected_revision,
            apply=apply,
            expected_game_version=GAME_VERSION,
            expected_executable_sha256=EXE_SHA256,
            binding=BINDING,
        )

    def append(
        self,
        receipt: dict[str, object],
        index: int,
        chunk: bytes,
        *,
        chunk_index: int | None = None,
        chunk_sha256: str | None = None,
        chunk_base64: str | None = None,
    ) -> dict[str, object]:
        return self.manager.append(
            upload_id=receipt["upload_id"],
            generation=receipt["generation"],
            chunk_index=index if chunk_index is None else chunk_index,
            chunk_count=receipt["chunk_count"],
            chunk_encoding="base64",
            chunk_bytes=len(chunk),
            chunk_sha256=chunk_sha256 or self.digest(chunk),
            chunk_base64=chunk_base64 or base64.b64encode(chunk).decode("ascii"),
            source_sha256=receipt["source_sha256"],
            expected_revision=receipt["expected_revision"],
            apply=receipt["apply"],
            expected_game_version=receipt["expected_game_version"],
            expected_executable_sha256=receipt[
                "expected_executable_sha256"
            ],
        )

    def finalize(
        self,
        receipt: dict[str, object],
        *,
        expected_revision: int = 0,
        apply: bool = True,
    ) -> tuple[str, dict[str, object], dict[str, object]]:
        return self.manager.finalize(
            upload_id=receipt["upload_id"],
            generation=receipt["generation"],
            chunk_count=receipt["chunk_count"],
            source_sha256=receipt["source_sha256"],
            expected_revision=expected_revision,
            apply=apply,
            expected_game_version=GAME_VERSION,
            expected_executable_sha256=EXE_SHA256,
        )


class CoatOfArmsSourceUploadV2Tests(unittest.TestCase):
    def test_over_128_kib_round_trip_is_exact_and_single_commit(self) -> None:
        harness = _Harness()
        payload = (
            b"coat_of_arms = {\r\n"
            + b" colored_emblem = { depth = 1 }\r\n" * 4_200
            + b"}\r\n"
        )
        self.assertGreater(len(payload), 128 * 1024)
        with self.assertRaises(ValueError):
            encode_coat_of_arms_source_v1(payload.decode("ascii"))

        receipt = harness.begin(payload)
        self.assertEqual(receipt["status"], "receiving")
        chunks = [
            payload[offset : offset + COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_CHUNK_BYTES]
            for offset in range(0, len(payload), COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_CHUNK_BYTES)
        ]
        for index, chunk in enumerate(chunks):
            progress = harness.append(receipt, index, chunk)
        self.assertEqual(progress["status"], "ready")
        self.assertEqual(progress["received_bytes"], len(payload))

        source, committed, binding = harness.finalize(receipt)
        self.assertEqual(source.encode("ascii"), payload)
        self.assertEqual(committed["status"], "committed")
        self.assertEqual(committed["source_sha256"], harness.digest(payload))
        self.assertEqual(binding, BINDING)
        with self.assertRaises(ValueError):
            harness.finalize(receipt)

    def test_v2_native_transport_bound_is_exact_and_v1_is_unchanged(self) -> None:
        source = "x" * COAT_OF_ARMS_SOURCE_V2_MAX_BYTES
        encoded = encode_coat_of_arms_source_transport_v2(source)
        self.assertEqual(encoded.source_bytes, COAT_OF_ARMS_SOURCE_V2_MAX_BYTES)
        with self.assertRaisesRegex(ValueError, "128 KiB"):
            encode_coat_of_arms_source_v1(source)
        with self.assertRaisesRegex(ValueError, "512 KiB"):
            encode_coat_of_arms_source_transport_v2(source + "x")

    def test_duplicate_or_out_of_order_chunk_destroys_session(self) -> None:
        harness = _Harness()
        payload = b"x" * (COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_CHUNK_BYTES + 1)
        receipt = harness.begin(payload)
        with self.assertRaisesRegex(ValueError, "duplicate or out of order"):
            harness.append(receipt, 0, payload[-1:], chunk_index=1)
        with self.assertRaisesRegex(ValueError, "unavailable or expired"):
            harness.append(receipt, 0, payload[:-1])

    def test_corrupt_chunk_destroys_session(self) -> None:
        harness = _Harness()
        payload = b"coat_of_arms = {}\r\n"
        receipt = harness.begin(payload)
        with self.assertRaisesRegex(ValueError, "length or SHA-256"):
            harness.append(receipt, 0, payload, chunk_sha256="0" * 64)
        with self.assertRaisesRegex(ValueError, "unavailable or expired"):
            harness.finalize(receipt)

    def test_noncanonical_base64_pad_bits_destroy_session(self) -> None:
        harness = _Harness()
        payload = b"a"
        receipt = harness.begin(payload)
        # Both strings decode to b"a" in permissive decoders, but only YQ==
        # has canonical zero pad bits.
        with self.assertRaisesRegex(ValueError, "canonical base64"):
            harness.append(receipt, 0, payload, chunk_base64="YR==")
        with self.assertRaisesRegex(ValueError, "unavailable or expired"):
            harness.finalize(receipt)

    def test_incomplete_finalize_and_changed_intent_fail_closed(self) -> None:
        harness = _Harness()
        payload = b"x" * (COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_CHUNK_BYTES + 1)
        receipt = harness.begin(payload)
        harness.append(receipt, 0, payload[:-1])
        with self.assertRaisesRegex(ValueError, "incomplete"):
            harness.finalize(receipt)
        with self.assertRaisesRegex(ValueError, "unavailable or expired"):
            harness.finalize(receipt)

        second = harness.begin(b"coat_of_arms = {}\r\n")
        harness.append(second, 0, b"coat_of_arms = {}\r\n")
        with self.assertRaisesRegex(ValueError, "apply intent changed"):
            harness.finalize(second, apply=False)
        with self.assertRaisesRegex(ValueError, "unavailable or expired"):
            harness.finalize(second)

    def test_expiry_and_abort_release_resources(self) -> None:
        harness = _Harness()
        payload = b"coat_of_arms = {}\r\n"
        expired = harness.begin(payload)
        harness.now[0] += COAT_OF_ARMS_SOURCE_UPLOAD_V2_TTL_SECONDS
        with self.assertRaisesRegex(ValueError, "unavailable or expired"):
            harness.append(expired, 0, payload)

        active = harness.begin(payload)
        aborted = harness.manager.abort(
            upload_id=active["upload_id"], generation=active["generation"]
        )
        self.assertEqual(aborted["status"], "aborted")
        with self.assertRaisesRegex(ValueError, "unavailable or expired"):
            harness.append(active, 0, payload)

    def test_declared_payload_budget_is_reserved_at_begin(self) -> None:
        harness = _Harness()
        first_size = 512 * 1024
        first = harness.begin(b"x" * first_size, chunk_count=11)
        self.assertEqual(first["total_bytes"], first_size)
        second_size = COAT_OF_ARMS_SOURCE_UPLOAD_V2_MAX_BUFFERED_BYTES - first_size + 1
        with self.assertRaisesRegex(ValueError, "byte budget exhausted"):
            harness.begin(b"y" * second_size, chunk_count=6)

    def test_noncanonical_line_endings_are_rejected_at_commit(self) -> None:
        harness = _Harness()
        payload = b"coat_of_arms = {\n}\n"
        receipt = harness.begin(payload)
        harness.append(receipt, 0, payload)
        with self.assertRaisesRegex(ValueError, "canonical CRLF"):
            harness.finalize(receipt)


if __name__ == "__main__":
    unittest.main()
