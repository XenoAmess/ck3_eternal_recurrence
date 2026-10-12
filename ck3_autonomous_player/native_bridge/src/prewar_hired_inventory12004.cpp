#include "xar_bridge/prewar_hired_inventory12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <algorithm>
#include <cstring>
#include <limits>
#include <set>
#include <utility>

#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12004 {
namespace {

constexpr std::int32_t kMaximumRegistryCapacity = 1'000'000;
constexpr std::size_t kMaximumEmployers = 256;
constexpr std::size_t kMaximumOrganisations = 8192;
constexpr std::int32_t kMaximumRoster = 65'536;
constexpr std::int32_t kMaximumRegimentOccurrences = 262'144;

template <class T> bool Read(const void *source, std::size_t offset, T &value) noexcept {
  if (source == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&value, static_cast<const std::byte *>(source) + offset, sizeof(T));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

template <class Function, class Value>
bool Call(Function function, void *receiver, Value &value) noexcept {
  if (function == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    value = function(receiver);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

template <class T>
bool ReadOptional(const void *source, std::size_t offset,
                  std::optional<T> &output) noexcept {
  T value{};
  if (!Read(source, offset, value)) {
    output.reset();
    return false;
  }
  output = value;
  return true;
}

struct Registry {
  const void *entries = nullptr;
  void *fallback = nullptr;
  std::int32_t capacity = 0;
};

bool ReadRegistry(void **slot, void **fallback_slot, Registry &registry) noexcept {
  void *storage = nullptr;
  if (!Read(slot, 0, storage) || storage == nullptr ||
      !Read(storage, 0x20, registry.entries) ||
      !Read(storage, 0x2C, registry.capacity) ||
      registry.capacity < 0 || registry.capacity > kMaximumRegistryCapacity ||
      (registry.capacity != 0 && registry.entries == nullptr)) return false;
  return fallback_slot == nullptr || Read(fallback_slot, 0, registry.fallback);
}

void ReadRegiment(const Registry &persistent, std::int32_t id,
                  std::int32_t source_index, PrewarHiredRegiment12004 &row) {
  row.source_index = source_index;
  row.persistent_regiment_id = id;
  row.failure = "persistent_full_generation_unavailable";
  if (id == -1) return;
  const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
  if (index >= static_cast<std::uint32_t>(persistent.capacity)) return;
  void *regiment = nullptr;
  if (!Read(persistent.entries, static_cast<std::size_t>(index) * 0x10 + 8, regiment) ||
      regiment == nullptr || regiment == persistent.fallback) return;
  std::int32_t actual = -1;
  std::uint32_t magic = 0;
  if (!Read(regiment, 0x10, actual) || !Read(regiment, 0x14, magic)) return;
  row.observed_full_id = actual;
  row.observed_magic = magic;
  if (actual != id || magic != 0x52656769U) return;
  std::int32_t owner = -1, capacity = 0;
  if (!Read(regiment, 0x12C, owner) || !Read(regiment, 0x128, capacity)) {
    row.failure = "persistent_inventory_fields_unavailable";
    return;
  }
  row.persistent_owner_character_id = owner;
  row.native_capacity_raw = capacity;
  bool complete = capacity >= 0;
  row.chunks.reserve(7);
  for (std::int32_t ordinal = 0; ordinal < 7; ++ordinal) {
    const auto *chunk = static_cast<const std::byte *>(regiment) + 0x18 +
        static_cast<std::size_t>(ordinal) * 0x24;
    PrewarHiredChunk12004 value{};
    value.chunk_index = ordinal;
    bool copied = true;
    copied = ReadOptional(chunk, 0x00, value.maximum_soldiers_raw) && copied;
    copied = ReadOptional(chunk, 0x04, value.current_soldiers_raw) && copied;
    copied = ReadOptional(chunk, 0x08, value.persistent_regiment_backlink) && copied;
    copied = ReadOptional(chunk, 0x0C, value.native_chunk_index) && copied;
    copied = ReadOptional(chunk, 0x10, value.army_regiment_id) && copied;
    copied = ReadOptional(chunk, 0x14, value.pending_raw) && copied;
    copied = ReadOptional(chunk, 0x18, value.state_raw) && copied;
    value.fields_copied = copied;
    value.identity_ready = copied && value.persistent_regiment_backlink == id &&
        value.native_chunk_index == ordinal && *value.maximum_soldiers_raw >= 0 &&
        *value.current_soldiers_raw >= 0;
    complete = complete && value.identity_ready;
    row.chunks.push_back(value);
  }
  row.available = complete;
  row.failure = complete ? std::string{} : "persistent_chunk_inventory_partial";
}

void ReadRoster(void *organisation, std::size_t offset,
                const Registry &persistent, bool persistent_ready,
                std::int32_t &remaining_regiments,
                PrewarHiredOrganisation12004 &row) {
  const void *ids = nullptr;
  std::int32_t capacity = -1, count = -1;
  const bool copied = Read(organisation, offset, ids) &&
      Read(organisation, offset + 8, capacity) && Read(organisation, offset + 12, count);
  if (copied) {
    row.source_regiment_capacity = capacity;
    row.source_regiment_count = count;
  }
  if (!copied || capacity < 0 || capacity > kMaximumRoster || count < 0 ||
      count > capacity || (count != 0 && ids == nullptr)) {
    row.failure = "hired_persistent_roster_invalid";
    return;
  }
  if (count > remaining_regiments) {
    row.failure = "hired_persistent_sample_budget_exceeded";
    return;
  }
  remaining_regiments -= count;
  row.persistent_roster_complete = persistent_ready || count == 0;
  std::set<std::int32_t> seen;
  row.regiments.reserve(static_cast<std::size_t>(count));
  for (std::int32_t ordinal = 0; ordinal < count; ++ordinal) {
    std::int32_t id = -1;
    PrewarHiredRegiment12004 regiment{};
    if (!Read(ids, static_cast<std::size_t>(ordinal) * 4, id)) {
      regiment.source_index = ordinal;
      regiment.failure = "hired_persistent_reference_unreadable";
    } else if (!persistent_ready) {
      regiment.source_index = ordinal;
      regiment.persistent_regiment_id = id;
      regiment.failure = "persistent_registry_unavailable";
    } else {
      ReadRegiment(persistent, id, ordinal, regiment);
    }
    if (!seen.insert(id).second) ++row.duplicate_persistent_occurrences;
    row.persistent_roster_complete = row.persistent_roster_complete && regiment.available;
    row.regiments.push_back(std::move(regiment));
  }
  if (!row.persistent_roster_complete && row.failure.empty())
    row.failure = "hired_persistent_roster_partial";
}

template <class Current, class IsMilitary>
bool ScanRegistry(const Registry &registry, PrewarHiredKind12004 kind,
                  Current current, IsMilitary is_military,
                  const Registry &persistent, bool persistent_ready,
                  std::int32_t &remaining_regiments,
                  PrewarHiredInventory12004 &out, std::int32_t &slots_scanned) {
  bool complete = true;
  for (std::int32_t index = 0; index < registry.capacity; ++index) {
    ++slots_scanned;
    void *organisation = nullptr;
    if (!Read(registry.entries, static_cast<std::size_t>(index) * 0x10 + 8, organisation))
      return false;
    if (organisation == nullptr || organisation == registry.fallback) continue;
    if (out.organisations.size() >= kMaximumOrganisations) return false;
    PrewarHiredOrganisation12004 row{};
    row.kind = kind;
    row.registry_slot_index = index;
    if (!Read(organisation, 0x10, row.full_id) || !Read(organisation, 0x14, row.magic)) {
      row.failure = "hired_registry_identity_unreadable";
      out.organisations.push_back(std::move(row));
      complete = false;
      continue;
    }
    const auto expected_magic = kind == PrewarHiredKind12004::mercenary
        ? 0x4D657263U : 0x486F4F72U;
    row.registry_identity_ready = row.full_id != -1 && row.magic == expected_magic &&
        (static_cast<std::uint32_t>(row.full_id) & 0xFFFFFFU) ==
            static_cast<std::uint32_t>(index);
    if (!row.registry_identity_ready) {
      row.failure = "hired_registry_full_generation_invalid";
      out.organisations.push_back(std::move(row));
      complete = false;
      continue;
    }
    std::int32_t employer = -1;
    if (!Read(organisation, kind == PrewarHiredKind12004::mercenary ? 0x48 : 0x80,
              employer)) {
      row.failure = "hired_employer_unreadable";
      out.organisations.push_back(std::move(row));
      complete = false;
      continue;
    }
    if (employer != -1) row.employer_character_id = employer;
    auto selected = std::find_if(out.employers.begin(), out.employers.end(),
        [employer](const auto &value) { return value.character_id == employer; });
    row.selected_employer = selected != out.employers.end();
    row.employer_identity_ready = row.selected_employer && selected->identity_ready;
    if (kind == PrewarHiredKind12004::mercenary) {
      row.military_kind = true;
    } else {
      bool military = false;
      if (Call(is_military, organisation, military)) row.military_kind = military;
    }
    // Only currently hired military organisations for selected employers
    // enter the force inventory. Every other employer/organisation identity
    // remains visible, without constructing price/reason/reinforcement data.
    if (row.selected_employer && row.military_kind == true) {
      std::int32_t soldiers = 0;
      if (Call(current, organisation, soldiers)) {
        row.native_current_soldiers = soldiers;
        row.native_current_ready = soldiers >= 0;
      }
      ReadRoster(organisation, kind == PrewarHiredKind12004::mercenary ? 0x30 : 0x68,
                 persistent, persistent_ready, remaining_regiments, row);
      if (!row.native_current_ready && row.failure.empty())
        row.failure = "hired_native_current_unavailable";
    }
    if (row.selected_employer && (!row.military_kind.has_value() ||
        !row.employer_identity_ready ||
        (row.military_kind == true && !row.native_current_ready))) complete = false;
    out.organisations.push_back(std::move(row));
  }
  return complete;
}

} // namespace

bool ReadPrewarHiredInventory12004(
    const ck3_12003::mercenary::CandidateBindings &mercenary,
    const ck3_12003::religion::holy_order::Bindings &holy_order,
    const ck3_12002::CoreBindings &core,
    const ck3_12002::ArmyBindings &armies,
    std::string_view executable_sha256,
    std::span<const std::int32_t> selected_employer_ids,
    PrewarHiredInventory12004 &output) noexcept {
  output = {};
  try {
    if (executable_sha256 != kExecutableSha256 || !core.enabled) {
      output.failure = "exact_12004_hired_bindings_required";
      return false;
    }
    output.exact_build_ready = true;
    const std::set<std::int32_t> unique(selected_employer_ids.begin(), selected_employer_ids.end());
    if (unique.empty() || unique.size() > kMaximumEmployers || unique.contains(-1) ||
        unique.size() != selected_employer_ids.size()) {
      output.failure = "selected_hired_employers_invalid";
      return false;
    }
    for (const auto id : selected_employer_ids) {
      PrewarHiredEmployer12004 row{};
      row.character_id = id;
      void *character = ck3_12002::ResolveCoreCharacter(core, id);
      std::int32_t actual = -1;
      std::uint32_t magic = 0;
      row.identity_ready = Read(character, 0x18, actual) && actual == id &&
          Read(character, 0x1C, magic) && magic == 0x43686172U;
      if (!row.identity_ready) row.failure = "hired_employer_full_generation_invalid";
      output.employers.push_back(std::move(row));
    }
    Registry persistent{}, companies{}, orders{};
    const bool persistent_ready = armies.enabled &&
        ReadRegistry(armies.persistent_regiment_storage_slot, nullptr, persistent);
    auto remaining_regiments = kMaximumRegimentOccurrences;
    if (mercenary.enabled &&
        ReadRegistry(mercenary.manager_slot, mercenary.fallback_slot, companies)) {
      output.mercenary_registry_capacity = companies.capacity;
      output.mercenary_registry_complete = ScanRegistry(companies,
          PrewarHiredKind12004::mercenary, mercenary.current_soldiers,
          holy_order.is_military, persistent, persistent_ready,
          remaining_regiments, output, output.mercenary_slots_scanned);
    }
    if (holy_order.enabled &&
        ReadRegistry(holy_order.manager_slot, holy_order.fallback_slot, orders)) {
      output.holy_order_registry_capacity = orders.capacity;
      output.holy_order_registry_complete = ScanRegistry(orders,
          PrewarHiredKind12004::holy_order, holy_order.current_soldiers,
          holy_order.is_military, persistent, persistent_ready,
          remaining_regiments, output, output.holy_order_slots_scanned);
    }
    bool complete = output.mercenary_registry_complete && output.holy_order_registry_complete;
    output.selected_physical_rosters_complete = complete;
    for (auto &employer : output.employers) {
      employer.mercenary_inventory_complete = output.mercenary_registry_complete && employer.identity_ready;
      employer.holy_order_inventory_complete = output.holy_order_registry_complete && employer.identity_ready;
      employer.physical_hired_rosters_complete = complete && employer.identity_ready;
      std::int64_t upper = 0;
      for (const auto &row : output.organisations) {
        if (row.employer_character_id != employer.character_id) continue;
        const bool ready = row.registry_identity_ready && row.employer_identity_ready &&
            row.military_kind.has_value() &&
            (row.military_kind == false || row.native_current_ready);
        if (!ready) {
          employer.physical_hired_rosters_complete = false;
          if (row.kind == PrewarHiredKind12004::mercenary) employer.mercenary_inventory_complete = false;
          else employer.holy_order_inventory_complete = false;
          continue;
        }
        if (row.military_kind != true) continue;
        employer.physical_hired_rosters_complete = employer.physical_hired_rosters_complete &&
            row.persistent_roster_complete;
        const auto soldiers = *row.native_current_soldiers;
        if (upper > std::numeric_limits<std::int64_t>::max() - soldiers) {
          employer.mercenary_inventory_complete = false;
          employer.holy_order_inventory_complete = false;
          employer.failure = "hired_stock_current_sum_overflow";
          continue;
        }
        upper += soldiers;
      }
      const bool employer_complete = employer.mercenary_inventory_complete && employer.holy_order_inventory_complete;
      if (employer_complete) employer.hired_stock_current_upper_bound = upper;
      else if (employer.failure.empty()) employer.failure = "hired_inventory_partial";
      complete = complete && employer_complete;
      output.selected_physical_rosters_complete = output.selected_physical_rosters_complete &&
          employer.physical_hired_rosters_complete;
    }
    if (!complete) output.failure = "hired_registry_or_current_inventory_partial";
    return complete;
  } catch (...) {
    output = {};
    output.failure = "hired_inventory_copy_exception";
    return false;
  }
}

} // namespace xar::ck3_12004
