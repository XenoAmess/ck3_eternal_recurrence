#pragma once

#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/ck3_12003_title_holder.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string_view>

// SOURCEONLY candidate, never compiled or installed by its author.
// This leaf must run inside ROOT's existing application-main read-only mailbox.
// The mailbox owns current snapshot revision/epoch and independently checks the
// actual Faith head-title/holder graph and seven political Title holders.
namespace xar::ck3_12003::title_properties {

inline constexpr std::uintptr_t kCLandedTitlePrimaryVtableRva = 0x4712A18;
inline constexpr std::size_t kTitleFullIdOffset = 0x10;
inline constexpr std::size_t kNativeDefinitiveFormOffset = 0x2C;
inline constexpr std::size_t kNativeDestroyIfInvalidHeirOffset = 0x34;
inline constexpr std::size_t kNativeNoAutomaticClaimsOffset = 0x38;
inline constexpr std::size_t kNativeAlwaysFollowsPrimaryHeirOffset = 0x39;

struct Bindings {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  TitleHolderBindingsV1 title_holder;
};

struct Observation {
  bool available = false;
  std::string_view unavailable_reason = "not_read";
  std::int32_t date_raw = 0;
  std::int32_t actor_character_id = -1;
  std::uint32_t requested_title_full_id = UINT32_MAX;
  std::optional<bool> destroy_if_invalid_heir;
  std::optional<bool> no_automatic_claims;
  std::optional<bool> definitive_form;
  std::optional<bool> always_follows_primary_heir;
  // Succession-law membership is deliberately outside this leaf. No absent
  // address, incomplete collection or unqualified saved path becomes false.
};

Bindings BindImage(std::uintptr_t image_base,
                   std::string_view executable_sha256) noexcept;
bool Read(const Bindings &bindings, const game::Snapshot &paused_frame,
          std::uint32_t requested_title_full_id, Observation &output) noexcept;

} // namespace xar::ck3_12003::title_properties
