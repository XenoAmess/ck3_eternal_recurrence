#pragma once
// SOURCE_PREPARED / NOTRUN. New isolated partial DATA candidate; no live wiring.
#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <variant>

namespace xar::ck3_1210::siege_read_only_partial_v1 {
inline constexpr std::string_view kSchema = "ck3.1210.siege_read_only_partial.v1";
inline constexpr std::string_view kExecutableSha256 =
    "2F2B236A16223891C2DA8B167F5F3738D2AE3E6D69DE1B4FBE190A5402998ACC";
inline constexpr std::int32_t kProvinceTableBound = 1'048'576;
inline constexpr std::int64_t kNativeProgressRatioScale = 100'000;
// Scale documents 293C090's real output ABI; this target-only reader never
// invokes the getter or derives a progress value from current work.
struct SourceFrame {
  std::uint64_t native_revision = 0;
  std::int32_t game_date_raw = 0;
  std::uint64_t query_sequence = 0;
  std::int32_t played_character_id = -1;
  friend bool operator==(const SourceFrame &, const SourceFrame &) = default;
};
struct Request {
  SourceFrame frame{};
  std::int32_t province_id = -1;
  friend bool operator==(const Request &, const Request &) = default;
};
struct ProvinceSelection { std::int32_t province_id = -1, validated_province_count = 0; };
struct UnknownTarget {};
struct AbsentTarget { ProvinceSelection province{}; };
struct IdentityOnlyTarget {
  ProvinceSelection province{};
  std::int32_t siege_full_id = -1;
  std::int64_t current_work_raw = -1;
};
using Target = std::variant<UnknownTarget, AbsentTarget, IdentityOnlyTarget>;
struct Captured {
  Request request{};
  Target target = UnknownTarget{};
  bool source_identity_admitted = false;
  bool source_frame_verified = false;
};
struct Bindings {
  bool exact_build_admitted = false;
  std::uintptr_t image_base = 0;
};
// The outer existing producer must fill actual revision/query/Core identities
// while it owns paused application-main custody. No default callback is supplied.
// This record does not create a lease or prove ownership by itself.
struct FrameEvidence {
  SourceFrame source{};
  std::uint64_t scope_epoch = 0;
  std::uintptr_t game_state = 0, jomini_state = 0, played_character = 0;
  std::int32_t local_player_id = -1;
  bool main_scope_held = false;
  bool map_ready = false;
  bool paused = false;
  bool has_live_played_character = false;
  friend bool operator==(const FrameEvidence &, const FrameEvidence &) = default;
};
using Copy = bool (*)(void *context, const void *source, void *destination,
    std::size_t size) noexcept;
using ReadFrame = bool (*)(void *context, FrameEvidence &output) noexcept;
struct ReadAccess {
  void *context = nullptr;
  Copy copy = nullptr;
  ReadFrame read_frame = nullptr;
};
Bindings BindImage(std::uintptr_t image_base, std::string_view sha256) noexcept;
// True means partial DATA was captured under the actual verified frame seam.
// A failed target graph may then be UNKNOWN; a failed source/frame/actor emits no
// leaf (false), and cannot be serialized. No native getter call occurs.
// No capability, Full availability, live qualification or action authority is
// granted by this component. A missing/unheld owner callback fails closed.
bool CopyTarget(const Bindings &, const Request &, Captured &, ReadAccess) noexcept;
// Transactional append. Only exact, internally valid candidate DATA is encoded.
// holder/subrealm/progress are fixed UNAVAILABLE; all qualification flags stay
// false. uint64 frame tokens and int64 work use canonical decimal JSON strings.
bool AppendJson(const Captured &, std::string &output) noexcept;
} // namespace xar::ck3_1210::siege_read_only_partial_v1
