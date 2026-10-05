#include "xar_bridge/ck3_12003_context_sources.hpp"
#include "xar_bridge/battle_context_source_inputs_v1_serializer.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
void Require(bool value, const char *label) {
  if (!value) throw std::runtime_error(label);
}
struct Memory {
  struct Region { std::unique_ptr<std::byte[]> data; std::size_t size; };
  struct Denied { std::uintptr_t begin; std::size_t size; std::size_t attempts = 0; };
  std::vector<Region> regions;
  std::vector<Denied> denied;
  void *Allocate(std::size_t size) {
    auto data = std::make_unique<std::byte[]>(size);
    void *pointer = data.get();
    regions.push_back({std::move(data), size});
    return pointer;
  }
  template <typename T> void Put(void *p, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(p) + offset, &value, sizeof(value));
  }
  void Deny(const void *p, std::size_t offset, std::size_t size) {
    denied.push_back({reinterpret_cast<std::uintptr_t>(p) + offset, size});
  }
  std::size_t Attempts() const {
    std::size_t result = 0;
    for (const auto &d : denied) result += d.attempts;
    return result;
  }
  static bool Read(void *context, const void *p, void *output,
                   std::size_t size) noexcept {
    auto &m = *static_cast<Memory *>(context);
    const auto begin = reinterpret_cast<std::uintptr_t>(p);
    for (auto &d : m.denied) {
      if (begin < d.begin + d.size && d.begin < begin + size) {
        ++d.attempts;
        return false;
      }
    }
    for (const auto &r : m.regions) {
      const auto base = reinterpret_cast<std::uintptr_t>(r.data.get());
      if (begin >= base && begin - base <= r.size &&
          size <= r.size - static_cast<std::size_t>(begin - base)) {
        std::memcpy(output, p, size);
        return true;
      }
    }
    return false;
  }
};
void *provider_pointer = nullptr;
std::size_t provider_calls = 0;
void *Provider() { ++provider_calls; return provider_pointer; }

struct Fixture {
  Memory m;
  xar::ck3_12002::ContextSourceBindingsV1 b;
  void *character = m.Allocate(0x1C0);
  void *carrier = m.Allocate(0x100);
  void *army = m.Allocate(0x130);
  void *army_fallback = m.Allocate(0x130);
  void *second = m.Allocate(0x180);
  void *second_fallback = m.Allocate(0x180);
  void *provider = m.Allocate(0x1648);
  void *definition = m.Allocate(0xC0);
  void *army_store_slot = m.Allocate(8);
  void *army_fallback_slot = m.Allocate(8);
  void *second_store_slot = m.Allocate(8);
  void *second_fallback_slot = m.Allocate(8);
  static constexpr std::uint32_t army_id = 0xAB000001U;
  static constexpr std::uint32_t second_id = 0xCD000001U;

  void Storage(void *slot, void *object) {
    void *storage = m.Allocate(0x30);
    void *table = m.Allocate(32);
    m.Put(slot, 0, storage);
    m.Put(storage, 0x2C, std::uint32_t{2});
    m.Put(storage, 0x20, table);
    m.Put(table, 24, object);
  }
  Fixture() {
    b.enabled = true;
    b.pre_291e210_1640_enabled = true;
    b.army_internal_storage_slot = army_store_slot;
    b.army_internal_fallback_slot = army_fallback_slot;
    b.pre_291e210_second_storage_slot = second_store_slot;
    b.pre_291e210_second_fallback_slot = second_fallback_slot;
    b.provider = &Provider;
    b.read_memory = &Memory::Read;
    b.read_context = &m;
    m.Put(character, 0x1B8, carrier);
    m.Put(carrier, 0xF4, army_id);
    m.Put(army, 0x10, army_id);
    m.Put(army, 0x124, second_id);
    m.Put(second, 0x10, second_id);
    m.Put(army_fallback_slot, 0, army_fallback);
    m.Put(second_fallback_slot, 0, second_fallback);
    m.Put(provider, 0x1640, definition);
    Storage(army_store_slot, army);
    Storage(second_store_slot, second);
    provider_pointer = provider;
    provider_calls = 0;
  }
  xar::game::ContextSourcePre291e2101640V1 Observe() {
    const auto sources = xar::ck3_12002::ReadCurrentContextSourceInputs12003(
        b, character, 29829);
    Require(sources.pre_291e210_1640.has_value(), "new current leaf missing");
    return *sources.pre_291e210_1640;
  }
};

