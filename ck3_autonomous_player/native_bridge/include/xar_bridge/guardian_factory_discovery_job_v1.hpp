#pragma once

#include "xar_bridge/ck3_12004_guardian_factory_metadata.hpp"
#include "xar_bridge/game_contract.hpp"
#include "xar_bridge/main_thread_query_mailbox_v1.hpp"

#include <filesystem>
#include <fstream>
#include <optional>
#include <string>
#include <string_view>
#include <utility>

namespace xar::bridge {

using GuardianFactoryDiscoverySnapshotReaderV1 =
    bool (*)(void *, xar::game::Snapshot &) noexcept;

// Private discovery accompanies the existing family query. It does not publish
// a gameplay capability, call a native factory, or observe guardian membership.
struct GuardianFactoryDiscoveryJobV1 {
  xar::game::Snapshot expected_snapshot{};
  xar::ck3_12004::GuardianFactoryReadEnvironment12004V1 environment{};
  std::uintptr_t image_size{};
  std::string executable_sha256;
  std::uint64_t native_revision{};
  std::int32_t heir_character_id{-1};
  std::string request_id;
  void *snapshot_context{};
  GuardianFactoryDiscoverySnapshotReaderV1 read_snapshot{};
  bool executed{};
  bool frame_observed{};
  std::string_view unavailable_reason{"job_not_executed"};
  xar::ck3_11906::MainThreadExecutionStampV1 execution_stamp{};
  std::optional<xar::ck3_12004::GuardianFactoryDiscoveryMetadata12004V1> metadata;
};

// The same executor is called by the production family callback and the fixture.
inline bool ExecuteGuardianFactoryDiscoveryJobV1(
    void *opaque,
    const xar::ck3_11906::MainThreadExecutionStampV1 &stamp) noexcept {
  if (opaque == nullptr) return false;
  auto &job = *static_cast<GuardianFactoryDiscoveryJobV1 *>(opaque);
  job.executed = true;
  job.frame_observed = false;
  job.execution_stamp = stamp;
  job.metadata.reset();
  job.unavailable_reason = "frame_changed";
  if (job.executable_sha256 != xar::ck3_12004::kExecutableSha256) {
    job.unavailable_reason = "exact_build_not_admitted";
    return true;
  }
  if (job.read_snapshot == nullptr) {
    job.unavailable_reason = "snapshot_reader_unavailable";
    return true;
  }
  try {
    xar::game::Snapshot before{};
    if (!stamp.paused || !job.expected_snapshot.paused ||
        stamp.date_raw != job.expected_snapshot.date_raw ||
        !job.read_snapshot(job.snapshot_context, before) ||
        before != job.expected_snapshot) return true;
    auto metadata = xar::ck3_12004::ReadGuardianFactoryDiscoveryMetadata12004V1(
        job.environment, job.image_size);
    xar::game::Snapshot after{};
    if (!job.read_snapshot(job.snapshot_context, after) || after != before)
      return true;
    job.metadata = std::move(metadata);
    job.frame_observed = true;
    job.unavailable_reason = {};
    return true;
  } catch (...) {
    job.metadata.reset();
    job.unavailable_reason = "discovery_exception";
    return false;
  }
}

namespace guardian_factory_job_detail {

inline void String(std::string &output, std::string_view value) {
  constexpr char digits[] = "0123456789abcdef";
  output += '"';
  for (const char character : value) {
    const auto byte = static_cast<unsigned char>(character);
    if (character == '"' || character == '\\') {
      output += '\\';
      output += character;
    } else if (byte < 0x20U) {
      output += "\\u00";
      output += digits[byte >> 4U];
      output += digits[byte & 0x0FU];
    } else {
      output += character;
    }
  }
  output += '"';
}

template <class Value>
inline void OptionalNumber(std::string &output,
                           const std::optional<Value> &value) {
  output += value ? std::to_string(*value) : "null";
}

inline std::string_view Status(
    xar::ck3_12004::ExistingGuardianFactoryStatusV1 value) noexcept {
  using StatusV1 = xar::ck3_12004::ExistingGuardianFactoryStatusV1;
  switch (value) {
  case StatusV1::found: return "found";
  case StatusV1::name_missing: return "name_missing";
  case StatusV1::factory_missing: return "factory_missing";
  default: return "unavailable";
  }
}

inline std::string_view Failure(
    xar::ck3_12004::GuardianFactoryLookupFailureV1 value) noexcept {
  using FailureV1 = xar::ck3_12004::GuardianFactoryLookupFailureV1;
  switch (value) {
  case FailureV1::none: return "";
  case FailureV1::environment_unavailable: return "environment_unavailable";
  case FailureV1::name_pool_unavailable: return "name_pool_unavailable";
  case FailureV1::registry_unavailable: return "registry_unavailable";
  case FailureV1::comparison_branch_unavailable: return "comparison_branch_unavailable";
  case FailureV1::name_map_unreadable: return "name_map_unreadable";
  case FailureV1::name_key_unreadable: return "name_key_unreadable";
  case FailureV1::factory_map_unreadable: return "factory_map_unreadable";
  case FailureV1::factory_record_unreadable: return "factory_record_unreadable";
  }
  return "unavailable";
}

inline std::string Json(const GuardianFactoryDiscoveryJobV1 &job,
                        bool qualified) {
  std::string output =
      "{\"schema\":\"xar.ck3.guardian-factory-discovery.v1\","
      "\"schema_version\":1,\"read_only\":true,\"advertised\":false,"
      "\"source_discovery_only\":true,\"guardian_membership_observed\":false,"
      "\"qualified\":";
  output += qualified ? "true" : "false";
  output += ",\"status\":";
  String(output, qualified ? "captured" : "unavailable");
  output += ",\"unavailable_reason\":";
  String(output, qualified ? std::string_view{} :
      (job.frame_observed ? std::string_view{"completion_frame_changed"}
                          : job.unavailable_reason));
  output += ",\"request_id\":";
  String(output, job.request_id);
  output += ",\"native_revision\":" + std::to_string(job.native_revision);
  output += ",\"heir_character_id\":" + std::to_string(job.heir_character_id);
  output += ",\"executable_sha256\":";
  String(output, job.executable_sha256);
  output += ",\"module_base\":" + std::to_string(job.environment.module_base);
  output += ",\"image_size\":" + std::to_string(job.image_size);
  output += ",\"date_raw\":" + std::to_string(job.expected_snapshot.date_raw);
  output += ",\"played_character_id\":" +
      std::to_string(job.expected_snapshot.played_character_id);
  output += ",\"paused\":";
  output += job.expected_snapshot.paused ? "true" : "false";
  output += ",\"pump_epoch\":" + std::to_string(job.execution_stamp.pump_epoch);
  output += ",\"thread_id\":" + std::to_string(job.execution_stamp.thread_id);
  output += ",\"factories\":[";
  for (std::size_t index = 0; index < xar::ck3_12004::kGuardianTriggerKeysV1.size();
       ++index) {
    if (index != 0) output += ',';
    const xar::ck3_12004::GuardianFactoryTypedMetadata12004V1 empty{};
    const auto &typed = qualified ? job.metadata->factories[index] : empty;
    const auto &lookup = typed.lookup;
    output += "{\"key\":";
    String(output, xar::ck3_12004::kGuardianTriggerKeysV1[index]);
    output += ",\"status\":";
    String(output, Status(lookup.status));
    output += ",\"unavailable_reason\":";
    String(output, qualified ? Failure(lookup.failure) :
        (job.frame_observed ? std::string_view{"completion_frame_changed"}
                            : job.unavailable_reason));
    output += ",\"stored_name\":";
    if (lookup.matched_stored_key_size != 0)
      String(output, {lookup.matched_stored_key.data(), lookup.matched_stored_key_size});
    else output += "null";
    output += ",\"name_id\":"; OptionalNumber(output, lookup.name_id);
    output += ",\"map_name_id\":"; OptionalNumber(output, lookup.map_name_id);
    output += ",\"record_name_id\":"; OptionalNumber(output, lookup.record_name_id);
    output += ",\"factory_address\":" + std::to_string(lookup.factory_address);
    output += ",\"vtable_address\":" + std::to_string(lookup.vtable_address);
    output += ",\"opaque_descriptor_address\":" + std::to_string(lookup.descriptor_address);
    output += ",\"virtual_slots\":[";
    for (std::size_t slot = 0; slot < typed.virtual_slots.size(); ++slot) {
      if (slot != 0) output += ',';
      const auto &value = typed.virtual_slots[slot];
      output += "{\"slot_index\":" + std::to_string(slot) + ",\"available\":";
      output += value.available ? "true" : "false";
      output += ",\"address\":";
      output += value.available ? std::to_string(value.address) : "null";
      output += ",\"rva\":"; OptionalNumber(output, value.rva);
      output += '}';
    }
    const auto &rtti = typed.rtti;
    output += "],\"rtti\":{\"col_pointer_available\":";
    output += rtti.col_pointer_available ? "true" : "false";
    output += ",\"col_address\":" + std::to_string(rtti.col_address);
    output += ",\"col_fields_available\":";
    output += rtti.col_fields_available ? "true" : "false";
    output += ",\"col_fields\":";
    if (rtti.col_fields_available) {
      output += '[';
      for (std::size_t field = 0; field < rtti.col_fields.size(); ++field) {
        if (field != 0) output += ',';
        output += std::to_string(rtti.col_fields[field]);
      }
      output += ']';
    } else output += "null";
    output += ",\"type_descriptor_address\":";
    OptionalNumber(output, rtti.type_descriptor_address);
    output += ",\"type_name_available\":";
    output += rtti.type_name_available ? "true" : "false";
    output += ",\"type_name\":";
    if (rtti.type_name_available) String(output, rtti.type_name);
    else output += "null";
    output += ",\"type_name_truncated\":";
    output += rtti.type_name_truncated ? "true" : "false";
    output += ",\"unavailable_reason\":";
    String(output, rtti.unavailable_reason);
    output += "}}";
  }
  output += "]}\n";
  return output;
}

} // namespace guardian_factory_job_detail

// Private export stages remain independent of the normal family observation.
struct GuardianFactoryDiscoveryExportV1 {
  bool requested{};
  bool path_parsed{};
  bool job_created{};
  bool job_reclaimed{};
  bool job_executed{};
  bool job_frame_observed{};
  bool metadata_copied{};
  bool completion_attempted{};
  bool sidecar_written{};
  std::string error;
};

inline std::string AppendGuardianFactoryDiscoveryExportV1(
    std::string frame, const GuardianFactoryDiscoveryExportV1 &value) {
  if (!value.requested || frame.empty() || frame.back() != '}') return frame;
  frame.pop_back();
  frame += ",\"guardian_factory_discovery_v1\":{\"schema_version\":1";
  const auto flag = [&frame](std::string_view key, bool observed) {
    frame += ',';
    guardian_factory_job_detail::String(frame, key);
    frame += observed ? ":true" : ":false";
  };
  flag("path_parsed", value.path_parsed);
  flag("job_created", value.job_created);
  flag("job_reclaimed", value.job_reclaimed);
  flag("job_executed", value.job_executed);
  flag("job_frame_observed", value.job_frame_observed);
  flag("metadata_copied", value.metadata_copied);
  flag("completion_attempted", value.completion_attempted);
  flag("sidecar_written", value.sidecar_written);
  frame += ",\"error\":";
  if (value.error.empty()) frame += "null";
  else guardian_factory_job_detail::String(frame, value.error);
  frame += "}}";
  return frame;
}

// Worker-only completion, after mailbox reclaim and the family's outer snapshot
// comparison. A written unavailable sidecar is not a qualified paused capture.
inline bool CompleteGuardianFactoryDiscoveryJobV1(
    const GuardianFactoryDiscoveryJobV1 &job,
    const xar::game::Snapshot &completion_snapshot,
    const std::filesystem::path &sidecar_path, std::string &error) noexcept {
  error.clear();
  try {
    const bool qualified = job.executed && job.frame_observed &&
        job.metadata.has_value() && completion_snapshot == job.expected_snapshot;
    const auto json = guardian_factory_job_detail::Json(job, qualified);
    std::ofstream output(sidecar_path, std::ios::binary | std::ios::trunc);
    if (!output) {
      error = "guardian_factory_sidecar_open_failed";
      return false;
    }
    output.write(json.data(), static_cast<std::streamsize>(json.size()));
    output.flush();
    if (!output) {
      error = "guardian_factory_sidecar_write_failed";
      return false;
    }
    return true;
  } catch (...) {
    error = "guardian_factory_sidecar_exception";
    return false;
  }
}

} // namespace xar::bridge
