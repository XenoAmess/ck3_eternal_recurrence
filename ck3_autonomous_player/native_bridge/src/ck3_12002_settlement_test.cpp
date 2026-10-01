#include "xar_bridge/ck3_12002_settlement.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <span>

namespace {
template <typename T>
void Put(std::span<std::byte> object, std::size_t offset, T value) {
  std::memcpy(object.data() + offset, &value, sizeof(value));
}

constexpr std::array<std::string_view, 12> names{
    "xa_settlement_ready", "xa_settlement_commit_serial",
    "xa_settlement_source_character", "xa_settlement_final_score",
    "xa_settlement_score_before_reject", "xa_settlement_record_candidate",
    "xa_settlement_old_record", "xa_settlement_record_delta",
    "xa_settlement_blessing_count", "xa_settlement_refusal_count",
    "xa_settlement_contract_progress", "xa_settlement_record_written"};
void *container = nullptr;
bool invalidate_on_second_ready_read = false;
int ready_reads = 0;
void *Global() { return container; }
void *Table() { return const_cast<std::array<std::string_view, 12> *>(&names); }
std::int32_t *Lookup(void *table, std::int32_t *output, const void *view) {
  const char *data = nullptr;
  std::int32_t length = 0;
  std::uint8_t indirect = 1;
  std::memcpy(&data, view, 8);
  std::memcpy(&length, static_cast<const std::byte *>(view) + 8, 4);
  std::memcpy(&indirect, static_cast<const std::byte *>(view) + 0x0C, 1);
  *output = -1;
  if (table != &names || data == nullptr || length < 0 || indirect != 0) {
    return output;
  }
  const std::string_view key(data, static_cast<std::size_t>(length));
  for (std::size_t index = 0; index < names.size(); ++index) {
    if (key == names[index]) {
      *output = static_cast<std::int32_t>(44011 + index);
      if (index == 0 && ++ready_reads == 2 && invalidate_on_second_ready_read) {
        void *entries = nullptr;
        std::memcpy(&entries, static_cast<std::byte *>(container) + 0x10, 8);
        const std::int64_t zero = 0;
        std::memcpy(static_cast<std::byte *>(entries) + 0x18, &zero, 8);
      }
      return output;
    }
  }
  return output;
}

bool Run() {
  using namespace xar::ck3_12002;
  std::array<std::byte, 0x30> globals{}, storage{};
  std::array<std::byte, 12 * 0x20> entries{};
  std::array<std::byte, 8 * 0x10> slots{};
  std::array<std::byte, 0x1D8> dead_character{};
  constexpr std::int32_t character_id = 0x05000004;
  for (std::size_t i = 0; i < names.size(); ++i) {
    Put(entries, i * 0x20 + 8, static_cast<std::int32_t>(44011 + i));
    Put(entries, i * 0x20 + 0x10, std::uint16_t{1});
  }
  const auto numeric = [&](std::size_t index, std::int64_t raw) {
    Put(entries, index * 0x20 + 0x18, raw);
  };
  numeric(0, 100000); numeric(1, 100000);
  Put(entries, 2 * 0x20 + 0x10, std::uint16_t{4});
  Put(entries, 2 * 0x20 + 0x18, character_id);
  numeric(3, 680001); numeric(4, 800000);
  numeric(5, 600000); numeric(6, 1000000); numeric(7, -400000);
  numeric(8, 100000); numeric(9, 200000); numeric(10, 800000);
  numeric(11, 100000);
  Put(globals, 0x10, entries.data());
  Put(globals, 0x1C, std::int32_t{12});
  Put(storage, 0x20, slots.data());
  Put(storage, 0x2C, std::int32_t{8});
  Put(slots, 4 * 0x10 + 8, dead_character.data());
  Put(dead_character, 0x18, character_id);
  Put(dead_character, 0x1D0, entries.data()); // A dead source remains resolvable.
  void *storage_pointer = storage.data();
  container = globals.data();
  SettlementGlobalAccessor accessor = &Global;
  SettlementBindings bindings{true, &accessor, &Table, &Lookup};
  CoreBindings core{};
  core.enabled = true;
  core.character_storage_slot = &storage_pointer;
  xar::game::Snapshot output;
  output.date_raw = 53175816;
  const auto read = [&]() { ready_reads = 0; return ReadSettlement(bindings, core, output); };
  if (read() != SettlementReadResult::published ||
      !output.has_one_life_settlement ||
      output.one_life_settlement.source_character_id != character_id ||
      output.one_life_settlement.final_score.raw != 680001 ||
      output.one_life_settlement.final_score.scale != 100000 ||
      output.one_life_settlement.record_delta != -4 ||
      output.one_life_settlement.blessing_count != 1 ||
      output.one_life_settlement.refusal_count != 2 ||
      output.one_life_settlement.contract_progress != 8 ||
      !output.one_life_settlement.record_written || output.date_raw != 53175816) {
    return false;
  }
  numeric(0, 0);
  if (read() != SettlementReadResult::not_published || output.has_one_life_settlement) return false;
  Put(entries, 0x10, std::uint16_t{0});
  if (read() != SettlementReadResult::not_published || output.has_one_life_settlement) return false;
  Put(entries, 0x10, std::uint16_t{1});
  Put(globals, 0x1C, std::int32_t{0});
  if (read() != SettlementReadResult::not_published || output.has_one_life_settlement) return false;
  Put(globals, 0x1C, std::int32_t{12});
  numeric(0, 200000);
  if (read() != SettlementReadResult::invalid_payload || output.has_one_life_settlement) return false;
  numeric(0, 100000); numeric(1, 150000);
  if (read() != SettlementReadResult::invalid_payload || output.has_one_life_settlement) return false;
  numeric(1, 100000);
  Put(dead_character, 0x18, std::int32_t{0x04000004});
  if (read() != SettlementReadResult::invalid_payload || output.has_one_life_settlement) return false;
  Put(dead_character, 0x18, character_id);
  Put(entries, 2 * 0x20 + 0x10, std::uint16_t{1});
  if (read() != SettlementReadResult::invalid_payload) return false;
  Put(entries, 2 * 0x20 + 0x10, std::uint16_t{4});
  Put(globals, 0x1C, std::int32_t{11});
  if (read() != SettlementReadResult::invalid_payload) return false;
  Put(globals, 0x1C, std::int32_t{12});
  invalidate_on_second_ready_read = true;
  if (read() != SettlementReadResult::not_published || output.has_one_life_settlement) return false;
  invalidate_on_second_ready_read = false; numeric(0, 100000);
  bindings.enabled = false;
  if (read() != SettlementReadResult::unavailable || output.has_one_life_settlement) return false;
  bindings.enabled = true; container = nullptr;
  if (read() != SettlementReadResult::unavailable) return false;
  constexpr std::uintptr_t image_base = 0x140000000;
  const auto bound = BindSettlementImage(image_base, kExecutableSha256);
  return bound.enabled &&
         reinterpret_cast<std::uintptr_t>(bound.global_accessor_slot) == image_base + 0x5C6A4B0 &&
         reinterpret_cast<std::uintptr_t>(bound.identifier_table) == image_base + 0x3F8A800 &&
         reinterpret_cast<std::uintptr_t>(bound.lookup_identifier) == image_base + 0x3F8A680 &&
         !BindSettlementImage(image_base, "old-or-unknown-build").enabled &&
         !BindSettlementImage(0, kExecutableSha256).enabled;
}
} // namespace

int main() {
  if (!Run()) { std::cerr << "FAIL: CK3 1.20.0.2 settlement fixture\n"; return 1; }
  std::cout << "PASS: CK3 1.20.0.2 settlement fixture; no game process access\n";
  return 0;
}
