#include "xar_bridge/ck3_12002_family_obligations_break.hpp"

#include <cstring>

namespace xar::ck3_12002 {
namespace {
template <typename T> T Load(const void *base, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(T));
  return value;
}
bool SameFrame(const CoreSnapshotPrefix &a, const CoreSnapshotPrefix &b) noexcept {
  return a.clock.date_raw == b.clock.date_raw && a.clock.paused == b.clock.paused &&
      a.clock.speed == b.clock.speed && a.local_player_id == b.local_player_id &&
      a.map_ready == b.map_ready && a.has_played_character == b.has_played_character &&
      a.played_character_id == b.played_character_id && a.played_character_alive == b.played_character_alive;
}
bool Frame(const FamilyObligationsBreakBindingsV1 &b, CoreSnapshotPrefix &out) noexcept {
  return b.enabled && b.interaction.enabled && ReadCoreSnapshot(b.interaction.core, out) &&
      out.clock.paused && out.map_ready && out.has_played_character && out.played_character_alive;
}
void *Alive(const FamilyObligationsBreakBindingsV1 &b, std::int32_t id) noexcept {
  void *character = ResolveCoreCharacter(b.interaction.core, id);
  return id > 0 && character != nullptr &&
      Load<void *>(character, kCharacterDeathDataOffset) == nullptr ? character : nullptr;
}
std::int32_t Betrothed(const void *character) noexcept {
  const void *family = Load<void *>(character, kMarriageCharacterFamilyDataOffset);
  if (family == nullptr) return -1;
  const auto id = Load<std::int32_t>(family, 0x10);
  return id == 0 ? -1 : id;
}
bool DefinitionIdentity(const void *definition, std::uint32_t hash, std::int32_t &ordinal) noexcept {
  if (definition == nullptr || Load<std::uint32_t>(definition, kFamilyBreakDefinitionKindOffsetV1) !=
      kFamilyBreakDefinitionKindV1 || Load<std::uint32_t>(definition, kFamilyBreakDefinitionHashOffsetV1) != hash)
    return false;
  const auto length = Load<std::size_t>(definition, kFamilyBreakDefinitionKeyOffsetV1 + 0x10);
  const auto capacity = Load<std::size_t>(definition, kFamilyBreakDefinitionKeyOffsetV1 + 0x18);
  if (length != kFamilyBreakDefinitionKeyV1.size() || capacity < length) return false;
  const auto *key = capacity > 15 ? Load<const char *>(definition, kFamilyBreakDefinitionKeyOffsetV1) :
      reinterpret_cast<const char *>(static_cast<const std::byte *>(definition) + kFamilyBreakDefinitionKeyOffsetV1);
  if (key == nullptr || std::string_view(key, length) != kFamilyBreakDefinitionKeyV1) return false;
  ordinal = Load<std::int32_t>(definition, kFamilyBreakDefinitionOrdinalOffsetV1);
  return ordinal >= 0;
}
struct alignas(8) ContextStorage { std::array<std::byte, 0x338> bytes{}; };
struct DestroyContext {
  const ContextBindings &bindings;
  void *context;
  ~DestroyContext() { bindings.destroy(context); }
};
} // namespace

FamilyObligationsBreakBindingsV1 BindFamilyObligationsBreakImageV1(
    std::uintptr_t base, std::string_view sha) noexcept {
  FamilyObligationsBreakBindingsV1 b{};
  b.interaction = BindContextImage(base, sha);
  if (!b.interaction.enabled) return b;
  b.enabled = true;
  b.penalty = family_break_penalty::BindFamilyBreakPenaltyImage(base, sha);
  b.get_database = reinterpret_cast<FamilyBreakDatabaseGetterV1>(base + kFamilyBreakDatabaseGetterRvaV1);
  b.stable_hash = reinterpret_cast<FamilyBreakStableHashV1>(base + kFamilyBreakStableHashRvaV1);
  b.lookup_definition = reinterpret_cast<FamilyBreakLookupDefinitionV1>(base + kFamilyBreakLookupDefinitionRvaV1);
  b.missing_definition_slot = reinterpret_cast<void **>(base + kFamilyBreakMissingDefinitionSlotRvaV1);
  return b;
}

