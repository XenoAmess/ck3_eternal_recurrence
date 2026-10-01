#include "xar_bridge/ck3_12002_realm_law.hpp"

#include <array>
#include <cassert>
#include <cstring>
#include <fstream>
#include <iostream>

using namespace xar::ck3_12002;
namespace {
constexpr std::uintptr_t base = 0x10000000, image = 0x140000000;
constexpr std::uintptr_t actor = base + 0x100, context = base + 0x400,
    active_slots = base + 0x800, database = base + 0x1000,
    crown = base + 0x1400, succession = base + 0x1800,
    groups = base + 0x1C00, crown_slots = base + 0x2000,
    succession_slots = base + 0x2100;
constexpr std::array<std::uintptr_t, 4> laws{base + 0x3000, base + 0x4000,
    base + 0x5000, base + 0x6000};
struct Memory {
  std::array<std::byte, 0x10000> bytes{};
  template <class T> void Store(std::uintptr_t address, const T &value) {
    std::memcpy(bytes.data() + address - base, &value, sizeof(value));
  }
  void Key(std::uintptr_t address, std::string_view text, std::uintptr_t heap) {
    Store(address + 0x18, heap);
    Store(address + 0x28, static_cast<std::uint64_t>(text.size()));
    Store(address + 0x30, std::uint64_t{63});
    std::memcpy(bytes.data() + heap - base, text.data(), text.size());
  }
  static bool Read(void *opaque, std::uintptr_t address, void *out, std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(opaque);
    if (address == image + private_law::kLawGroupDatabaseSingletonRva12002) {
      std::memcpy(out, &database, size); return true;
    }
    if (address < base || address - base + size > memory.bytes.size()) return false;
    std::memcpy(out, memory.bytes.data() + address - base, size); return true;
  }
};
std::size_t LawIndex(const void *law) {
  const auto address = reinterpret_cast<std::uintptr_t>(law);
  for (std::size_t i = 0; i < laws.size(); ++i) if (address == laws[i]) return i;
  assert(false); return 0;
}
bool Kind(const void *) { return true; }
bool Active(const void *who, const void *law) {
  assert(reinterpret_cast<std::uintptr_t>(who) == actor);
  return LawIndex(law) % 2 == 0;
}
bool Final(const void *law, const void *, void *) { return LawIndex(law) == 1; }
std::int64_t *Cost(std::int64_t *out, const void *block, std::uint32_t who) {
  assert(who == 29829);
  const auto index = LawIndex(reinterpret_cast<const void *>(
      reinterpret_cast<std::uintptr_t>(block) - private_law::kRealmLawCompiledCostOffset));
  for (std::size_t i = 0; i < 10; ++i) out[i] = index == 1 ? static_cast<std::int64_t>(i) * 300003 : 0;
  return out;
}
bool Reason(const void *law, const void *, void *out) {
  static constexpr char blocked[] = "Fixture native reason: council \"no\"\n";
  const auto index = LawIndex(law);
  const char *text = index == 1 ? "" : blocked;
  const std::uint64_t size = std::strlen(text), capacity = size > 15 ? size : 15;
  auto *sink = static_cast<std::byte *>(out);
  if (size > 15) std::memcpy(sink, &text, sizeof(text));
  std::memcpy(sink + 0x10, &size, 8); std::memcpy(sink + 0x18, &capacity, 8);
  return index == 1;
}
void Destroy(void *) {}
}
int main(int argc, char **argv) {
  Memory memory{};
  memory.Store(actor + 0x1C0, context);
  memory.Store(context + 0x200, active_slots);
  memory.Store(context + 0x20C, std::int32_t{2});
  memory.Store(active_slots, laws[0]); memory.Store(active_slots + 8, laws[2]);
  memory.Store(database + 0x50, groups); memory.Store(database + 0x5C, std::int32_t{2});
  memory.Store(groups, crown); memory.Store(groups + 8, succession);
  memory.Key(crown, "crown_authority", base + 0x7000);
  memory.Key(succession, "succession_order_laws", base + 0x7100);
  memory.Store(crown + 0x58, crown_slots); memory.Store(crown + 0x64, std::int32_t{2});
  memory.Store(succession + 0x58, succession_slots); memory.Store(succession + 0x64, std::int32_t{2});
  constexpr std::array<std::string_view, 4> keys{"crown_authority_0", "crown_authority_1",
      "confederate_partition_succession_law", "high_partition_succession_law"};
  for (std::size_t i = 0; i < laws.size(); ++i) {
    memory.Store((i < 2 ? crown_slots : succession_slots) + (i % 2) * 8, laws[i]);
    memory.Store(laws[i] + 0x40, i < 2 ? crown : succession);
    memory.Key(laws[i], keys[i], base + 0x7200 + i * 0x100);
  }
  const private_law::RealmLawActiveCollectionAccess access{
      private_law::kRealmLawActiveCollectionExeSha25612002, actor, &memory, &Memory::Read};
  const private_law::RealmLawFinalTerms12002Operations operations{
      {&Kind, &Active, &Final, &Cost}, &Reason, &Destroy};
  RealmLawReadback12002 readback{};
  assert(CaptureRealmLawReadback12002(access, image, {74, 53169072, 29829}, operations, readback));
  assert(readback.collection.groups[0].candidate_count == 2 && readback.collection.groups[1].candidate_count == 2);
  assert(readback.final[0][1].terms.status == private_law::RealmLawFinalTerms12002Status::can_enact);
  assert(readback.final[1][1].terms.status == private_law::RealmLawFinalTerms12002Status::engine_blocked);
  const auto serialized = SerializeRealmLawReadback12002(readback);
  assert(serialized.find("council \\\"no\\\"\\u000a") != std::string::npos);
  if (argc == 2) { std::ofstream out(argv[1], std::ios::binary); out << serialized << '\n'; assert(out.good()); }
  std::cout << "PASS: actual 1.20 native-layout collections -> final terms -> existing JSON DTO wire\n";
}
