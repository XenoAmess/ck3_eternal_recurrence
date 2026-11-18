#include "xar_bridge/ck3_1210_full_clock_request_v1.hpp"

#include <charconv>

namespace xar::ck3_1210 {
namespace {
// Private scalar cursor, intentionally independent of the existing Core
// parser. No allocation, recursion, general object skipping or native calls.
struct Cursor {
  std::string_view text;
  std::size_t at = 0;

  void Space() noexcept {
    while (at < text.size() && (text[at] == ' ' || text[at] == '\n' ||
        text[at] == '\r' || text[at] == '\t')) ++at;
  }
  bool Take(char value) noexcept {
    Space();
    if (at == text.size() || text[at] != value) return false;
    ++at;
    return true;
  }
  bool String(std::string_view &output) noexcept {
    if (!Take('"')) return false;
    const auto start = at;
    while (at < text.size() && text[at] != '"') {
      const auto ch = static_cast<unsigned char>(text[at]);
      if (ch < 0x20 || ch >= 0x7F || ch == '\\' || at - start >= 192) return false;
      ++at;
    }
    if (at == text.size()) return false;
    output = text.substr(start, at - start);
    ++at;
    return true;
  }
  bool Unsigned(std::uint64_t &output) noexcept {
    Space();
    const auto start = at;
    while (at < text.size() && text[at] >= '0' && text[at] <= '9') ++at;
    if (at == start || (at - start > 1 && text[start] == '0')) return false;
    std::uint64_t value = 0;
    const auto result = std::from_chars(text.data() + start, text.data() + at, value);
    if (result.ec != std::errc{} || result.ptr != text.data() + at) return false;
    output = value;
    return true;
  }
};

bool EqualString(Cursor &cursor, std::string_view expected) noexcept {
  std::string_view value;
  return cursor.String(value) && value == expected;
}

bool ExactHash(Cursor &cursor) noexcept {
  std::string_view value;
  if (!cursor.String(value) || value.size() != 64) return false;
  for (std::size_t i = 0; i < value.size(); ++i) {
    char ch = value[i];
    if (ch >= 'a' && ch <= 'f') ch = static_cast<char>(ch - 'a' + 'A');
    if (ch != kExecutableSha256[i]) return false;
  }
  return true;
}

bool SafeRequestId(std::string_view value) noexcept {
  if (value.empty() || value.size() > 96) return false;
  for (const char ch : value)
    if (!((ch >= '0' && ch <= '9') || (ch >= 'a' && ch <= 'z') ||
          (ch >= 'A' && ch <= 'Z') || ch == '-' || ch == '_' || ch == '.')) return false;
  return true;
}

bool SnapshotId(Cursor &cursor, std::uint64_t &revision) noexcept {
  std::string_view value;
  if (!cursor.String(value) || !value.starts_with("native:")) return false;
  value.remove_prefix(7);
  if (value.empty() || value.front() == '0') return false;
  for (const char ch : value) if (ch < '0' || ch > '9') return false;
  std::uint64_t parsed = 0;
  const auto result = std::from_chars(value.data(), value.data() + value.size(), parsed);
  if (result.ec != std::errc{} || result.ptr != value.data() + value.size() || parsed == 0)
    return false;
  revision = parsed;
  return true;
}

bool Claim(Cursor &cursor, std::uint64_t &revision, std::uint64_t &deadline) noexcept {
  if (!cursor.Take('{')) return false;
  std::uint32_t seen = 0;
  std::uint64_t snapshot_revision = 0;
  bool first = true;
  while (!cursor.Take('}')) {
    if (!first && !cursor.Take(',')) return false;
    first = false;
    std::string_view key;
    if (!cursor.String(key) || !cursor.Take(':')) return false;
    std::uint32_t bit = 0;
    bool valid = false;
    if (key == "schema") {
      bit = 1U << 0; valid = EqualString(cursor, kFullClockRequestClaimSchemaV1);
    } else if (key == "game_version") {
      bit = 1U << 1; valid = EqualString(cursor, kGameVersion);
    } else if (key == "executable_sha256") {
      bit = 1U << 2; valid = ExactHash(cursor);
    } else if (key == "adapter_id") {
      bit = 1U << 3; valid = EqualString(cursor, kAdapterId);
    } else if (key == "backend") {
      bit = 1U << 4; valid = EqualString(cursor, kCoreBackendV1);
    } else if (key == "snapshot_id") {
      bit = 1U << 5; valid = SnapshotId(cursor, snapshot_revision);
    } else if (key == "native_revision") {
      bit = 1U << 6; valid = cursor.Unsigned(revision) && revision > 0;
    } else if (key == "deadline_unix_ms") {
      bit = 1U << 7; valid = cursor.Unsigned(deadline) && deadline > 0;
    }
    if (!valid || bit == 0 || (seen & bit) != 0) return false;
    seen |= bit;
  }
  return seen == 255U && snapshot_revision == revision;
}

bool NormalizeStep(FullClockRequestV1 &parsed) noexcept {
  if (parsed.step == "pause-map") {
    parsed.operation = CoreControlOperationV1::pause; parsed.step = "pause-map";
  } else if (parsed.step == "resume-map") {
    parsed.operation = CoreControlOperationV1::resume; parsed.step = "resume-map";
  } else if (parsed.step == "save-checkpoint") {
    parsed.operation = CoreControlOperationV1::save; parsed.step = "save-checkpoint";
  } else if (parsed.step.size() == 11 && parsed.step.starts_with("set-speed-") &&
      parsed.step[10] >= '1' && parsed.step[10] <= '5') {
    static constexpr std::string_view steps[]{"set-speed-1", "set-speed-2", "set-speed-3",
        "set-speed-4", "set-speed-5"};
    parsed.operation = CoreControlOperationV1::speed;
    parsed.public_speed = parsed.step[10] - '0';
    parsed.step = steps[parsed.public_speed - 1];
  } else return false;
  return true;
}
} // namespace

bool ParseFullClockRequestV1(std::string_view payload,
    FullClockRequestV1 &output) noexcept {
  output = {};
  if (payload.size() > 16384) return false;
  Cursor cursor{payload};
  FullClockRequestV1 parsed{};
  std::uint64_t expected_revision = 0;
  std::uint32_t seen = 0;
  bool first = true;
  if (!cursor.Take('{')) return false;
  while (!cursor.Take('}')) {
    if (!first && !cursor.Take(',')) return false;
    first = false;
    std::string_view key, value;
    if (!cursor.String(key) || !cursor.Take(':')) return false;
    std::uint32_t bit = 0;
    std::uint64_t number = 0;
    bool valid = false;
    if (key == "type") {
      bit = 1U << 0; valid = EqualString(cursor, "execute_step");
    } else if (key == "protocol_version") {
      bit = 1U << 1; valid = cursor.Unsigned(number) && number == 1;
    } else if (key == "request_id") {
      bit = 1U << 2; valid = cursor.String(value) && SafeRequestId(value);
    } else if (key == "step") {
      bit = 1U << 3; valid = cursor.String(parsed.step);
    } else if (key == "expected_revision") {
      bit = 1U << 4; valid = cursor.Unsigned(expected_revision) && expected_revision > 0;
    } else if (key == "full_snapshot_clock_control") {
      bit = 1U << 5;
      valid = Claim(cursor, parsed.native_revision, parsed.deadline_unix_ms);
    } else if (key == "arguments") {
      bit = 1U << 6; valid = cursor.Take('{') && cursor.Take('}');
    }
    if (!valid || bit == 0 || (seen & bit) != 0) return false;
    seen |= bit;
  }
  cursor.Space();
  if (cursor.at != payload.size() || (seen & 63U) != 63U ||
      expected_revision != parsed.native_revision || !NormalizeStep(parsed)) return false;
  output = parsed;
  return true;
}

} // namespace xar::ck3_1210
