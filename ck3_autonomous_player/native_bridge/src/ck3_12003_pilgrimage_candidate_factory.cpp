#include "xar_bridge/ck3_12003_pilgrimage_candidate_factory.hpp"

#include <cstring>
#include <utility>

namespace xar::ck3_12003::religion::pilgrimage_candidate_factory {
namespace {
template <class T> T Load(const void *object, std::size_t offset = 0) noexcept {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(object) + offset, sizeof(result));
  return result;
}
template <class T> void Store(void *object, std::size_t offset, T value) noexcept {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}
const void *ResolveFullReference(void **slot, std::uint32_t id) noexcept {
  if (!slot || !*slot || id == 0xFFFFFFFFU) return nullptr;
  const auto *storage = *slot;
  const auto capacity = Load<std::int32_t>(storage, 0x2C);
  const auto index = id & 0xFFFFFFU;
  const auto *rows = Load<const std::byte *>(storage, 0x20);
  if (!rows || capacity <= 0 || index >= static_cast<std::uint32_t>(capacity)) return nullptr;
  const auto *object = Load<const void *>(rows, static_cast<std::size_t>(index) * 0x10 + 8);
  return object && Load<std::uint32_t>(object, 0x10) == id ? object : nullptr;
}

class OwnedArray {
public:
  explicit OwnedArray(const void *allocator) noexcept { array_.allocator = allocator; }
  ~OwnedArray() {
    if (array_.data) {
      using NativeRelease = void (*)(const void *, void *, std::size_t);
      const auto *vtable = Load<const void *>(array_.allocator);
      const auto release = Load<NativeRelease>(vtable, 0x10);
      release(array_.allocator, array_.data, 8);
    }
  }
  NativeArray *get() noexcept { return &array_; }
  const NativeArray &view() const noexcept { return array_; }
  OwnedArray(const OwnedArray &) = delete;
  OwnedArray &operator=(const OwnedArray &) = delete;
private:
  NativeArray array_{};
};

class NativeScope {
public:
  NativeScope(const Bindings &b, std::int32_t actor) : bindings_(b) {
    (void)b.actor_root_construct(bytes_.data(), &actor);
  }
  NativeScope(const Bindings &b, std::int32_t province, std::int32_t actor) : bindings_(b) {
    (void)b.root_construct(bytes_.data());
    Store<std::int32_t>(bytes_.data(), 0, 8);
    Store<std::uint64_t>(bytes_.data(), 8, static_cast<std::uint64_t>(province));
    save(*b.host_token, 4, static_cast<std::uint32_t>(actor));
  }
  ~NativeScope() { bindings_.root_destroy(bytes_.data()); }
  void *get() noexcept { return bytes_.data(); }
  void special(const void *definition) {
    if (definition) save(*bindings_.special_token, 3, Load<std::uint32_t>(definition, 8) & 0xFFFFFFU);
  }
  void location(std::int32_t province) {
    save(*bindings_.location_token, 8, static_cast<std::uint64_t>(province));
  }
  NativeScope(const NativeScope &) = delete;
  NativeScope &operator=(const NativeScope &) = delete;
private:
  void save(std::int32_t name, std::int32_t kind, std::uint64_t payload) {
    const ScopeToken token{kind, 0, payload};
    bindings_.named_scope_save(bytes_.data() + 0x18, name, &token);
  }
  alignas(8) std::array<std::byte, 0x168> bytes_{};
  const Bindings &bindings_;
};

class NativeReason {
public:
  explicit NativeReason(const Bindings &b) noexcept : bindings_(b) {
    Store<std::size_t>(bytes_.data(), 0x18, 15);
  }
  ~NativeReason() { bindings_.reason_destroy(bytes_.data()); }
  void *get() noexcept { return bytes_.data(); }
  bool copy(std::string &out) const {
    const auto size = Load<std::size_t>(bytes_.data(), 0x10);
    const auto capacity = Load<std::size_t>(bytes_.data(), 0x18);
    if (size > capacity) return false;
    const auto *text = capacity < 16 ? reinterpret_cast<const char *>(bytes_.data())
                                  : Load<const char *>(bytes_.data());
    if (size && !text) return false;
    if (size == 0) out.clear(); else out.assign(text, size);
    return true;
  }
  NativeReason(const NativeReason &) = delete;
  NativeReason &operator=(const NativeReason &) = delete;
private:
  alignas(8) std::array<std::byte, 0x20> bytes_{};
  const Bindings &bindings_;
};

struct ReasonParameters {
  std::uint8_t mode[3]{2, 2, 0};
  std::uint8_t padding[5]{};
  void *reason = nullptr;
  void *evaluator = nullptr;
};
static_assert(offsetof(ReasonParameters, reason) == 8);
static_assert(offsetof(ReasonParameters, evaluator) == 0x10);
class OwnedEvaluator {
public:
  explicit OwnedEvaluator(const Bindings &b) : bindings_(b) {
    auto *storage = b.allocate(0xD8);
    if (storage) parameters_.evaluator = b.evaluator_construct(storage);
  }
  ~OwnedEvaluator() {
    if (parameters_.evaluator) {
      bindings_.evaluator_destroy(parameters_.evaluator);
      bindings_.deallocate(parameters_.evaluator, 0xD8);
    }
  }
  void *get() noexcept { return parameters_.evaluator; }
  void format(void *reason) {
    parameters_.reason = reason;
    Store<std::uint8_t>(get(), 0xD0, 0);
    bindings_.evaluator_prepare_first(get());
    bindings_.evaluator_prepare_second(get());
    Store<std::uint8_t>(get(), 0xD0, 1);
    // The native formatter may consume/replace the evaluator. Destroy only
    // the reloaded owning pointer in this very parameters block, as its caller.
    bindings_.evaluator_format(&parameters_.evaluator, &parameters_, reason);
  }
  OwnedEvaluator(const OwnedEvaluator &) = delete;
  OwnedEvaluator &operator=(const OwnedEvaluator &) = delete;
private:
  const Bindings &bindings_;
  ReasonParameters parameters_{};
};

PredicateResult ReadPredicate(const Bindings &b, const void *definition, NativeScope &scope) {
  PredicateResult result;
  NativeReason reason(b);
  OwnedEvaluator evaluator(b);
  if (evaluator.get()) {
    result.value = b.predicate_with_evaluator(definition, scope.get(), evaluator.get());
    evaluator.format(reason.get());
    result.reasons_available = reason.copy(result.reasons);
  } else {
    // This is the actual native caller's no-evaluator Boolean path. A missing
    // reason allocation does not manufacture a denial or change a false value.
    result.value = b.predicate(definition, scope.get());
  }
  return result;
}

bool ReadPhaseChoices(const Bindings &b, void *actor, std::int32_t id,
    const void *type, const void *special, Candidate &candidate) {
  OwnedArray choices(b.phase_choice_allocator);
  const PhaseContext context{type, actor, special};
  b.phase_offers(&context, 1, candidate.province, choices.get());
  const auto &view = choices.view();
  if (view.count < 0 || view.capacity < view.count || (view.count && !view.data)) return false;
  candidate.phase_choices.reserve(static_cast<std::size_t>(view.count));
  for (std::int32_t index = 0; index < view.count; ++index) {
    const auto *row = static_cast<const std::byte *>(view.data) + static_cast<std::size_t>(index) * 0x18;
    PhaseChoice choice;
    choice.phase_definition = Load<const void *>(row);
    choice.province = Load<const void *>(row, 8);
    choice.native_ai_choice_score = Load<std::int32_t>(row, 0x10);
    if (!choice.phase_definition || !choice.province || choice.province != candidate.province) return false;
    choice.phase_definition_index = Load<std::int32_t>(choice.phase_definition, 8);
    choice.province_id = Load<std::int32_t>(choice.province, 0x10);
    // Mode1 retains failed predicates and negative AI scores. Evaluate actual
    // shown/location independently; never adopt the mode0 positive-score filter.
    NativeScope shown_scope(b, id);
    shown_scope.special(special);
    choice.shown = ReadPredicate(b, static_cast<const std::byte *>(choice.phase_definition) + 0x10, shown_scope);
    NativeScope location_scope(b, id);
    location_scope.special(special); location_scope.location(choice.province_id);
    choice.location = ReadPredicate(b, static_cast<const std::byte *>(choice.phase_definition) + 0xE0, location_scope);
    choice.can_select = choice.shown.value && choice.location.value;
    candidate.phase_choices.push_back(std::move(choice));
  }
  return true;
}
} // namespace

