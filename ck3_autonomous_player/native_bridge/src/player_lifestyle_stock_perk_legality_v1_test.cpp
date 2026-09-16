#include "xar_bridge/player_lifestyle_stock_perk_legality_v1.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>

namespace {
using namespace xar::ck3_11906;
using Status = StockPerkLegalityStatusV1;
using Key = xar::game::PlayerLifestyleWindowStableKeyV1;

void Require(bool value, std::string_view why) {
  if (!value) throw std::runtime_error(std::string(why));
}

template <std::size_t N, typename T>
void Write(std::array<std::byte, N> &object, std::size_t offset,
           T value) {
  Require(offset + sizeof(T) <= object.size(), "fixture write outside object");
  std::memcpy(object.data() + offset, &value, sizeof(T));
}

Key MakeKey(std::string_view text) {
  Key key{};
  Require(!text.empty() && text.size() < key.bytes.size(), "bad test key");
  key.size = static_cast<std::uint16_t>(text.size());
  std::memcpy(key.bytes.data(), text.data(), text.size());
  return key;
}

struct Fixture {
  static constexpr std::uintptr_t kModule = 0x1000000000ULL;
  std::array<std::byte, 0x90> database{};
  std::array<std::byte, 0x490> target_definition{};
  std::array<std::byte, 0x50> lifestyle_definition{};
  std::array<std::byte, 0x30> character{};
  std::array<std::uintptr_t, 2> database_rows{};
  std::array<char, 64> target_key_text{};
  std::array<char, 64> lifestyle_key_text{};
  std::uint32_t global_player_id = 29829;
  std::uintptr_t validator_slot = kModule + 0x25DFAF0;
  StockPerkLegalityFrameV1 frame{};
  StockPerkLegalityPlayerStateV1 player_state{};
  int capture_calls = 0;
  int validator_calls = 0;
  bool native_validator_result = true;
  bool change_frame_on_last_capture = false;
  bool state_observation_available = true;
  bool main_thread = true;
  bool command_fields_valid = true;
  static Fixture *active;

  void Init() {
    constexpr std::string_view target = "cutting_corners_perk";
    constexpr std::string_view lifestyle = "stewardship_lifestyle";
    std::memcpy(target_key_text.data(), target.data(), target.size());
    std::memcpy(lifestyle_key_text.data(), lifestyle.data(), lifestyle.size());
    const auto target_text =
        reinterpret_cast<std::uintptr_t>(target_key_text.data());
    const auto lifestyle_text =
        reinterpret_cast<std::uintptr_t>(lifestyle_key_text.data());
    const auto lifestyle_pointer =
        reinterpret_cast<std::uintptr_t>(lifestyle_definition.data());
    Write(target_definition, 0x18, target_text);
    Write(target_definition, 0x28,
          static_cast<std::uint64_t>(target.size()));
    Write(target_definition, 0x30,
          static_cast<std::uint64_t>(target_key_text.size() - 1));
    Write(target_definition, 0x468, lifestyle_pointer);
    Write(lifestyle_definition, 0x18, lifestyle_text);
    Write(lifestyle_definition, 0x28,
          static_cast<std::uint64_t>(lifestyle.size()));
    Write(lifestyle_definition, 0x30,
          static_cast<std::uint64_t>(lifestyle_key_text.size() - 1));
    Write(character, 0x18, global_player_id);
    database_rows[0] =
        reinterpret_cast<std::uintptr_t>(target_definition.data());
    Write(database, 0x68,
          reinterpret_cast<std::uintptr_t>(database_rows.data()));
    Write(database, 0x70, static_cast<std::int32_t>(2));
    Write(database, 0x74, static_cast<std::int32_t>(1));
    std::memcpy(frame.episode_run_id.data(), "ordinary-feudal-episode",
                sizeof("ordinary-feudal-episode"));
    std::memcpy(frame.snapshot_id.data(), "native:23", sizeof("native:23"));
    frame.public_revision = 23;
    frame.native_revision = 7;
    frame.proof_epoch = 7;
    frame.date_raw = 53178312;
    frame.played_character_id = global_player_id;
    frame.played_character =
        reinterpret_cast<std::uintptr_t>(character.data());
    frame.paused = true;
    frame.map_ready = true;
    frame.played_character_alive = true;
    frame.storage_round_trip = true;
    player_state.current_lifestyle_key = MakeKey(lifestyle);
    player_state.unspent_perk_points = 1;
    player_state.owned_perk_state_known = true;
    player_state.target_perk_owned = false;
    active = this;
  }

