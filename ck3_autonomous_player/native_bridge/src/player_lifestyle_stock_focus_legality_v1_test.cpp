#include "xar_bridge/player_lifestyle_stock_focus_legality_v1.hpp"

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
using Status = StockFocusLegalityStatusV1;

void Require(bool value, std::string_view reason) {
  if (!value) throw std::runtime_error(std::string(reason));
}

template <std::size_t N, typename T>
void Write(std::array<std::byte, N> &object, std::size_t offset, T value) {
  Require(offset + sizeof(T) <= object.size(), "fixture write out of range");
  std::memcpy(object.data() + offset, &value, sizeof(T));
}

struct Fixture {
  static constexpr std::uintptr_t kModule = 0x1000000000ULL;
  std::array<std::byte, 0xF40> database{};
  std::array<std::byte, 0x900> definition{};
  std::array<std::byte, 0x50> lifestyle{};
  std::array<std::byte, 0x30> character{};
  std::array<std::uintptr_t, 2> rows{};
  std::array<char, 64> definition_key{};
  std::array<char, 64> lifestyle_key{};
  std::uintptr_t database_global = 0;
  std::uint32_t played_id = 29829;
  std::uintptr_t validator_slot = kModule + 0x25DF570;
  StockFocusLegalityFrameV1 frame{};
  int captures = 0;
  int validator_calls = 0;
  int progress_calls = 0;
  bool validator_result = true;
  bool progress_available = true;
  bool progress_drift = false;
  bool on_main = true;
  bool drift = false;
  bool command_correct = true;
  static Fixture *active;

  void Init() {
    constexpr std::string_view focus_name = "stewardship_wealth_focus";
    constexpr std::string_view lifestyle_name = "stewardship_lifestyle";
    std::memcpy(definition_key.data(), focus_name.data(), focus_name.size());
    std::memcpy(lifestyle_key.data(), lifestyle_name.data(),
                lifestyle_name.size());
    Write(definition, 0x18,
          reinterpret_cast<std::uintptr_t>(definition_key.data()));
    Write(definition, 0x28,
          static_cast<std::uint64_t>(focus_name.size()));
    Write(definition, 0x30,
          static_cast<std::uint64_t>(definition_key.size() - 1));
    Write(definition, 0x880,
          reinterpret_cast<std::uintptr_t>(lifestyle.data()));
    Write(lifestyle, 0x18,
          reinterpret_cast<std::uintptr_t>(lifestyle_key.data()));
    Write(lifestyle, 0x28,
          static_cast<std::uint64_t>(lifestyle_name.size()));
    Write(lifestyle, 0x30,
          static_cast<std::uint64_t>(lifestyle_key.size() - 1));
    Write(character, 0x18, played_id);
    rows[0] = reinterpret_cast<std::uintptr_t>(definition.data());
    Write(database, 0xF20,
          reinterpret_cast<std::uintptr_t>(rows.data()));
    Write(database, 0xF28, static_cast<std::int32_t>(2));
    Write(database, 0xF2C, static_cast<std::int32_t>(1));
    database_global = reinterpret_cast<std::uintptr_t>(database.data());
    std::memcpy(frame.episode_run_id.data(), "life-focus-fixture",
                sizeof("life-focus-fixture"));
    std::memcpy(frame.snapshot_id.data(), "native:23",
                sizeof("native:23"));
    frame.public_revision = 23;
    frame.native_revision = 7;
    frame.proof_epoch = 7;
    frame.date_raw = 53178312;
    frame.played_character_id = played_id;
    frame.played_character =
        reinterpret_cast<std::uintptr_t>(character.data());
    frame.paused = true;
    frame.map_ready = true;
    frame.played_character_alive = true;
    frame.storage_round_trip = true;
    active = this;
  }