Bindings BindPlayerPilgrimageCandidateFactoryImage12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (!base || sha != kExecutableSha256) return b;
  b.enabled = true; b.provinces.enabled = true;
  b.provinces.game_state_slot = reinterpret_cast<void **>(base + kGameStateSlotRva);
  b.character_rite = reinterpret_cast<ObjectGetter>(base + 0x28D2F90);
  b.rite_faith = reinterpret_cast<ObjectGetter>(base + 0x24FC560);
  b.holy_site_storage = reinterpret_cast<void **>(base + 0x5D1DE80);
  b.title_storage = reinterpret_cast<void **>(base + 0x5D1DAF8);
  b.province_array_allocator = reinterpret_cast<const void *>(base + 0x54DEF30);
  b.phase_choice_allocator = reinterpret_cast<const void *>(base + 0x54E13F8);
  b.filter_provinces = reinterpret_cast<ProvinceFilter>(base + 0x2C29710);
  b.root_construct = reinterpret_cast<RootConstruct>(base + 0x889F60);
  b.actor_root_construct = reinterpret_cast<ActorRootConstruct>(base + 0x9F9E20);
  b.root_destroy = reinterpret_cast<Destroy>(base + 0x87E0E0);
  b.named_scope_save = reinterpret_cast<NamedScopeSave>(base + 0x373A110);
  b.host_token = reinterpret_cast<const std::int32_t *>(base + 0x5D4BE40);
  b.special_token = reinterpret_cast<const std::int32_t *>(base + 0x5D4C0B8);
  b.location_token = reinterpret_cast<const std::int32_t *>(base + 0x5D4BDDC);
  b.predicate = reinterpret_cast<Predicate>(base + 0x372DF30);
  b.predicate_with_evaluator = reinterpret_cast<PredicateWithEvaluator>(base + 0x372E4F0);
  b.allocate = reinterpret_cast<Allocate>(base + 0x4223BB4);
  b.deallocate = reinterpret_cast<Deallocate>(base + 0x4223F64);
  b.evaluator_construct = reinterpret_cast<EvaluatorConstruct>(base + 0x37C66E0);
  b.evaluator_prepare_first = reinterpret_cast<Destroy>(base + 0x37EB190);
  b.evaluator_prepare_second = reinterpret_cast<Destroy>(base + 0x37EB290);
  b.evaluator_format = reinterpret_cast<EvaluatorFormat>(base + 0x375DCC0);
  b.evaluator_destroy = reinterpret_cast<Destroy>(base + 0x219FE20);
  b.reason_destroy = reinterpret_cast<Destroy>(base + 0x856050);
  b.total_phase_cap = reinterpret_cast<PhaseCap>(base + 0x3114510);
  b.same_province_phase_cap = reinterpret_cast<PhaseCap>(base + 0x31145A0);
  b.phase_offers = reinterpret_cast<PhaseOfferProvider>(base + 0x1A721E0);
  return b;
}