void Run() {
  using xar::ck3_12002::BindContextSourceInputs12003;
  constexpr std::uintptr_t base = 0x140000000;
  const auto bound = BindContextSourceInputs12003(base, xar::ck3_12003::kExecutableSha256);
  Require(bound.pre_291e210_1640_enabled, "exact build must bind observer");
  Require(bound.pre_291e210_second_storage_slot == reinterpret_cast<void *>(base + 0x5D1E380), "second registry RVA");
  Require(bound.pre_291e210_second_fallback_slot == reinterpret_cast<void *>(base + 0x5D1E378), "second fallback RVA");
  Require(!BindContextSourceInputs12003(base, "other-build").enabled, "wrong build binding");
  {
    Fixture f;
    f.m.Put(f.army, 0x120, std::uint32_t{0x80000007U});
    f.m.Put(f.second, 0x174, std::uint32_t{0x80000007U});
    f.m.Deny(f.definition, 0x40, 8);
    f.m.Deny(f.definition, 0xA8, 16);
    const auto o = f.Observe();
    Require(o.ready && o.admitted == true && o.character_id == 29829, "negative raw match");
    Require(o.army_key_f4_raw == static_cast<std::int32_t>(Fixture::army_id), "full Army generation bits");
    Require(o.army_selection == "registry_full_id" && o.second_selection == "registry_full_id", "full registry selections");
    Require(o.property_block && o.property_block->keys_count == 0, "actual empty PC");
    Require(f.m.Attempts() == 0 && provider_calls == 1, "zero keys skip value fields");
    xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 s;
    s.pre_291e210_1640 = o;
    const auto wire = xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(s);
    Require(wire.find("\"army_field_120_raw\":-2147483641") != std::string::npos, "signed DWORD serializer");
  }
  {
    Fixture f;
    f.m.Put(f.army, 0x120, std::int32_t{-1});
    f.m.Deny(f.army, 0x124, 4);
    f.m.Deny(f.second_store_slot, 0, 8);
    f.m.Deny(f.provider, 0x1640, 8);
    const auto o = f.Observe();
    Require(o.ready && o.admitted == false && !o.second_selection && !o.property_block, "FFFFFFFF early false");
    Require(f.m.Attempts() == 0 && provider_calls == 0, "early false short circuit");
  }
  {
    Fixture f;
    f.m.Put(f.army, 0x120, std::int32_t{0});
    f.m.Put(f.second, 0x174, std::int32_t{1});
    const auto o = f.Observe();
    Require(o.ready && o.admitted == false && !o.property_block && provider_calls == 0, "false equality skips provider");
  }
  {
    Fixture f;
    f.m.Put(f.army, 0x10, std::uint32_t{0xAC000001U});
    f.m.Put(f.army_fallback, 0x120, std::int32_t{0});
    f.m.Put(f.second_store_slot, 0, static_cast<void *>(nullptr));
    f.m.Deny(f.army_fallback, 0x124, 4);
    const auto o = f.Observe();
    Require(o.ready && o.admitted == true && o.army_selection == "native_fallback" && o.second_selection == "native_fallback", "generation miss and actual zero fallback equality");
    Require(!o.army_field_124_raw && f.m.Attempts() == 0, "null second store skips +124");
  }
  {
    Fixture f;
    f.m.Put(f.character, 0x1B8, static_cast<void *>(nullptr));
    f.m.Put(f.army_fallback, 0x120, std::int32_t{-1});
    f.m.Deny(f.army_store_slot, 0, 8);
    const auto o = f.Observe();
    Require(o.ready && o.admitted == false && !o.army_key_f4_raw && f.m.Attempts() == 0, "null carrier still tests fallback Army");
  }
  {
    Fixture f;
    f.m.Deny(f.army_store_slot, 0, 8);
    const auto o = f.Observe();
    Require(!o.ready && !o.admitted && !o.army_selection && o.status == "partial", "unread registry is not fallback or false");
    Require(o.unavailable_reason == "registry_store_read_unavailable", "failed read reason");
  }
  {
    Fixture f;
    f.m.Deny(f.second, 0x174, 4);
    const auto o = f.Observe();
    Require(!o.ready && !o.admitted && provider_calls == 0, "unread compared operand");
  }
  {
    Fixture f;
    f.m.Put(f.definition, 0x4C, std::int32_t{1});
    f.m.Deny(f.definition, 0x40, 8);
    const auto o = f.Observe();
    Require(!o.ready && o.admitted == true && o.property_block, "admitted predicate survives missing demanded PC");
  }
}
} // namespace

int main() {
  try {
    Run();
    std::cout << "pre_291e210_1640 source observer GREEN\n";
    return 0;
  } catch (const std::exception &e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
