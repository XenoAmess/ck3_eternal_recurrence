#include "council_observation65.hpp"
#include <array>
#include <cstring>
#include <limits>
#include <utility>

namespace xar::council_observation65 {
namespace {
constexpr std::uintptr_t kMaxImageRva = 0x6A6A1B0;
constexpr std::size_t kReadBytesLimit = 65536;
struct ReadRecord {
  std::uintptr_t address = 0;
  std::vector<std::byte> bytes;
  friend bool operator==(const ReadRecord &, const ReadRecord &) = default;
};
struct Store {
  std::uintptr_t object = 0, slots = 0;
  std::int32_t bound = 0;
};
struct Pass {
  const Bindings &b;
  const Access &a;
  const FrameSource &f;
  std::size_t bytes = 0;
  std::string_view reason = "council65_bad_read";
  std::vector<ReadRecord> trace;
  std::vector<TaskRow> rows;
  std::vector<std::uintptr_t> task_pointers, position_pointers;

  bool Block(std::uintptr_t from, void *to, std::size_t n) {
    if (!from || !n || from > std::numeric_limits<std::uintptr_t>::max() - (n - 1) ||
        n > kReadBytesLimit - bytes || trace.size() >= 4096) return false;
    ReadRecord r; r.address = from; r.bytes.resize(n);
    if (!a.copy(a.context, from, r.bytes.data(), n)) return false;
    std::memcpy(to, r.bytes.data(), n); bytes += n;
    trace.push_back(std::move(r)); return true;
  }
  template<class T> bool At(std::uintptr_t p, std::size_t offset, T &out) {
    if (!p || p > std::numeric_limits<std::uintptr_t>::max() - offset) return false;
    return Block(p + offset, &out, sizeof(out));
  }
  template<class T> bool Global(std::uintptr_t rva, T &out) {
    return At(b.image_base, rva, out);
  }
  bool StoreAt(std::uintptr_t rva, Store &s) {
    return Global(rva, s.object) && s.object &&
        At(s.object, 0x20, s.slots) && At(s.object, 0x2C, s.bound) &&
        s.bound >= 0 && s.bound <= 0x1000000 && (!s.bound || s.slots);
  }
  bool Resolve(const Store &s, std::int32_t id, std::size_t full_id_offset,
               std::uintptr_t &object) {
    if (id == -1) return false;
    const auto index = static_cast<std::uint32_t>(id) & 0xFFFFFFU;
    std::int32_t actual = -1;
    return index < static_cast<std::uint32_t>(s.bound) &&
        At(s.slots, static_cast<std::size_t>(index) * 16 + 8, object) && object &&
        At(object, full_id_offset, actual) && actual == id;
  }
  bool Key(std::uintptr_t object, std::uintptr_t vt_rva, std::string &key) {
    std::uintptr_t vt = 0;
    std::int32_t id = -1;
    std::uint32_t hash = 0, tag = 0;
    std::array<std::byte, 32> str{};
    if (!At(object, 0, vt) || vt != b.image_base + vt_rva ||
        !At(object, 0x10, id) || id == -1 || !At(object, 0x14, hash) ||
        !At(object, 0x38, tag) || tag != 0x4744624FU ||
        !At(object, 0x18, str)) return false;
    std::uint64_t length = 0, capacity = 0;
    std::memcpy(&length, str.data() + 16, 8);
    std::memcpy(&capacity, str.data() + 24, 8);
    // These are conservative local observation limits, not engine maxima.
    if (!length || length > kKeyLimit || capacity < length || capacity > 4096 ||
        (capacity < 16 && capacity != 15)) return false;
    std::uintptr_t data = object + 0x18;
    if (capacity >= 16) std::memcpy(&data, str.data(), sizeof(data));
    std::array<char, kKeyLimit + 1> text{};
    if (!Block(data, text.data(), static_cast<std::size_t>(length) + 1) ||
        text[length] != '\0') return false;
    for (std::size_t i = 0; i < length; ++i) {
      const unsigned char c = static_cast<unsigned char>(text[i]);
      if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
            (c >= '0' && c <= '9') || c == '_' || c == '-' || c == '.' || c == ':'))
        return false;
    }
    key.assign(text.data(), static_cast<std::size_t>(length)); return true;
  }
  bool Sample() {
    reason = "council65_frame_source";
    std::uintptr_t state = 0, data = 0, actor = 0, death = 0, owned = 0;
    std::int32_t date = 0;
    std::uint32_t actor_tag = 0;
    Store characters{}, tasks{};
    if (!Global(0x68B2FD0, state) || state != f.game_state ||
        !At(state, 0xA0, data) || data != f.game_data ||
        !At(state, 8, date) || date != f.date_raw ||
        !StoreAt(0x68A9868, characters) || characters.object != f.character_store ||
        !Resolve(characters, f.actor_id, 0x18, actor) || actor != f.actor ||
        !At(actor, 0x1C, actor_tag) || actor_tag != 0x43686172U ||
        !At(actor, 0x1D0, death) || death ||
        !At(actor, 0x1C0, owned) || !owned) return false;
    reason = "council65_manager_store";
    std::uintptr_t manager_vt = 0, manager_store = 0, store_vt = 0;
    if (data > std::numeric_limits<std::uintptr_t>::max() - 0x1EFA0) return false;
    const auto manager = data + 0x1EFA0;
    if (!At(manager, 0, manager_vt) || manager_vt != b.image_base + 0x4EA11E0 ||
        !At(manager, 0x20, manager_store) ||
        !StoreAt(0x6A67930, tasks) || tasks.object != manager_store ||
        !At(tasks.object, 0, store_vt) || store_vt != b.image_base + 0x4EA1290)
      return false;
    reason = "council65_owned_task_list";
    std::uintptr_t ids = 0, default_type = 0;
    std::int32_t count = 0;
    if (!Global(0x6A6A1B0, default_type) ||
        !At(owned, 0x248, ids) || !At(owned, 0x254, count) ||
        count < 0 || count > static_cast<std::int32_t>(kRowLimit) || (count && !ids))
      return false;
    for (std::int32_t i = 0; i < count; ++i) {
      TaskRow row;
      std::uintptr_t task = 0, task_vt = 0, type = 0, position = 0;
      std::int32_t owner = -1, holder_id = -1;
      std::uint32_t task_tag = 0;
      reason = "council65_task_identity";
      if (!At(ids, static_cast<std::size_t>(i) * 4, row.task_id) ||
          !Resolve(tasks, row.task_id, 0x10, task) ||
          !At(task, 0, task_vt) || task_vt != b.image_base + 0x4BB2860 ||
          !At(task, 0x14, task_tag) || task_tag != 0x4163436CU ||
          !At(task, 0x44, owner) || owner != f.actor_id ||
          !At(task, 0x18, type) || !type ||
          !At(type, 0x40, position) || !position) return false;
      reason = "council65_default_or_invalid_definition";
      if (type == default_type ||
          !Key(type, 0x50114C0, row.stored_task_type_key) ||
          !Key(position, 0x5012808, row.position_key)) return false;
      for (std::size_t n = 0; n < rows.size(); ++n) {
        if (rows[n].task_id == row.task_id || task_pointers[n] == task ||
            position_pointers[n] == position || rows[n].position_key == row.position_key) {
          reason = "council65_duplicate_source"; return false;
        }
      }
      reason = "council65_holder_identity";
      if (!At(task, 0x40, holder_id)) return false;
      if (holder_id != -1) {
        std::uintptr_t holder = 0, holder_death = 0, council = 0;
        std::int32_t reverse = -1;
        std::uint32_t tag = 0;
        if (!Resolve(characters, holder_id, 0x18, holder) ||
            !At(holder, 0x1C, tag) || tag != 0x43686172U ||
            !At(holder, 0x1D0, holder_death) ||
            !At(holder, 0x1B8, council) || !council ||
            !At(council, 0x108, reverse) || reverse != row.task_id) return false;
        row.holder_id = holder_id;
        row.holder_alive = holder_death == 0;
        row.current_type_source_verified = row.holder_alive;
      }
      task_pointers.push_back(task); position_pointers.push_back(position);
      rows.push_back(std::move(row));
    }
    return true;
  }
};
bool Fail(Observation &out, std::string_view reason) noexcept {
  out.rows.clear(); out.reason = reason; return false;
}
} // namespace
Bindings BindImage(std::uintptr_t base, std::string_view sha256) noexcept {
  return base && sha256 == kExecutableSha256 &&
      base <= std::numeric_limits<std::uintptr_t>::max() - kMaxImageRva - 8
      ? Bindings{base} : Bindings{};
}
bool Read(const Bindings &b, const Access &a, const FrameSource &f,
          Observation &out) noexcept {
  out.rows.clear(); out.reason = "council65_not_read";
  if (!BindImage(b.image_base, kExecutableSha256).image_base || !a.copy ||
      !a.consistent || !f.native_revision || f.actor_id == -1 ||
      !f.game_state || !f.game_data || !f.character_store || !f.actor)
    return Fail(out, "council65_missing_input");
  if (!a.consistent(a.context)) return Fail(out, "council65_consistency");
  try {
    Pass first{b, a, f}, second{b, a, f};
    if (!first.Sample()) return Fail(out, first.reason);
    if (!a.consistent(a.context)) return Fail(out, "council65_consistency");
    if (!second.Sample()) return Fail(out, second.reason);
    if (!a.consistent(a.context)) return Fail(out, "council65_consistency");
    if (first.trace != second.trace || first.rows != second.rows)
      return Fail(out, "council65_graph_changed");
    out.rows = std::move(second.rows); out.reason = {}; return true;
  } catch (...) { return Fail(out, "council65_copy_or_allocation_exception"); }
}
} // namespace xar::council_observation65
