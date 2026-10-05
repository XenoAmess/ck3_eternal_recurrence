#include "xar_bridge/ck3_12002_army.hpp"
#include "xar_bridge/ck3_12003_army_replenishment_records.hpp"
#include "xar_bridge/army_strength_v1_serializer.hpp"

#include <array>
#include <cstddef>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {
constexpr std::int32_t kArRg = 117440517;
constexpr std::int32_t kRegi = 301989889;
void *expected_receiver = nullptr;
int predicate_calls = 0;
bool skipped = false;
template <class T, std::size_t N>
void Put(std::array<std::byte, N> &bytes, std::size_t offset, T value) {
  std::memcpy(bytes.data() + offset, &value, sizeof value);
}
void Require(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
bool Admission(void *receiver) {
  Require(receiver == expected_receiver, "admission receives resolvedArRg");
  ++predicate_calls;
  return skipped;
}
bool CanRegiment(void *, void *) { return false; }
bool CanChunk(void *) { return false; }
std::int64_t *Fraction(void *, std::int64_t *out) { *out = 0; return out; }
}

int main() {
  try {
    std::array<std::byte, 0x60> raised{};
    std::array<std::byte, 0x200> persistent{};
    std::array<std::byte, 0x10> data{};
    std::array<std::byte, 0x30> storage{};
    std::array<std::byte, 2 * 0x10> slots{};
    void *storage_ptr = storage.data();
    Put(raised, 0x10, kArRg);
    Put(raised, 0x14, std::uint32_t{0x41725267U});
    Put(raised, 0x20, static_cast<void *>(data.data()));
    Put(raised, 0x28, std::int32_t{1});
    Put(raised, 0x2C, std::int32_t{1});
    Put(data, 8, kRegi);
    Put(data, 0xC, std::int32_t{0});
    Put(persistent, 0x10, kRegi);
    Put(persistent, 0x14, std::uint32_t{0x52656769U});
    Put(persistent, 0x18, std::int32_t{25});
    Put(persistent, 0x1C, std::int32_t{20});
    Put(persistent, 0x20, kRegi);
    Put(persistent, 0x24, std::int32_t{0});
    Put(persistent, 0x28, kArRg);
    Put(slots, 0x18, static_cast<void *>(persistent.data()));
    Put(storage, 0x20, static_cast<void *>(slots.data()));
    Put(storage, 0x2C, std::int32_t{2});
    expected_receiver = raised.data();
    xar::ck3_12002::ArmyBindings bindings{};
    bindings.enabled = true;
    bindings.persistent_regiment_storage_slot = &storage_ptr;
    bindings.can_regiment_replenish = CanRegiment;
    bindings.can_chunk_replenish = CanChunk;
    bindings.get_regiment_monthly_replenishment_fraction = Fraction;
    bindings.is_army_regiment_loss_writer_skipped = Admission;
    auto row = xar::ck3_12003::ReadArmyRegimentReplenishmentRecordsV1(bindings, raised.data(), kArRg);
    Require(row.status == xar::game::ArmyRegimentReplenishmentRecordsStatusV1::available &&
                row.native_loss_writer_skipped == false && predicate_calls == 1,
            "production reader publishes false admission as a knownvalue");
    Require(row.records.size() == 1 && row.records[0].chunk_army_regiment_id == kArRg &&
                row.records[0].current_soldiers == 20 && row.records[0].maximum_soldiers == 25,
            "complete DATA publishes its exact non−1 setter association");
    xar::game::ArmyStrengthSnapshot strength{};
    strength.available = true;
    strength.regiment_replenishment_records_v1 = std::vector{row};
    std::string wire;
    xar::game::AppendArmyStrengthV1(wire, strength,
        [](std::int64_t value) { return std::to_string(value); },
        [](std::string &out, const std::vector<std::int32_t> &) { out += "[]"; },
        [](std::string &out, std::string_view value) { out += '"'; out += value; out += '"'; });
    Require(wire.find("\"native_loss_writer_skipped\":false") != std::string::npos &&
                wire.find("\"chunk_army_regiment_id\":117440517") != std::string::npos,
            "production serializer retains admission and raw setter association");
    skipped = true;
    row = xar::ck3_12003::ReadArmyRegimentReplenishmentRecordsV1(bindings, raised.data(), kArRg);
    Require(row.native_loss_writer_skipped == true && predicate_calls == 2,
            "character-writer skip remains independent of DATA health");
    bindings.is_army_regiment_loss_writer_skipped = nullptr;
    row = xar::ck3_12003::ReadArmyRegimentReplenishmentRecordsV1(bindings, raised.data(), kArRg);
    Require(!row.native_loss_writer_skipped.has_value() &&
                row.loss_writer_admission_unavailable_reason == "loss_writer_admission_bindings_unavailable" &&
                row.status == xar::game::ArmyRegimentReplenishmentRecordsStatusV1::available,
            "older binding preserves knownDATA without inventing admission");
    std::cout << "PASS: production loss admission and associated DATA reader/wire\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
