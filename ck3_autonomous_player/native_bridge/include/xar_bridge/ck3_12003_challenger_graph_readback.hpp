#pragma once

#include "xar_bridge/ck3_12003_challenger_graph_request.hpp"
#include "xar_bridge/ck3_12003_religious_title_readback.hpp"
#include <optional>
#include <span>
#include <vector>

// Exact current .3 source-qualified, read-only candidate. No mutator, hook,
// provider install, runtime validation or saved-variable authority is implied.
namespace xar::ck3_12003::challenger_graph {
inline constexpr std::uintptr_t kFaithStorageSlotRva = 0x5D1E300;
inline constexpr std::uintptr_t kCFaithPrimaryVtableRva = 0x472FA48;
inline constexpr std::uint32_t kFaithKindMagic = 0x46616974U;
inline constexpr std::size_t kFaithFullIdOffset = 0x08;
inline constexpr std::size_t kFaithKindOffset = 0x0C;
inline constexpr std::size_t kFaithChallengersDataOffset = 0xC0;
inline constexpr std::size_t kFaithChallengersCountOffset = 0xCC;
inline constexpr std::int32_t kMaximumChallengersPerFaith = 4096;
inline constexpr std::size_t kMaximumCapturedFaiths = 64;
inline constexpr std::size_t kMaximumTotalCapturedRecords = 32768;
struct NativeRecord {
  std::uint32_t challenger_title_full_id = UINT32_MAX;
  std::uint32_t sponsor_title_full_id = UINT32_MAX;
  bool operator==(const NativeRecord &) const = default;
};
static_assert(sizeof(NativeRecord) == 8);
struct Bindings {
  bool enabled = false;
  religious_title::Bindings titles{};
  void **faith_storage_slot = nullptr;
};
struct TitleObservation {
  bool available = false;
  std::string unavailable_reason = "not_read";
  std::optional<bool> title_absent;
  std::optional<std::uint32_t> title_full_id;
  std::optional<std::string> native_title_class;
  std::optional<bool> holder_absent;
  std::optional<std::uint32_t> holder_character_full_id;
  std::optional<std::uint32_t> holder_current_faith_full_id;
  title_properties::Observation properties{};
  title_laws::Observation laws{};
};
struct ChallengerObservation {
  std::uint32_t challenger_title_full_id = UINT32_MAX;
  bool available = false;
  std::string unavailable_reason = "not_read";
  TitleObservation challenger_title{};
  TitleObservation registered_sponsor_title{};
  bool scope_sponsor_available = false;
  bool scope_lookup_complete = false;
  std::string scope_sponsor_unavailable_reason = "not_read";
  std::optional<std::uint32_t> scope_lookup_faith_full_id;
  std::optional<std::int32_t> scope_lookup_native_count;
  std::optional<bool> scope_lookup_faith_matches_collection;
  std::optional<bool> scope_matches_registered_pair;
  TitleObservation scope_sponsor_title{};
};
struct FaithObservation {
  std::uint32_t requested_faith_full_id = UINT32_MAX;
  bool available = false;
  bool collection_complete = false;
  std::string unavailable_reason = "not_read";
  std::optional<std::int32_t> native_count;
  std::optional<std::vector<std::uint32_t>> complete_native_challenger_title_ids;
  std::optional<std::vector<ChallengerObservation>> challengers;
};
struct Observation {
  bool available = false;
  bool graph_complete = false;
  std::string unavailable_reason = "not_read";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::vector<std::uint32_t> requested_faith_full_ids;
  std::optional<std::vector<FaithObservation>> faiths;
};
Bindings BindImage(std::uintptr_t image_base, std::string_view exact_current_sha256) noexcept;
bool Read(const Bindings &, const game::Snapshot &paused_frame, std::uint64_t capture_epoch,
          std::span<const std::uint32_t> requested_faith_full_ids, Observation &) noexcept;
std::string Serialize(const Observation &);
} // namespace xar::ck3_12003::challenger_graph
