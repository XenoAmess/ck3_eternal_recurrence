#pragma once

#include "xar_bridge/game_contract.hpp"

#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace xar::game {

enum class H2743ExistingTruceStatusV1 : std::uint32_t {
  unavailable = 0,
  existing_truce = 1,
  no_existing_truce = 2,
};

struct H2743ExistingTruceSnapshotV1 {
  H2743ExistingTruceStatusV1 status =
      H2743ExistingTruceStatusV1::unavailable;
  std::uint64_t snapshot_revision = 0;
  std::int32_t date_raw = 0;
  bool same_frame_stable = false;
  bool preaction_existing_expiry_observable = false;
  std::int32_t preaction_existing_expiry_date_raw = 0;
  std::string_view unavailable_reason = "not_queried";
};

} // namespace xar::game

namespace xar::ck3_11906 {

inline constexpr std::string_view kH2743ExistingTruceV1Step =
    "query-h2743-preaction-existing-truce-v1";
inline constexpr std::string_view kH2743ExistingTruceV1Capability =
    "game.command.query-h2743-preaction-existing-truce-v1";
inline constexpr std::string_view kH2743EpisodeIdV1 =
    "native-29829-2bc2d599f7f9";
inline constexpr std::string_view kH2743CheckpointSha256V1 =
    "A5012030DA500A4352EF79D1EA10269D45DD5D19DAC508E22DD835663A5106E9";
inline constexpr std::int32_t kH2743TruceWarIdV1 = 16777231;
inline constexpr std::int32_t kH2743TruceAttackerIdV1 = 30097;
inline constexpr std::int32_t kH2743TruceDefenderIdV1 = 29829;
inline constexpr std::int32_t kH2743TruceDateRawV1 = 53217264;
inline constexpr std::string_view kH2743ExeSha256V1 =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";

struct H2743PreactionFrameClaimV1 {
  std::uint64_t public_revision = 0;
  std::uint64_t native_revision = 0;
  std::uint64_t date_raw = 0;
  std::uint64_t actor_character_id = 0;
  std::uint64_t war_id = 0;
  std::string snapshot_id;
  std::string episode_id;
  std::string checkpoint_sha256;
  std::string exe_sha256;
};

bool AdmitH2743PreactionFrameClaimV1(
    const H2743PreactionFrameClaimV1 &claim,
    std::uint64_t state_revision,
    const game::Snapshot &actual);

struct H2743TruceWarIdentityV1 {
  const void *war_object = nullptr;
  const void *casus_belli_object = nullptr;
  std::int32_t war_id = -1;
  std::int32_t primary_attacker_id = -1;
  std::int32_t primary_defender_id = -1;
  std::int32_t casus_belli_database_index = -1;
  bool exact_casus_belli_key = false;
  std::vector<std::int32_t> target_title_ids;

  friend bool operator==(const H2743TruceWarIdentityV1 &,
                         const H2743TruceWarIdentityV1 &) = default;
};

using H2743ReadSnapshotV1 = bool (*)(void *, game::Snapshot &) noexcept;
using H2743ReadWarIdentityV1 =
    bool (*)(void *, H2743TruceWarIdentityV1 &) noexcept;
using H2743ResolveCharacterV1 = void *(*)(void *, std::int32_t) noexcept;
using H2743HasTruceV1 = bool (*)(void *, void *);
using H2743GetTruceEndDateV1 = const void *(*)(void *, void *);

struct H2743ExistingTruceAccessV1 {
  bool exact_build_admitted = false;
  void *context = nullptr;
  H2743ReadSnapshotV1 read_snapshot = nullptr;
  H2743ReadWarIdentityV1 read_war_identity = nullptr;
  H2743ResolveCharacterV1 resolve_living_character = nullptr;
  H2743HasTruceV1 has_truce = nullptr;
  H2743GetTruceEndDateV1 get_truce_end_date = nullptr;
};

game::H2743ExistingTruceStatusV1 ReadH2743PreactionExistingTruceV1(
    const H2743ExistingTruceAccessV1 &access,
    game::H2743ExistingTruceSnapshotV1 &output) noexcept;

std::string SerializeH2743PreactionExistingTruceV1(
    const game::H2743ExistingTruceSnapshotV1 &snapshot);

} // namespace xar::ck3_11906