FamilyObligationsBreakTermsV1 ReadFamilyObligationsBreakTermsV1(
    const FamilyObligationsBreakBindingsV1 &b, std::int32_t subject_id, std::int32_t recipient_id) noexcept {
  FamilyObligationsBreakTermsV1 out{};
  out.subject_character_id = subject_id;
  out.requested_recipient_character_id = recipient_id;
  CoreSnapshotPrefix before{}, after{};
  if (!Frame(b, before)) return out;
  out.actor_character_id = before.played_character_id;
  void *subject = Alive(b, subject_id);
  if (subject == nullptr) { out.unavailable_reason = "break_betrothal_subject_unavailable"; return out; }
  const auto partner_id = Betrothed(subject);
  if (partner_id == -1) {
    if (!Frame(b, after) || !SameFrame(before, after) || Betrothed(subject) != -1) return out;
    out.status = FamilyObligationsBreakStatusV1::no_betrothal;
    out.unavailable_reason = {};
    out.outcome_resource_penalty.unavailable_reason = "subject_has_no_betrothal";
    return out;
  }
  out.betrothed_character_id = partner_id;
  void *partner = Alive(b, partner_id);
  if (partner == nullptr || partner_id == subject_id || Betrothed(partner) != subject_id) {
    out.unavailable_reason = "break_betrothal_bilateral_pair_unavailable"; return out;
  }
  if (Alive(b, recipient_id) == nullptr) {
    out.unavailable_reason = "break_betrothal_recipient_unavailable"; return out;
  }
  const auto &c = b.interaction;
  if (b.get_database == nullptr || b.stable_hash == nullptr || b.lookup_definition == nullptr ||
      b.missing_definition_slot == nullptr || c.redirect_roles == nullptr || c.construct_all_roles == nullptr ||
      c.refresh == nullptr || c.finalize == nullptr || c.validate == nullptr || c.destroy == nullptr ||
      c.evaluate_cost == nullptr) return out;
  void *database = b.get_database();
  if (database == nullptr) { out.unavailable_reason = "break_betrothal_definition_database_unavailable"; return out; }
  const auto signed_hash = b.stable_hash(database, kFamilyBreakDefinitionKeyV1.data(),
      static_cast<std::uint32_t>(kFamilyBreakDefinitionKeyV1.size()));
  const auto hash = static_cast<std::uint32_t>(signed_hash);
  void *definition = b.lookup_definition(database, signed_hash);
  if (definition == *b.missing_definition_slot || !DefinitionIdentity(definition, hash, out.definition_ordinal)) {
    out.unavailable_reason = "break_betrothal_definition_unavailable"; return out;
  }
  out.definition_stable_hash = hash;
  auto actor = before.played_character_id;
  auto recipient = recipient_id;
  auto secondary_actor = subject_id, secondary_recipient = partner_id;
  std::int32_t intermediary = -1, sixth_role = -1;
  c.redirect_roles(definition, &actor, &recipient, &secondary_actor, &secondary_recipient, &intermediary, &sixth_role);
  if (actor != before.played_character_id || secondary_actor != subject_id ||
      Alive(b, recipient) == nullptr || (intermediary != -1 && Alive(b, intermediary) == nullptr)) {
    out.unavailable_reason = "break_betrothal_redirect_selected_another_subject"; return out;
  }
  ContextStorage storage{};
  void *context = storage.bytes.data();
  if (c.construct_all_roles(context, definition, actor, recipient, secondary_actor,
      secondary_recipient, intermediary, nullptr) != context) return out;
  DestroyContext destroy{c, context};
  c.refresh(context, true); c.finalize(context);
  out.recipient_character_id = Load<std::int32_t>(context, 0x2DC);
  out.secondary_actor_character_id = Load<std::int32_t>(context, 0x2E0);
  out.secondary_recipient_character_id = Load<std::int32_t>(context, 0x2E4);
  out.intermediary_character_id = Load<std::int32_t>(context, 0x2E8);
  if (Load<void *>(context, 0) != definition || Load<std::int32_t>(context, 0x2D8) != actor ||
      out.recipient_character_id != recipient || out.secondary_actor_character_id != subject_id ||
      out.secondary_recipient_character_id != secondary_recipient || out.intermediary_character_id != intermediary) {
    out.unavailable_reason = "break_betrothal_context_roles_changed"; return out;
  }
  out.complete_can_send = c.validate(context, nullptr);
  out.final_legality_sampled = true;
  c.evaluate_cost(static_cast<const std::byte *>(definition) + 0x40,
      static_cast<const std::byte *>(context) + 8, out.native_send_costs_raw.data());
  out.native_send_costs_available = true;
  family_break_penalty::ReadFamilyBreakPenalty(b.penalty, Alive(b, actor), subject, partner,
      out.outcome_resource_penalty);
  if (!Frame(b, after) || !SameFrame(before, after) || Alive(b, subject_id) != subject ||
      Alive(b, partner_id) != partner || Betrothed(subject) != partner_id || Betrothed(partner) != subject_id) {
    out.final_legality_sampled = out.native_send_costs_available = false;
    out.native_send_costs_raw = {};
    out.outcome_resource_penalty = {};
    out.outcome_resource_penalty.unavailable_reason = "break_betrothal_frame_changed";
    out.unavailable_reason = "break_betrothal_frame_changed"; return out;
  }
  out.status = FamilyObligationsBreakStatusV1::available;
  out.unavailable_reason = {};
  return out;
}

} // namespace xar::ck3_12002