bool CollectPlayerPilgrimageCandidates12003(const Bindings &b, void *actor,
    std::int32_t id, const void *type, const void *special, PhaseRowView phase_rows,
    Candidates &out) noexcept {
  out = {}; out.played_character_id = id; out.configured_phase_count = phase_rows.count;
  if (!b.enabled || !b.character_rite || !b.rite_faith || !b.holy_site_storage || !b.title_storage ||
      !b.province_array_allocator || !b.phase_choice_allocator || !b.filter_provinces ||
      !b.root_construct || !b.actor_root_construct || !b.root_destroy || !b.named_scope_save ||
      !b.host_token || !b.special_token || !b.location_token || !b.predicate || !b.predicate_with_evaluator ||
      !b.allocate || !b.deallocate || !b.evaluator_construct || !b.evaluator_prepare_first ||
      !b.evaluator_prepare_second || !b.evaluator_format || !b.evaluator_destroy || !b.reason_destroy ||
      !b.total_phase_cap || !b.same_province_phase_cap || !b.phase_offers) return false;
  if (!actor || id <= 0 || Load<std::int32_t>(actor, 0x18) != id) {
    out.unavailable_reason = "played_character_unavailable"; return false;
  }
  if (!type || phase_rows.count < 0 || (phase_rows.count && !phase_rows.data)) {
    out.unavailable_reason = "native_activity_configuration_unavailable"; return false;
  }
  try {
    out.rite_id = Load<std::uint32_t>(actor, 0xB4);
    auto *rite = b.character_rite(actor);
    if (out.rite_id == 0xFFFFFFFFU || !rite || Load<std::uint32_t>(rite, 8) != out.rite_id) {
      out.unavailable_reason = "actual_player_rite_unavailable"; return false;
    }
    out.faith_id = Load<std::uint32_t>(rite, 0x4B8);
    auto *faith = b.rite_faith(rite);
    if (out.faith_id == 0xFFFFFFFFU || !faith || Load<std::uint32_t>(faith, 8) != out.faith_id) {
      out.unavailable_reason = "actual_player_rite_faith_unavailable"; return false;
    }
    out.native_filter = Load<std::int32_t>(type, 0x3BC0);
    out.single_location = Load<std::uint8_t>(type, 0x3BED) != 0;
    // This fixed pilgrimage factory assigns exact Faith HolySite/Title identity
    // pairing only for the proved native holy-site filter branch5.
    if (out.native_filter != 5) {
      out.unavailable_reason = "pilgrimage_native_filter_not_holy_sites"; return false;
    }
    OwnedArray provinces(b.province_array_allocator);
    b.filter_provinces(static_cast<const std::byte *>(type) + 0x3BC0, actor, provinces.get());
    const auto &native = provinces.view();
    const auto holy_count = Load<std::int32_t>(faith, 0x89C);
    const auto *holy_ids = Load<const std::uint32_t *>(faith, 0x890);
    if (native.count < 0 || native.capacity < native.count || (native.count && !native.data) ||
        holy_count != native.count || (holy_count && !holy_ids)) {
      out.unavailable_reason = "native_holy_site_candidate_material_unavailable"; return false;
    }
    NativeScope actor_scope(b, id);
    out.total_phase_cap = b.total_phase_cap(type, actor_scope.get());
    // In the exact single_location branch 11B6F9E skips the total-count gate.
    // The generic 11B6780 count is not raw phase_rows.count; do not fake it.
    // It is not required for fixed pilgrimage's genuine native bypass.
    out.candidates.reserve(static_cast<std::size_t>(native.count));
    for (std::int32_t index = 0; index < native.count; ++index) {
      Candidate candidate;
      candidate.holy_site_id = holy_ids[index];
      const auto *holy_site = ResolveFullReference(b.holy_site_storage, candidate.holy_site_id);
      if (!holy_site) { out.unavailable_reason = "holy_site_identity_unavailable"; return false; }
      candidate.title_id = Load<std::uint32_t>(holy_site, 0xB0);
      if (!ResolveFullReference(b.title_storage, candidate.title_id)) {
        out.unavailable_reason = "holy_site_title_identity_unavailable"; return false;
      }
      candidate.province = Load<const void *>(native.data, static_cast<std::size_t>(index) * sizeof(void *));
      if (!candidate.province) { out.unavailable_reason = "holy_site_province_unavailable"; return false; }
      candidate.province_id = Load<std::int32_t>(candidate.province, 0x10);
      if (ck3_12002::ResolveObjectiveProvince(b.provinces, candidate.province_id) != candidate.province) {
        out.unavailable_reason = "holy_site_province_identity_unavailable"; return false;
      }
      for (std::int32_t row = 0; row < phase_rows.count; ++row) {
        if (Load<std::int32_t>(phase_rows.data, static_cast<std::size_t>(row) * PhaseRowView::stride + 8) ==
            candidate.province_id) ++candidate.same_province_phase_count;
      }
      candidate.same_province_cap_applies = candidate.same_province_phase_count > 0;
      if (candidate.same_province_cap_applies) {
        candidate.same_province_phase_cap = b.same_province_phase_cap(type, actor_scope.get());
        candidate.same_province_cap_allows = candidate.same_province_phase_count < *candidate.same_province_phase_cap;
      }
      candidate.total_cap_applies = !out.single_location;
      if (!candidate.total_cap_applies) candidate.total_cap_allows = true;
      NativeScope province_scope(b, candidate.province_id, id);
      province_scope.special(special);
      candidate.location_predicate = ReadPredicate(b, static_cast<const std::byte *>(type) + 0x450, province_scope);
      if (!candidate.location_predicate.value || !candidate.same_province_cap_allows)
        candidate.can_select = false;
      else if (candidate.total_cap_allows) candidate.can_select = *candidate.total_cap_allows;
      if (!ReadPhaseChoices(b, actor, id, type, special, candidate)) {
        out.unavailable_reason = "native_phase_choice_material_unavailable"; return false;
      }
      out.candidates.push_back(std::move(candidate));
    }
    out.available = true; out.unavailable_reason.clear();
    return true;
  } catch (...) { out.unavailable_reason = "native_pilgrimage_candidate_copy_exception"; return false; }
}

} // namespace xar::ck3_12003::religion::pilgrimage_candidate_factory
