#pragma once

#include "xar_bridge/ck3_12003_title_laws_leaf.hpp"

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

// SOURCEONLY additive candidate. The private default-OFF mailbox owns the
// application-main thread and current expected snapshot revision before/after.
// No caller-supplied TitleID, command execution, ownership-variable inference,
// registration, process discovery or public provider belongs to this reader.
namespace xar::ck3_12003::religious_title {

inline constexpr std::uintptr_t kCurrentCharacterFaithGetterRva = 0x289E750;
inline constexpr std::uintptr_t kCurrentFaithHeadGetterRva = 0x2439E10;
inline constexpr std::uintptr_t kCurrentFaithHeadTitleGetterRva = 0x2443FA0;
inline constexpr std::uintptr_t kCurrentTitleFallbackSlotRva = 0x5D1DAE0;
inline constexpr std::uintptr_t kCurrentFaithFallbackSlotRva = 0x5D1E2E0;
inline constexpr std::size_t kFaithReferenceIdentityOffset = 0x08;
inline constexpr std::size_t kFaithHeadTitleIdOffset = 0x300;
using ObjectGetter = void *(*)(void *);

struct Bindings {
  bool enabled = false;
  title_properties::Bindings properties{};
  void **title_fallback_slot = nullptr;
  void **faith_fallback_slot = nullptr;
  ObjectGetter character_faith = nullptr;
  ObjectGetter faith_head = nullptr;
  ObjectGetter faith_head_title = nullptr;
};

struct Observation {
  bool available = false;
  std::string unavailable_reason = "not_read";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  bool graph_available = false;
  std::string graph_unavailable_reason = "not_read";
  std::optional<bool> legal_head_title_absent;
  std::optional<std::uint32_t> faith_full_id;
  std::optional<std::uint32_t> head_title_full_id;
  std::optional<std::uint32_t> native_title_holder_full_id;
  std::optional<bool> native_title_holder_absent;
  std::optional<std::string> native_title_class;
  // The independent native full-generation graph above is authoritative.
  // The pre-existing political liege reader has a signed TitleID limitation;
  // its unavailable subrow does not erase a qualified high-generation graph.
  game::TitleHolderV1 title_holder{};
  title_properties::Observation title_properties{};
  title_laws::Observation title_laws{};
};

Bindings BindImage(std::uintptr_t image_base,
                   std::string_view exact_current_sha256) noexcept;
bool Read(const Bindings &bindings, const game::Snapshot &paused_frame,
          std::uint64_t capture_epoch, Observation &output) noexcept;
std::string Serialize(const Observation &observation);

} // namespace xar::ck3_12003::religious_title
