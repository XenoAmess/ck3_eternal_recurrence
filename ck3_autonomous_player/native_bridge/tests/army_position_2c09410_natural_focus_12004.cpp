// New no-main fragment for the one33b/34b connected phase compound.
#include "xar_bridge/army_position_2c09410_12004.hpp"

#include <algorithm>
#include <cstring>
#include <map>
#include <stdexcept>
#include <vector>

namespace xar::ck3_12004 {
namespace {

constexpr std::uintptr_t image = 0x10000000;
constexpr std::uintptr_t actor = 0x20000000;
constexpr std::uintptr_t actor_data = 0x21000000;
constexpr std::uintptr_t list = 0x22000000;
constexpr std::uintptr_t record_storage = 0x23000000;
constexpr std::uintptr_t record_rows = 0x24000000;
constexpr std::uintptr_t record = 0x25000000;
constexpr std::uintptr_t fallback_record = 0x26000000;
constexpr std::uintptr_t character_storage = 0x27000000;
constexpr std::uintptr_t character_rows = 0x28000000;
constexpr std::uintptr_t opposing = 0x29000000;
constexpr std::uintptr_t holder = 0x2A000000;
constexpr std::uintptr_t filter = 0x2B000000;
constexpr std::uintptr_t participant_rows = 0x2C000000;
constexpr std::uintptr_t participant = 0x2D000000;
constexpr std::uintptr_t fallback_character = 0x2E000000;
constexpr std::uint32_t actor_id = 0x03000007;
constexpr std::uint32_t record_id = 0x02000002;
constexpr std::uint32_t opposing_id = 0x04000001;

struct Memory {
  std::map<std::uintptr_t, std::vector<unsigned char>> atoms;
  std::vector<std::uintptr_t> reads;
  std::uintptr_t denied = 0;
  std::size_t remaining_bytes = 4 * 1024 * 1024;

