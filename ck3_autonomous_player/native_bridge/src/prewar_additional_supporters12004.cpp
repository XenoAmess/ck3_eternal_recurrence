#include "xar_bridge/prewar_additional_supporters12004.hpp"

#include "xar_bridge/ck3_12004_religion_adopted_observers.hpp"
#include "xar_bridge/ck3_12004_religion_bindings.hpp"

#include <algorithm>
#include <cstring>
#include <limits>
#if defined(_MSC_VER)
#include <windows.h>
#endif

namespace xar::ck3_12004 {
namespace {
constexpr std::int32_t kMaximumSlots = 1'048'576;
constexpr std::int32_t kMaximumContracts = 4096;

bool Copy(const void *source, void *target, std::size_t size) noexcept {
  if (!source) return false;
#if defined(_MSC_VER)
  __try { std::memcpy(target, source, size); return true; }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  std::memcpy(target, source, size); return true;
#endif
}
template <typename T> bool Read(const void *base, std::size_t offset, T &value) noexcept {
  const auto address = reinterpret_cast<std::uintptr_t>(base);
  return base && offset <= (std::numeric_limits<std::uintptr_t>::max)() - address &&
      Copy(reinterpret_cast<const void *>(address + offset), &value, sizeof(value));
}
bool Getter(PrewarAdditionalObjectGetter12004 getter, void *input, void *&out) noexcept {
  out = nullptr;
  if (!getter || !input) return false;
#if defined(_MSC_VER)
  __try { out = getter(input); return true; }
  __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#else
  out = getter(input); return true;
#endif
}
void Reason(PrewarAdditionalSupportersSnapshot12004 &out, std::string_view value) noexcept {
  if (out.reason.empty()) out.reason = value;
}
bool Identity(const PrewarAdditionalSupportersBindings12004 &b, const void *p,
              std::int32_t &id, bool &alive) noexcept {
  const void *death = nullptr;
  id = -1; alive = false;
  if (!Read(p, kCharacterFullIdOffset, id) || id == -1 ||
      xar::ck3_12004::ResolveCoreCharacter(b.core, id) != p ||
      !Read(p, kCharacterDeathDataOffset, death)) return false;
  alive = death == nullptr;
  return true;
}
void Append(PrewarAdditionalSupportersSnapshot12004 &out, std::int32_t root,
            std::int32_t id, PrewarAdditionalSupportSource12004 source) {
  const PrewarAdditionalSupporter12004 row{root, id, source};
  if (id != root && std::find(out.candidates.begin(), out.candidates.end(), row) == out.candidates.end())
    out.candidates.push_back(row);
}
bool Neighbor(const PrewarAdditionalSupportersBindings12004 &b, void *root,
              std::int32_t root_id, PrewarAdditionalObjectGetter12004 getter,
              PrewarAdditionalSupportSource12004 source,
              PrewarAdditionalSupportersSnapshot12004 &out) {
  void *p = nullptr, *fallback = nullptr;
  if (!Getter(getter, root, p) || !Read(b.character_fallback_slot, 0, fallback)) return false;
  if (!p || p == fallback || p == root) return true;
  std::int32_t id = -1; bool alive = false;
  if (!Identity(b, p, id, alive)) {
    if (id != -1) out.unresolved_source_character_ids.push_back(id);
    return false;
  }
  if (alive) Append(out, root_id, id, source);
  else out.dead_source_character_ids.push_back(id);
  return true;
}
void *ResolveContract(const PrewarAdditionalSupportersBindings12004 &b,
                      std::int32_t id) noexcept {
  void *storage = nullptr, *slots = nullptr, *p = nullptr, *fallback = nullptr;
  std::int32_t capacity = 0, actual = -1;
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  if (id == -1 || !Read(b.subject_contract_storage_slot, 0, storage) ||
      !Read(storage, 0x2C, capacity) || capacity < 0 || capacity > kMaximumSlots ||
      index >= static_cast<std::uint32_t>(capacity) || !Read(storage, 0x20, slots) ||
      !Read(slots, static_cast<std::size_t>(index) * 16 + 8, p) ||
      !Read(b.subject_contract_fallback_slot, 0, fallback) || p == fallback ||
      !Read(p, 8, actual) || actual != id) return nullptr;
  return p;
}
void InitialBranchInputs(const PrewarAdditionalSupportersBindings12004 &b,
                         const PrewarAdditionalSupportersNativeScope12004 &scope,
                         PrewarAdditionalSupportersSnapshot12004 &out) noexcept {
  // Actual builder 2A7F431/43F passes the embedded CB+870 receiver to3765760.
  // Actual492E2E0+B0 is3766300; its complete71B body skips all child calls
  // for signed count+3C==0. A zero constructor store alone is not proof.
  const void *vtable = nullptr, *execute = nullptr, *child_data = nullptr;
  out.cb_start_effect_observed = Read(scope.actual_cb, 0x870, vtable);
  out.cb_start_effect_receiver_type_matches = out.cb_start_effect_observed &&
      b.compiled_effect_vtable && vtable == b.compiled_effect_vtable;
  out.cb_start_effect_execute_matches = out.cb_start_effect_receiver_type_matches &&
      b.compiled_effect_execute && Read(vtable, 0xB0, execute) &&
      execute == b.compiled_effect_execute;
  if (out.cb_start_effect_execute_matches) {
    out.cb_start_effect_observed = Read(scope.actual_cb, 0x8A0, child_data) &&
        Read(scope.actual_cb, 0x8AC, out.cb_start_effect_child_count);
    if (out.cb_start_effect_observed) {
      std::memcpy(out.cb_start_effect_header_identity_bytes.data(), &child_data, 8);
      std::memcpy(out.cb_start_effect_header_identity_bytes.data() + 8,
                  &out.cb_start_effect_child_count, 4);
      if (out.cb_start_effect_child_count < 0) out.cb_start_effect_observed = false;
    }
    out.cb_start_effect_child_data_present = child_data != nullptr;
    out.cb_start_effect_known_empty = out.cb_start_effect_observed &&
        out.cb_start_effect_child_count == 0;
  } else out.cb_start_effect_observed = false;
  // Actual2A7F498/4A8/4CB/4D5 loads manager+38, table+2D8 and dispatches
  // 37CCC30. Its already closed complete body returns for a null row.
  void *manager = nullptr, *table = nullptr, *row = nullptr;
  out.war_started_on_action_observed = Read(b.event_manager_slot, 0, manager) &&
      manager && Read(manager, 0x38, table) && table && Read(table, 0x2D8, row);
  out.war_started_on_action_known_empty = out.war_started_on_action_observed && !row;
  out.holy_initial_participants_applicable = out.cb_flags_observed &&
      (out.cb_flags_raw & (1U << 15)) != 0;
  out.holy_initial_participants_complete = out.cb_flags_observed &&
      (!out.holy_initial_participants_applicable || scope.holy_initial_participants_complete);
}
bool ForcedRound(const PrewarAdditionalSupportersBindings12004 &b, void *root,
                 std::int32_t root_id, void *opposing, void *term,
                 bool attacker, PrewarAdditionalSupportersSnapshot12004 &out) {
  void *land = nullptr, *ids = nullptr;
  std::int32_t count = 0;
  std::uint8_t default_level = 0;
  if (!Read(root, 0x1C0, land) || !Read(term, 0x9F28, default_level)) return false;
  if (land && (!Read(land, 0x248, ids) || !Read(land, 0x254, count) ||
      count < 0 || count > kMaximumContracts || (count && !ids))) return false;
  (attacker ? out.attacker_source_contract_count : out.defender_source_contract_count) =
      static_cast<std::uint32_t>(count);
  for (std::int32_t order = 0; order < count; ++order) {
    std::int32_t contract_id = -1, term_count = 0;
    void *terms = nullptr, *levels = nullptr, *subject = nullptr, *suzerain = nullptr;
    if (!Read(ids, static_cast<std::size_t>(order) * 4, contract_id)) return false;
    void *contract = ResolveContract(b, contract_id);
    if (!contract || !Read(contract, 0x28, suzerain) || suzerain != root ||
        !Read(contract, 0x38, terms) || !Read(contract, 0x44, term_count) ||
        term_count < 0 || term_count > kMaximumContracts || (term_count && !terms)) return false;
    std::int32_t first = -1;
    for (std::int32_t i = 0; i < term_count; ++i) {
      void *candidate = nullptr;
      if (!Read(terms, static_cast<std::size_t>(i) * 8, candidate)) return false;
      if (candidate == term) { first = i; break; }
    }
    if (first == -1) continue;
    std::uint8_t active = 0;
    if (!Read(contract, 0x68, levels) || !Read(levels, static_cast<std::size_t>(first), active)) return false;
    if (active == default_level) continue;
    std::int32_t subject_id = -1; bool alive = false;
    if (!Read(contract, 0x20, subject) || !Identity(b, subject, subject_id, alive)) return false;
    const PrewarForcedInitialParticipant12004 row{subject_id, attacker, root_id,
        contract_id, static_cast<std::uint32_t>(order), active, default_level};
    if (attacker && subject == opposing) out.excluded_primary_defender_collisions.push_back(row);
    else {
      out.forced_participants.push_back(row);
      if (alive) Append(out, root_id, subject_id, PrewarAdditionalSupportSource12004::forced_initial_participant);
      else out.dead_source_character_ids.push_back(subject_id);
    }
  }
  return true;
}
bool Followers(const PrewarAdditionalSupportersBindings12004 &b,
               const std::vector<void *> &roots, const std::vector<std::int32_t> &root_ids,
               PrewarAdditionalSupportersSnapshot12004 &out) {
  // Stock religious_head_call requires the selected leader's actual
  // religious_head_or_challenger to be that leader. A mapped callback can
  // prove this source inapplicable; a different formal head alone cannot.
  std::vector<bool> source_needed(roots.size(), true);
  bool complete = b.religious_authority != nullptr;
  void *fallback = nullptr;
  const bool fallback_observed = Read(b.character_fallback_slot, 0, fallback);
  for (std::size_t j = 0; j < roots.size(); ++j) {
    void *authority = nullptr;
    if (!b.religious_authority || !Getter(b.religious_authority, roots[j], authority) ||
        !fallback_observed) { complete = false; continue; }
    if (!authority || authority == fallback) { source_needed[j] = false; continue; }
    std::int32_t id = -1; bool alive = false;
    if (!Identity(b, authority, id, alive)) { complete = false; continue; }
    source_needed[j] = authority == roots[j];
  }
  if (std::find(source_needed.begin(), source_needed.end(), true) == source_needed.end())
    return complete;
  void *storage = nullptr, *slots = nullptr;
  std::int32_t capacity = 0;
  if (!b.character_faith || !b.faith_head || !Read(b.core.character_storage_slot, 0, storage) ||
      !Read(storage, kCharacterStorageSlotsOffset, slots) ||
      !Read(storage, kCharacterStorageCapacityOffset, capacity) ||
      capacity < 0 || capacity > kMaximumSlots || (capacity && !slots)) return false;
  out.character_storage_slot_count = capacity;
  std::vector<void *> root_faiths;
  for (std::size_t j = 0; j < roots.size(); ++j) {
    void *faith = nullptr;
    if (source_needed[j] && (!Getter(b.character_faith, roots[j], faith) || !faith)) complete = false;
    root_faiths.push_back(faith);
  }
  for (std::int32_t i = 0; i < capacity; ++i) {
    void *p = nullptr;
    if (!Read(slots, static_cast<std::size_t>(i) * kCharacterStorageSlotStride +
              kCharacterStorageObjectOffset, p)) { complete = false; break; }
    ++out.character_storage_visited_count;
    if (!p) continue;
    std::int32_t id = -1; bool alive = false;
    if (!Identity(b, p, id, alive) || (static_cast<std::uint32_t>(id) & 0xFFFFFFU) !=
        static_cast<std::uint32_t>(i)) {
      if (id != -1) out.unresolved_source_character_ids.push_back(id);
      complete = false; continue;
    }
    if (!alive) { out.dead_source_character_ids.push_back(id); continue; }
    void *faith = nullptr, *head = nullptr, *authority = nullptr;
    if (!Getter(b.character_faith, p, faith) || !faith ||
        !Getter(b.faith_head, faith, head)) { complete = false; continue; }
    const bool authority_sampled = b.religious_authority && Getter(b.religious_authority, p, authority);
    if (b.religious_authority && !authority_sampled) complete = false;
    for (std::size_t j = 0; j < roots.size(); ++j) {
      if (!source_needed[j]) continue;
      // Same-faith adjacency deliberately over-includes possible challenger
      // followers while the exact authority/challenger callback is unbound.
      // It is not an observed follower identity or future callability result.
      if (head == roots[j] || (authority_sampled && authority == roots[j]) ||
          (root_faiths[j] && faith == root_faiths[j]))
        Append(out, root_ids[j], id, PrewarAdditionalSupportSource12004::religious_follower);
    }
  }
  return complete && out.character_storage_visited_count == capacity;
}
} // namespace

PrewarAdditionalSupportersBindings12004 BindPrewarAdditionalSupportersImage12004(
    std::uintptr_t base, std::string_view sha) noexcept {
  PrewarAdditionalSupportersBindings12004 b{};
  b.core = BindCoreImage(base, sha);
  if (!b.core.enabled) return b;
  const auto context = religion::BindReligionContextImage12004(base, sha);
  const auto governance = religion::adopted::BindRiteGovernanceImage12004(base, sha);
  if (!context.enabled || !governance.enabled) return b;
  b.character_fallback_slot = reinterpret_cast<void **>(base + 0x5C67570);
  b.immediate_liege = reinterpret_cast<PrewarAdditionalObjectGetter12004>(base + 0x28BFC50);
  b.top_liege = reinterpret_cast<PrewarAdditionalObjectGetter12004>(base + 0x28BFD80);
  b.character_faith = reinterpret_cast<PrewarAdditionalObjectGetter12004>(context.character_faith);
  b.faith_head = reinterpret_cast<PrewarAdditionalObjectGetter12004>(governance.heads.faith_religious_head);
  b.subject_contract_storage_slot = reinterpret_cast<void **>(base + 0x5D1EB88);
  b.subject_contract_fallback_slot = reinterpret_cast<void **>(base + 0x5D1EB40);
  b.subject_contract_database_slot = reinterpret_cast<void **>(base + 0x5D1DED0);
  b.compiled_effect_vtable = reinterpret_cast<const void *>(base + 0x492E2E0);
  b.compiled_effect_execute = reinterpret_cast<const void *>(base + 0x3766300);
  b.event_manager_slot = reinterpret_cast<void **>(base + 0x5D1F6C8);
  b.enabled = true;
  return b;
}

bool ReadPrewarAdditionalSupporters12004(
    const PrewarAdditionalSupportersBindings12004 &b, const CoreSnapshotPrefix &frame,
    const PrewarAdditionalSupportersNativeScope12004 &scope,
    PrewarAdditionalSupportersSnapshot12004 &out, std::string_view *reason) noexcept {
  out = {}; if (reason) *reason = {};
  try {
    bool actor_alive = false, additional_alive = false, recipient_alive = false;
    if (!b.enabled || !b.core.enabled || !frame.clock.paused || !frame.map_ready ||
        !frame.has_played_character || !frame.played_character_alive || !scope.actual_cb ||
        !Identity(b, scope.actor, out.actor_character_id, actor_alive) || !actor_alive ||
        out.actor_character_id != frame.played_character_id ||
        !Identity(b, scope.additional, out.additional_character_id, additional_alive) || !additional_alive ||
        !Identity(b, scope.recipient, out.recipient_character_id, recipient_alive) || !recipient_alive ||
        scope.additional == scope.recipient) {
      Reason(out, "prewar_additional_selected_scope_unavailable");
      if (reason) *reason = out.reason; return false;
    }
    out.sampled = true;
    out.cb_flags_observed = Read(scope.actual_cb, 0x1548, out.cb_flags_raw);
    InitialBranchInputs(b, scope, out);
    std::vector<void *> roots{scope.additional, scope.recipient};
    std::vector<std::int32_t> ids{out.additional_character_id, out.recipient_character_id};
    out.immediate_liege_complete = true; out.top_liege_complete = true;
    out.diarch_complete = b.diarch != nullptr;
    out.religious_authority_complete = b.religious_authority != nullptr;
    for (std::size_t i = 0; i < roots.size(); ++i) {
      out.immediate_liege_complete &= Neighbor(b, roots[i], ids[i], b.immediate_liege,
          PrewarAdditionalSupportSource12004::immediate_liege, out);
      out.top_liege_complete &= Neighbor(b, roots[i], ids[i], b.top_liege,
          PrewarAdditionalSupportSource12004::top_liege, out);
      if (b.diarch) out.diarch_complete &= Neighbor(b, roots[i], ids[i], b.diarch,
          PrewarAdditionalSupportSource12004::diarch, out);
      if (b.religious_authority) out.religious_authority_complete &= Neighbor(b, roots[i], ids[i],
          b.religious_authority, PrewarAdditionalSupportSource12004::religious_authority, out);
      else {
        void *faith = nullptr, *head = nullptr;
        if (Getter(b.character_faith, roots[i], faith) &&
            Getter(b.faith_head, faith, head) && head) {
          std::int32_t head_id = -1; bool alive = false;
          if (Identity(b, head, head_id, alive) && alive)
            Append(out, ids[i], head_id, PrewarAdditionalSupportSource12004::religious_authority);
        }
      }
    }
    out.religious_follower_complete = Followers(b, roots, ids, out);
    void *database = nullptr, *term = nullptr;
    out.forced_contract_subset_complete = Read(b.subject_contract_database_slot, 0, database) &&
        Read(database, 0xF00, term) && term &&
        ForcedRound(b, scope.additional, ids[0], scope.recipient, term, true, out) &&
        ForcedRound(b, scope.recipient, ids[1], scope.additional, term, false, out);
    out.complete_initial_participants_ready = out.forced_contract_subset_complete &&
        out.cb_flags_observed && out.cb_start_effect_known_empty &&
        out.war_started_on_action_known_empty && out.holy_initial_participants_complete &&
        out.excluded_primary_defender_collisions.empty();
    if (!out.diarch_complete || !out.religious_authority_complete)
      Reason(out, "prewar_additional_diarch_or_challenger_source_unmapped");
    else if (!out.immediate_liege_complete || !out.top_liege_complete ||
             !out.religious_follower_complete || !out.forced_contract_subset_complete)
      Reason(out, "prewar_additional_source_partial");
    if (reason) *reason = out.reason;
    return true;
  } catch (...) {
    out.immediate_liege_complete = false; out.top_liege_complete = false;
    out.diarch_complete = false; out.religious_authority_complete = false;
    out.religious_follower_complete = false; out.forced_contract_subset_complete = false;
    out.complete_initial_participants_ready = false;
    Reason(out, "prewar_additional_capture_exception");
    if (reason) *reason = out.reason;
    return false;
  }
}
} // namespace xar::ck3_12004
