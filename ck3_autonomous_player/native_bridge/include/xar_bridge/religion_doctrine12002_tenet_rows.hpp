#pragma once

#include "xar_bridge/ck3_12002_religion_context.hpp"

#include <optional>
#include <string>
#include <vector>

namespace xar::ck3_12002::religion::doctrine12002 {
inline constexpr std::uintptr_t kNativeTenetStateRva = 0x24F88A0;
inline constexpr std::size_t kRiteCoreTenetsOffset = 0x758;
inline constexpr std::size_t kRiteTenetStatesOffset = 0x788;
inline constexpr std::size_t kCharacterExtensionOffset = 0x1C8;
inline constexpr std::size_t kPersonalTenetsOffset = 0x88;
inline constexpr std::size_t kTenetDefinitionKeyOffset = 0x18;
using NativeTenetState = std::uint8_t (*)(void *, const void *);
struct TenetRowsBindings {
  bool enabled{};
  NativeTenetState tenet_state{};
};
struct TenetEntry {
  std::string key;
  std::optional<std::uint8_t> current_rite_status;
  bool operator==(const TenetEntry &) const = default;
};
struct RiteCoreTenets {
  std::uint32_t rite_id{};
  std::vector<TenetEntry> core_tenets;
  bool operator==(const RiteCoreTenets &) const = default;
};
struct TenetRowsContext {
  bool available{};
  std::string failure{"bindings_unavailable"};
  std::uint64_t capture_epoch{};
  std::int32_t date_raw{};
  std::uint32_t played_character_id{};
  std::optional<std::uint32_t> faith_id;
  std::optional<RiteCoreTenets> current_rite;
  std::optional<RiteCoreTenets> faith_main_rite;
  std::vector<TenetEntry> personal_tenets;
  std::vector<TenetEntry> effective_tenet_states;
};
TenetRowsBindings BindTenetRows12002(std::uintptr_t module_base,
                                   std::string_view executable_sha) noexcept;
bool ReadPlayedTenetRows12002(const religion::Bindings &religion_bindings,
                             const TenetRowsBindings &tenet_bindings,
                             std::uint64_t capture_epoch,
                             TenetRowsContext &output) noexcept;
std::string SerializeTenetRows12002(const TenetRowsContext &context);
bool CopyTenetDefinitionKey12002(const void *definition, std::string &output);
} // namespace xar::ck3_12002::religion::doctrine12002
