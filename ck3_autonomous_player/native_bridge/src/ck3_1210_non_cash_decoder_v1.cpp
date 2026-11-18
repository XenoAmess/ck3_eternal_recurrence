#include "xar_bridge/ck3_1210_non_cash_decoder_v1.hpp"
#include <limits>

// Exact1210: GetPrestige 2DB4650->2DA2810; GetPiety 2DB4610->2DA27E0;
// Dynasty.GetPrestige 291C810->291A2B0; Character.GetDynasty
// 2DB9980->2D840A0; GetTreasury D9F070->D83AC0->A3BA90.
// All resource callbacks marshal through A3F3C0. Slot43 REPORT.json retains
// exact binary spans/hashes and the independent Q100000 type evidence.
namespace xar::ck3_1210 {
namespace {
constexpr std::uintptr_t kHouseStoreRva = 0x6A66340;
constexpr std::uintptr_t kDynastyStoreRva = 0x6A666D8;
constexpr std::uintptr_t kTitleStoreRva = 0x6A66348;
constexpr std::uint32_t kCharacterType = 0x43686172U, kLandType = 0x4C616E64U;
using Status = NonCashDecodeStatusV1;
struct Reader {
  NonCashReadMemoryV1 read;
  void *context;
  template <class T> bool Get(std::uintptr_t base, std::size_t offset,
      T &out) const noexcept {
    constexpr auto max = (std::numeric_limits<std::uintptr_t>::max)();
    return read != nullptr && base != 0 && offset <= max - base &&
        sizeof(T) - 1 <= max - (base + offset) &&
        read(context, base + offset, &out, sizeof(out));
  }
};
struct Resolution {
  std::uintptr_t store = 0, slots = 0, object = 0;
  std::int32_t capacity = 0, id = -1;
  friend bool operator==(const Resolution &, const Resolution &) = default;
};
Status Resolve(const Reader &r, std::uintptr_t slot, std::int32_t id,
    Resolution &out) noexcept {
  if (id == -1) return Status::source_unavailable;
  if (!r.Get(slot, 0, out.store)) return Status::read_failed;
  if (out.store == 0) return Status::source_unavailable;
  if (!r.Get(out.store, 0x20, out.slots) ||
      !r.Get(out.store, 0x2C, out.capacity)) return Status::read_failed;
  const auto index = static_cast<std::uint32_t>(id) & 0x00FFFFFFU;
  // Decoder scope bound follows the 24-bit index domain, not an engine limit.
  if (out.capacity < 0 || out.capacity > 0x01000000 || out.slots == 0 ||
      index >= static_cast<std::uint32_t>(out.capacity))
    return Status::source_unavailable;
  if (!r.Get(out.slots, static_cast<std::size_t>(index) * 0x10 + 8,
      out.object)) return Status::read_failed;
  if (out.object == 0) return Status::source_unavailable;
  if (!r.Get(out.object, 0x10, out.id)) return Status::read_failed;
  return out.id == id ? Status::decoded : Status::source_unavailable;
}
struct Sample {
  std::int32_t actor_id = -1, house_id = -1, dynasty_id = -1, title_id = -1;
  std::uint32_t actor_type = 0, title_type = 0;
  std::uintptr_t death = 0, living = 0, land = 0, primary_ids = 0;
  std::int32_t primary_count = 0;
  Resolution house{}, dynasty{}, title{};
  std::optional<std::int32_t> source_id;
  std::int64_t raw = 0;
  bool native_zero = false;
  friend bool operator==(const Sample &, const Sample &) = default;
};
Status ReadSample(const NonCashDecodeBindingsV1 &b, const Reader &r,
    std::uintptr_t actor, std::int32_t expected_id, NonCashResourceV1 kind,
    Sample &s) noexcept {
  if (!r.Get(actor, 0x18, s.actor_id) || !r.Get(actor, 0x1C, s.actor_type) ||
      !r.Get(actor, 0x1D0, s.death)) return Status::read_failed;
  if (expected_id == -1 || s.actor_id != expected_id ||
      s.actor_type != kCharacterType || s.death != 0) return Status::invalid_actor;
  if (kind == NonCashResourceV1::dynasty_renown) {
    if (!r.Get(actor, 0x158, s.house_id)) return Status::read_failed;
    auto status = Resolve(r, b.house_storage_slot, s.house_id, s.house);
    if (status != Status::decoded) return status;
    if (!r.Get(s.house.object, 0x2C, s.dynasty_id)) return Status::read_failed;
    status = Resolve(r, b.dynasty_storage_slot, s.dynasty_id, s.dynasty);
    if (status != Status::decoded) return status;
    if (!r.Get(s.dynasty.object, 0x160, s.raw)) return Status::read_failed;
    s.source_id = s.dynasty_id;
    return Status::decoded;
  }
  if (!r.Get(actor, 0x1B0, s.living)) return Status::read_failed;
  if (kind == NonCashResourceV1::prestige || kind == NonCashResourceV1::piety) {
    s.source_id = expected_id;
    if (s.living == 0) { s.native_zero = true; return Status::decoded; }
    return r.Get(s.living, kind == NonCashResourceV1::prestige ? 0x130 : 0x110,
        s.raw) ? Status::decoded : Status::read_failed;
  }
  if (kind != NonCashResourceV1::government_treasury) return Status::invalid_resource;
  if (s.living == 0) { s.native_zero = true; return Status::decoded; }
  // D83AC0 uses death-data only when alive-land is null. This scope already
  // proved death==null, so null land is the native no-primary-title zero branch.
  if (!r.Get(actor, 0x1C0, s.land)) return Status::read_failed;
  if (s.land == 0) { s.native_zero = true; return Status::decoded; }
  if (!r.Get(s.land, 0x204, s.primary_count)) return Status::read_failed;
  if (s.primary_count < 0) return Status::source_unavailable;
  if (s.primary_count == 0) { s.native_zero = true; return Status::decoded; }
  // Stock consumes only the first ID. No adjacent capacity, remaining IDs,
  // government flag, or budget routing is inferred.
  if (!r.Get(s.land, 0x1F8, s.primary_ids)) return Status::read_failed;
  if (s.primary_ids == 0) return Status::source_unavailable;
  if (!r.Get(s.primary_ids, 0, s.title_id)) return Status::read_failed;
  const auto status = Resolve(r, b.title_storage_slot, s.title_id, s.title);
  if (status != Status::decoded) return status;
  if (!r.Get(s.title.object, 0x14, s.title_type)) return Status::read_failed;
  if (s.title_type != kLandType) return Status::source_unavailable;
  if (!r.Get(s.title.object, 0x370, s.raw)) return Status::read_failed;
  s.source_id = s.title_id;
  return Status::decoded;
}
} // namespace

NonCashDecodeBindingsV1 BindNonCashDecodeImageV1(std::uintptr_t image_base,
    std::string_view sha) noexcept {
  NonCashDecodeBindingsV1 out{};
  constexpr auto max = (std::numeric_limits<std::uintptr_t>::max)();
  if (image_base == 0 || sha != kExecutableSha256 ||
      image_base > max - kDynastyStoreRva - (sizeof(std::uintptr_t) - 1)) return out;
  out.exact_build_admitted = true;
  out.house_storage_slot = image_base + kHouseStoreRva;
  out.dynasty_storage_slot = image_base + kDynastyStoreRva;
  out.title_storage_slot = image_base + kTitleStoreRva;
  return out;
}

bool DecodeNonCashRawV1(const NonCashDecodeBindingsV1 &b, NonCashReadMemoryV1 read,
    void *context, std::uintptr_t actor, std::int32_t expected_id,
    NonCashResourceV1 kind, NonCashRawDecodeV1 &out) noexcept {
  out = {};
  if (!b.exact_build_admitted) { out.status = Status::unsupported_build; return false; }
  switch (kind) {
  case NonCashResourceV1::prestige: case NonCashResourceV1::piety:
  case NonCashResourceV1::dynasty_renown: case NonCashResourceV1::government_treasury:
    break;
  default: out.status = Status::invalid_resource; return false;
  }
  if (expected_id == -1 || actor == 0) { out.status = Status::invalid_actor; return false; }
  const Reader r{read, context};
  Sample first{}, second{};
  out.status = ReadSample(b, r, actor, expected_id, kind, first);
  if (out.status != Status::decoded) return false;
  out.status = ReadSample(b, r, actor, expected_id, kind, second);
  if (out.status != Status::decoded) return false;
  if (first != second) { out.status = Status::source_changed; return false; }
  out.raw = first.raw;
  out.source_full_id = first.source_id;
  out.native_zero_branch = first.native_zero;
  return true;
}
} // namespace xar::ck3_1210
