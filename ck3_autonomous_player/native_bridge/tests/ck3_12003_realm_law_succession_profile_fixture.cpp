#include "xar_bridge/ck3_12002_realm_law.hpp"
#include "xar_bridge/realm_law_succession_profile_12003.hpp"

#include <array>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

// Root-owned, unrun fixture candidate. This is a synthetic producer/serializer
// check, not the whole production session, a private reply, or live evidence.
using namespace xar::ck3_12002;
namespace {
constexpr std::uintptr_t base = 0x10000000, image = 0x140000000;
constexpr std::uintptr_t actor = base + 0x100, context = base + 0x400,
    active_slots = base + 0x800, database = base + 0x1000,
    crown = base + 0x1400, succession = base + 0x1800,
    groups = base + 0x1c00, crown_slots = base + 0x2000,
    succession_slots = base + 0x2100;
constexpr std::array<std::uintptr_t, 6> laws{
    base + 0x3000, base + 0x4000, base + 0x5000,
    base + 0x6000, base + 0x7000, base + 0x8000};
constexpr std::string_view exact_3 =
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6";

void Require(bool value, std::string_view message) {
  if (!value) throw std::runtime_error(std::string(message));
}
std::string_view CandidateWire(const std::string &wire, std::string_view key) {
  const auto start = wire.find("{\"law_key\":\"" + std::string(key) + "\"");
  Require(start != std::string::npos, "candidate missing from actual serializer");
  const auto next = wire.find("{\"law_key\":", start + 1);
  return std::string_view(wire).substr(start, next == std::string::npos
                                               ? std::string::npos : next - start);
}
struct Memory {
  std::array<std::byte, 0x20000> bytes{};
  std::size_t profile_reads = 0;
  bool fail_profile = false;
  template <class T> void Store(std::uintptr_t address, const T &value) {
    std::memcpy(bytes.data() + address - base, &value, sizeof(value));
  }
  void Key(std::uintptr_t address, std::string_view text, std::uintptr_t heap) {
    Store(address + 0x18, heap);
    Store(address + 0x28, static_cast<std::uint64_t>(text.size()));
    Store(address + 0x30, std::uint64_t{127});
    std::memcpy(bytes.data() + heap - base, text.data(), text.size());
  }
  void Policy(std::size_t law, std::uint8_t order, std::uint8_t traversal,
              std::uint8_t rank, std::uint8_t division, std::int64_t share,
              bool creates) {
    const auto start = laws[law] + private_law::kRealmLawSuccessionPolicyOffset;
    Store(start, order); Store(start + 1, traversal); Store(start + 3, rank);
    Store(start + 4, division);
    Store(start + 6, static_cast<std::uint8_t>(creates ? 1 : 0));
    Store(start + 0x60, share);
  }
  static bool Read(void *opaque, std::uintptr_t address, void *out,
                   std::size_t size) noexcept {
    auto &memory = *static_cast<Memory *>(opaque);
    if (address == image + private_law::kLawGroupDatabaseSingletonRva12002) {
      if (size != sizeof(database)) return false;
      std::memcpy(out, &database, size); return true;
    }
    if (size == 0x68) {
      ++memory.profile_reads;
      // Only profile bytes for this candidate are unavailable. Collection and
      // fresh final terms remain readable, as in the independent production
      // profile producer's failure status.
      if (memory.fail_profile &&
          address == laws[2] + private_law::kRealmLawSuccessionPolicyOffset)
        return false;
    }
    if (address < base || size > memory.bytes.size() ||
        address - base > memory.bytes.size() - size) return false;
    std::memcpy(out, memory.bytes.data() + address - base, size); return true;
  }
};
std::size_t LawIndex(const void *law) {
  const auto address = reinterpret_cast<std::uintptr_t>(law);
  for (std::size_t i = 0; i < laws.size(); ++i)
    if (address == laws[i]) return i;
  throw std::runtime_error("unexpected native fixture law");
}
bool Kind(const void *) { return true; }
bool Active(const void *who, const void *law) {
  Require(reinterpret_cast<std::uintptr_t>(who) == actor, "wrong current actor");
  const auto i = LawIndex(law); return i == 0 || i == 2;
}
bool Final(const void *law, const void *, void *) {
  const auto i = LawIndex(law); return i >= 3 && i <= 5;
}
std::int64_t *Cost(std::int64_t *out, const void *block, std::uint32_t who) {
  Require(who == 29829, "wrong final-terms actor identity");
  const auto i = LawIndex(reinterpret_cast<const void *>(
      reinterpret_cast<std::uintptr_t>(block) - private_law::kRealmLawCompiledCostOffset));
  for (std::size_t n = 0; n < 10; ++n)
    out[n] = i >= 3 && i <= 5 ? static_cast<std::int64_t>(n) * 300003 : 0;
  return out;
}
bool Reason(const void *law, const void *, void *out) {
  static constexpr char blocked[] = "Fixture native reason: succession eligibility\n";
  const auto i = LawIndex(law);
  const bool allowed = i >= 3 && i <= 5;
  const char *text = allowed ? "" : blocked;
  const std::uint64_t size = std::strlen(text), capacity = size > 15 ? size : 15;
  auto *sink = static_cast<std::byte *>(out);
  if (size > 15) std::memcpy(sink, &text, sizeof(text));
  std::memcpy(sink + 0x10, &size, 8); std::memcpy(sink + 0x18, &capacity, 8);
  return allowed;
}
void Destroy(void *) {}
}  // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: fixture <synthetic DTO output.json>");
    Memory memory{};
    memory.Store(actor + 0x1c0, context);
    memory.Store(context + 0x200, active_slots);
    memory.Store(context + 0x20c, std::int32_t{2});
    memory.Store(active_slots, laws[0]); memory.Store(active_slots + 8, laws[2]);
    memory.Store(database + 0x50, groups);
    memory.Store(database + 0x5c, std::int32_t{2});
    memory.Store(groups, crown); memory.Store(groups + 8, succession);
    memory.Key(crown, "crown_authority", base + 0xc000);
    memory.Key(succession, "succession_order_laws", base + 0xc100);
    memory.Store(crown + 0x58, crown_slots); memory.Store(crown + 0x64, std::int32_t{2});
    memory.Store(succession + 0x58, succession_slots);
    memory.Store(succession + 0x64, std::int32_t{4});
    constexpr std::array<std::string_view, 6> keys{
        "crown_authority_0", "crown_authority_1",
        "confederate_partition_succession_law", "partition_succession_law",
        "high_partition_succession_law", "single_heir_succession_law"};
    for (std::size_t i = 0; i < laws.size(); ++i) {
      memory.Store((i < 2 ? crown_slots : succession_slots) + (i < 2 ? i : i - 2) * 8, laws[i]);
      memory.Store(laws[i] + 0x40, i < 2 ? crown : succession);
      memory.Key(laws[i], keys[i], base + 0xc200 + i * 0x100);
      memory.Policy(i, 9, 3, 2, 2, 0, false);
    }
    memory.Policy(2, 0, 0, 0, 1, 0, true);
    memory.Policy(3, 0, 0, 0, 1, 0, false);
    memory.Policy(4, 0, 0, 0, 1, 50000, false);
    memory.Policy(5, 0, 0, 0, 0, 0, false);

    const private_law::RealmLawActiveCollectionAccess access{
        private_law::kRealmLawActiveCollectionExeSha25612002, actor, &memory, &Memory::Read};
    const private_law::RealmLawFinalTerms12002Operations operations{
        {&Kind, &Active, &Final, &Cost}, &Reason, &Destroy};
    RealmLawReadback12002 readback{};
    Require(CaptureRealmLawReadback12002(access, image, {74, 53169072, 29829},
                                       operations, readback, exact_3),
            "new exact .3 profile capture failed");
    const auto serialized = SerializeRealmLawReadback12002(readback);
    Require(memory.profile_reads == 4, "read profiles outside group1 or missed a group1 candidate");
    const auto confederate_wire = CandidateWire(serialized, keys[2]);
    const auto partition_wire = CandidateWire(serialized, keys[3]);
    const auto high_wire = CandidateWire(serialized, keys[4]);
    const auto single_wire = CandidateWire(serialized, keys[5]);
    Require(confederate_wire.find("\"create_primary_tier_titles\":true") != std::string::npos,
            "confederate create flag absent");
    Require(partition_wire.find("\"create_primary_tier_titles\":false") != std::string::npos,
            "partition actual false title-creation value lost");
    Require(high_wire.find("\"primary_heir_minimum_share_raw\":50000") != std::string::npos,
            "high-partition native share lost");
    Require(partition_wire.find("\"primary_heir_minimum_share_raw\":0") != std::string::npos,
            "legal zero native share lost");
    Require(single_wire.find("\"division\":\"single_heir\"") != std::string::npos,
            "single heir division lost");
    Require(serialized.substr(0, serialized.find("\"group_key\":\"succession_order_laws\""))
                .find("succession_profile") == std::string::npos,
            "group0 existing six-field candidate wire changed");
    Require(serialized.find("succession eligibility\\u000a") != std::string::npos,
            "existing native final reason wire changed");
    std::ofstream out(argv[1], std::ios::binary);
    out << serialized << '\n';
    Require(out.good(), "synthetic DTO output failed");

    // The collection intentionally retains its existing four-law allowlist.
    // These two actual source shapes and a failed source read exercise the
    // same new helper/field serializer on a relevant native CLaw, without
    // inventing additional eligible candidate keys or changing admission.
    using ProfileStatus = xar::ck3_12003::private_law::RealmLawSuccessionProfile12003Status;
    memory.Policy(2, 9, 3, 2, 2, 0, false);
    const auto absent = xar::ck3_12003::private_law::ReadRealmLawSuccessionProfile12003(
        access, laws[2], exact_3);
    Require(absent.status == ProfileStatus::absent, "native default absence lost");
    memory.Policy(2, 9, 3, 2, 2, 0, true);
    const auto bool_only = xar::ck3_12003::private_law::ReadRealmLawSuccessionProfile12003(
        access, laws[2], exact_3);
    std::string bool_wire;
    xar::ck3_12003::private_law::AppendRealmLawSuccessionProfileFields12003(bool_wire, bool_only);
    Require(bool_only.status == ProfileStatus::available &&
                bool_wire.find("\"order\":null") != std::string::npos &&
                bool_wire.find("\"create_primary_tier_titles\":true") != std::string::npos,
            "native selector absence incorrectly hid a read title-creation flag");
    memory.fail_profile = true;
    const auto unreadable = xar::ck3_12003::private_law::ReadRealmLawSuccessionProfile12003(
        access, laws[2], exact_3);
    Require(unreadable.status == ProfileStatus::unavailable,
            "native profile read failure incorrectly exposed a default value");

    const auto reads_before_legacy = memory.profile_reads;
    RealmLawReadback12002 legacy{};
    Require(CaptureRealmLawReadback12002(access, image, {75, 53169072, 29829}, operations, legacy),
            "existing .2 final-terms capture changed");
    Require(memory.profile_reads == reads_before_legacy, ".2 invoked new .3 native profile reader");
    Require(SerializeRealmLawReadback12002(legacy).find("succession_profile") == std::string::npos,
            "existing .2 candidate wire changed");
    std::cout << "PASS: synthetic actual collection->finalterms->group1 profile->serializer\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL: " << error.what() << '\n'; return 1;
  }
}
