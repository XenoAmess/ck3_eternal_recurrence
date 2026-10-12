#include "xar_bridge/prewar_force_coalition_v2.hpp"

#include "xar_bridge/ck3_12004_adapter.hpp"

#include <algorithm>
#include <array>
#include <cstring>
#include <limits>
#include <map>
#include <set>
#include <sstream>
#include <utility>
#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12004 {
namespace {

void SetFailure(std::string &failure, std::string_view reason) noexcept {
  try { failure.assign(reason); }
  catch (...) { failure.clear(); }
}

template <class T> bool Copy(const void *base, std::size_t offset, T &out) noexcept {
  if (!base) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&out, static_cast<const std::byte *>(base) + offset, sizeof(T));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

template <class Fn, class... Args> bool Call(Fn fn, Args... args) noexcept {
  if (!fn) return false;
#if defined(_MSC_VER)
  __try {
#endif
    fn(args...);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

template <class Fn, class Result, class... Args>
bool ResultOf(Fn fn, Result &out, Args... args) noexcept {
  if (!fn) return false;
#if defined(_MSC_VER)
  __try {
#endif
    out = fn(args...);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool ReadCore(const CoreBindings *bindings, CoreSnapshotPrefix *frame) noexcept {
  if (!bindings || !frame) return false;
#if defined(_MSC_VER)
  __try {
#endif
    return ck3_12004::ReadCoreSnapshot(*bindings, *frame);
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

class RaiseCommandOwner {
public:
  explicit RaiseCommandOwner(const ck3_12002::MilitaryBindings &bindings) noexcept : bindings_(bindings) {}
  ~RaiseCommandOwner() { (void)Close(); }
  void *pointer() noexcept { return storage_.data(); }
  void Constructed() noexcept { active_ = true; }
  bool Close() noexcept {
    if (!active_) return cleanup_ready_;
    active_ = false;
    cleanup_ready_ = Call(bindings_.destroy_raise, pointer(), std::uint32_t{0});
    return cleanup_ready_;
  }
private:
  // Place the native command first and account for the complete aligned tail.
  // The local owner retains its 16-byte alignment without implicit padding.
  alignas(16) std::array<std::byte, 0x50> storage_{};
  const ck3_12002::MilitaryBindings &bindings_;
  bool active_ = false;
  bool cleanup_ready_ = false;
  std::array<std::byte, 16 - sizeof(void *) - 2> alignment_tail_{};
};

void ReadNativeRaise(const PrewarForceCoalitionV2Bindings12004 &bindings,
    const ck3_12002::MilitaryWorldAccess &world, std::int32_t actor,
    PrewarForceMobilization12004 &out) {
  const auto &military = bindings.military;
  if (!military.enabled || !world.resolve_character || !world.resolve_province ||
      !military.construct_raise || !military.validate_raise || !military.destroy_raise ||
      !military.raise_primary || !military.raise_secondary) return;
  void *character = nullptr;
  if (!ResultOf(world.resolve_character, character, world.context, actor) || !character) return;
  std::int32_t actual = -1;
  if (!Copy(character, 0x18, actual) || actual != actor) return;
  void *province = nullptr;
  if (!ResultOf(&ck3_12002::ResolveMilitaryDefaultRaiseProvince, province,
                military, character) || !province) return;
  std::int32_t province_id = -1;
  void *resolved = nullptr;
  if (!Copy(province, 0x10, province_id) || province_id < 1 ||
      !ResultOf(world.resolve_province, resolved, world.context, province_id) ||
      resolved != province) return;
  RaiseCommandOwner command(military);
  const std::array<std::int32_t, 2> entry{province_id, -1};
  void *constructed = nullptr;
  if (!ResultOf(military.construct_raise, constructed, command.pointer(), actor, entry.data()) ||
      constructed != command.pointer()) return;
  command.Constructed();
  std::uintptr_t primary = 0, secondary = 0;
  if (!Copy(command.pointer(), 0, primary) || !Copy(command.pointer(), 0x18, secondary) ||
      primary != military.raise_primary || secondary != military.raise_secondary) return;
  bool legal = false;
  if (!ResultOf(military.validate_raise, legal, command.pointer(), nullptr)) return;
  if (!command.Close()) return;
  out.native_raise_legal = legal;
  out.default_raise_province_id = province_id;
}

std::string Quote(std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  std::string out = "\"";
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') { out += '\\'; out += static_cast<char>(c); }
    else if (c < 0x20) { out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15]; }
    else out += static_cast<char>(c);
  }
  return out + '"';
}

template <class T> void Nullable(std::ostream &out, const std::optional<T> &value) {
  if (value) out << *value;
  else out << "null";
}

void Strings(std::ostream &out, const std::vector<std::string> &values) {
  out << '[';
  for (std::size_t i = 0; i < values.size(); ++i) {
    if (i) out << ',';
    out << Quote(values[i]);
  }
  out << ']';
}

void Missing(PrewarForceCoalitionV2Sample12004 &out, std::string_view reason) {
  if (std::find(out.missing_required_domains.begin(), out.missing_required_domains.end(),
                reason) == out.missing_required_domains.end())
    out.missing_required_domains.emplace_back(reason);
}

std::string CanonicalId(const game::DeclarableWarSnapshot &selected) {
  return std::to_string(selected.target_character_id) + '-' +
      std::to_string(selected.casus_belli_index) + '-' +
      std::to_string(selected.configuration_index);
}

using NativeVector = ck3_12002::religion::holy_war_defender_join::NativeCharacterVector;
using HolyBindings = religion::holy_war_defender_join::Bindings;
using NativeFree = ck3_12002::religion::holy_war_defender_join::FreeRows;

// This leaf contains no C++ object requiring unwinding. In particular it never
// catches an AV above a C++ vector owner, where /EHsc would skip its cleanup.
bool ReleaseRows(const HolyBindings &bindings, NativeVector &vector) noexcept {
  if (!vector.rows) return true;
#if defined(_MSC_VER)
  __try {
#endif
    if (!vector.allocator) return false;
    if (bindings.free_rows) {
      bindings.free_rows(vector.allocator, vector.rows, std::size_t{8});
    } else {
      const void *vtable = nullptr;
      NativeFree release = nullptr;
      std::memcpy(&vtable, vector.allocator, sizeof(vtable));
      if (!vtable) return false;
      std::memcpy(&release, static_cast<const std::byte *>(vtable) + 0x10,
                  sizeof(release));
      if (!release) return false;
      release(vector.allocator, vector.rows, std::size_t{8});
    }
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

class HolyVectorOwner {
public:
  explicit HolyVectorOwner(const HolyBindings &bindings) noexcept : bindings_(bindings) {
    value.allocator = bindings.engine_allocator;
  }
  ~HolyVectorOwner() { (void)Close(); }
  bool Close() noexcept {
    if (!active_) return cleanup_ready_;
    active_ = false;
    cleanup_ready_ = ReleaseRows(bindings_, value);
    return cleanup_ready_;
  }
  NativeVector value{};
private:
  const HolyBindings &bindings_;
  bool active_ = true;
  bool cleanup_ready_ = false;
};

bool CharacterIdentity(const CoreBindings &core, void *pointer,
                       std::int32_t &id) noexcept {
  if (!pointer || !Copy(pointer, 0x18, id) || id == -1) return false;
  void *resolved = nullptr;
  return ResultOf(&ResolveCoreCharacter, resolved, core, id) && resolved == pointer;
}

// The same actual4 accepted-NPC collector is reused. Its rule evaluation has
// already selected the rows. Faith/fervor diagnostics do not qualify soldier
// coverage, so this reader observes only complete accepted IDs and real flags.
bool ReadHolyAcceptedIds(const PrewarForceCoalitionV2Bindings12004 &bindings,
    const PrewarSelectedDeclarationNativeScope12004 &scope,
    const PrewarSelectedDeclarationObservation12004 &selected,
    std::vector<std::int32_t> &ids, std::string &whole_observation) {
  ids.clear();
  whole_observation.clear();
  std::uint32_t flags = 0;
  if (!selected.available || !selected.finalized_roles_ready ||
      !bindings.holy_join.enabled || !scope.actual_cb ||
      !Copy(scope.actual_cb, 0x1548, flags)) return false;
  std::int32_t attacker = -1, defender = -1;
  if (!CharacterIdentity(bindings.core, scope.context_additional_role, attacker) ||
      !CharacterIdentity(bindings.core, scope.context_recipient, defender) ||
      selected.native_cb_attacker_character_id != attacker ||
      selected.native_cb_defender_character_id != defender) return false;
  const bool enabled = ((flags >> 15) & 1U) != 0;
  std::ostringstream evidence;
  evidence << "{\"flags\":" << flags << ",\"attacker\":" << attacker
           << ",\"defender\":" << defender << ",\"enabled\":"
           << (enabled ? "true" : "false");
  bool complete = true;
  if (enabled) {
    HolyVectorOwner native(bindings.holy_join);
    const bool called = Call(bindings.holy_join.collector, scope.actual_cb,
        scope.context_additional_role, scope.context_recipient, &native.value);
    const bool header = called && native.value.count >= 0 &&
        native.value.capacity >= native.value.count &&
        native.value.count <= kPrewarPotentialMaximumCharacterSlots12004 &&
        (native.value.count == 0 || native.value.rows != nullptr);
    evidence << ",\"called\":" << (called ? "true" : "false")
             << ",\"count\":" << native.value.count
             << ",\"capacity\":" << native.value.capacity << ",\"rows\":[";
    complete = header;
    if (header) for (std::int32_t i = 0; i < native.value.count; ++i) {
      if (i) evidence << ',';
      void *pointer = nullptr;
      std::int32_t id = -1;
      const bool copied = Copy(native.value.rows, static_cast<std::size_t>(i) * sizeof(void *), pointer);
      const bool verified = copied && CharacterIdentity(bindings.core, pointer, id);
      evidence << "{\"id\":";
      if (copied && pointer && id != -1) evidence << id;
      else evidence << "null";
      evidence << ",\"verified\":" << (verified ? "true" : "false") << '}';
      if (verified) ids.push_back(id);
      else complete = false;
    }
    const bool closed = native.Close();
    evidence << "],\"cleanup\":" << (closed ? "true" : "false");
    complete = complete && closed;
  } else {
    evidence << ",\"called\":false,\"count\":0,\"capacity\":0,\"rows\":[],\"cleanup\":true";
  }
  std::uint32_t after = 0;
  std::int32_t after_attacker = -1, after_defender = -1;
  complete = complete && Copy(scope.actual_cb, 0x1548, after) && after == flags &&
      CharacterIdentity(bindings.core, scope.context_additional_role, after_attacker) &&
      CharacterIdentity(bindings.core, scope.context_recipient, after_defender) &&
      after_attacker == attacker && after_defender == defender;
  evidence << ",\"complete\":" << (complete ? "true" : "false") << '}';
  whole_observation = evidence.str();
  return complete;
}

void Participant(std::map<std::int32_t, std::set<std::string>> &participants,
                 std::int32_t id, std::string_view source,
                 std::int32_t actor, std::int32_t attacker) {
  // These fixed attacker-side roots cannot simultaneously join the defender.
  if (id == -1 || id == actor || id == attacker) return;
  participants[id].emplace(source);
}

const char *AdditionalSource(PrewarAdditionalSupportSource12004 source) noexcept {
  switch (source) {
  case PrewarAdditionalSupportSource12004::immediate_liege: return "immediate_liege";
  case PrewarAdditionalSupportSource12004::top_liege: return "top_liege";
  case PrewarAdditionalSupportSource12004::diarch: return "diarch";
  case PrewarAdditionalSupportSource12004::religious_authority: return "religious_authority";
  case PrewarAdditionalSupportSource12004::religious_follower: return "religious_follower";
  case PrewarAdditionalSupportSource12004::forced_initial_participant: return "forced_initial_participant";
  }
  return "forced_initial_participant";
}

struct Consumer {
  const PrewarForceCoalitionV2Bindings12004 *bindings = nullptr;
  const PrewarForceCoalitionRequest12004 *request = nullptr;
  const ck3_12002::MilitaryWorldAccess *world = nullptr;
  const game::Snapshot *frame = nullptr;
  PrewarForceCoalitionV2Sample12004 *output = nullptr;
};

bool Consume(void *opaque, const PrewarSelectedDeclarationNativeScope12004 &scope,
             const PrewarSelectedDeclarationObservation12004 &selected) noexcept {
  try {
    auto &context = *static_cast<Consumer *>(opaque);
    auto &out = *context.output;
    const auto &bindings = *context.bindings;
    if (!selected.native_cb_attacker_character_id || !selected.native_cb_defender_character_id ||
        !selected.native_cb_role_names_ready || !selected.finalized_roles_ready) {
      Missing(out, "finalized_selected_cb_roles");
      return true;
    }
    const auto attacker = *selected.native_cb_attacker_character_id;
    const auto defender = *selected.native_cb_defender_character_id;
    if (defender == out.actor_character_id || defender == attacker) {
      Missing(out, "selected_cb_opposing_roles");
      return true;
    }
    std::map<std::int32_t, std::set<std::string>> participants;
    Participant(participants, defender, "primary_defender", out.actor_character_id, attacker);
    std::vector<std::int32_t> holy_ids;
    out.holy_joiners_complete = ReadHolyAcceptedIds(bindings, scope, selected,
        holy_ids, out.holy_join_complete_observation);
    for (const auto id : holy_ids)
      Participant(participants, id, "holy_war_joiner", out.actor_character_id, attacker);
    if (!out.holy_joiners_complete) Missing(out, "selected_cb_holy_defender_joiners");

    CoreSnapshotPrefix frame;
    if (!ReadCore(&bindings.core, &frame) ||
        !frame.clock.paused || !frame.map_ready || !frame.has_played_character ||
        !frame.played_character_alive || frame.clock.date_raw != out.date_raw ||
        frame.played_character_id != out.actor_character_id) return false;
    std::string_view reason;
    const bool potential_observed = ReadPrewarPotentialSupporters12004(
        bindings.potential, frame, defender, out.potential, &reason);
    out.current_allies_complete = potential_observed &&
        out.potential.current_allies_available && out.potential.current_allies.collection_complete;
    if (!potential_observed || !out.potential.covered_source_subset_complete)
      Missing(out, "current_alliances_contract_confederation_house_sources");
    for (const auto &candidate : out.potential.candidates) {
      const std::pair<std::uint32_t, const char *> sources[] = {
          {1U << 0, "current_ally"}, {1U << 1, "contract_subject"},
          {1U << 2, "contract_suzerain"}, {1U << 3, "confederation_member"},
          {1U << 4, "same_house"}};
      for (const auto &[bit, source] : sources) if (candidate.source_mask & bit)
        Participant(participants, candidate.character_id, source, out.actor_character_id, attacker);
    }
    PrewarAdditionalSupportersNativeScope12004 additional_scope{
        scope.actual_cb, scope.context_actor, scope.context_additional_role,
        scope.context_recipient, out.holy_joiners_complete};
    const bool additional_observed = ReadPrewarAdditionalSupporters12004(
        bindings.additional, frame, additional_scope, out.additional, &reason);
    out.additional_supporters_complete = additional_observed &&
        out.additional.immediate_liege_complete && out.additional.top_liege_complete &&
        out.additional.diarch_complete && out.additional.religious_authority_complete &&
        out.additional.religious_follower_complete && out.additional.forced_contract_subset_complete;
    out.selected_cb_initial_complete = additional_observed &&
        out.additional.complete_initial_participants_ready;
    if (!out.additional_supporters_complete) Missing(out, "additional_current_supporter_sources");
    if (!out.selected_cb_initial_complete) Missing(out, "selected_cb_initial_participant_branches");
    for (const auto &candidate : out.additional.candidates)
      if (candidate.source_root_character_id == defender)
        Participant(participants, candidate.character_id, AdditionalSource(candidate.source),
                    out.actor_character_id, attacker);
    for (const auto &forced : out.additional.forced_participants)
      if (!forced.attacker_side)
        Participant(participants, forced.character_id, "forced_initial_participant",
                    out.actor_character_id, attacker);
    for (const auto &[id, sources] : participants)
      out.enemy_participants.push_back({id, std::vector<std::string>(sources.begin(), sources.end())});
    out.potential_enemy_collection_complete = potential_observed &&
        out.potential.covered_source_subset_complete && out.holy_joiners_complete &&
        out.additional_supporters_complete && out.selected_cb_initial_complete;
    out.complete_initial_participants_ready = out.selected_cb_initial_complete &&
        out.holy_joiners_complete && selected.finalized_selection_ready && selected.finalized_roles_ready;

    std::set<std::int32_t> owner_set{out.actor_character_id, attacker};
    for (const auto &participant : out.enemy_participants) owner_set.insert(participant.character_id);
    const std::vector<std::int32_t> owners(owner_set.begin(), owner_set.end());
    (void)ReadPrewarHiredInventory12004(bindings.mercenary, bindings.holy_order,
        bindings.core, bindings.armies, kExecutableSha256, owners, out.hired);
    ReadNativeRaise(bindings, *context.world, out.actor_character_id,
                    out.native_mobilization_qualification);
    bool enemy_complete = out.potential_enemy_collection_complete;
    std::int64_t enemy_upper = 0;
    for (const auto id : owners) {
      PrewarForceCoalitionV2Owner12004 owner;
      PrewarOwnerInventoryRequest12004 inventory_request{
          context.request->expected_native_revision, out.date_raw, out.actor_character_id, id};
      (void)ReadPrewarOwnerInventory12004(bindings.owner_inventory, *context.world,
          inventory_request, owner.inventory);
      PrewarLevyInventoryRequest12004 levy_request{
          context.request->expected_native_revision, out.date_raw, out.actor_character_id, id};
      (void)ReadPrewarLevyInventory12004(bindings.levy_inventory, *context.world,
          levy_request, owner.levy);
      (void)ProjectPrewarForceOwnerBounds12004(owner.inventory, owner.levy,
          out.hired, owner.bounds);
      if (id == out.actor_character_id) {
        auto &mobilization = out.native_mobilization_qualification;
        (void)ReadPrewarCommandableRaised12004(bindings.armies, bindings.military,
            *context.world, *context.frame, owner.inventory, out.commandable_raised);
        if (out.commandable_raised.available && out.commandable_raised.known_lower_soldiers &&
            *out.commandable_raised.known_lower_soldiers >= 0) {
          mobilization.raised_commandable_lower_soldiers = out.commandable_raised.known_lower_soldiers;
          mobilization.raised_lower_ready = true;
        }
        if (owner.bounds.actor_lower_ready) {
          mobilization.physical_inventory_lower_soldiers = owner.bounds.actor_lower_soldiers;
        }
        if (owner.inventory.native_all_unraised_stock_ready &&
            owner.inventory.native_all_unraised_stock &&
            *owner.inventory.native_all_unraised_stock >= 0) {
          mobilization.native_unraised_stock_soldiers = owner.inventory.native_all_unraised_stock;
          mobilization.native_unraised_stock_ready = true;
        }
        if (mobilization.physical_inventory_lower_soldiers &&
            *mobilization.physical_inventory_lower_soldiers >= 0 &&
            mobilization.native_unraised_stock_ready) {
          mobilization.unraised_lower_soldiers = (std::min)(
              *mobilization.physical_inventory_lower_soldiers,
              static_cast<std::int64_t>(*mobilization.native_unraised_stock_soldiers));
          mobilization.unraised_lower_ready = true;
        }
        if (mobilization.raised_lower_ready)
          mobilization.executable_lower_soldiers = mobilization.raised_commandable_lower_soldiers;
        if (mobilization.native_raise_legal == true && mobilization.unraised_lower_ready) {
          const auto current = mobilization.executable_lower_soldiers.value_or(0);
          mobilization.executable_lower_soldiers = (std::max)(
              current, *mobilization.unraised_lower_soldiers);
        }
        if (mobilization.executable_lower_soldiers.has_value()) {
          mobilization.executable_lower_ready = true;
          mobilization.available = true;
          mobilization.unavailable_reason.clear();
        } else if (mobilization.native_raise_legal == false) {
          mobilization.unavailable_reason = "native_raise_not_legal_and_raised_control_lower_unavailable";
        }
        owner.bounds.actor_lower_soldiers = mobilization.executable_lower_soldiers;
        owner.bounds.actor_lower_ready = mobilization.executable_lower_ready;
        if (!mobilization.available)
          owner.bounds.unavailable_reasons.push_back(mobilization.unavailable_reason);
        out.actor_lower_soldiers = mobilization.executable_lower_soldiers;
        if (!out.actor_lower_soldiers) Missing(out, "actor_current_inventory_lower");
        if (!mobilization.available) Missing(out, "native_mobilization_qualification");
      } else if (participants.contains(id) &&
                 (!owner.bounds.inventory_upper_ready || !owner.bounds.inventory_upper_soldiers ||
                 *owner.bounds.inventory_upper_soldiers < 0 ||
                 *owner.bounds.inventory_upper_soldiers >
                     (std::numeric_limits<std::int64_t>::max)() - enemy_upper)) {
        enemy_complete = false;
        if (owner.bounds.inventory_upper_ready && owner.bounds.inventory_upper_soldiers &&
            *owner.bounds.inventory_upper_soldiers >= 0 &&
            *owner.bounds.inventory_upper_soldiers >
                (std::numeric_limits<std::int64_t>::max)() - enemy_upper)
          out.enemy_upper_aggregate_overflow = true;
        Missing(out, "enemy_owner_current_inventory:" + std::to_string(id));
      } else if (participants.contains(id)) {
        enemy_upper += *owner.bounds.inventory_upper_soldiers;
      }
      out.owners.push_back(std::move(owner));
    }
    out.enemy_force_coverage_complete = enemy_complete;
    if (enemy_complete) out.enemy_upper_soldiers = enemy_upper;
    if (!enemy_complete) Missing(out, "enemy_complete_current_inventory_upper");
    return true;
  } catch (...) { return false; }
}

} // namespace

bool ReadPrewarForceCoalitionV2Sample12004(
    const PrewarForceCoalitionV2Bindings12004 &bindings,
    const PrewarForceCoalitionRequest12004 &request,
    ck3_12002::QueryMailboxEnvelope &envelope,
    const ck3_12002::MilitaryWorldAccess &world,
    PrewarForceCoalitionV2Sample12004 &output, std::string &failure) noexcept {
  failure.clear();
  try {
    output = {};
    if (!envelope.game || !ck3_12002::IsQueryOwningThread(&envelope) ||
        envelope.snapshot_comparison != ck3_12002::QuerySnapshotComparison12002::full_snapshot ||
        !game::IsCk3_12004Descriptor(envelope.game->descriptor()) ||
        request.expected_native_revision != envelope.expected_snapshot_revision ||
        !request.expected_native_revision || !request.expected_public_revision ||
        request.declaration_id != CanonicalId(request.selected)) {
      failure = "prewar_v2_current_request_unavailable";
      return false;
    }
    game::Snapshot before;
    if (!ck3_12002::CaptureQuerySnapshot(&envelope, before) || !before.paused ||
        !before.map_ready || !before.has_played_character || !before.played_character_alive ||
        before.played_character_id <= 0 ||
        before.played_character_id > (std::numeric_limits<std::int32_t>::max)() ||
        before.date_raw < (std::numeric_limits<std::int32_t>::min)() ||
        before.date_raw > (std::numeric_limits<std::int32_t>::max)()) {
      failure = "prewar_v2_current_player_frame_unavailable";
      return false;
    }
    output.selected = request.selected;
    output.native_revision = request.expected_native_revision;
    output.date_raw = static_cast<std::int32_t>(before.date_raw);
    output.actor_character_id = static_cast<std::int32_t>(before.played_character_id);
    Consumer context{&bindings, &request, &world, &before, &output};
    const bool selected_available = ReadPrewarSelectedDeclaration12004(
        bindings.declarations, envelope, request.declaration_id, request.selected,
        output.final_cb_roles, &Consume, &context);
    if (!selected_available || !output.final_cb_roles.available ||
        !output.final_cb_roles.consumer_completed ||
        !output.final_cb_roles.context_cleanup_completed ||
        !output.final_cb_roles.scratch_cleanup_completed) {
      Missing(output, "finalized_selected_cb_context_or_consumer");
      output.potential_enemy_collection_complete = false;
      output.complete_initial_participants_ready = false;
      output.enemy_force_coverage_complete = false;
      output.enemy_upper_soldiers.reset();
    }
    // A partial source still describes the entire known owner scope with
    // explicit unknown rows. It must not omit the current actor or known roles.
    std::set<std::int32_t> required_owners{output.actor_character_id};
    for (const auto &id : {output.final_cb_roles.native_cb_attacker_character_id,
                           output.final_cb_roles.native_cb_defender_character_id})
      if (id && *id != -1) required_owners.insert(*id);
    for (const auto &participant : output.enemy_participants)
      required_owners.insert(participant.character_id);
    for (const auto id : required_owners) {
      if (std::any_of(output.owners.begin(), output.owners.end(),
          [id](const auto &row) { return row.bounds.owner_character_id == id; })) continue;
      PrewarForceCoalitionV2Owner12004 unavailable;
      unavailable.inventory.snapshot_revision = request.expected_native_revision;
      unavailable.inventory.date_raw = output.date_raw;
      unavailable.inventory.actor_character_id = output.actor_character_id;
      unavailable.inventory.owner_character_id = id;
      unavailable.bounds.owner_character_id = id;
      unavailable.bounds.unavailable_reasons.emplace_back("selected_context_owner_source_unavailable");
      output.owners.push_back(std::move(unavailable));
    }
    std::sort(output.owners.begin(), output.owners.end(), [](const auto &left, const auto &right) {
      return left.bounds.owner_character_id < right.bounds.owner_character_id;
    });
    const auto actor = std::find_if(output.owners.begin(), output.owners.end(), [&](const auto &row) {
      return row.bounds.owner_character_id == output.actor_character_id;
    });
    if (actor == output.owners.end() || !actor->bounds.actor_lower_ready) {
      output.actor_lower_soldiers.reset();
      output.native_mobilization_qualification.available = false;
      output.native_mobilization_qualification.executable_lower_ready = false;
      output.native_mobilization_qualification.executable_lower_soldiers.reset();
      if (output.native_mobilization_qualification.unavailable_reason.empty())
        output.native_mobilization_qualification.unavailable_reason = "actor_owner_executable_lower_unavailable";
    }
    const bool role_ready = output.final_cb_roles.available && output.final_cb_roles.finalized_roles_ready;
    output.potential_enemy_collection_complete = output.potential_enemy_collection_complete && role_ready;
    // Owner inventory completeness is independent of unknown membership. The
    // public missing-domain enum must preserve that distinction.
    bool known_owner_upper_ready = true;
    std::int64_t known_owner_upper_sum = 0;
    output.enemy_upper_aggregate_overflow = false;
    for (const auto &participant : output.enemy_participants) {
      const auto owner = std::find_if(output.owners.begin(), output.owners.end(), [&](const auto &row) {
        return row.bounds.owner_character_id == participant.character_id;
      });
      if (owner == output.owners.end() || !owner->bounds.inventory_upper_ready ||
          !owner->bounds.inventory_upper_soldiers || *owner->bounds.inventory_upper_soldiers < 0) {
        known_owner_upper_ready = false;
        continue;
      }
      if (*owner->bounds.inventory_upper_soldiers >
          (std::numeric_limits<std::int64_t>::max)() - known_owner_upper_sum) {
        output.enemy_upper_aggregate_overflow = true;
      } else {
        known_owner_upper_sum += *owner->bounds.inventory_upper_soldiers;
      }
    }
    // Overflow is a full-known-sum condition; a missing owner has no complete
    // sum to qualify or overflow in the strict public projection.
    if (!known_owner_upper_ready) output.enemy_upper_aggregate_overflow = false;
    output.complete_initial_participants_ready = output.potential_enemy_collection_complete;
    output.enemy_force_coverage_complete = output.complete_initial_participants_ready &&
        known_owner_upper_ready && !output.enemy_upper_aggregate_overflow;
    if (output.enemy_force_coverage_complete) output.enemy_upper_soldiers = known_owner_upper_sum;
    else output.enemy_upper_soldiers.reset();
    game::Snapshot after;
    if (!ck3_12002::CaptureQuerySnapshot(&envelope, after) || after != before) {
      failure = "prewar_v2_complete_sample_frame_changed";
      return false;
    }
    // Keep the small public missing-domain enum canonical. Detailed source
    // failures remain in the complete native DTO and per-owner diagnostics.
    output.missing_required_domains.clear();
    if (!output.final_cb_roles.available || !output.final_cb_roles.finalized_roles_ready)
      Missing(output, "final_cb_roles");
    if (!output.potential_enemy_collection_complete)
      Missing(output, "potential_enemy_participants");
    if (!output.current_allies_complete)
      Missing(output, "potential_enemy_current_allies");
    if (!output.holy_joiners_complete)
      Missing(output, "potential_enemy_holy_joiners");
    if (!output.additional_supporters_complete)
      Missing(output, "potential_enemy_additional_supporters");
    if (!output.selected_cb_initial_complete)
      Missing(output, "selected_cb_initial_participants");
    if (!output.actor_lower_soldiers)
      Missing(output, "actor_current_inventory_lower");
    if (!known_owner_upper_ready)
      Missing(output, "enemy_current_inventory_upper");
    if (output.enemy_upper_aggregate_overflow)
      Missing(output, "enemy_upper_aggregate_overflow");
    if (!output.native_mobilization_qualification.available)
      Missing(output, "native_mobilization_qualification");
    output.coverage_available = output.missing_required_domains.empty() &&
        output.final_cb_roles.available && output.final_cb_roles.finalized_roles_ready &&
        output.potential_enemy_collection_complete && output.complete_initial_participants_ready &&
        output.enemy_force_coverage_complete && output.enemy_upper_soldiers.has_value() &&
        output.actor_lower_soldiers.has_value();
    output.sampled = true;
    return true;
  } catch (...) {
    output.sampled = false;
    SetFailure(failure, "prewar_v2_sample_exception");
    return false;
  }
}

std::string SerializePrewarForceCoalitionV2_12004(
    const PrewarForceCoalitionV2Sample12004 &sample,
    const PrewarForceCoalitionRequest12004 &request,
    std::uint64_t capture_epoch, std::uint64_t ticket_sequence,
    std::uint64_t query_sequence, std::int32_t date_raw, std::int32_t actor_character_id) {
  if (!sample.sampled || !capture_epoch || !ticket_sequence || query_sequence != ticket_sequence ||
      sample.selected != request.selected || sample.native_revision != request.expected_native_revision ||
      sample.date_raw != date_raw || sample.actor_character_id != actor_character_id) return {};
  std::ostringstream out;
  out << std::boolalpha << "{\"schema_version\":2,\"status\":"
      << Quote(sample.coverage_available ? "available" : "partial")
      << ",\"read_only\":true,\"game_version\":" << Quote(kGameVersion)
      << ",\"executable_sha256\":" << Quote(kExecutableSha256)
      << ",\"capture_epoch\":" << capture_epoch
      << ",\"native_revision\":" << request.expected_native_revision
      << ",\"public_revision\":" << request.expected_public_revision
      << ",\"date_raw\":" << date_raw << ",\"actor_character_id\":" << actor_character_id
      << ",\"declaration_id\":" << Quote(request.declaration_id)
      << ",\"selected_declaration\":";
  const auto &selected = request.selected;
  out << "{\"target_character_id\":" << selected.target_character_id
      << ",\"casus_belli_index\":" << selected.casus_belli_index
      << ",\"casus_belli_key\":" << Quote(selected.casus_belli_key)
      << ",\"configuration_index\":" << selected.configuration_index
      << ",\"claimant_character_id\":" << selected.claimant_character_id << ",\"target_title_ids\":[";
  for (std::size_t i = 0; i < selected.target_title_ids.size(); ++i) {
    if (i) out << ',';
    out << selected.target_title_ids[i];
  }
  out << "]},\"effective_target_character_id\":";
  Nullable(out, sample.generic_effective_target_character_id);
  out << ",\"ticket\":" << ticket_sequence << ",\"query_sequence\":" << query_sequence
      << ",\"two_round_observation\":{\"round_count\":2,\"complete_dto_equal\":true,"
         "\"frame_binding_equal\":true,\"unavailable_reason\":null},\"final_cb_roles\":{\"available\":"
      << (sample.final_cb_roles.available && sample.final_cb_roles.finalized_roles_ready)
      << ",\"unavailable_reason\":";
  if (sample.final_cb_roles.available && sample.final_cb_roles.finalized_roles_ready) out << "null";
  else out << Quote(sample.final_cb_roles.failure.empty() ? "selected_cb_roles_unavailable" : sample.final_cb_roles.failure);
  out << ",\"primary_attacker_character_id\":";
  Nullable(out, sample.final_cb_roles.native_cb_attacker_character_id);
  out << ",\"primary_defender_character_id\":";
  Nullable(out, sample.final_cb_roles.native_cb_defender_character_id);
  out << ",\"source\":\"finalized_selected_cb_context\",\"native_fallback\":"
      << (sample.final_cb_roles.available && sample.final_cb_roles.finalized_roles_ready ? "false" : "null")
      << ",\"final_can_send\":";
  Nullable(out, sample.final_cb_roles.final_can_send);
  out << "},\"potential_enemy_participants\":{\"available\":" << sample.potential_enemy_collection_complete
      << ",\"unavailable_reason\":";
  if (sample.potential_enemy_collection_complete) out << "null";
  else out << "\"potential_enemy_source_coverage_partial\"";
  out << ",\"collection_complete\":" << sample.potential_enemy_collection_complete
      << ",\"current_allies_complete\":" << sample.current_allies_complete
      << ",\"holy_joiners_complete\":" << sample.holy_joiners_complete
      << ",\"additional_supporters_complete\":" << sample.additional_supporters_complete
      << ",\"selected_cb_initial_complete\":" << sample.selected_cb_initial_complete << ",\"participants\":[";
  for (std::size_t i = 0; i < sample.enemy_participants.size(); ++i) {
    if (i) out << ',';
    const auto &participant = sample.enemy_participants[i];
    out << "{\"character_id\":" << participant.character_id << ",\"sources\":";
    Strings(out, participant.sources);
    out << '}';
  }
  out << "]},\"owner_forces\":[";
  for (std::size_t i = 0; i < sample.owners.size(); ++i) {
    if (i) out << ',';
    const auto &bounds = sample.owners[i].bounds;
    out << "{\"owner_character_id\":" << bounds.owner_character_id << ",\"actor_lower_soldiers\":";
    const bool actor = bounds.owner_character_id == actor_character_id;
    if (actor) Nullable(out, bounds.actor_lower_soldiers);
    else out << "null";
    out << ",\"actor_lower_ready\":" << (actor && bounds.actor_lower_ready) << ",\"inventory_upper_soldiers\":";
    Nullable(out, bounds.inventory_upper_soldiers);
    out << ",\"inventory_upper_ready\":" << bounds.inventory_upper_ready
        << ",\"inventory_scope\":\"same_frame_owned_current_inventory_v1\",\"unavailable_reasons\":";
    Strings(out, bounds.unavailable_reasons);
    out << '}';
  }
  const auto &mobilization = sample.native_mobilization_qualification;
  out << "],\"native_mobilization_qualification\":{\"available\":" << mobilization.available
      << ",\"unavailable_reason\":";
  if (mobilization.available) out << "null";
  else out << Quote(mobilization.unavailable_reason);
  out << ",\"source\":\"actual4_raise_command_final_validator_and_owned_current_rosters\",\"native_raise_legal\":";
  Nullable(out, mobilization.native_raise_legal);
  out << ",\"default_raise_province_id\":";
  Nullable(out, mobilization.default_raise_province_id);
  out << ",\"physical_inventory_lower_soldiers\":";
  Nullable(out, mobilization.physical_inventory_lower_soldiers);
  out << ",\"native_unraised_stock_soldiers\":";
  Nullable(out, mobilization.native_unraised_stock_soldiers);
  out << ",\"native_unraised_stock_ready\":" << mobilization.native_unraised_stock_ready
      << ",\"component_combination\":\"maximum_proven_component\"";
  out << ",\"unraised_lower_soldiers\":";
  Nullable(out, mobilization.unraised_lower_soldiers);
  out << ",\"unraised_lower_ready\":" << mobilization.unraised_lower_ready
      << ",\"raised_commandable_lower_soldiers\":";
  Nullable(out, mobilization.raised_commandable_lower_soldiers);
  out << ",\"raised_lower_ready\":" << mobilization.raised_lower_ready
      << ",\"executable_lower_soldiers\":";
  Nullable(out, mobilization.executable_lower_soldiers);
  out << ",\"executable_lower_ready\":" << mobilization.executable_lower_ready
      << "},\"actor_lower_soldiers\":";
  Nullable(out, sample.actor_lower_soldiers);
  out << ",\"enemy_upper_soldiers\":";
  Nullable(out, sample.enemy_upper_soldiers);
  out << ",\"enemy_force_coverage_complete\":" << sample.enemy_force_coverage_complete
      << ",\"complete_initial_participants_ready\":" << sample.complete_initial_participants_ready
      << ",\"missing_required_domains\":";
  Strings(out, sample.missing_required_domains);
  out << '}';
  return out.str();
}

} // namespace xar::ck3_12004