  template <typename T>
  static bool CopyRange(std::uintptr_t address, void *out,
                        std::size_t size, const T &object) noexcept {
    const auto first = reinterpret_cast<std::uintptr_t>(object.data());
    if (address < first || size > sizeof(object)) return false;
    const auto offset = address - first;
    if (offset > sizeof(object) - size) return false;
    std::memcpy(out,
                reinterpret_cast<const std::byte *>(object.data()) + offset,
                size);
    return true;
  }

  static bool ReadMemory(void *context, std::uintptr_t address,
                         void *out, std::size_t size) noexcept {
    const auto &f = *static_cast<Fixture *>(context);
    if (address == kModule + 0x570BDE8 && size == sizeof(f.database_global)) {
      std::memcpy(out, &f.database_global, size);
      return true;
    }
    if (address == kModule + 0x4FE7EE0 && size == sizeof(f.played_id)) {
      std::memcpy(out, &f.played_id, size);
      return true;
    }
    if (address == kModule + 0x4323C10 && size == sizeof(f.validator_slot)) {
      std::memcpy(out, &f.validator_slot, size);
      return true;
    }
    return CopyRange(address, out, size, f.database) ||
           CopyRange(address, out, size, f.definition) ||
           CopyRange(address, out, size, f.lifestyle) ||
           CopyRange(address, out, size, f.character) ||
           CopyRange(address, out, size, f.rows) ||
           CopyRange(address, out, size, f.definition_key) ||
           CopyRange(address, out, size, f.lifestyle_key);
  }

  static bool Capture(void *context,
                      StockFocusLegalityFrameV1 &out) noexcept {
    auto &f = *static_cast<Fixture *>(context);
    ++f.captures;
    out = f.frame;
    if (f.drift && f.captures == 3) ++out.public_revision;
    return true;
  }

  static bool OnMain(void *context) noexcept {
    return static_cast<Fixture *>(context)->on_main;
  }

  static bool CaptureTargetProgress(
      void *context, const StockFocusLegalityFrameV1 &frame,
      std::uintptr_t lifestyle,
      StockFocusTargetProgressV1 &out) noexcept {
    auto &f = *static_cast<Fixture *>(context);
    ++f.progress_calls;
    if (!f.progress_available || frame != f.frame ||
        lifestyle != reinterpret_cast<std::uintptr_t>(f.lifestyle.data())) {
      return false;
    }
    out = {true, f.progress_drift && f.progress_calls == 2 ? 1 : 0,
           0, 1000, 0, 0};
    return true;
  }

  static bool Validate(void *command, void *context) {
    if (active == nullptr) return false;
    auto &f = *active;
    ++f.validator_calls;
    const auto *bytes = static_cast<const std::byte *>(command);
    std::uintptr_t primary = 0;
    std::uintptr_t secondary = 0;
    std::uintptr_t definition_pointer = 0;
    std::uint32_t played = 0;
    std::uint32_t current = 0;
    std::memcpy(&primary, bytes, sizeof(primary));
    std::memcpy(&secondary, bytes + 0x18, sizeof(secondary));
    std::memcpy(&played, bytes + 0x20, sizeof(played));
    std::memcpy(&definition_pointer, bytes + 0x28,
                sizeof(definition_pointer));
    std::memcpy(&current, bytes + 0x30, sizeof(current));
    f.command_correct = f.command_correct && context == nullptr &&
                        primary == kModule + 0x4323BE0 &&
                        secondary == kModule + 0x4323BB0 &&
                        played == f.played_id && current == f.played_id &&
                        definition_pointer == f.rows[0];
    return f.validator_result;
  }

  StockFocusLegalityResultV1 Run(bool exact = true) {
    active = this;
    const StockFocusLegalityEnvironmentV1 env{
        exact, kStockFocusLegalityExeSha256V1, kModule, true,
        &Fixture::Validate};
    const StockFocusLegalityAccessV1 access{
        this, &Fixture::OnMain, &Fixture::Capture, &Fixture::ReadMemory,
        &Fixture::CaptureTargetProgress};
    return ReadStockFocusLegalityV1(env, access);
  }
};
Fixture *Fixture::active = nullptr;

