#include "xar_bridge/ck3_12003_pilgrimage_candidate_route.hpp"

#include <array>
#include <cstring>
#include <sstream>

namespace xar::ck3_12003::religion::pilgrimage_route {
namespace {
template <class T> T Load(const void *object, std::size_t offset = 0) noexcept {
  T result{};
  std::memcpy(&result, static_cast<const std::byte *>(object) + offset, sizeof(result));
  return result;
}
template <class T> void Store(void *object, std::size_t offset, T value) noexcept {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}

class NativeCreationInput {
public:
  explicit NativeCreationInput(const Bindings &bindings) noexcept : bindings_(bindings) {}
  ~NativeCreationInput() { if (initialized_) bindings_.creation_input_destroy(bytes_.data()); }
  void initialize(std::int32_t actor_id, std::int32_t candidate) {
    // Exact local initializer in 2325435..2325620 (input = RSP+20).
    // Native array initializers install their embedded allocators and buffers.
    Store(bytes_.data(), 0, actor_id);
    Store<std::int32_t>(bytes_.data(), 4, -1);
    Store(bytes_.data(), 0x18, bindings_.participant_allocator);
    (void)bindings_.province_ids_initialize(bytes_.data() + 0x20);
    (void)bindings_.waypoints_initialize(bytes_.data() + 0x50);
    Store(bytes_.data(), 0xB8, bindings_.travel_option_allocator);
    Store(bytes_.data(), 0xD0, bindings_.descriptor_allocator);
    Store<std::int32_t>(bytes_.data(), 0xD8, -1);
    Store(bytes_.data(), 0xDC, Load<std::uint64_t>(bindings_.native_default_date));
    Store<std::int32_t>(bytes_.data(), 0xE4, -1);
    Store<std::int32_t>(bytes_.data(), 0xE8, -1);
    for (const auto offset : {0xF0U, 0x110U, 0x140U, 0x160U, 0x190U, 0x1B0U}) {
      Store<std::uint64_t>(bytes_.data(), offset + 0x18, 15);
    }
    (void)bindings_.root_construct(bytes_.data() + 0x1E0);
    Store<std::int32_t>(bytes_.data(), 0x348, 3);
    Store<std::int32_t>(bytes_.data(), 0x34C, -1);
    Store<std::uint8_t>(bytes_.data(), 0x352, 1);
    Store<std::int32_t>(bytes_.data(), 0x354, -1);
    initialized_ = true;
    // The actual caller passes insertion index/current count, begin and end.
    bindings_.province_ids_append(bytes_.data() + 0x20,
        Load<std::int32_t>(bytes_.data(), 0x2C), &candidate, &candidate + 1);
  }
  const void *get() const noexcept { return bytes_.data(); }
  NativeCreationInput(const NativeCreationInput &) = delete;
  NativeCreationInput &operator=(const NativeCreationInput &) = delete;
private:
  alignas(16) std::array<std::byte, kCreationInputBytes> bytes_{};
  const Bindings &bindings_;
  bool initialized_ = false;
};

class NativeTravelData {
public:
  explicit NativeTravelData(const Bindings &bindings) noexcept : bindings_(bindings) {}
  ~NativeTravelData() { if (constructed_) bindings_.data_destroy(bytes_.data()); }
  void construct(const void *input) {
    // This is the real fresh CData constructor from a creation input, not the
    // copy constructor or the live CTravelPlan constructor/global counter path.
    (void)bindings_.data_construct(bytes_.data(), input);
    constructed_ = true;
  }
  void *get() noexcept { return bytes_.data(); }
  NativeTravelData(const NativeTravelData &) = delete;
  NativeTravelData &operator=(const NativeTravelData &) = delete;
private:
  alignas(16) std::array<std::byte, kTravelDataBytes> bytes_{};
  const Bindings &bindings_;
  bool constructed_ = false;
};

std::string Quote(std::string_view text) {
  static constexpr char hex[] = "0123456789abcdef";
  std::string result = "\"";
  for (const unsigned char byte : text) {
    if (byte == '"' || byte == '\\') { result += '\\'; result += static_cast<char>(byte); }
    else if (byte < 0x20) { result += "\\u00"; result += hex[byte >> 4]; result += hex[byte & 15]; }
    else result += static_cast<char>(byte);
  }
  return result + '"';
}
} // namespace

Bindings BindPlayerPilgrimageCandidateRouteImage12003(
    std::uintptr_t base, std::string_view sha) noexcept {
  Bindings b{};
  if (base == 0 || sha != kExecutableSha256) return b;
  b.enabled = true;
  b.provinces.enabled = true;
  b.provinces.game_state_slot = reinterpret_cast<void **>(base + kGameStateSlotRva);
  b.participant_allocator = reinterpret_cast<const void *>(base + 0x54DEC70);
  b.travel_option_allocator = reinterpret_cast<const void *>(base + 0x54DEC68);
  b.descriptor_allocator = reinterpret_cast<const void *>(base + 0x54DEC78);
  b.native_default_date = reinterpret_cast<const std::uint64_t *>(base + 0x5C7DD38);
  b.province_ids_initialize = reinterpret_cast<ArrayInitialize>(base + 0xB2C530);
  b.waypoints_initialize = reinterpret_cast<ArrayInitialize>(base + 0xB2C460);
  b.province_ids_append = reinterpret_cast<ProvinceIdAppend>(base + 0xADD0D0);
  b.root_construct = reinterpret_cast<RootConstruct>(base + 0x889F60);
  b.creation_input_destroy = reinterpret_cast<NativeDestroy>(base + 0x9DDFF0);
  b.data_construct = reinterpret_cast<TravelDataConstruct>(base + 0x23237A0);
  b.data_destroy = reinterpret_cast<NativeDestroy>(base + 0x9DE150);
  b.start_province = reinterpret_cast<StartProvince>(base + 0x2324970);
  b.evaluate_route = reinterpret_cast<RouteEvaluate>(base + 0x2329550);
  b.evaluate_arrival = reinterpret_cast<ArrivalEvaluate>(base + 0x232A090);
  return b;
}

bool ReadPlayerPilgrimageCandidateRoute12003(const Bindings &b, void *character,
    std::int32_t id, std::int32_t date, std::uint64_t epoch,
    std::int32_t candidate_id, Terms &out) noexcept {
  out = {};
  out.capture_epoch = epoch; out.date_raw = date; out.played_character_id = id;
  out.candidate_province_id = candidate_id;
  if (!b.enabled || !b.participant_allocator || !b.travel_option_allocator ||
      !b.descriptor_allocator || !b.native_default_date || !b.province_ids_initialize ||
      !b.waypoints_initialize || !b.province_ids_append || !b.root_construct ||
      !b.creation_input_destroy || !b.data_construct || !b.data_destroy ||
      !b.start_province || !b.evaluate_route || !b.evaluate_arrival) return false;
  if (!character || id <= 0 || Load<std::int32_t>(character, 0x18) != id) {
    out.unavailable_reason = "played_character_unavailable"; return false;
  }
  const auto *candidate = ck3_12002::ResolveObjectiveProvince(b.provinces, candidate_id);
  if (!candidate) { out.unavailable_reason = "candidate_province_unavailable"; return false; }
  try {
    NativeCreationInput input(b);
    input.initialize(id, candidate_id);
    NativeTravelData data(b);
    data.construct(input.get());
    const auto *rows = Load<const std::byte *>(data.get(), 0x360);
    const auto count = Load<std::int32_t>(data.get(), 0x36C);
    const auto next_index = Load<std::int32_t>(data.get(), 0x83C);
    if (Load<std::int32_t>(data.get(), 8) != id || !rows || count != 1 || next_index != 0 ||
        Load<const void *>(rows, 8) != candidate) {
      out.unavailable_reason = "candidate_route_native_material_unavailable"; return false;
    }
    // 2324970 is the native start resolver also called by 2329550; it does not
    // initialize/register a plan. Preserve its native current-location fallback.
    const auto *start = b.start_province(data.get());
    if (!start || ck3_12002::ResolveObjectiveProvince(b.provinces,
        Load<std::int32_t>(start, 0x10)) != start) {
      out.unavailable_reason = "native_start_province_unavailable"; return false;
    }
    out.native_start_province_id = Load<std::int32_t>(start, 0x10);
    out.route_valid = b.evaluate_route(data.get());
    if (*out.route_valid) {
      // Native evaluator writes the destination's 8-byte Date at +38. Only
      // its first raw int32 is the existing public DateRaw representation.
      b.evaluate_arrival(data.get());
      out.outbound_arrival_date_raw = Load<std::int32_t>(rows, 0x38);
    }
    out.available = true; out.unavailable_reason.clear();
    return true;
  } catch (...) { out.unavailable_reason = "candidate_route_native_copy_exception"; return false; }
}

std::string SerializePlayerPilgrimageCandidateRoute12003(const Terms &t) {
  std::ostringstream out;
  out << std::boolalpha << "{\"schema\":" << Quote(kSchema)
      << ",\"configuration_source\":" << Quote(kConfigurationSource)
      << ",\"read_only\":true,\"available\":" << t.available
      << ",\"unavailable_reason\":" << (t.available ? "null" : Quote(t.unavailable_reason))
      << ",\"capture_epoch\":" << t.capture_epoch << ",\"date_raw\":" << t.date_raw
      << ",\"played_character_id\":" << t.played_character_id
      << ",\"candidate_province_id\":" << t.candidate_province_id
      << ",\"native_start_province_id\":";
  if (t.native_start_province_id) out << *t.native_start_province_id; else out << "null";
  out << ",\"route_valid\":";
  if (t.route_valid) out << *t.route_valid; else out << "null";
  out << ",\"outbound_arrival_date_raw\":";
  if (t.outbound_arrival_date_raw) out << *t.outbound_arrival_date_raw; else out << "null";
  out << '}';
  return out.str();
}

} // namespace xar::ck3_12003::religion::pilgrimage_route
