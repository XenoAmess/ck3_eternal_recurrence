#include "xar_bridge/ck3_12003_context_sources.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "xar_bridge/battle_context_source_inputs_v1_serializer.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
void Require(bool v, const char *label) {
  if (!v) throw std::runtime_error(label);
}
struct Memory {
  struct Region { std::unique_ptr<std::byte[]> data; std::size_t size; };
  struct Denied { std::uintptr_t begin; std::size_t size; std::size_t attempts = 0; };
  std::vector<Region> regions;
  std::vector<Denied> denied;
  void *Allocate(std::size_t size) {
    auto data = std::make_unique<std::byte[]>(size);
    void *p = data.get();
    regions.push_back({std::move(data), size});
    return p;
  }
  template <typename T> void Put(void *p, std::size_t off, T value) {
    std::memcpy(static_cast<std::byte *>(p) + off, &value, sizeof(value));
  }
  void Deny(const void *p, std::size_t off, std::size_t size) {
    denied.push_back({reinterpret_cast<std::uintptr_t>(p) + off, size});
  }
  std::size_t Attempts() const {
    std::size_t n = 0;
    for (const auto &d : denied) n += d.attempts;
    return n;
  }
  static bool Read(void *context, const void *p, void *out, std::size_t size) noexcept {
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
        std::memcpy(out, p, size);
        return true;
      }
    }
    return false;
  }
};
struct Fixture {
  Memory m;
  xar::ck3_12002::ContextSourceBindingsV1 b{};
  void *character = m.Allocate(0x1D0);
  void *carrier = m.Allocate(0x300);
  void *second_carrier = m.Allocate(0x390);
  void *header = m.Allocate(0x10);
  void *store_slot = m.Allocate(8);
  void *fallback_slot = m.Allocate(8);
  void *guarded_fallback_slot = m.Allocate(8);
  void *object = m.Allocate(0x250);
  void *fallback = m.Allocate(0x250);
  void *guarded = m.Allocate(0xB20);
  void *store = m.Allocate(0x30);
  void *table = m.Allocate(32);
  void *ids = m.Allocate(12);
  static constexpr std::uint32_t id = 0xAB000001U;
  Fixture() {
    b.enabled = true;
    b.later_direct_enabled = true;
    b.later_ordered_fallback_header = header;
    b.later_ordered_storage_slot = store_slot;
    b.later_ordered_fallback_slot = fallback_slot;
    b.later_guarded_fallback_slot = guarded_fallback_slot;
    b.read_memory = &Memory::Read;
    b.read_context = &m;
    m.Put(character, 0x1B0, carrier);
    m.Put(character, 0x1C0, second_carrier);
    m.Put(carrier, 0x98, ids);
    m.Put(carrier, 0xA4, std::int32_t{2});
    m.Put(ids, 0, id);
    m.Put(ids, 4, id);
    m.Put(store_slot, 0, store);
    m.Put(fallback_slot, 0, fallback);
    m.Put(guarded_fallback_slot, 0, guarded);
    m.Put(store, 0x20, table);
    m.Put(store, 0x2C, std::uint32_t{2});
    m.Put(table, 24, object);
    m.Put(object, 0x10, id);
    m.Put(object, 0x24C, std::int32_t{-7});
    m.Put(second_carrier, 0x388, guarded);
    m.Put(guarded, 0x38, std::uint32_t{0x4744624F});
  }
  xar::game::ContextSourceLaterDirectV1 Observe() {
    const auto s = xar::ck3_12002::ReadCurrentContextSourceInputs12003(b, character, 29829);
    Require(s.later_direct_291c3fb_44c.has_value(), "later direct section missing");
    return *s.later_direct_291c3fb_44c;
  }
};
void Save(const std::filesystem::path &dir, const char *name,
          const xar::game::ContextSourceLaterDirectV1 &leaf) {
  if (dir.empty()) return;
  xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 s{};
  s.status = "partial";
  s.character_id = 29829;
  s.reason = "other_source_families_unobserved";
  s.later_direct_291c3fb_44c = leaf;
  std::ofstream out(dir / (std::string(name) + ".json"), std::ios::binary);
  out << xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(s);
  if (!out) throw std::runtime_error("wire output failed");
}
void Run(const std::filesystem::path &dir) {
  constexpr std::uintptr_t base = 0x140000000;
  const auto b = xar::ck3_12002::BindContextSourceInputs12003(base, xar::ck3_12003::kExecutableSha256);
  Require(b.later_direct_enabled, "exact build bound");
  Require(b.later_ordered_fallback_header == reinterpret_cast<void *>(base + 0x545A3E8), "inline fallback header RVA");
  Require(b.later_ordered_storage_slot == reinterpret_cast<void *>(base + 0x5D1FC58), "registry RVA");
  Require(b.later_ordered_fallback_slot == reinterpret_cast<void *>(base + 0x5D1FC48), "registry fallback RVA");
  Require(b.later_guarded_fallback_slot == reinterpret_cast<void *>(base + 0x5D1DCB0), "guarded fallback RVA");
  Require(!xar::ck3_12002::BindContextSourceInputs12003(base, "other-build").enabled, "wrong build");
  {
    Fixture f;
    f.m.Deny(f.object, 0x80, 8);
    f.m.Deny(f.object, 0xE8, 16);
    f.m.Deny(f.guarded, 0xAA0, 8);
    f.m.Deny(f.guarded, 0xB08, 16);
    const auto s = f.Observe();
    Require(s.ready && s.ordered_rows && s.ordered_rows->size() == 2, "duplicate occurrences retained");
    const auto &r = *s.ordered_rows;
    Require(r[0].admitted == true && r[0].selected_field_24c_raw == -7, "negative nonzero admission");
    Require(r[0].requested_full_id_raw == static_cast<std::int32_t>(Fixture::id), "full signed wire DWORD bits");
    Require(r[0].selected_identity == r[1].selected_identity, "same selected identity");
    Require(s.guarded_admitted == true && s.guarded_property_block->keys_count == 0, "AA0 native empty PC");
    Require(f.m.Attempts() == 0, "empty PC skips unused fields");
    Save(dir, "duplicates-negative-admitted", s);
  }
  {
    Fixture f;
    f.m.Put(f.character, 0x1B0, static_cast<void *>(nullptr));
    f.m.Put(f.character, 0x1C0, static_cast<void *>(nullptr));
    f.m.Put(f.guarded, 0x38, std::uint32_t{0});
    f.m.Deny(f.store_slot, 0, 8);
    f.m.Deny(f.fallback_slot, 0, 8);
    f.m.Deny(f.guarded, 0xAA0, 0x80);
    const auto s = f.Observe();
    Require(s.ready && s.ordered_count == 0 && s.ordered_rows->empty(), "inline fallback zero count");
    Require(s.ordered_header_selection == "inline_static_545a3e8", "fallback is inline header");
    Require(s.guarded_selection == "native_fallback" && s.guarded_admitted == false, "wrong magic fallback false");
    Require(f.m.Attempts() == 0, "zero list and false magic skip demanded body");
    Save(dir, "zero-and-false-fallback", s);
  }
  {
    Fixture f;
    f.m.Put(f.object, 0x10, std::uint32_t{0xAC000001U});
    f.m.Deny(f.fallback, 0x80, 0x80);
    const auto s = f.Observe();
    Require(s.ready && (*s.ordered_rows)[0].selection == "native_fallback", "full generation mismatch chooses fallback");
    Require((*s.ordered_rows)[0].admitted == false && f.m.Attempts() == 0, "fallback zero skips PC");
    Save(dir, "generation-fallback-zero", s);
  }
  {
    Fixture f;
    f.m.Deny(f.store, 0x2C, 4);
    const auto s = f.Observe();
    Require(!s.ready && !(*s.ordered_rows)[0].selection && !(*s.ordered_rows)[0].admitted, "failed registry read does not become fallback");
    Save(dir, "registry-read-unavailable", s);
  }
  {
    Fixture f;
    f.m.Put(f.object, 0x8C, std::int32_t{1});
    f.m.Deny(f.object, 0x80, 8);
    const auto s = f.Observe();
    Require(!s.ready && (*s.ordered_rows)[0].admitted == true, "admission survives unread consumed PC");
    Save(dir, "property-read-unavailable", s);
  }
  {
    Fixture f;
    f.m.Deny(f.guarded, 0x38, 4);
    const auto s = f.Observe();
    Require(!s.ready && !s.guarded_admitted, "unread magic differs from false");
    Save(dir, "magic-read-unavailable", s);
  }
  {
    Fixture f;
    f.m.Put(f.carrier, 0xA4, std::int32_t{-1});
    const auto s = f.Observe();
    Require(!s.ready && s.ordered_count == -1 && !s.ordered_rows, "negative count is not empty");
    Save(dir, "negative-count-unrepresentable", s);
  }
}
} // namespace

int main(int argc, char **argv) {
  try {
    const std::filesystem::path dir = argc == 2 ? argv[1] : "";
    if (!dir.empty()) std::filesystem::create_directories(dir);
    Run(dir);
    std::cout << "later direct source observer GREEN\n";
    return 0;
  } catch (const std::exception &e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
