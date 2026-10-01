#include "xar_bridge/ck3_12002_prewar_participants.hpp"
#include "xar_bridge/ck3_12002.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <vector>

using namespace xar::ck3_12002;
namespace {
constexpr std::int32_t kAttacker = 0x01000001;
constexpr std::int32_t kDefender = 0x02000002;
constexpr std::int32_t kSubjectA = 0x03000003;
constexpr std::int32_t kSubjectB = 0x04000004;
constexpr std::int32_t kContractA = 0x10000001;
constexpr std::int32_t kContractB = 0x11000002;
constexpr std::int32_t kContractC = 0x12000003;
constexpr std::int32_t kContractD = 0x13000004;
constexpr std::int32_t kContractE = 0x14000005;

template <std::size_t N, typename T>
void Put(std::array<std::byte, N> &target, std::size_t offset, T value) {
  if (offset + sizeof(value) > N) throw std::runtime_error("fixture offset");
  std::memcpy(target.data() + offset, &value, sizeof(value));
}
void Require(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
struct Segment { std::uintptr_t start; std::size_t size; };
struct Fixture {
  std::array<std::array<std::byte, 0x1C8>, 4> chars{};
  std::array<std::array<std::byte, 0x258>, 2> lands{};
  std::array<std::array<std::byte, 0x70>, 5> contracts{};
  std::array<std::byte, 0x9F30> term{};
  std::array<std::byte, 16> unrelated_term{};
  std::array<std::byte, 0xF08> database{};
  std::array<std::byte, 0x30> character_storage{}, contract_storage{};
  std::array<std::byte, 0x50> character_slots{};
  std::array<std::byte, 0x60> contract_slots{};
  std::array<std::int32_t, 4> attacker_contracts{
      kContractA, kContractB, kContractA, kContractD};
  std::array<std::int32_t, 2> defender_contracts{kContractC, kContractE};
  std::array<void *, 2> terms{};
  std::array<std::array<std::uint8_t, 2>, 5> levels{};
  void *character_storage_pointer = nullptr;
  void *contract_storage_pointer = nullptr;
  void *database_pointer = nullptr;
  void *fallback_pointer = nullptr;
  std::vector<Segment> segments;
  unsigned default_reads = 0;
  bool change_second_sample = false;

  template <typename T> void Admit(T &value) {
    segments.push_back({reinterpret_cast<std::uintptr_t>(&value), sizeof(value)});
  }
  Fixture() {
    const std::array<std::int32_t, 4> ids{kAttacker, kDefender, kSubjectA, kSubjectB};
    for (std::size_t i = 0; i < chars.size(); ++i) {
      Put(chars[i], 0x18, ids[i]);
      Put(character_slots, (i + 1) * 0x10 + 8, chars[i].data());
    }
    Put(chars[0], 0x1C0, lands[0].data());
    Put(chars[1], 0x1C0, lands[1].data());
    Put(lands[0], 0x248, attacker_contracts.data());
    Put(lands[0], 0x254, std::int32_t{4});
    Put(lands[1], 0x248, defender_contracts.data());
    Put(lands[1], 0x254, std::int32_t{2});
    terms = {unrelated_term.data(), term.data()};
    const std::array<std::int32_t, 5> contract_ids{
        kContractA, kContractB, kContractC, kContractD, kContractE};
    const std::array<void *, 5> subjects{
        chars[2].data(), chars[3].data(), chars[0].data(),
        chars[1].data(), chars[1].data()};
    for (std::size_t i = 0; i < contracts.size(); ++i) {
      levels[i] = {0, static_cast<std::uint8_t>(i == 1 ? 0 : 1)};
      Put(contracts[i], 0x08, contract_ids[i]);
      Put(contracts[i], 0x20, subjects[i]);
      Put(contracts[i], 0x28, chars[i == 2 || i == 4 ? 1 : 0].data());
      Put(contracts[i], 0x38, terms.data());
      Put(contracts[i], 0x44, std::int32_t{2});
      Put(contracts[i], 0x68, levels[i].data());
      Put(contract_slots, (i + 1) * 0x10 + 8, contracts[i].data());
    }
    Put(database, 0xF00, term.data());
    Put(character_storage, 0x20, character_slots.data());
    Put(character_storage, 0x2C, std::int32_t{5});
    Put(contract_storage, 0x20, contract_slots.data());
    Put(contract_storage, 0x2C, std::int32_t{6});
    character_storage_pointer = character_storage.data();
    contract_storage_pointer = contract_storage.data();
    database_pointer = database.data();
    Admit(chars); Admit(lands); Admit(contracts); Admit(term); Admit(unrelated_term);
    Admit(database); Admit(character_storage); Admit(contract_storage);
    Admit(character_slots); Admit(contract_slots); Admit(attacker_contracts);
    Admit(defender_contracts); Admit(terms); Admit(levels);
    Admit(character_storage_pointer); Admit(contract_storage_pointer);
    Admit(database_pointer); Admit(fallback_pointer);
  }
  static bool ReadMemory(void *context, const void *source, void *output,
                         std::size_t size) noexcept {
    auto &self = *static_cast<Fixture *>(context);
    const auto address = reinterpret_cast<std::uintptr_t>(source);
    if (source == self.term.data() + 0x9F28) {
      ++self.default_reads;
      if (self.change_second_sample && self.default_reads == 3)
        self.term[0x9F28] = std::byte{1};
    }
    for (const auto &segment : self.segments) {
      if (address >= segment.start && address - segment.start <= segment.size &&
          size <= segment.size - (address - segment.start)) {
        std::memcpy(output, source, size);
        return true;
      }
    }
    return false;
  }
  PrewarParticipantsBindings12002 Bindings() {
    return {true, &character_storage_pointer, &contract_storage_pointer,
            &fallback_pointer, &database_pointer};
  }
  bool Query(ForcedPrewarParticipantsSnapshot12002 &out, std::string_view &failure) {
    return ReadForcedPrewarParticipants12002(Bindings(), {this, ReadMemory},
                                             kAttacker, kDefender, out, failure);
  }
};
} // namespace

int main() {
  try {
    unsigned cases = 0;
    ForcedPrewarParticipantsSnapshot12002 out;
    std::string_view failure;
    {
      auto bindings = BindPrewarParticipantsImage12002(0x140000000, kExecutableSha256);
      Require(bindings.enabled, "exact binding");
      Require(reinterpret_cast<std::uintptr_t>(bindings.subject_contract_database_slot) ==
                  0x145D1DED0ULL, "new database slot");
      Require(!BindPrewarParticipantsImage12002(0x140000000, "old-build").enabled,
              "old executable must not bind");
      ++cases;
    }
    {
      Fixture f;
      Require(f.Query(out, failure), "normal native graph");
      Require(out.available && !out.complete_initial_participants_ready, "subset boundary");
      Require(out.forced_participants.size() == 4, "duplicates and self rows retained");
      Require(out.forced_participants[0].subject_contract_id == kContractA &&
                  out.forced_participants[1].source_contract_native_order == 2 &&
                  !out.forced_participants[2].attacker_side &&
                  out.forced_participants[2].character_id == kAttacker &&
                  out.forced_participants[3].character_id == kDefender,
              "native order and asymmetric collision");
      Require(out.excluded_primary_defender_collisions.size() == 1 &&
                  out.excluded_primary_defender_collisions[0].subject_contract_id == kContractD,
              "attacker collision excluded");
      const auto wire = SerializeForcedPrewarParticipants12002(out);
      Require(wire.find("\"complete_initial_participants_ready\":false") != std::string::npos &&
                  wire.find("\"source_contract_native_order\":2") != std::string::npos,
              "portable JSON source fields");
      std::cout << wire << '\n';
      ++cases;
    }
    {
      Fixture f;
      Put(f.chars[0], 0x1C0, static_cast<void *>(nullptr));
      Put(f.chars[1], 0x1C0, static_cast<void *>(nullptr));
      Require(f.Query(out, failure) && out.forced_participants.empty(), "unlanded native empty");
      ++cases;
    }
    {
      Fixture f; f.database_pointer = nullptr;
      Require(!f.Query(out, failure) && failure == "subject_contract_obligation_database_unavailable",
              "no lazy database initialization");
      ++cases;
    }
    {
      Fixture f;
      Put(f.contracts[0], 0x08, std::int32_t{0x20000001});
      Require(!f.Query(out, failure) && failure == "subject_contract_identity_unavailable",
              "full contract generation");
      ++cases;
    }
    {
      Fixture f;
      Put(f.contracts[0], 0x28, f.chars[1].data());
      Require(!f.Query(out, failure), "source endpoint must match");
      ++cases;
    }
    {
      Fixture f;
      Put(f.character_slots, 3 * 0x10 + 8, f.chars[3].data());
      Require(!f.Query(out, failure) && failure == "subject_character_identity_unavailable",
              "subject identity must resolve");
      ++cases;
    }
    {
      Fixture f;
      f.fallback_pointer = f.contracts[0].data();
      Require(!f.Query(out, failure), "fallback object is not valid contract");
      ++cases;
    }
    {
      Fixture f;
      f.terms[1] = f.unrelated_term.data();
      Require(f.Query(out, failure) && out.forced_participants.empty(), "absent obligation not forced");
      ++cases;
    }
    {
      Fixture f;
      f.terms[0] = f.term.data();
      Require(f.Query(out, failure) && out.forced_participants.empty(),
              "duplicate term selects first native occurrence");
      ++cases;
    }
    {
      Fixture f; f.change_second_sample = true;
      Require(!f.Query(out, failure) && failure == "prewar_subject_contract_samples_changed",
              "changed observation cannot publish stable subset");
      ++cases;
    }
    std::cout << "GREEN forced_prewar_participants_cases=" << cases
              << " live_verified=false game_process_touched=false\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "RED " << error.what() << '\n';
    return 1;
  }
}
