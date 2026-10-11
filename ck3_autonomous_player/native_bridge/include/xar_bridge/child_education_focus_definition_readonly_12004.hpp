#pragma once

#include "xar_bridge/ck3_12004_lifestyle.hpp"

#include <cstdint>
#include <optional>
#include <string_view>

namespace xar::ck3_12004::education {

struct ChildEducationFocusDefinitionReadAccess12004 {
  void *context = nullptr;
  lifestyle::ReadPlayerLifestyleMemoryV1 read_memory = nullptr;
};

struct ChildEducationFocusDefinitionRawSpan12004 {
  std::uintptr_t data = 0;
  std::int32_t capacity = -1;
  std::int32_t count = -1;

  friend bool operator==(const ChildEducationFocusDefinitionRawSpan12004 &,
                         const ChildEducationFocusDefinitionRawSpan12004 &) =
      default;
};

enum class ChildEducationFocusDefinitionStatus12004 : std::uint8_t {
  unavailable,
  missing,
  ambiguous,
  resolved,
};

struct ChildEducationFocusDefinitionRead12004 {
  bool available = false;
  ChildEducationFocusDefinitionStatus12004 status =
      ChildEducationFocusDefinitionStatus12004::unavailable;
  std::string_view unavailable_reason = "not_read";
  game::PlayerLifestyleStableKeyV1 requested_key{};
  // These identities belong to the caller's current paused native frame.
  // They must never be serialized, retained for another query, or dispatched
  // after that frame ends. This lookup grants no native selection legality.
  std::uintptr_t definition_identity = 0;
  std::uintptr_t database_identity = 0;
  ChildEducationFocusDefinitionRawSpan12004 rawspan{};
  std::uint32_t match_count = 0;
  std::optional<std::uint32_t> uniqueindex{};
  bool table_stable = false;
};

// The outer native host owns actual child/controller identity, pause/main
// thread qualification and the frame lifetime. The leaf only reads the exact
// build's general FocusDB; it imposes no selected-lifestyle or age policy.
ChildEducationFocusDefinitionRead12004
ReadChildEducationFocusDefinitionReadonly12004(
    const ChildEducationFocusDefinitionReadAccess12004 &access,
    std::uintptr_t module_base, bool exact_build_admitted,
    std::string_view admitted_executable_sha256,
    std::string_view requested_key) noexcept;

} // namespace xar::ck3_12004::education