  template <typename T>
  static bool CopyRange(std::uintptr_t address, void *output,
                        std::size_t size, const T &object) noexcept {
    const auto first = reinterpret_cast<std::uintptr_t>(object.data());
    if (address < first || size > sizeof(object)) return false;
    const auto offset = address - first;
    if (offset > sizeof(object) - size) return false;
    std::memcpy(output,
                reinterpret_cast<const std::byte *>(object.data()) + offset,
                size);
    return true;
  }

  static bool ReadMemory(void *context, std::uintptr_t address,
                         void *output, std::size_t size) noexcept {
    auto &f = *static_cast<Fixture *>(context);
    if (address == kModule + 0x4FE7EE0 && size == sizeof(f.global_player_id)) {
      std::memcpy(output, &f.global_player_id, size);
      return true;
    }
    if (address == kModule + 0x4323A80 && size == sizeof(f.validator_slot)) {
      std::memcpy(output, &f.validator_slot, size);
      return true;
    }
    return CopyRange(address, output, size, f.database) ||
           CopyRange(address, output, size, f.target_definition) ||
           CopyRange(address, output, size, f.lifestyle_definition) ||
           CopyRange(address, output, size, f.character) ||
           CopyRange(address, output, size, f.database_rows) ||
           CopyRange(address, output, size, f.target_key_text) ||
           CopyRange(address, output, size, f.lifestyle_key_text);
  }

  static bool Capture(void *context,
                      StockPerkLegalityFrameV1 &output) noexcept {
    auto &f = *static_cast<Fixture *>(context);
    ++f.capture_calls;
    output = f.frame;
    if (f.change_frame_on_last_capture && f.capture_calls == 3) {
      ++output.public_revision;
    }
    return true;
  }

  static bool ReadPlayer(void *context,
                         const StockPerkLegalityFrameV1 &,
                         StockPerkLegalityPlayerStateV1 &output) noexcept {
    auto &f = *static_cast<Fixture *>(context);
    if (!f.state_observation_available) return false;
    output = f.player_state;
    return true;
  }

  static bool OnMain(void *context) noexcept {
    return static_cast<Fixture *>(context)->main_thread;
  }

  static void *Database() {
    return active == nullptr ? nullptr : active->database.data();
  }

  static bool Validate(void *command, void *context) {
    if (active == nullptr) return false;
    auto &f = *active;
    ++f.validator_calls;
    const auto bytes = static_cast<const std::byte *>(command);
    std::uintptr_t primary = 0;
    std::uintptr_t secondary = 0;
    std::uintptr_t definition = 0;
    std::uint32_t character_id = 0;
    std::memcpy(&primary, bytes, sizeof(primary));
    std::memcpy(&secondary, bytes + 0x18, sizeof(secondary));
    std::memcpy(&character_id, bytes + 0x20, sizeof(character_id));
    std::memcpy(&definition, bytes + 0x28, sizeof(definition));
    f.command_fields_valid = f.command_fields_valid && context == nullptr &&
                             primary == kModule + 0x4323A50 &&
                             secondary == kModule + 0x4323A20 &&
                             character_id == f.global_player_id &&
                             definition == f.database_rows[0];
    return f.native_validator_result;
  }