void TestLegalAndExactBinder() {
  Fixture f{};
  f.Init();
  const auto result = f.Run();
  Require(result.status == Status::observed_native_legal &&
              result.validator_invoked_twice && f.validator_calls == 2 &&
              f.progress_calls == 2 && result.target_progress.available &&
              result.target_progress.xp_total_raw == 0 &&
              result.target_progress.unspent_perk_points == 0 &&
              f.captures == 3 && f.command_correct &&
              result.scanned_database_rows == 1 &&
              result.target_definition == f.rows[0],
          "exact focus source and two native calls must agree");
  const auto bound = BindStockFocusLegalityEnvironmentV1(
      Fixture::kModule, true, kStockFocusLegalityExeSha256V1);
  Require(reinterpret_cast<std::uintptr_t>(bound.validate_focus_command) ==
              Fixture::kModule + 0x25DF570,
          "production binder must point at exact focus validator");
}

void TestTargetProgressUnavailableAndDriftStayTyped() {
  Fixture unavailable{};
  unavailable.Init();
  unavailable.progress_available = false;
  const auto legal = unavailable.Run();
  Require(legal.status == Status::observed_native_legal &&
              !legal.target_progress.available &&
              legal.target_progress.xp_total_raw == -1 &&
              legal.target_progress.unspent_perk_points == -1,
          "unread target progress must not become zero");
  Fixture drift{};
  drift.Init();
  drift.progress_drift = true;
  Require(drift.Run().status == Status::unavailable_drift,
          "target progress changing between same-frame reads is drift");
}

void TestNativeRejectionIsNotUnknown() {
  Fixture f{};
  f.Init();
  f.validator_result = false;
  Require(f.Run().status == Status::observed_native_illegal &&
              f.validator_calls == 2,
          "two stock false results are a native rejection");
}

void TestUnresolvedSourceNeverCallsValidator() {
  Fixture absent{};
  absent.Init();
  absent.database_global = 0;
  Require(absent.Run().status == Status::unavailable_database &&
              absent.validator_calls == 0,
          "missing database must stay unavailable");
  Fixture duplicate{};
  duplicate.Init();
  duplicate.rows[1] = duplicate.rows[0];
  Write(duplicate.database, 0xF2C, static_cast<std::int32_t>(2));
  Require(duplicate.Run().status == Status::unavailable_candidate &&
              duplicate.validator_calls == 0,
          "duplicate stable target must stay unavailable");
  Fixture mismatched{};
  mismatched.Init();
  mismatched.validator_slot = 0;
  Require(mismatched.Run().status == Status::unavailable_validator &&
              mismatched.validator_calls == 0,
          "changed exact validator slot must stay unavailable");
}

void TestFrameAndBuildGates() {
  Fixture f{};
  f.Init();
  f.on_main = false;
  Require(f.Run().status == Status::unavailable_binding &&
              f.validator_calls == 0,
          "non-main thread must not call stock validator");
  Fixture g{};
  g.Init();
  g.drift = true;
  Require(g.Run().status == Status::unavailable_drift &&
              g.validator_calls == 2,
          "frame drift cannot publish legality");
  Fixture h{};
  h.Init();
  Require(h.Run(false).status == Status::unavailable_exact_build &&
              h.validator_calls == 0,
          "other builds cannot read exact offsets");
}
} // namespace

int main() {
  try {
    TestLegalAndExactBinder();
    TestNativeRejectionIsNotUnknown();
    TestTargetProgressUnavailableAndDriftStayTyped();
    TestUnresolvedSourceNeverCallsValidator();
    TestFrameAndBuildGates();
    std::cout << "stock focus legality: 5/5 GREEN\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "stock focus legality: RED: " << error.what() << '\n';
    return 1;
  }
}
