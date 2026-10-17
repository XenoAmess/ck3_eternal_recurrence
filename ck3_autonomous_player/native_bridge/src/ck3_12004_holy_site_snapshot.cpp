#include "xar_bridge/ck3_12004_holy_site_snapshot.hpp"

#include <windows.h>
#include <algorithm>
#include <array>
#include <limits>
#include <utility>

namespace xar::ck3_12004::religion::holy_site {
namespace {
constexpr std::uint32_t kAbsent = 0xFFFFFFFFU;
constexpr std::size_t kMaximumRows = 8192;
constexpr std::uintptr_t kHolySiteStorage = 0x5D1DE80;
constexpr std::uintptr_t kFaithStorage = 0x5D1E300;
constexpr std::uintptr_t kHolySiteWindowVtable = 72950584;

bool ProcessRead(void *, const void *address, void *out, std::size_t size) noexcept {
  SIZE_T got = 0;
  return address && out && size &&
      ReadProcessMemory(GetCurrentProcess(), address, out, size, &got) && got == size;
}

const void *At(const void *base, std::size_t offset) noexcept {
  const auto value = reinterpret_cast<std::uintptr_t>(base);
  return value && offset <= std::numeric_limits<std::uintptr_t>::max() - value
      ? reinterpret_cast<const void *>(value + offset) : nullptr;
}

template <class T> bool Read(const Bindings &b, const void *base,
    std::size_t offset, T &out) noexcept {
  const auto *address = At(base, offset);
  return b.read_memory && address && b.read_memory(b.read_context, address, &out, sizeof(out));
}

struct Array {
  const void *data = nullptr;
  std::uint32_t capacity = 0, count = 0;
  const void *allocator = nullptr;
  friend bool operator==(const Array &, const Array &) = default;
};

bool Header(const Bindings &b, const void *base, std::size_t offset, Array &a) noexcept {
  const auto *header = At(base, offset);
  return Read(b, header, 0, a.data) && Read(b, header, 8, a.capacity) &&
      Read(b, header, 12, a.count) && Read(b, header, 16, a.allocator) &&
      a.count <= a.capacity && a.count <= kMaximumRows && (a.count == 0 || a.data);
}

bool Ids(const Bindings &b, const void *base, std::size_t offset,
    std::vector<std::uint32_t> &out) {
  Array before{}, after{};
  out.clear();
  if (!Header(b, base, offset, before)) return false;
  out.resize(before.count);
  if (before.count && (!b.read_memory || !b.read_memory(b.read_context,
      before.data, out.data(), out.size() * sizeof(std::uint32_t)))) return false;
  return Header(b, base, offset, after) && before == after;
}

const void *Resolve(const Bindings &b, void **global, std::uint32_t id,
    std::size_t identity_offset) noexcept {
  const void *storage = nullptr, *rows = nullptr, *object = nullptr;
  std::uint32_t capacity = 0, actual_id = kAbsent;
  if (id == kAbsent || !Read(b, global, 0, storage) || !storage ||
      !Read(b, storage, 0x20, rows) || !rows ||
      !Read(b, storage, 0x2C, capacity) || (id & 0xFFFFFFU) >= capacity ||
      !Read(b, rows, static_cast<std::size_t>(id & 0xFFFFFFU) * 16 + 8, object) ||
      !object || !Read(b, object, identity_offset, actual_id) || actual_id != id) return nullptr;
  return object;
}

bool TypeKey(const Bindings &b, const void *site, std::string &out) {
  const void *type = nullptr, *text = nullptr;
  std::uint32_t magic = 0;
  std::uint64_t size = 0, capacity = 0;
  if (!Read(b, site, 0x20, type) || !type || !Read(b, type, 0x38, magic) ||
      magic != 0x4744624FU) return false;
  const auto *key = At(type, 0x18);
  if (!Read(b, key, 0x10, size) || !Read(b, key, 0x18, capacity) ||
      size == 0 || size > 1024 || size > capacity || (capacity < 16 && capacity != 15)) return false;
  text = key;
  if (capacity >= 16 && (!Read(b, key, 0, text) || !text)) return false;
  std::array<char, 1025> bytes{};
  if (!b.read_memory(b.read_context, text, bytes.data(), static_cast<std::size_t>(size) + 1) ||
      bytes[static_cast<std::size_t>(size)] != 0) return false;
  out.assign(bytes.data(), static_cast<std::size_t>(size));
  return true;
}

bool ReadInventory(const Bindings &b, const void *site, std::uint32_t id,
    Inventory &out) {
  out = {};
  out.owner_holy_site_id = id;
  std::uint32_t native_site = kAbsent, native_character = kAbsent;
  if (!Read(b, site, 0x28 + 0x3C, native_site) ||
      !Read(b, site, 0x28 + 0x38, native_character)) {
    out.unavailable_reason = "inventory_owner_fields_unavailable";
    return false;
  }
  if (native_site != kAbsent) out.native_holy_site_owner_id = native_site;
  if (native_character != kAbsent) out.native_character_owner_id = native_character;
  // Registered HolySite.GetInventory: site+28. Registered Inventory.GetArtifacts
  // and its destructor agree on u32 array inventory+58, with native row order.
  if (!Ids(b, site, 0x28 + 0x58, out.artifact_ids)) {
    out.unavailable_reason = "inventory_artifact_array_unavailable";
    return false;
  }
  out.available = true;
  return true;
}

void ReadRoster(const Bindings &b, Snapshot &out) {
  const void *storage = nullptr, *rows = nullptr;
  std::uint32_t count = 0;
  if (!Read(b, b.holy_site_storage, 0, storage) || !storage ||
      !Read(b, storage, 0x20, rows) || !Read(b, storage, 0x2C, count) ||
      count > kMaximumRows || (count && !rows)) return;
  out.loaded_registry_slot_count = count;
  for (std::uint32_t index = 0; index < count; ++index) {
    const void *site = nullptr;
    if (!Read(b, rows, static_cast<std::size_t>(index) * 16 + 8, site)) {
      ++out.loaded_registry_unreadable_slots; continue;
    }
    if (!site) continue;
    RosterEntry entry{};
    std::uint32_t magic = 0;
    if (!Read(b, site, 0x10, entry.holy_site_id) || !Read(b, site, 0x14, magic) ||
        magic != 0x486F5374U || entry.holy_site_id == kAbsent ||
        (entry.holy_site_id & 0xFFFFFFU) != index ||
        Resolve(b, b.holy_site_storage, entry.holy_site_id, 0x10) != site ||
        !TypeKey(b, site, entry.type_key) || !Read(b, site, 0xB0, entry.barony_title_id)) {
      ++out.loaded_registry_unreadable_slots; continue;
    }
    out.loaded_registry_roster.push_back(std::move(entry));
  }
  const void *after_storage = nullptr, *after_rows = nullptr;
  std::uint32_t after_count = 0;
  out.loaded_registry_roster_available = Read(b, b.holy_site_storage, 0, after_storage) &&
      after_storage == storage && Read(b, storage, 0x20, after_rows) && after_rows == rows &&
      Read(b, storage, 0x2C, after_count) && after_count == count;
}

bool ReadSite(const Bindings &b, std::uint32_t id, Site &out) {
  out = {};
  out.holy_site_id = id;
  out.inventory.owner_holy_site_id = id;
  out.inventory.unavailable_reason = "holy_site_inventory_not_read";
  const auto fail = [&](const char *why) { out.unavailable_reason = why; return false; };
  const auto *site = Resolve(b, b.holy_site_storage, id, 0x10);
  if (!site) return fail("holy_site_full_reference_unavailable");
  if (!TypeKey(b, site, out.type_key)) return fail("holy_site_type_key_unavailable");
  if (!Read(b, site, 0xB0, out.barony_title_id)) return fail("holy_site_barony_id_unavailable");
  std::vector<std::uint32_t> faith_ids;
  if (!Ids(b, site, 0x98, faith_ids)) return fail("holy_site_faith_array_unavailable");
  for (const auto faith_id : faith_ids) {
    FaithRelation relation{};
    relation.faith_id = faith_id;
    const auto *faith = Resolve(b, b.faith_storage, faith_id, 8);
    std::vector<std::uint32_t> sites, eminent;
    if (!faith) relation.unavailable_reason = "faith_full_reference_unavailable";
    else if (!Ids(b, faith, 0x890, sites) || !Ids(b, faith, 0x8A8, eminent))
      relation.unavailable_reason = "faith_holy_site_membership_unavailable";
    else {
      relation.faith_lists_site = std::find(sites.begin(), sites.end(), id) != sites.end();
      relation.eminent = std::find(eminent.begin(), eminent.end(), id) != eminent.end();
      relation.available = true;
    }
    out.associated_faiths.push_back(std::move(relation));
  }
  if (!ReadInventory(b, site, id, out.inventory)) return fail("holy_site_inventory_unavailable");
  const auto *after = Resolve(b, b.holy_site_storage, id, 0x10);
  std::vector<std::uint32_t> after_faiths;
  if (after != site || !Ids(b, site, 0x98, after_faiths) || after_faiths != faith_ids)
    return fail("holy_site_identity_or_faiths_changed");
  out.available = true;
  return true;
}

void ReadWindow(const Bindings &b, const void *owner, WindowModel &out) {
  out = {};
  const void *gfx = nullptr, *handler = nullptr, *window = nullptr;
  const auto fail = [&](const char *why) { out.unavailable_reason = why; };
  if (!Read(b, owner, 0x10, gfx) || !gfx || !Read(b, gfx, 0x88, handler) || !handler ||
      !Read(b, handler, 0x5D8, window)) return fail("holy_site_window_owner_chain_unavailable");
  out.present = window != nullptr;
  if (!window) { out.available = true; return; }
  std::uintptr_t vtable = 0;
  const void *back_gfx = nullptr, *back_handler = nullptr, *root = nullptr;
  std::uint32_t site_id = kAbsent, item = kAbsent;
  if (!Read(b, window, 0, vtable) || vtable != b.image_base + kHolySiteWindowVtable ||
      !Read(b, window, 0x98, back_gfx) || back_gfx != gfx ||
      !Read(b, window, 0xA0, back_handler) || back_handler != handler ||
      !Read(b, window, 0x60, root) || !Read(b, window, 0xC8, site_id) ||
      !Read(b, window, 0xCC, item)) return fail("holy_site_window_type_or_backlinks_unavailable");
  out.root_present = root != nullptr;
  if (site_id != kAbsent) out.holy_site_id = site_id;
  if (item != kAbsent) out.holy_site_item_raw = item;
  out.available = true;
}
} // namespace

Bindings BindHolySiteSnapshotImage12004(std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (!base || sha != ck3_12004::kExecutableSha256) return b;
  b.enabled = true;
  b.image_base = base;
  b.holy_site_storage = reinterpret_cast<void **>(base + kHolySiteStorage);
  b.faith_storage = reinterpret_cast<void **>(base + kFaithStorage);
  b.read_memory = &ProcessRead;
  return b;
}

bool ReadHolySiteSnapshot12004(const Bindings &b, const void *owner,
    const ck3_12002::religion::Context &context,
    std::optional<std::uint32_t> requested, Snapshot &out) noexcept {
  out = {};
  out.capture_epoch = context.capture_epoch;
  out.date_raw = context.date_raw;
  out.played_character_id = context.played_character_id;
  out.player_rite_id = context.rite_id;
  out.player_faith_id = context.faith_id;
  out.requested_holy_site_id = requested;
  try {
    if (!b.enabled || !b.image_base || !b.read_memory || !context.available ||
        !context.faith_id || !context.capture_epoch || context.played_character_id <= 0) {
      out.unavailable_reason = "current_player_religion_context_unavailable"; return false;
    }
    const auto *faith = Resolve(b, b.faith_storage, *context.faith_id, 8);
    if (!faith || !Ids(b, faith, 0x890, out.current_faith_holy_site_ids)) {
      out.unavailable_reason = "current_faith_holy_site_array_unavailable"; return false;
    }
    for (const auto id : out.current_faith_holy_site_ids) {
      Site site{};
      (void)ReadSite(b, id, site);
      out.current_faith_sites.push_back(std::move(site));
    }
    ReadRoster(b, out);
    ReadWindow(b, owner, out.window_model);
    const auto selected = requested ? requested : out.window_model.holy_site_id;
    out.selection_source = requested ? "explicit_full_reference" : "registered_window_model";
    if (selected) {
      out.selected_holy_site.emplace();
      (void)ReadSite(b, *selected, *out.selected_holy_site);
    }
    std::vector<std::uint32_t> after_ids;
    if (Resolve(b, b.faith_storage, *context.faith_id, 8) != faith ||
        !Ids(b, faith, 0x890, after_ids) || after_ids != out.current_faith_holy_site_ids) {
      out.unavailable_reason = "current_faith_holy_site_array_changed"; return false;
    }
    out.available = true;
    return true;
  } catch (...) { out.unavailable_reason = "holy_site_snapshot_copy_exception"; return false; }
}
} // namespace xar::ck3_12004::religion::holy_site
