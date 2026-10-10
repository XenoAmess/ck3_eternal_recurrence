#include "xar_bridge/construction_owner_mode3_raw_receiver_12004.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <map>

namespace xar::ck3_12004::construction_owner_mode3 {
namespace {

constexpr std::uintptr_t module = 0x10000000;
constexpr std::uintptr_t province = 0x20000000;
constexpr std::uintptr_t title_storage = 0x30000000;
constexpr std::uintptr_t title_table = 0x31000000;
constexpr std::uintptr_t fallback_title = 0x40000000;
constexpr std::uintptr_t first_title = 0x41000000;
constexpr std::uintptr_t second_title = 0x42000000;
constexpr std::uintptr_t context = 0x50000000;
constexpr std::uintptr_t child_object = 0x60000000;
constexpr std::uintptr_t character_storage = 0x70000000;
constexpr std::uintptr_t character_table = 0x71000000;
constexpr std::uintptr_t character_object = 0x72000000;
constexpr std::uintptr_t fallback_character = 0x73000000;

struct Fixture {
  std::map<std::uintptr_t, std::uint8_t> bytes;
  std::uintptr_t expected_child_title = first_title;
  std::uintptr_t child_return = child_object;
  bool child_available = true;
  int missing_reads = 0;
  int child_calls = 0;

  template <typename T>
  void Put(std::uintptr_t address, const T &value) {
    const auto *source = reinterpret_cast<const std::uint8_t *>(&value);
    for (std::size_t i = 0; i < sizeof(value); ++i)
      bytes[address + i] = source[i];
  }

  void Remove(std::uintptr_t address, std::size_t size) {
    for (std::size_t i = 0; i < size; ++i) bytes.erase(address + i);
  }

  Fixture() {
    Put(province + 0x10, std::int32_t{71});
    Put(province + 0x620 + 0xF0, context);
    Put(context + 0x738, std::uint32_t{0x80000002u});
    Put(module + 0x5D1DAF8, title_storage);
    Put(module + 0x5D1DAE0, fallback_title);
    Put(title_storage + 0x2C, std::uint32_t{4});
    Put(title_storage + 0x20, title_table);
    Put(title_table + 2 * 16 + 8, first_title);
    Put(title_table + 3 * 16 + 8, second_title);
    Put(first_title + 0x10, std::uint32_t{0x80000002u});
    Put(first_title + 0xE8, std::uint32_t{0x09000003u});
    Put(first_title + 0x128, std::uint32_t{0x12000000u});
    Put(second_title + 0x10, std::uint32_t{0x08000003u});
    Put(second_title + 0x128, std::uint32_t{0xFF000000u});
    Put(fallback_title + 0x128, std::uint32_t{0x83000001u});
    Put(child_object + 0x1C, std::uint32_t{0x43686172u});
    Put(child_object + 0x18, std::uint32_t{0});
    Put(module + 0x5C67568, character_storage);
    Put(module + 0x5C67570, fallback_character);
    Put(character_storage + 0x2C, std::uint32_t{2});
    Put(character_storage + 0x20, character_table);
    Put(character_table + 16 + 8, character_object);
    Put(character_object + 0x18, std::uint32_t{0x83000001u});
    Put(character_object + 0x1C, std::uint32_t{0x43686172u});
    Put(fallback_character + 0x18, std::uint32_t{0xFFFFFFFFu});
    Put(fallback_character + 0x1C, std::uint32_t{0x12345678u});
  }

  static bool Read(void *opaque, const void *source, void *destination,
                   std::size_t size) {
    auto &f = *static_cast<Fixture *>(opaque);
    const auto address = reinterpret_cast<std::uintptr_t>(source);
    auto *out = static_cast<std::uint8_t *>(destination);
    for (std::size_t i = 0; i < size; ++i) {
      const auto found = f.bytes.find(address + i);
      if (found == f.bytes.end()) {
        ++f.missing_reads;
        return false;
      }
      out[i] = found->second;
    }
    return true;
  }

  static bool ReadChild(void *opaque, const RawReceiverAccessV1 &access,
                        std::uintptr_t title,
                        std::uintptr_t &returned) noexcept {
    auto &f = *static_cast<Fixture *>(opaque);
    ++f.child_calls;
    if (access.context != &f || title != f.expected_child_title ||
        !f.child_available) return false;
    returned = f.child_return;
    return true;
  }

  AggregateRawReceiverV1 Run() {
    const RawReceiverAccessV1 access{this, Read, module, true};
    const ReadActualTitleReturnV1 child{this, ReadChild};
    return ReadAggregateRawReceiverV1(access, province, 71, child);
  }

