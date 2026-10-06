#include "xar_bridge/knight_current_model_association_v1.hpp"

#include <cassert>
#include <fstream>
#include <map>
#include <utility>

namespace {
using namespace xar::ck3_12002;
struct Memory {
  std::map<std::uintptr_t, std::vector<std::byte>> blocks;
  void Add(std::uintptr_t address, std::size_t size) { blocks[address].resize(size); }
  template<class T> void Put(std::uintptr_t address, T value) {
    for (auto &[base, bytes] : blocks) {
      if (address >= base && address - base <= bytes.size() &&
          sizeof(value) <= bytes.size() - (address - base)) {
        std::memcpy(bytes.data() + (address - base), &value, sizeof(value));
        return;
      }
    }
    assert(false);
  }
  static bool Read(void *context, const void *address, void *out, std::size_t count) noexcept {
    auto &self = *static_cast<Memory *>(context);
    const auto pointer = reinterpret_cast<std::uintptr_t>(address);
    for (const auto &[base, bytes] : self.blocks) {
      if (pointer >= base && pointer - base <= bytes.size() &&
          count <= bytes.size() - (pointer - base)) {
        std::memcpy(out, bytes.data() + (pointer - base), count);
        return true;
      }
    }
    return false;
  }
};
constexpr std::uintptr_t kSelected = 0x10000, kCarrier = 0x20000;
constexpr std::uintptr_t kInstalled = 0x30000, kOtherOld = 0x40000, kPaired = 0x50000;
constexpr std::uintptr_t kSlot = 0x60000, kRoot = 0x70000, kWorld = 0x80000;
constexpr std::uintptr_t kOldRows = 0xA0000, kPairs = 0xB0000;
Memory Full() {
  Memory m;
  m.Add(kSelected, 0x1B8); m.Add(kCarrier, 0x260);
  for (const auto model : {kInstalled, kOtherOld, kPaired}) {
    m.Add(model, 0x20); m.Put(model + 8, kSelected);
  }
  m.Add(kSlot, 8); m.Add(kRoot, 0xA8); m.Add(kWorld, 0xCD00);
  m.Add(kOldRows, 24); m.Add(kPairs, 48);
  m.Put(kSelected + 0x1B0, kCarrier); m.Put(kCarrier + 0x258, kInstalled);
  m.Put(kSlot, kRoot); m.Put(kRoot + 0xA0, kWorld);
  const auto manager = kWorld + 0xCBD8;
  m.Put(manager + 0x98, kOldRows); m.Put(manager + 0xA4, std::int32_t{3});
  m.Put(manager + 0x78, kPairs); m.Put(manager + 0x84, std::int32_t{3});
  m.Put(kOldRows, kInstalled); m.Put(kOldRows + 8, kOtherOld);
  m.Put(kOldRows + 16, kInstalled);
  m.Put(kPairs + 8, kPaired); m.Put(kPairs + 24, kInstalled);
  m.Put(kPairs + 40, std::uintptr_t{0});
  return m;
}
auto Observe(Memory &m, std::uintptr_t receiver = kInstalled + 0x10) {
  return ReadKnightCurrentModelAssociationV1(
      reinterpret_cast<void *>(kSelected), 29829, reinterpret_cast<void *>(receiver),
      reinterpret_cast<void *>(kSlot), {&m, Memory::Read});
}
} // namespace

int main(int argc, char **argv) {
  std::vector<std::pair<std::string, xar::game::KnightCurrentModelAssociationV1>> cases;
  {
    auto m = Full(); auto out = Observe(m);
    assert(out.current_status == "available" && out.queue_status == "available");
    assert(out.owner_matches_selected == true && out.getter_receiver_matches_model_inline == true);
    assert(out.relevant_occurrences.size() == 3);
    assert(out.relevant_occurrences[0].old_model_matches_installed == true);
    assert(out.relevant_occurrences[0].paired_owner_matches_selected == true);
    assert(out.relevant_occurrences[0].paired_model_matches_installed == false);
    assert(out.relevant_occurrences[1].old_model_matches_installed == false);
    assert(out.relevant_occurrences[1].paired_model_matches_installed == true);
    assert(out.relevant_occurrences[2].occurrence == 2);
    assert(out.relevant_occurrences[2].paired_model_present == false);
    assert(!out.relevant_occurrences[2].paired_owner_matches_selected);
    cases.emplace_back("actual_indices_duplicate_old_and_distinct_same_owner_models", out);
  }
  {
    auto m = Full(); m.Put(kSelected + 0x1B0, std::uintptr_t{0});
    m.Put(kWorld + 0xCBD8 + 0xA4, std::int32_t{0});
    m.Put(kWorld + 0xCBD8 + 0x84, std::int32_t{0});
    auto out = Observe(m, 0xD0000);
    assert(out.current_status == "available" && out.context_source == "fallback_static");
    assert(out.carrier_present == false && out.installed_model_present == false);
    assert(!out.owner_matches_selected && out.old_count_raw == 0);
    assert(out.queue_status == "available" && out.relevant_occurrences.empty());
    cases.emplace_back("present_empty_queue_and_no_carrier_fallback", out);
  }
  {
    auto m = Full(); m.Put(kPairs + 8, std::uintptr_t{0xDEAD0});
    auto out = Observe(m);
    assert(out.current_status == "available" && out.queue_status == "partial");
    assert(out.relevant_occurrences[0].paired_model_present == true);
    assert(!out.relevant_occurrences[0].paired_owner_matches_selected);
    assert(out.relevant_occurrences[1].paired_model_matches_installed == true);
    cases.emplace_back("unread_paired_owner_preserves_actual_pointer_and_later_rows", out);
  }
  {
    auto m = Full(); m.blocks.erase(kCarrier);
    auto out = Observe(m);
    assert(out.current_status == "unavailable" && !out.installed_model_present);
    assert(out.queue_status == "available" && out.relevant_occurrences.size() == 3);
    assert(!out.relevant_occurrences[0].old_model_matches_installed);
    assert(out.relevant_occurrences[0].old_owner_matches_selected == true);
    cases.emplace_back("unread_installed_pointer_retains_independent_same_owner_queue", out);
  }
  if (argc > 1) {
    std::ofstream file(argv[1]);
    assert(file);
    file << "[";
    for (std::size_t i = 0; i < cases.size(); ++i) {
      if (i) file << ',';
      file << "{\"case\":\"" << cases[i].first << "\",\"observation\":"
           << SerializeKnightCurrentModelAssociationV1(cases[i].second) << '}';
    }
    file << "]\n";
  }
  return 0;
}
