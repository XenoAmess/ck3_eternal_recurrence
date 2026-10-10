#pragma once

#include "xar_bridge/army_natural_phase_scope_12004.hpp"
#include "xar_bridge/army_assault_consumer_parent_12004.hpp"
#include <array>
#include <charconv>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace xar::game {
inline constexpr std::size_t kArmyAssaultReleasePayloadLimit12004 = 64;
inline constexpr std::size_t kArmyAssaultReleaseJournalCapacity12004 = 256;

enum ArmyAssaultReleaseCaptureFailure12004 : std::uint32_t {
  assault_release_capture_none = 0,
  assault_release_capture_header_before = 1U << 0,
  assault_release_capture_header_after = 1U << 1,
  assault_release_capture_payload_before = 1U << 2,
  assault_release_capture_payload_after = 1U << 3,
  assault_release_capture_payload_truncated = 1U << 4,
  assault_release_capture_parent = 1U << 5,
  assault_release_capture_slot = 1U << 6,
  assault_release_capture_clock = 1U << 7,
};

struct ArmyAssaultReleaseVectorSnapshot12004 {
  std::optional<std::uint64_t> data_address;
  std::optional<std::int32_t> count_raw_i32, capacity_raw_i32;
  std::optional<std::uint64_t> allocator_address;
  std::optional<bool> allocator_matches_expected;
  std::uint32_t expected_allocator_rva_u32 = 0;
  std::uint32_t payload_count = 0;
  bool payload_complete = false;
  std::array<std::uint32_t, kArmyAssaultReleasePayloadLimit12004> raw_full_ids_u32{};
};

using ArmyAssaultReleaseParent12004 = ck3_12004::ArmyAssaultConsumerParent12004;

struct ArmyAssaultGroupReleaseObservation12004 {
  std::uint64_t sequence = 0;
  ck3_12004::ArmyNaturalPhaseEvent12004 entry_event, returned_event;
  ArmyAssaultReleaseParent12004 parent{};
  std::uint32_t thread_id = 0;
  std::uint64_t caller_return_rva = 0, callsite_rva = 0;
  std::uint64_t record_plus10_address = 0;
  std::optional<std::uint64_t> entries_address;
  std::optional<std::uint64_t> physical_slot;
  std::optional<std::uint8_t> control_before, control_at_record_return;
  std::optional<std::int32_t> occupied_count_before, occupied_count_at_record_return;
  ArmyAssaultReleaseVectorSnapshot12004 arrgs_before{}, armies_before{};
  ArmyAssaultReleaseVectorSnapshot12004 arrgs_after{}, armies_after{};
  bool original_returned = false, same_parent_at_return = false;
  std::optional<bool> same_clock_thread_order;
  std::uint64_t original_rax_raw_u64 = 0;
  std::uint32_t capture_failure_flags = assault_release_capture_none;
};

struct ArmyAssaultGroupReleaseObservations12004 {
  bool observer_installed = false, current_session_guard = false;
  std::uint64_t oldest_available_sequence = 0, latest_sequence = 0;
  std::uint64_t overwritten_events = 0, unattributed_capture_failures = 0;
  std::uint64_t ignored_noncanonical_receivers = 0;
  std::vector<ArmyAssaultGroupReleaseObservation12004> events;
};

namespace army_assault_release_json_12004 {
template <typename I> inline void Number(std::string &out, I value) {
  char buffer[32]{};
  const auto end = std::to_chars(buffer, buffer + sizeof(buffer), value);
  out.append(buffer, end.ptr);
}
template <typename I> inline void Optional(std::string &out, const std::optional<I> &value) {
  if (value) Number(out, *value); else out += "null";
}
inline void Boolean(std::string &out, bool value) { out += value ? "true" : "false"; }
inline void Event(std::string &out, const ck3_12004::ArmyNaturalPhaseEvent12004 &e) {
  out += "{\"clock_identity\":"; Number(out, e.clock_identity);
  out += ",\"sequence\":"; Number(out, e.sequence);
  out += ",\"thread_id\":"; Optional(out, e.thread_id); out += '}';
}
inline void Snapshot(std::string &out, const ArmyAssaultReleaseVectorSnapshot12004 &v) {
  out += "{\"data_address\":"; Optional(out, v.data_address);
  out += ",\"count_raw_i32\":"; Optional(out, v.count_raw_i32);
  out += ",\"capacity_raw_i32\":"; Optional(out, v.capacity_raw_i32);
  out += ",\"allocator_address\":"; Optional(out, v.allocator_address);
  out += ",\"allocator_matches_expected\":";
  if (v.allocator_matches_expected) Boolean(out, *v.allocator_matches_expected); else out += "null";
  out += ",\"expected_allocator_rva_u32\":"; Number(out, v.expected_allocator_rva_u32);
  out += ",\"payload_complete\":"; Boolean(out, v.payload_complete);
  out += ",\"payload_count\":"; Number(out, v.payload_count);
  out += ",\"raw_full_ids_u32\":[";
  for (std::size_t i = 0; i < v.payload_count; ++i) { if (i) out += ','; Number(out, v.raw_full_ids_u32[i]); }
  out += "]}";
}
} // namespace army_assault_release_json_12004