  template <class T> void Put(std::uintptr_t address, T value) {
    auto &bytes = atoms[address];
    bytes.resize(sizeof(value));
    std::memcpy(bytes.data(), &value, sizeof(value));
  }
  static bool Copy(void *context, std::uintptr_t address, void *output,
                   std::size_t bytes) noexcept {
    try {
      auto &memory = *static_cast<Memory *>(context);
      memory.reads.push_back(address);
      if (address == memory.denied || bytes > memory.remaining_bytes) return false;
      const auto found = memory.atoms.find(address);
      if (found == memory.atoms.end() || found->second.size() != bytes) return false;
      memory.remaining_bytes -= bytes;
      std::memcpy(output, found->second.data(), bytes);
      return true;
    } catch (...) {
      return false;
    }
  }
  ArmyRegularCoreReadonlyAccess12004 Access() {
    return {image, this, Copy, 65536};
  }
  std::size_t Reads(std::uintptr_t address) const {
    return static_cast<std::size_t>(std::count(reads.begin(), reads.end(), address));
  }
};

void Require(bool value, const char *reason) {
  if (!value) throw std::runtime_error(reason);
}

Memory Base() {
  Memory memory;
  memory.Put(actor + 0x1C0, actor_data);
  memory.Put(actor + 0x18, actor_id);
  memory.Put(actor_data + 0x318, list);
  memory.Put(actor_data + 0x324, std::int32_t{2});
  memory.Put(list, record_id);
  memory.Put(list + 4, record_id); // Repeated occurrences must remain ordered.
  memory.Put(image + 0x5D1DE58, record_storage);
  memory.Put(image + 0x5D1DE40, fallback_record);
  memory.Put(record_storage + 0x2C, std::uint32_t{3});
  memory.Put(record_storage + 0x20, record_rows);
  memory.Put(record_rows + 2 * 0x10 + 8, record);
  memory.Put(record + 8, record_id);
  memory.Put(fallback_record + 8, std::uint32_t{0x06000002});
  memory.Put(filter + 8, record_id);
  memory.Put(record + 0x20 + 8, participant_rows);
  memory.Put(record + 0x20 + 0x14, std::int32_t{1});
  memory.Put(participant_rows, participant);
  memory.Put(participant + 8, actor_id);
  memory.Put(record + 0x80 + 8, std::uintptr_t{0});
  memory.Put(record + 0x80 + 0x14, std::int32_t{0});
  memory.Put(record + 0x28C, opposing_id);
  memory.Put(image + 0x5C67568, character_storage);
  memory.Put(image + 0x5C67570, fallback_character);
  memory.Put(character_storage + 0x2C, std::uint32_t{2});
  memory.Put(character_storage + 0x20, character_rows);
  memory.Put(character_rows + 0x10 + 8, opposing);
  memory.Put(opposing + 0x18, opposing_id);
  memory.Put(opposing + 0x1C, std::uint32_t{0x43686172});
  memory.Put(holder + 0x18, opposing_id);
  memory.Put(fallback_character + 0x18, opposing_id);
  memory.Put(fallback_character + 0x1C, std::uint32_t{0x43686172});
  return memory;
}

void KnownFalse(const ArmyRegularCoreReadonlyPredicate12004 &result, const char *reason) {
  Require(result.value.has_value() && !*result.value && result.unavailable_reason.empty(), reason);
}
} // namespace

//33b owns this exact export's invocation within its only new compound main.
//The populated selected-character/holder same-full-ID shortcut uses real16b
//and28b source adapters; no predicate stubs or original/native calls are used.
void RunArmyPositionNaturalFocus12004() {
  {
    auto memory = Base();
    KnownFalse(ReadArmyPosition2C0941012004(memory.Access(), actor, holder),
               "2c09410_nonempty_same_id_child_false");
    Require(memory.Reads(list) == 1 && memory.Reads(list + 4) == 1 &&
            memory.Reads(record + 0x28C) == 2,
            "2c09410_repeated_occurrences_preserved");
  }
  {
    auto memory = Base();
    memory.Put(participant + 8, std::uint32_t{0x05000007});
    KnownFalse(ReadArmyPosition2C0941012004(memory.Access(), actor, holder),
               "2c09410_participant_complete_id_not_low24");
    Require(memory.Reads(record + 0x28C) == 0 &&
            memory.Reads(image + 0x5C67570) == 2,
            "2c09410_neither_side_uses_minus1_character_fallback");
  }
  {
    auto memory = Base();
    memory.Put(record + 8, std::uint32_t{0x07000002});
    KnownFalse(ReadArmyPosition2C0941012004(memory.Access(), actor, holder, filter),
               "2c09410_record_generation_mismatch_uses_fallback_then_filter");
    Require(memory.Reads(fallback_record + 8) == 2 &&
            memory.Reads(record + 0x20 + 8) == 0,
            "2c09410_filter_compares_resolved_fallback_complete_id");
  }
  {
    auto memory = Base();
    KnownFalse(ReadArmyPosition2C0941012004(memory.Access(), actor, holder, filter),
               "2c09410_optional_pointer_filter_admits_same_complete_id");
    Require(memory.Reads(record + 0x28C) == 2,
            "2c09410_optional_pointer_is_not_boolean");
  }
  {
    auto memory = Base();
    memory.denied = record + 0x28C;
    const auto result = ReadArmyPosition2C0941012004(memory.Access(), actor, holder);
    Require(!result.value.has_value() && !result.unavailable_reason.empty(),
            "2c09410_unread_opposing_id_remains_unknown");
  }
  {
    auto memory = Base();
    memory.remaining_bytes = sizeof(std::uintptr_t);
    const auto result = ReadArmyPosition2C0941012004(memory.Access(), actor, holder);
    Require(!result.value.has_value() && !result.unavailable_reason.empty(),
            "2c09410_shared_read_budget_does_not_become_false");
  }
  {
    auto memory = Base();
    auto access = memory.Access();
    access.maximum_occurrences = 1;
    const auto result = ReadArmyPosition2C0941012004(access, actor, holder);
    Require(!result.value.has_value() && memory.Reads(list) == 0,
            "2c09410_truncated_list_cannot_be_complete");
  }
  {
    auto memory = Base();
    memory.Put(actor + 0x1C0, std::uintptr_t{0});
    memory.Put(image + 0x5459D38, std::uintptr_t{0});
    memory.Put(image + 0x5459D44, std::int32_t{0});
    KnownFalse(ReadArmyPosition2C0941012004(memory.Access(), actor, holder),
               "2c09410_empty_default_list_is_known_false");
    Require(memory.Reads(image + 0x5D1DE58) == 0,
            "2c09410_empty_list_reads_no_record_registry");
  }
}
} // namespace xar::ck3_12004
