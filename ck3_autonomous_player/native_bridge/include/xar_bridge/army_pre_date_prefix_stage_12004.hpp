#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::ck3_12004::army_pre_date_prefix_stage {

inline constexpr std::string_view kExecutableSha256 =
    "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
inline constexpr std::uintptr_t kSourceCountOffset = 0xD4;

// The receiver is supplied by the existing actual4 primary binder. This leaf
// observes a current conditional entrance only; it never reads an earlier CALL.
using ReadBytes = bool (*)(void *context, std::uintptr_t address,
                          void *destination, std::size_t byte_count);

struct CurrentHeaderFrame {
  std::string executable_sha256;
  std::uintptr_t primary_identity = 0;
  std::optional<std::int32_t> source_count_d4;
  std::string unavailable_reason;
};

enum class Verdict {
  unavailable,
  no_work,
  positive_occurrence_inputs_required,
};

struct ConditionalProjection {
  Verdict verdict = Verdict::unavailable;
  bool source_count_ready = false;
  bool complete_no_work_arm = false;
  bool primary_state_preserved_by_prefix = false;
  // This cannot turn true from a current header observation.
  bool historical_invocation_reconstructed = false;
  std::string unavailable_reason;
};

CurrentHeaderFrame ObserveCurrentHeader(std::string_view executable_sha256,
    std::uintptr_t actual_primary, ReadBytes read_bytes, void *context);

ConditionalProjection ProjectCurrentHeader(const CurrentHeaderFrame &frame);

} // namespace xar::ck3_12004::army_pre_date_prefix_stage
