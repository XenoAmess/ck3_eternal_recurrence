#pragma once

#include "xar_bridge/construction_owner_mode3_raw_receiver_12004.hpp"
#include "xar_bridge/piety_price_evaluator_1233a40_readonly_12004.hpp"
#include "xar_bridge/piety_price_numeric_access_12004.hpp"

#include <cstdint>
#include <optional>
#include <string>

namespace xar::ck3_12004::piety_price_raw_inputs {

using Numeric31D9930Bindings12004 = PietyPriceNumericAccess12004;

struct Numeric31D9930Observation12004 {
  bool source_ready = false;
  const char *status = "unavailable";
  std::string reason;
  std::optional<std::int32_t> native_eax_raw;
  std::uintptr_t definition_pointer = 0;
  std::uintptr_t current_rite_pointer = 0;
  std::uint64_t frame_key = 0;
  std::uint32_t source_rva = 0x31D9930;
  const char *source_pin =
      "73f026b43bd7ba74cb7f3ea915c281f247b955cbd978cd9f1262bea6c2e77d8b";
  std::optional<std::uintptr_t> selected_expression_identity;
  std::optional<PietyPriceEvaluator1233A40Readonly12004> evaluator;
  bool actual_original_consumed_values = false;
};

// Actual31D9945 selects definition+760; CALL31D99C5 receives that exact
// expression. The numeric child result is saved in EBX and returned unchanged.
// Mode0 numerical demand bypasses context/name/frame construction. Dynamic
// paths retain the unique evaluator's concrete unavailable frontier.
Numeric31D9930Observation12004 ReadPietyPriceNumeric31D993012004(
    const Numeric31D9930Bindings12004 &bindings,
    std::uintptr_t definition_pointer,
    std::uintptr_t current_rite_pointer,
    std::uint64_t unchanged_snapshot_revision) noexcept;

// Adapter for the existing edit parent's readonly scalar seam. The caller's
// access and full revision are retained; out changes only when EAX is available.
bool ReadPietyPriceNumeric31D9930Adapter12004(
    void *unused_context,
    const construction_owner_mode3::RawReceiverAccessV1 &access,
    std::uintptr_t definition_pointer,
    std::uintptr_t current_rite_pointer,
    std::uint64_t unchanged_snapshot_revision,
    std::int32_t &out) noexcept;

} // namespace xar::ck3_12004::piety_price_raw_inputs