  StockPerkLegalityResultV1 Run(bool exact = true) {
    active = this;
    const StockPerkLegalityEnvironmentV1 env{
        exact, kStockPerkLegalityExeSha256V1, kModule, true,
        &Fixture::Database, &Fixture::Validate};
    const StockPerkLegalityAccessV1 access{
        this, &Fixture::OnMain, &Fixture::Capture,
        &Fixture::ReadMemory, &Fixture::ReadPlayer};
    return ReadStockPerkLegalityV1(env, access);
  }
};
Fixture *Fixture::active = nullptr;

void TestLegalWithoutWindow() {
  Fixture f{};
  f.Init();
  const auto result = f.Run();
  Require(result.status == Status::observed_native_legal,
          std::string("bound stock validator should observe legal target: ") +
              std::string(StockPerkLegalityStatusKeyV1(result.status)));
  Require(result.validator_invoked_twice && f.validator_calls == 2 &&
              f.capture_calls == 3 && f.command_fields_valid,
          "both native validations must use the exact command in one frame");
  Require(result.scanned_database_rows == 1 &&
              result.observed_unspent_points == 1 &&
              result.target_definition == f.database_rows[0],
          "complete observed database/player state must be published");
}

void TestProductionBinder() {
  const auto bound = BindStockPerkLegalityEnvironmentV1(
      Fixture::kModule, true, kStockPerkLegalityExeSha256V1);
  Require(bound.module_base == Fixture::kModule &&
              reinterpret_cast<std::uintptr_t>(
                  bound.get_character_perk_database) ==
                  Fixture::kModule + 0x88EC20 &&
              reinterpret_cast<std::uintptr_t>(bound.validate_perk_command) ==
                  Fixture::kModule + 0x25DFAF0,
          "production binder must expose only the frozen exact functions");
}

void TestObservedNativeRejection() {
  Fixture f{};
  f.Init();
  f.native_validator_result = false;
  f.player_state.unspent_perk_points = 0;
  const auto result = f.Run();
  Require(result.status == Status::observed_native_illegal &&
              result.validator_invoked_twice && f.validator_calls == 2,
          "observed zero points and native false is illegal, not unknown");
}

void TestUnknownPointAndOwnershipRemainUnavailable() {
  Fixture f{};
  f.Init();
  f.player_state.unspent_perk_points = -1;
  Require(f.Run().status == Status::unavailable_state && f.validator_calls == 0,
          "unknown points must stop before native validation");
  Fixture g{};
  g.Init();
  g.player_state.owned_perk_state_known = false;
  Require(g.Run().status == Status::unavailable_state &&
              g.validator_calls == 0,
          "unknown owned state must not be false");
}

void TestDuplicateDefinitionAndAbiMismatch() {
  Fixture f{};
  f.Init();
  f.database_rows[1] = f.database_rows[0];
  Write(f.database, 0x74, static_cast<std::int32_t>(2));
  const auto duplicate = f.Run();
  Require(duplicate.status == Status::unavailable_candidate &&
              f.validator_calls == 0,
          std::string("duplicate exact target must not become a legal candidate: ") +
              std::string(StockPerkLegalityStatusKeyV1(duplicate.status)));
  Fixture g{};
  g.Init();
  g.validator_slot = 0;
  Require(g.Run().status == Status::unavailable_validator &&
              g.validator_calls == 0,
          "mismatched exact validator ABI must stay unavailable");
}

void TestBoundedDatabaseWithoutCapacityGuess() {
  Fixture f{};
  f.Init();
  Write(f.database, 0x70, static_cast<std::int32_t>(1024));
  Require(f.Run().status == Status::observed_native_legal &&
              f.validator_calls == 2,
          "overallocated database capacity with one row is still valid");
  Fixture g{};
  g.Init();
  Write(g.database, 0x70, static_cast<std::int32_t>(513));
  Write(g.database, 0x74, static_cast<std::int32_t>(513));
  Require(g.Run().status == Status::unavailable_database &&
              g.validator_calls == 0,
          "more than 512 effective rows must stop before any read");
}

void TestFrameDriftAndManualReservationBoundary() {
  Fixture f{};
  f.Init();
  f.change_frame_on_last_capture = true;
  Require(f.Run().status == Status::unavailable_drift &&
              f.validator_calls == 2,
          "later frame drift must reject an otherwise legal result");
  Fixture g{};
  g.Init();
  g.main_thread = false;
  Require(g.Run().status == Status::unavailable_binding &&
              g.validator_calls == 0,
          "worker thread must not call the stock validator");
  Fixture h{};
  h.Init();
  Require(h.Run(false).status == Status::unavailable_exact_build &&
              h.validator_calls == 0,
          "unadmitted build must stop before native reads");
}
} // namespace

int main() {
  try {
    TestLegalWithoutWindow();
    TestObservedNativeRejection();
    TestUnknownPointAndOwnershipRemainUnavailable();
    TestDuplicateDefinitionAndAbiMismatch();
    TestBoundedDatabaseWithoutCapacityGuess();
    TestFrameDriftAndManualReservationBoundary();
    TestProductionBinder();
    std::cout << "stock perk legality private fixture: 7/7 green\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "stock perk legality private fixture RED: " << error.what()
              << '\n';
    return 1;
  }
}
