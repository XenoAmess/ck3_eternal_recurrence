#include "xar_bridge/ck3_12003_title_laws_leaf.hpp"
#include "xar_bridge/ck3_12004_confucian_title_profile.hpp"

#include <array>
#include <bit>
#include <cstring>
#include <utility>

#if defined(_MSC_VER)
#include <Windows.h>
#endif

namespace xar::ck3_12003::title_laws {
namespace {

template <typename T>
bool Load(const void *base, std::size_t offset, T &value) noexcept {
  if (base == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(T));
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

bool Copy(const void *base, void *destination, std::size_t bytes) noexcept {
  if (base == nullptr || destination == nullptr) return false;
#if defined(_MSC_VER)
  __try {
#endif
    std::memcpy(destination, base, bytes);
    return true;
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return false; }
#endif
}

void *Resolve(const title_properties::Bindings &bindings,
              std::uint32_t id) noexcept {
  if (id == UINT32_MAX) return nullptr;
#if defined(_MSC_VER)
  __try {
#endif
    return ck3_12002::ResolveObjectiveTitle(bindings.title_holder.provinces,
                                          std::bit_cast<std::int32_t>(id));
#if defined(_MSC_VER)
  } __except (EXCEPTION_EXECUTE_HANDLER) { return nullptr; }
#endif
}

struct Header {
  std::uintptr_t vptr = 0, data = 0;
  std::uint32_t title_id = UINT32_MAX, raw_holder_id = UINT32_MAX;
  std::int32_t capacity = -1, count = -1;
};

bool Same(const Header &a, const Header &b) noexcept {
  return a.vptr == b.vptr && a.data == b.data && a.title_id == b.title_id &&
      a.raw_holder_id == b.raw_holder_id && a.capacity == b.capacity &&
      a.count == b.count;
}

bool ReadHeader(const title_properties::Bindings &bindings, const void *title,
                std::uint32_t requested, Header &out) noexcept {
  return Load(title, 0, out.vptr) &&
      out.vptr == bindings.image_base +
          bindings.primary_title_vtable_rva &&
      Load(title, 0x10, out.title_id) && out.title_id == requested &&
      Load(title, 0x128, out.raw_holder_id) &&
      Load(title, 0x228, out.data) && Load(title, 0x230, out.capacity) &&
      Load(title, 0x234, out.count) && out.count >= 0 &&
      out.count <= kMaximumLaws && out.capacity >= out.count &&
      out.capacity <= 1'000'000 && (out.count == 0 || out.data != 0);
}

struct LawSample {
  std::uintptr_t pointer = 0, vptr = 0;
  std::uint32_t id = 0, magic = 0;
  std::array<std::byte, 32> key_header{};
  std::string key;
};

bool ReadLaw(const title_properties::Bindings &bindings,
             std::uintptr_t pointer, LawSample &out) {
  if (pointer == 0) return false;
  const auto *law = reinterpret_cast<const void *>(pointer);
  out.pointer = pointer;
  if (!Load(law, 0, out.vptr) ||
      out.vptr != bindings.image_base + (bindings.actual4
          ? ck3_12004::confucian_titles::kCLawPrimaryVtableRva
          : kCLawPrimaryVtableRva) ||
      !Load(law, 0x10, out.id) || !Load(law, 0x38, out.magic) ||
      out.magic != kCLawDatabaseObjectMagic ||
      !Copy(static_cast<const std::byte *>(law) + 0x18,
            out.key_header.data(), out.key_header.size())) return false;
  std::uint64_t size = 0, capacity = 0;
  std::memcpy(&size, out.key_header.data() + 0x10, sizeof(size));
  std::memcpy(&capacity, out.key_header.data() + 0x18, sizeof(capacity));
  if (size == 0 || size >= kMaximumKeyBytes || capacity < size) return false;
  const void *text = static_cast<const std::byte *>(law) + 0x18;
  if (capacity >= 16) {
    std::uintptr_t heap = 0;
    std::memcpy(&heap, out.key_header.data(), sizeof(heap));
    if (heap == 0) return false;
    text = reinterpret_cast<const void *>(heap);
  }
  out.key.resize(static_cast<std::size_t>(size));
  if (!Copy(text, out.key.data(), out.key.size())) return false;
  char terminator = 1;
  if (!Load(text, static_cast<std::size_t>(size), terminator) || terminator != 0)
    return false;
  for (const unsigned char character : out.key)
    if (character < 0x21 || character > 0x7E) return false;
  std::uintptr_t after_vptr = 0;
  std::uint32_t after_id = 0, after_magic = 0;
  std::array<std::byte, 32> after_header{};
  return Load(law, 0, after_vptr) && after_vptr == out.vptr &&
      Load(law, 0x10, after_id) && after_id == out.id &&
      Load(law, 0x38, after_magic) && after_magic == out.magic &&
      Copy(static_cast<const std::byte *>(law) + 0x18,
           after_header.data(), after_header.size()) &&
      after_header == out.key_header;
}

struct Sample {
  Header header;
  std::vector<LawSample> rows;
};

bool Capture(const title_properties::Bindings &bindings, void *title,
             std::uint32_t requested, Sample &out) {
  if (!ReadHeader(bindings, title, requested, out.header)) return false;
  out.rows.reserve(static_cast<std::size_t>(out.header.count));
  const auto *slots = reinterpret_cast<const void *>(out.header.data);
  for (std::int32_t i = 0; i < out.header.count; ++i) {
    std::uintptr_t law_pointer = 0;
    if (!Load(slots, static_cast<std::size_t>(i) * sizeof(std::uintptr_t),
              law_pointer)) return false;
    LawSample law;
    if (!ReadLaw(bindings, law_pointer, law)) return false;
    for (const auto &old : out.rows)
      if (old.pointer == law.pointer || old.id == law.id || old.key == law.key)
        return false;
    out.rows.push_back(std::move(law));
  }
  Header after;
  return ReadHeader(bindings, title, requested, after) &&
      Same(out.header, after) && Resolve(bindings, requested) == title;
}

bool Same(const Sample &a, const Sample &b) noexcept {
  if (!Same(a.header, b.header) || a.rows.size() != b.rows.size()) return false;
  for (std::size_t i = 0; i < a.rows.size(); ++i) {
    const auto &x = a.rows[i];
    const auto &y = b.rows[i];
    if (x.pointer != y.pointer || x.vptr != y.vptr || x.id != y.id ||
        x.magic != y.magic || x.key_header != y.key_header || x.key != y.key)
      return false;
  }
  return true;
}

} // namespace

bool Read(const title_properties::Bindings &bindings, const game::Snapshot &frame,
          std::uint32_t requested, Observation &output) noexcept {
  output = {};
  output.date_raw = frame.date_raw;
  output.actor_character_id = frame.played_character_id;
  output.requested_title_full_id = requested;
  const auto fail = [&output](std::string_view reason) {
    output.unavailable_reason = reason;
    return false;
  };
  if (!bindings.enabled || bindings.image_base == 0 ||
      !bindings.title_holder.enabled ||
      !bindings.title_holder.provinces.enabled)
    return fail("title_laws_bindings_unavailable");
  if (!frame.paused || !frame.map_ready || !frame.has_played_character ||
      !frame.played_character_alive)
    return fail("paused_player_frame_unavailable");
  if (requested == UINT32_MAX) return fail("title_reference_absent");
  void *title = Resolve(bindings, requested);
  if (title == nullptr) return fail("title_generation_unavailable");
  try {
    Sample first, second;
    if (!Capture(bindings, title, requested, first) ||
        Resolve(bindings, requested) != title ||
        !Capture(bindings, title, requested, second) || !Same(first, second) ||
        Resolve(bindings, requested) != title)
      return fail("title_law_collection_or_identity_unavailable");
    std::vector<NamedLaw> rows;
    rows.reserve(first.rows.size());
    bool member = false;
    for (const auto &law : first.rows) {
      rows.push_back({law.id, law.key});
      member = member || law.key == kExpectedLawKey;
    }
    output.native_count = first.header.count;
    output.complete_laws = std::move(rows);
    output.temporal_head_of_faith_succession_law_member = member;
    output.available = true;
    output.unavailable_reason = {};
    return true;
  } catch (...) {
    // A partial collection, unsupported key size, allocation failure or failed
    // native leaf never turns into an empty collection or negative predicate.
    output.native_count.reset();
    output.complete_laws.reset();
    output.temporal_head_of_faith_succession_law_member.reset();
    return fail("title_law_observation_failed");
  }
}

} // namespace xar::ck3_12003::title_laws