  void UseSuffix() {
    Put(child_object + 0x18, std::uint32_t{0xFFFFFFFFu});
  }
};

} // namespace

// Own2467660 branch cases use a typed synthetic child-return packet. They
// do not qualify38's child source. Central10 adds the connected real leaf
// composition and invokes these authored cases once; this file has no main.
int RunConstructionMode3RawReceiver12004NewCases() {
  int failures = 0;
  const auto require = [&](bool condition) {
    if (!condition) ++failures;
  };
  {
    Fixture f;
    const auto r = f.Run();
    require(r.observed && r.route == RawReceiverRouteV1::direct_child &&
            r.context_title_id_raw == 0x80000002u && r.child_id_raw == 0 &&
            r.returned_receiver_pointer == child_object && f.missing_reads == 0);
  }
  {
    Fixture f;
    f.Put(first_title + 0x10, std::uint32_t{0x81000002u});
    f.expected_child_title = fallback_title;
    const auto r = f.Run();
    require(r.observed && r.first_title_pointer == fallback_title &&
            r.returned_receiver_pointer == child_object);
  }
  {
    Fixture f;
    f.Put(module + 0x5D1DAF8, std::uintptr_t{0});
    f.Remove(province + 0x620 + 0xF0, sizeof(std::uintptr_t));
    f.Remove(context + 0x738, sizeof(std::uint32_t));
    f.expected_child_title = fallback_title;
    const auto r = f.Run();
    require(r.observed && !r.context_title_id_observed &&
            r.first_title_pointer == fallback_title && f.missing_reads == 0);
  }
  {
    Fixture f;
    f.UseSuffix();
    const auto r = f.Run();
    require(r.observed && r.secondary_title_pointer == fallback_title &&
            r.character_id_raw == 0x83000001u &&
            r.route == RawReceiverRouteV1::character_registry &&
            r.returned_receiver_pointer == character_object);
  }
  {
    Fixture f;
    f.UseSuffix();
    f.Put(second_title + 0x10, std::uint32_t{0x09000003u});
    f.Put(character_table + 8, character_object);
    f.Put(character_object + 0x18, std::uint32_t{0xFF000000u});
    const auto r = f.Run();
    require(r.observed && r.secondary_title_pointer == second_title &&
            r.character_id_raw == 0xFF000000u &&
            r.returned_receiver_pointer == character_object);
  }
  {
    Fixture f;
    f.UseSuffix();
    f.Put(character_object + 0x18, std::uint32_t{0x82000001u});
    const auto r = f.Run();
    require(r.observed && r.route == RawReceiverRouteV1::character_fallback &&
            r.returned_receiver_pointer == fallback_character &&
            r.returned_identity_observed && r.returned_tag_raw == 0x12345678u);
  }
  {
    Fixture f;
    f.UseSuffix();
    f.Put(module + 0x5C67568, std::uintptr_t{0});
    f.Remove(fallback_title + 0x128, sizeof(std::uint32_t));
    const auto r = f.Run();
    require(r.observed && !r.character_id_observed &&
            r.route == RawReceiverRouteV1::character_fallback &&
            f.missing_reads == 0);
  }
  {
    Fixture f;
    f.Put(child_object + 0x1C, std::uint32_t{0x12345678u});
    f.Remove(child_object + 0x18, sizeof(std::uint32_t));
    const auto r = f.Run();
    require(r.observed && !r.child_id_observed &&
            r.returned_receiver_pointer == character_object &&
            f.missing_reads == 0);
  }
  {
    Fixture f;
    f.Remove(first_title + 0x10, sizeof(std::uint32_t));
    const auto r = f.Run();
    require(!r.observed && r.failure == RawReceiverFailureV1::title_registry &&
            f.child_calls == 0);
  }
  {
    Fixture f;
    f.child_available = false;
    const auto r = f.Run();
    require(!r.observed && r.failure == RawReceiverFailureV1::child_return &&
            r.returned_receiver_pointer == 0);
  }
  {
    Fixture f;
    f.UseSuffix();
    f.Put(module + 0x5C67568, std::uintptr_t{0});
    f.Put(module + 0x5C67570, std::uintptr_t{0});
    const auto r = f.Run();
    require(r.observed && r.returned_receiver_pointer == 0 &&
            !r.returned_identity_observed &&
            r.route == RawReceiverRouteV1::character_fallback);
  }
  return failures;
}

} // namespace xar::ck3_12004::construction_owner_mode3