inline void AppendArmyAssaultGroupReleaseObservations12004(
    std::string &out, const ArmyAssaultGroupReleaseObservations12004 &journal) {
  using namespace army_assault_release_json_12004;
  out += "{\"schema_version\":1,\"source_contract_game_version\":\"1.20.0.4\","
      "\"source_executable_sha256\":\"98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518\","
      "\"source_release_rva\":10293744,\"source\":\"native_natural_assault_record_entry_return\","
      "\"membership_basis\":\"raw_group_armies_at_release_entry\",\"observer_installed\":";
  Boolean(out, journal.observer_installed);
  out += ",\"current_session_guard\":"; Boolean(out, journal.current_session_guard);
  out += ",\"oldest_available_sequence\":"; Number(out, journal.oldest_available_sequence);
  out += ",\"latest_sequence\":"; Number(out, journal.latest_sequence);
  out += ",\"overwritten_events\":"; Number(out, journal.overwritten_events);
  out += ",\"unattributed_capture_failures\":"; Number(out, journal.unattributed_capture_failures);
  out += ",\"ignored_noncanonical_receivers\":"; Number(out, journal.ignored_noncanonical_receivers);
  out += ",\"event_count\":"; Number(out, journal.events.size()); out += ",\"events\":[";
  bool first = true;
  for (const auto &e : journal.events) {
    if (!first) out += ','; first = false;
    out += "{\"sequence\":"; Number(out, e.sequence);
    out += ",\"entry_event\":"; Event(out, e.entry_event);
    out += ",\"returned_event\":"; Event(out, e.returned_event);
    out += ",\"thread_id\":"; Number(out, e.thread_id);
    out += ",\"consumer_entry_event\":"; Event(out, e.parent.entry_event);
    out += ",\"natural_parent_entry_event\":"; Event(out, e.parent.phase_entry_event);
    out += ",\"exact_post_date_parent\":"; Boolean(out, e.parent.exact_post_date_parent);
    out += ",\"primary_manager_address\":"; Number(out, e.parent.manager_identity);
    out += ",\"source_consumer_rva\":"; Number(out, e.parent.actual_entry_rva);
    out += ",\"consumer_caller_return_rva\":"; Optional(out, e.parent.caller_return_rva);
    out += ",\"passed_date_raw64\":"; Optional(out, e.parent.date_raw);
    out += ",\"absolute_day_raw\":"; Optional(out, e.parent.absolute_day_raw);
    out += ",\"caller_return_rva\":"; Number(out, e.caller_return_rva);
    out += ",\"callsite_rva\":"; Number(out, e.callsite_rva);
    out += ",\"record_plus10_address\":"; Number(out, e.record_plus10_address);
    out += ",\"entries_address\":"; Optional(out, e.entries_address);
    out += ",\"physical_slot\":"; Optional(out, e.physical_slot);
    out += ",\"control_before\":"; Optional(out, e.control_before);
    out += ",\"control_at_record_return\":"; Optional(out, e.control_at_record_return);
    out += ",\"occupied_count_before\":"; Optional(out, e.occupied_count_before);
    out += ",\"occupied_count_at_record_return\":"; Optional(out, e.occupied_count_at_record_return);
    out += ",\"arrgs_before\":"; army_assault_release_json_12004::Snapshot(out, e.arrgs_before);
    out += ",\"armies_before\":"; army_assault_release_json_12004::Snapshot(out, e.armies_before);
    out += ",\"arrgs_after\":"; army_assault_release_json_12004::Snapshot(out, e.arrgs_after);
    out += ",\"armies_after\":"; army_assault_release_json_12004::Snapshot(out, e.armies_after);
    out += ",\"original_returned\":"; Boolean(out, e.original_returned);
    out += ",\"original_rax_raw_u64\":"; Number(out, e.original_rax_raw_u64);
    out += ",\"same_parent_at_return\":"; Boolean(out, e.same_parent_at_return);
    out += ",\"same_clock_thread_order\":";
    if (e.same_clock_thread_order) Boolean(out, *e.same_clock_thread_order); else out += "null";
    out += ",\"capture_failure_flags\":"; Number(out, e.capture_failure_flags);
    out += ",\"post_stage\":\"after_record_return_before_caller_bookkeeping\",\"actual\":";
    Boolean(out, journal.observer_installed && journal.current_session_guard); out += '}';
  }
  out += "]}";
}
} // namespace xar::game
