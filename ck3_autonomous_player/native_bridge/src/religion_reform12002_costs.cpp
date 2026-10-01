#include "xar_bridge/religion_reform12002_costs.hpp"

#include <cstring>

namespace xar::ck3_12002::religion_reform {
namespace {
template <typename T> T Load(const void *p, std::size_t offset) noexcept {
  T v{};
  std::memcpy(&v, static_cast<const std::byte *>(p) + offset, sizeof(v));
  return v;
}

CostFailure ReadOnce(const CostBindings &b, const CurrentDraftView &v,
                     CostQuote &out) noexcept {
  if (!v.window) return CostFailure::draft_unavailable;
  const auto actor = Load<std::int32_t>(v.window, kRiteCreationActorOffset);
  if (actor != v.played_character_id || actor == -1)
    return CostFailure::draft_actor_mismatch;
  const auto rite = Load<std::uint32_t>(v.window, kRiteCreationSourceRiteOffset);
  const auto editing = b.editing_owned_current_rite(v.window);
  std::int64_t price{}, missing{};
  if (b.piety_cost(v.window, &price) != &price ||
      b.piety_missing(v.window, &missing) != &missing)
    return CostFailure::native_quote_unavailable;
  if (Load<std::int32_t>(v.window, kRiteCreationActorOffset) != actor ||
      Load<std::uint32_t>(v.window, kRiteCreationSourceRiteOffset) != rite)
    return CostFailure::quote_changed;
  out.capture_epoch = v.capture_epoch;
  out.date_raw = v.date_raw;
  out.played_character_id = actor;
  if (rite != 0xFFFFFFFFU) out.source_rite_id = rite;
  out.editing_owned_current_rite = editing;
  out.piety_cost_raw = price;
  out.piety_missing_signed_raw = missing;
  out.has_enough_piety = missing <= 0;
  out.available = true;
  out.failure = CostFailure::none;
  return CostFailure::none;
}

template <typename T> std::string Number(const std::optional<T> &v) {
  return v ? std::to_string(*v) : "null";
}
std::string Boolean(const std::optional<bool> &v) {
  return v ? (*v ? "true" : "false") : "null";
}
} // namespace

CostBindings BindRiteCreationCostsImage12002(std::uintptr_t base,
                                            std::string_view sha) noexcept {
  CostBindings b{};
  if (!base || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.piety_cost = reinterpret_cast<WindowFixedGetter>(base + kRiteCreationPietyCostRva);
  b.piety_missing = reinterpret_cast<WindowFixedGetter>(base + kRiteCreationPietyMissingRva);
  b.editing_owned_current_rite = reinterpret_cast<WindowBoolGetter>(base + kRiteCreationEditOwnedRiteRva);
  return b;
}

bool ReadCurrentRiteCreationCosts12002(const CostBindings &b,
                                     const CurrentDraftView &v,
                                     CostQuote &out) noexcept {
  out = {};
  out.capture_epoch = v.capture_epoch;
  out.date_raw = v.date_raw;
  out.played_character_id = v.played_character_id;
  if (!b.enabled || !b.piety_cost || !b.piety_missing ||
      !b.editing_owned_current_rite) return false;
  CostQuote first{}, second{};
  auto failure = ReadOnce(b, v, first);
  if (failure == CostFailure::none) failure = ReadOnce(b, v, second);
  if (failure == CostFailure::none &&
      (first.source_rite_id != second.source_rite_id ||
       first.editing_owned_current_rite != second.editing_owned_current_rite ||
       first.piety_cost_raw != second.piety_cost_raw ||
       first.piety_missing_signed_raw != second.piety_missing_signed_raw))
    failure = CostFailure::quote_changed;
  if (failure != CostFailure::none) { out.failure = failure; return false; }
  out = first;
  return true;
}

const char *RiteCreationCostFailureKey(CostFailure f) noexcept {
  switch (f) {
  case CostFailure::none: return "none";
  case CostFailure::bindings_unavailable: return "bindings_unavailable";
  case CostFailure::draft_unavailable: return "draft_unavailable";
  case CostFailure::draft_actor_mismatch: return "draft_actor_mismatch";
  case CostFailure::native_quote_unavailable: return "native_quote_unavailable";
  case CostFailure::quote_changed: return "quote_changed";
  }
  return "bindings_unavailable";
}

std::string SerializeCurrentRiteCreationCosts12002(const CostQuote &q) {
  return "{\"schema\":\"ck3_12002_rite_creation_costs_v1\","
      "\"game_version\":\"1.20.0.2\",\"executable_sha256\":\"" +
      std::string(kExecutableSha256) + "\",\"available\":" +
      (q.available ? "true" : "false") + ",\"unavailable_reason\":" +
      (q.available ? std::string("null") :
       "\"" + std::string(RiteCreationCostFailureKey(q.failure)) + "\"") +
      ",\"capture_epoch\":" + std::to_string(q.capture_epoch) +
      ",\"date_raw\":" + std::to_string(q.date_raw) +
      ",\"played_character_id\":" + std::to_string(q.played_character_id) +
      ",\"source_rite_id\":" + Number(q.source_rite_id) +
      ",\"editing_owned_current_rite\":" + Boolean(q.editing_owned_current_rite) +
      ",\"piety_cost_raw\":" + Number(q.piety_cost_raw) +
      ",\"piety_missing_signed_raw\":" + Number(q.piety_missing_signed_raw) +
      ",\"has_enough_piety\":" + Boolean(q.has_enough_piety) +
      ",\"raw_scale\":100000,\"final_creation_legality_observed\":false,"
      "\"other_resource_costs_observed\":false}";
}
} // namespace xar::ck3_12002::religion_reform
