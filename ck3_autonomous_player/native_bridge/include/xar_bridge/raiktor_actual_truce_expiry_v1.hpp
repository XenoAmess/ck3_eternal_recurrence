#pragma once

#include "xar_bridge/game_contract.hpp"

#include <cstdint>
#include <string>
#include <string_view>

namespace xar::game {

enum class RaiktorActualTruceExpiryStatusV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
  no_truce = 2,
};

struct RaiktorActualTruceExpirySnapshotV1 {
  RaiktorActualTruceExpiryStatusV1 status =
      RaiktorActualTruceExpiryStatusV1::unavailable;
  std::uint64_t snapshot_revision = 0;
  std::int32_t current_date_raw = 0;
  std::int32_t owner_character_id = -1;
  std::int32_t toward_character_id = -1;
  bool native_has_truce = false;
  bool actual_expiry_observable = false;
  std::int32_t expiry_date_raw = 0;
  bool same_frame_stable = false;
  bool readiness = false;
  std::string temporal_semantics =
      "post_application_persisted_relation_state";
  std::string unavailable_reason;

  friend bool operator==(const RaiktorActualTruceExpirySnapshotV1 &,
                         const RaiktorActualTruceExpirySnapshotV1 &) =
      default;
};

enum class ReadRaiktorActualTruceExpiryResultV1 : std::uint32_t {
  unavailable = 0,
  available = 1,
  no_truce = 2,
  requires_paused = 3,
  no_played_character = 4,
  toward_character_not_found = 5,
  unstable_snapshot = 6,
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kRaiktorActualTruceExpiryV1Capability =
    "game.command.query-raiktor-actual-truce-expiry-v1-N";
inline constexpr std::string_view kRaiktorActualTruceExpiryV1StepPrefix =
    "query-raiktor-actual-truce-expiry-v1-";
inline constexpr std::string_view kRaiktorActualTruceExpiryV1BackendId =
    "ck3-1.19.0.6-native-raiktor-actual-truce-expiry-v1";

using RaiktorReadSnapshotV1 =
    bool (*)(void *context, game::Snapshot &output) noexcept;
using RaiktorResolveCharacterV1 =
    void *(*)(void *context, std::int32_t character_id) noexcept;
using RaiktorHasTruceV1 = bool (*)(void *owner, void *toward);
using RaiktorGetTruceEndDateV1 = const void *(*)(void *owner, void *toward);

struct RaiktorActualTruceExpiryAccessV1 {
  bool exact_build_admitted = false;
  void *context = nullptr;
  RaiktorReadSnapshotV1 read_snapshot = nullptr;
  RaiktorResolveCharacterV1 resolve_character = nullptr;
  RaiktorHasTruceV1 has_truce = nullptr;
  RaiktorGetTruceEndDateV1 get_truce_end_date = nullptr;
};

game::ReadRaiktorActualTruceExpiryResultV1 ReadRaiktorActualTruceExpiryV1(
    const RaiktorActualTruceExpiryAccessV1 &access,
    std::int32_t toward_character_id,
    game::RaiktorActualTruceExpirySnapshotV1 &output) noexcept;

std::string SerializeRaiktorActualTruceExpiryV1(
    const game::RaiktorActualTruceExpirySnapshotV1 &snapshot);

} // namespace xar::ck3_11906
