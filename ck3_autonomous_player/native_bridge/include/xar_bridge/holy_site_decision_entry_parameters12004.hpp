#pragma once
#include "xar_bridge/ck3_12004_holy_site_snapshot.hpp"
#include "xar_bridge/holy_site_decision_action_v1.hpp"
#include <array>

namespace xar::ck3_12004::religion::holy_site {
// CAE7A0 returns its caller-owned row_out address. It changes only row_out.
using CacheLookup = const void **(__fastcall *)(const void *, const void **,
                                               const void *const *);
struct EntryParameterBindings {
  bool enabled = false;
  std::uintptr_t image_base = 0;
  ReadMemory read_memory = nullptr;
  void *read_context = nullptr;
  CacheLookup cache_lookup = nullptr;
  void **holy_site_storage = nullptr;
  const std::uint32_t *selected_item_token = nullptr;
  const std::uint32_t *decision_params_runtime_class_id = nullptr;
};
struct EntryParameterSnapshot {
  bool available = false;
  // True only after both complete identity passes, including selected_item and
  // site storage. A fully verified different fixed key can exclude a sibling
  // button. Every unknown/provider/unstable/ID failure keeps this false.
  bool decision_key_verified = false;
  const void *params = nullptr, *definition = nullptr, *source_widget = nullptr;
  std::string decision_key;
  std::uint32_t holy_site_id = 0xFFFFFFFFU;
  // Preserve the native field without assigning an unclosed semantic mapping.
  std::uint32_t self_return_type_raw = 0;
  std::string unavailable_reason;
};
EntryParameterBindings BindHolySiteDecisionEntryParametersImage12004(
    std::uintptr_t image_base, std::string_view executable_sha256) noexcept;
// actual_button must already be bound by the caller to the owned window/root.
// This reader rechecks the chosen callback group and resolves borrowed input;
// it neither evaluates arbitrary providers nor creates/frees parameter objects.
bool ReadHolySiteDecisionEntryParameters12004(const EntryParameterBindings &,
    const void *actual_button, DecisionAction, std::uint32_t full_site_id,
    EntryParameterSnapshot &) noexcept;

namespace entry_parameters_source {
struct Pin { std::uintptr_t rva; std::string_view hex; };
// Frozen original code from gui-management-source.json and
// decision-params-source.json; fixtures populate these same exact-build pins.
inline constexpr std::array<Pin, 10> kPins{{
 {0x3AA30E0,"488bc1488d5110488b89f000000048ff6008"},
 {0x3A9F960,"48895c2408574883ec50488bfa488bd9e82bd6ddfc48894424200f57c00f1144"},
 {0x3AC38C0,"48895c2408488974241048897c2418554154415541564157488dac24c0feffff"},
 {0x3AC3EF0,"48895c241848895424105556574154415541564157488bec4881ec800000000f"},
 {0x3AC1C00,"40534881ec90000000480fbe414084c00f890201000048894424400f28442440"},
 {0x3E4BC50,"4c89442418488954241048894c2408535657415641574881ec800000004863b1"},
 {0x3E4C090,"48895c240848896c241048897424185741544155415641574883ec504d8be94d"},
 {0xCAB1C0,"40534883ec20488bda48894c2430e88d3800004c8bc0488d542430488bcbe8ad"},
 {0xCAE7A0,"48895c2408410fb6004d8bd835c59d1c81488bd94469c8930100014c8bd2410f"},
 {0xCAE5D0,"4883ec2865488b042558000000ba10000000488b088b040a3905ae1b0a057f0c"},
}};
}
} // namespace xar::ck3_12004::religion::holy_site
