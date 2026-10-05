#include "xar_bridge/ck3_12003_context_sources.hpp"
#include "xar_bridge/battle_context_source_inputs_v1_serializer.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {
std::vector<std::string> fixture_wires;
void Require(bool ok, const char *message) {
  if (!ok) throw std::runtime_error(message);
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
  template <typename T> void Put(void *p, std::size_t offset, T value) {
    std::memcpy(static_cast<std::byte *>(p) + offset, &value, sizeof(value));
  }
  void Deny(const void *p, std::size_t offset, std::size_t size) {
    denied.push_back({reinterpret_cast<std::uintptr_t>(p) + offset, size});
  }
  std::size_t Attempts() const {
    std::size_t total = 0;
    for (const auto &d : denied) total += d.attempts;
    return total;
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
  xar::ck3_12002::ContextSourceBindingsV1 b;
  void *character = m.Allocate(0x1C8);
  void *carrier = m.Allocate(0x290);
  void *carrier280 = m.Allocate(0x10);
  void *carrier288 = m.Allocate(0x20);
  void *selected630 = m.Allocate(0x6B0);
  void *fallback630 = m.Allocate(0x6B0);
  void *selected40 = m.Allocate(0xC0);
  void *holder = m.Allocate(0x210);
  void *static_header = m.Allocate(0x10);
  void *threshold = m.Allocate(4);
  void *fallback_slot = m.Allocate(8);

  Fixture() {
    b.enabled = true;
    b.post_291d7e0_sources_enabled = true;
    b.post_ab_object_fallback_slot = fallback_slot;
    b.post_ab_signed_character_threshold_slot = threshold;
    b.post_ab_static_inline_source_list_header = static_header;
    b.read_memory = &Memory::Read;
    b.read_context = &m;
    m.Put(character, 0x1B0, carrier);
    m.Put(character, 0x1C0, holder);
    m.Put(character, 0x68, std::int16_t{-5});
    m.Put(carrier, 0x280, carrier280);
    m.Put(carrier, 0x288, carrier288);
    m.Put(carrier280, 8, selected630);
    m.Put(carrier288, 0x18, selected40);
    m.Put(selected630, 0x38, std::int32_t{0x4744624F});
    m.Put(threshold, 0, std::int32_t{-5});
    m.Put(fallback_slot, 0, fallback630);
  }
  void *Source(std::uint16_t key, std::int64_t value) {
    void *source = m.Allocate(0x160);
    void *keys = m.Allocate(2);
    void *values = m.Allocate(8);
    m.Put(keys, 0, key);
    m.Put(values, 0, value);
    m.Put(source, 0xD8, keys);
    m.Put(source, 0xE4, std::int32_t{1});
    m.Put(source, 0x140, values);
    m.Put(source, 0x14C, std::int32_t{9});
    return source;
  }
  void List(void *header, const std::vector<void *> &sources) {
    void *data = m.Allocate(sources.size() * 8 + 1);
    for (std::size_t i = 0; i < sources.size(); ++i) m.Put(data, i * 8, sources[i]);
    m.Put(header, 0, data);
    m.Put(header, 0xC, static_cast<std::int32_t>(sources.size()));
  }
  xar::game::ContextSourcePost291d7e0V1 Observe() {
    const auto snapshot = xar::ck3_12002::ReadCurrentContextSourceInputs12003(b, character, 29829);
    Require(snapshot.post_291d7e0_sources.has_value(), "reachable current post-A/B section");
    fixture_wires.push_back(xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(snapshot));
    return *snapshot.post_291d7e0_sources;
  }
};

void Run() {
  constexpr std::uintptr_t base = 0x140000000;
  const auto b = xar::ck3_12002::BindContextSourceInputs12003(base, xar::ck3_12003::kExecutableSha256);
  Require(b.post_291d7e0_sources_enabled, "exact build observer binding");
  Require(b.post_ab_object_fallback_slot == reinterpret_cast<void *>(base + 0x5D1E308), "fallback binding");
  Require(b.post_ab_signed_character_threshold_slot == reinterpret_cast<void *>(base + 0x5C6A19C), "signed threshold binding");
  Require(b.post_ab_static_inline_source_list_header == reinterpret_cast<void *>(base + 0x54E7270), "INLINE static header binding");
  {
    Fixture f;
    void *a = f.Source(65535, 0);
    void *other = f.Source(7, -200000);
    f.List(static_cast<std::byte *>(f.holder) + 0x200, {a, other, a});
    f.m.Deny(f.selected630, 0x630, 8);
    f.m.Deny(f.selected630, 0x698, 16);
    f.m.Deny(f.selected40, 0x40, 8);
    f.m.Deny(f.selected40, 0xA8, 16);
    const auto o = f.Observe();
    Require(o.ready && o.guarded630.admitted == true && o.carrier40.admitted == true, "signed equality admits both actual empty PCs");
    Require(f.m.Attempts() == 0, "empty property keys skip unused value reads");
    const auto &rows = *o.ordered_d8.occurrences;
    Require(rows.size() == 3 && rows[0].source_identity == rows[2].source_identity, "stored duplicate occurrences retained");
    Require(rows[0].source_identity != rows[1].source_identity && rows[2].source_index == 2, "physical source order");
    Require(rows[1].property_block->values_q64->at(0) == -200000, "signed actual paired value");
    Require(rows[0].property_block->values_count == 9 && rows[0].property_block->keys_u16->at(0) == 65535, "independent count and native FFFF preserved");
    xar::game::BattleCurrentPersonContextSourceInputsSnapshotV1 parent;
    parent.post_291d7e0_sources = o;
    const auto wire = xar::bridge::SerializeBattleCurrentPersonContextSourceInputsV1(parent);
    Require(wire.find("\"post_291d7e0_sources\"") != std::string::npos &&
            wire.find("\"source_count_raw\":3") != std::string::npos, "new section reaches existing serializer");
  }
  {
    Fixture f;
    f.m.Put(f.selected630, 0x38, std::uint32_t{0xFFFFFFFFU});
    f.m.Deny(f.character, 0x68, 2);
    f.m.Deny(f.threshold, 0, 4);
    f.m.Deny(f.selected630, 0x63C, 4);
    const auto o = f.Observe();
    Require(o.ready && o.guarded630.admitted == false && o.guarded630.selected_field38_raw == -1, "wrong raw magic known false");
    Require(!o.guarded630.character68_signed && !o.guarded630.property_block && f.m.Attempts() == 0, "wrong magic short circuit");
  }
  {
    Fixture f;
    f.m.Put(f.threshold, 0, std::int32_t{-4});
    f.m.Deny(f.selected630, 0x63C, 4);
    const auto o = f.Observe();
    Require(o.ready && o.guarded630.admitted == false && f.m.Attempts() == 0, "signed JL skips guarded property");
  }
  {
    Fixture f;
    f.m.Put(f.character, 0x1B0, static_cast<void *>(nullptr));
    f.m.Put(f.character, 0x1C0, static_cast<void *>(nullptr));
    f.m.Put(f.fallback630, 0x38, std::int32_t{0x4744624F});
    void *source = f.Source(9, 0);
    f.List(f.static_header, {source, source});
    const auto o = f.Observe();
    Require(o.ready && o.guarded630.admitted == true && o.carrier40.admitted == false, "null carrier still evaluates actual fallback");
    Require(o.guarded630.selection == "native_fallback5D1E308" && !o.carrier40.carrier288_present, "carrier and selected object are separate");
    Require(o.ordered_d8.header_selection == "inline_static54E7270" && o.ordered_d8.source_count_raw == 2, "actual nonempty INLINE static fallback");
  }
  {
    Fixture f;
    f.m.Put(f.carrier, 0x280, static_cast<void *>(nullptr));
    f.m.Put(f.carrier, 0x288, static_cast<void *>(nullptr));
    f.m.Deny(f.carrier288, 0x18, 8);
    const auto o = f.Observe();
    Require(o.ready && o.guarded630.admitted == false && o.carrier40.admitted == false && f.m.Attempts() == 0, "readable null nested pointer guards");
  }
  {
    Fixture f;
    f.m.Deny(f.carrier288, 0x18, 8);
    const auto o = f.Observe();
    Require(!o.ready && o.carrier40.admitted == true && !o.carrier40.property_block, "known pointer admission retains unread selected PC");
    Require(o.guarded630.ready && o.ordered_d8.ready, "independent source leaves remain useful");
  }
  {
    Fixture f;
    f.m.Put(f.holder, 0x20C, std::int32_t{-1});
    const auto o = f.Observe();
    Require(!o.ready && o.ordered_d8.source_count_raw == -1 && !o.ordered_d8.occurrences, "negative count retained as unavailable, never empty");
  }
  {
    Fixture f;
    f.m.Deny(f.holder, 0x200, 8);
    const auto o = f.Observe();
    Require(!o.ready && !o.ordered_d8.source_count_raw && !o.ordered_d8.occurrences, "unread header pointer is not native zero list");
  }
}
} // namespace

int main(int argc, char **argv) {
  try {
    Run();
    if (argc == 2) {
      std::ofstream output(argv[1], std::ios::binary);
      Require(static_cast<bool>(output), "fixture wire output open");
      output << '[';
      for (std::size_t i = 0; i < fixture_wires.size(); ++i) {
        if (i) output << ',';
        output << fixture_wires[i];
      }
      output << "]\n";
      Require(static_cast<bool>(output), "fixture wire output write");
    }
    std::cout << "post_291d7e0_sources observer GREEN\n";
    return 0;
  } catch (const std::exception &e) {
    std::cerr << e.what() << '\n';
    return 1;
  }
}
