#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace xar::ck3_12003::religion::holy_order {

inline constexpr std::string_view kExecutableSha256 =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";
inline constexpr std::string_view kSchema = "ck3_12003_player_holy_order_context_v1";
inline constexpr std::int64_t kRawScale = 100000;

using Patron = void *(*)(void *);
using IsMilitary = bool (*)(void *);
using CanHire = bool (*)(void *, void *, void *);
using Cost = std::int64_t *(*)(void *, std::int64_t *, void *);
using CanAfford = bool (*)(const std::int64_t *, void *, void *);
using ReasonDestroy = void (*)(void *);

struct Bindings {
  bool enabled = false;
  void **manager_slot = nullptr;
  void **fallback_slot = nullptr;
  Patron patron = nullptr;
  IsMilitary is_military = nullptr;
  CanHire can_hire = nullptr;
  Cost cost = nullptr;
  CanAfford can_afford = nullptr;
  ReasonDestroy reason_destroy = nullptr;
};

struct MilitaryTerms {
  bool available = false;
  std::string unavailable_reason = "not_sampled";
  std::optional<bool> can_hire;
  std::optional<bool> can_afford;
  // Native order: gold, prestige, piety, renown, influence, herd,
  // treasury, treasury_or_gold, merit, barter_goods.
  std::optional<std::array<std::int64_t, 10>> resource_costs_raw;
  bool can_hire_reasons_available = false;
  std::optional<std::string> can_hire_reason_literal;
  bool can_afford_reasons_available = false;
  std::optional<std::string> can_afford_reason_literal;
};
struct Row {
  std::uint32_t holy_order_id = UINT32_MAX;
  std::uint32_t rite_id = UINT32_MAX;
  bool is_military = false;
  std::optional<std::uint32_t> founder_id;
  std::optional<std::uint32_t> patron_id;
  std::optional<std::uint32_t> employer_id;
  std::vector<std::uint32_t> leased_title_ids;
  // Nonmilitary organisations have no hire terms; JSON emits null.
  std::optional<MilitaryTerms> military_terms;
};
struct Context {
  bool available = false;
  std::string unavailable_reason = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::vector<Row> rows;
};

Bindings BindPlayerHolyOrderImage12003(std::uintptr_t module_base,
    std::string_view executable_sha256) noexcept;
// Existing paused application-main owner supplies the player and frame.
// Manager objects and native getters are read only. Only copied values escape.
bool ReadPlayerHolyOrderContext12003(const Bindings &, void *played_character,
    std::int32_t played_character_id, std::int32_t date_raw,
    std::uint64_t capture_epoch, Context &) noexcept;
std::string SerializePlayerHolyOrderContext12003(const Context &);

} // namespace xar::ck3_12003::religion::holy_order
