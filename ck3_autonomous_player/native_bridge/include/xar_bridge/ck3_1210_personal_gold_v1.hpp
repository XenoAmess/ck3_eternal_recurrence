#pragma once

#include "xar_bridge/ck3_1210.hpp"

#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_1210 {

inline constexpr char kPersonalGoldSchemaV1[] = "ck3_1210_personal_gold_frame_v1";
inline constexpr std::int64_t kPersonalGoldScaleV1 = 100'000;
inline constexpr std::size_t kPersonalGoldCharacterTypeOffsetV1 = 0x1C;
inline constexpr std::size_t kPersonalGoldLivingExtensionOffsetV1 = 0x1B0;
inline constexpr std::size_t kPersonalGoldBalanceOffsetV1 = 0x100;

// New-image evidence: FINANCE-ABI-CANDIDATES01.json, exact Florin SHA.
// GetGold name 4B59400 -> registration 894F3/8951D -> callback D9E760.
// D9E771 reads Character+1B0, D9E796 reads living+100; null living is zero.
// This is the personal wallet. It is not the separate GetTreasury source.
struct PersonalGoldBindingsV1 {
  bool exact_build_admitted = false;
  CoreBindings core{};
};

struct PersonalGoldObservationV1 {
  std::string_view schema = kPersonalGoldSchemaV1;
  std::string_view game_version = kGameVersion;
  std::string_view steam_build_id = kSteamBuildId;
  std::string_view executable_sha256 = kExecutableSha256;
  std::size_t executable_file_size = kExecutableFileSize;
  bool available = false;
  // Means the two complete Core prefixes agree, not a main-thread receipt.
  // The integration owner must separately establish owning paused custody.
  bool same_frame_ready = false;
  bool partial = true;
  bool full_snapshot_available = false;
  bool treasury_observed = false;
  bool monthly_flow_observed = false;
  CoreSnapshotPrefix frame{};
  std::optional<std::int64_t> personal_gold_raw;
  std::int64_t scale = kPersonalGoldScaleV1;
  std::string_view unavailable_reason = "personal_gold_not_read";
};

// Only the exact Florin identity selects these 1.21 Core bindings. This
// function calculates addresses; it does not inspect or start a process.
PersonalGoldBindingsV1 BindPersonalGoldImageV1(std::uintptr_t image_base,
    std::string_view executable_sha256) noexcept;

// Caller owns the application main thread in the expected paused frame.
// Reads Core before/after, resolves full-generation identity twice and checks
// actor pointer/type/full ID/alive/living pointer plus the signed balance.
// Failure clears the optional amount; it never turns a failed read into zero.
// No serializer, capability registration, command or complete Snapshot here.
bool ReadPersonalGoldV1(const PersonalGoldBindingsV1 &bindings,
    const CoreSnapshotPrefix &expected,
    PersonalGoldObservationV1 &output) noexcept;

} // namespace xar::ck3_1210
