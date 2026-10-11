#pragma once

#include "xar_bridge/create_piety_final_price_source_model_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12004::religion_price_source {

inline constexpr std::string_view kReligionPriceSourceExecutableSha25612004 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";

// Copied mailbox metadata. None of these fields is a native event/frame ID.
struct ReligionCreationPriceSourceFrame12004 {
  bool actual_application_query = false;
  std::uint64_t snapshot_revision = 0;
  std::uint64_t query_sequence = 0;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::uint32_t played_character_id = 0;
  std::uint32_t owning_thread_id = 0;
  std::int32_t stamp_date_raw = 0;
  bool stamp_paused = false;
  bool mailbox_before_accepted = false;
  std::optional<bool> mailbox_after_accepted;
};

struct ReligionPriceResolvedObject12004 {
  bool ready = false;
  std::string_view reason = "not_read";
  std::optional<std::uint32_t> requested_full_id;
  std::optional<std::uintptr_t> selected_identity;
  std::optional<std::uint32_t> resolved_full_id;
  std::optional<bool> used_fallback;
  bool operator==(const ReligionPriceResolvedObject12004 &) const = default;
};

struct ReligionCreationPriceSourceInputs12004 {
  bool complete = false;
  std::string_view reason = "not_read";
  std::uintptr_t window_identity = 0;
  std::optional<std::uintptr_t> price_payload_identity;
  std::optional<std::uint32_t> window_source_rite_carrier;
  std::optional<std::uintptr_t> character_storage_identity;
  std::optional<std::uintptr_t> character_fallback_identity;
  std::optional<std::uintptr_t> rite_storage_identity;
  std::optional<std::uintptr_t> rite_fallback_identity;
  ReligionPriceResolvedObject12004 first_actor;
  ReligionPriceResolvedObject12004 current_rite;
  ReligionPriceResolvedObject12004 second_actor;
  bool operator==(const ReligionCreationPriceSourceInputs12004 &) const = default;
};

struct ReligionCreationPriceSourcePacket12004 {
  ReligionCreationPriceSourceFrame12004 frame;
  bool source_ready = false;
  std::string_view reason = "source_not_completed";
  std::optional<bool> editing_owned_current_rite;
  ReligionCreationPriceSourceInputs12004 before;
  std::optional<ReligionCreationPriceSourceInputs12004> after;
  std::optional<bool> copied_spans_still_current;
  std::optional<bool> input_mappings_still_current;
  std::size_t copied_read_count = 0;
  std::size_t copied_bytes = 0;
  std::optional<piety_price_raw_inputs::CreatePietyFinalPriceSourceObservation12004>
      source_model;
  std::optional<std::int64_t> final_piety_price_raw_q64;
};

// The probe is local to one owning application-thread mailbox execution. It
// preserves every successful read occurrence, including duplicate reads.
struct ReligionCreationPriceSourceReadAtom12004 {
  std::uintptr_t address = 0;
  std::vector<std::byte> bytes;
};
struct ReligionCreationPriceSourceProbe12004 {
  piety_price_raw_inputs::PietyPriceNumericAccess12004 access;
  ReligionCreationPriceSourcePacket12004 packet;
  std::vector<ReligionCreationPriceSourceReadAtom12004> copied_reads;
  std::size_t copied_bytes = 0;
  bool copy_budget_exceeded = false;
  static constexpr std::size_t maximum_copied_bytes = 262144;
  static constexpr std::size_t maximum_read_occurrences = 16384;
};

piety_price_raw_inputs::PietyPriceNumericAccess12004
BindReligionCreationPriceSourceAccess12004(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;
ReligionCreationPriceSourceProbe12004 BeginReligionCreationPriceSource12004(
    const piety_price_raw_inputs::PietyPriceNumericAccess12004 &,
    std::uintptr_t actual_window,
    const ReligionCreationPriceSourceFrame12004 &) noexcept;
ReligionCreationPriceSourcePacket12004 CompleteReligionCreationPriceSource12004(
    ReligionCreationPriceSourceProbe12004 &, std::optional<bool> existing_selector,
    bool existing_native_quote_available) noexcept;
void FinishReligionCreationPriceSourceMailbox12004(
    ReligionCreationPriceSourcePacket12004 &, bool actual_finish_accepted) noexcept;
std::string SerializeReligionCreationPriceSource12004(
    const ReligionCreationPriceSourcePacket12004 &);

} // namespace xar::ck3_12004::religion_price_source
