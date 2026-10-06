#include "xar_bridge/ck3_12004_core_frame_v1.hpp"
#include "xar_bridge/ck3_12004_thread_runtime.hpp"
#include "xar_bridge/ck3_12003.hpp"
#include "ck3_12004_foundation_fixture_support.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace {
namespace current = xar::ck3_12004;
namespace mailbox = xar::ck3_11906;
constexpr std::int32_t kDate = 45000000;
constexpr std::uintptr_t kFixtureBase = 0x140000000;
void *g_tls_context = nullptr;

void Check(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
BOOL WINAPI FakePeek(LPMSG, HWND, UINT, UINT, UINT) { return FALSE; }
void *__fastcall FakeTls() noexcept { return g_tls_context; }

struct PumpFixture {
  std::array<std::byte, 0x18> rng{};
  std::uintptr_t rng_wrapper = 0;
  std::uintptr_t rng_slot = 0;
  std::array<std::byte, 0x28> jomini{};
  std::array<std::byte, 0x18> game{};
  std::uintptr_t jomini_slot = 0;
  std::uintptr_t game_slot = 0;
  std::uint8_t tls_initialized = 1;
  std::array<std::byte, 0x28> tls{};
  void *peek_slot = reinterpret_cast<void *>(&FakePeek);
  DWORD protection = PAGE_READONLY;

  explicit PumpFixture(std::uint32_t owner) {
    std::memcpy(rng.data() + 0x10, &owner, sizeof(owner));
    rng_wrapper = reinterpret_cast<std::uintptr_t>(rng.data());
    rng_slot = reinterpret_cast<std::uintptr_t>(&rng_wrapper);
    jomini[0x20] = std::byte{1};
    std::memcpy(game.data() + 0x08, &kDate, sizeof(kDate));
    jomini_slot = reinterpret_cast<std::uintptr_t>(jomini.data());
    game_slot = reinterpret_cast<std::uintptr_t>(game.data());
    tls[0x20] = std::byte{1};
    g_tls_context = tls.data();
  }

  static bool Query(void *opaque, const void *address,
      MEMORY_BASIC_INFORMATION &information) noexcept {
    auto &runtime = *static_cast<PumpFixture *>(opaque);
    if (address != &runtime.peek_slot) return false;
    const auto page = reinterpret_cast<std::uintptr_t>(address) & ~std::uintptr_t{4095};
    information = {};
    information.BaseAddress = reinterpret_cast<void *>(page);
    information.AllocationBase = information.BaseAddress;
    information.RegionSize = 4096;
    information.State = MEM_COMMIT;
    information.Protect = runtime.protection;
    information.Type = MEM_IMAGE;
    return true;
  }
  static bool Protect(void *opaque, void *, std::size_t bytes,
      DWORD requested, DWORD &previous) noexcept {
    auto &runtime = *static_cast<PumpFixture *>(opaque);
    if (bytes != 4096) return false;
    previous = runtime.protection;
    runtime.protection = requested;
    return true;
  }

  mailbox::MainThreadQueryInstallEnvironmentV1 Environment() {
    // Use the production one-executor registration and actual .4 profile.
    // Only caller-owned IAT/memory/TLS objects are overridden for this fixture.
    auto environment = current::BindCoreFrameMailboxEnvironmentV1(
        kFixtureBase, current::kExecutableSha256);
    environment.offline_fixture = true;
    environment.peek_message_iat_slot_override = &peek_slot;
    environment.resolved_peek_message_override = &FakePeek;
    environment.global_rng_wrapper_slot_override = reinterpret_cast<std::uintptr_t>(&rng_slot);
    environment.jomini_state_slot_override = reinterpret_cast<std::uintptr_t>(&jomini_slot);
    environment.game_state_slot_override = reinterpret_cast<std::uintptr_t>(&game_slot);
    environment.tls_initialized_flag_override = reinterpret_cast<std::uintptr_t>(&tls_initialized);
    environment.tls_context_getter_override = &FakeTls;
    environment.memory_protection_context = this;
    environment.memory_query_override = &Query;
    environment.memory_protect_override = &Protect;
    environment.system_page_size_override = 4096;
    return environment;
  }
};

struct Scene {
  const char *filename;
  int mutation;
  bool available;
  bool has_character;
  std::int32_t character_id;
};

void WriteScene(const Scene &scene, const std::filesystem::path &output) {
  current::fixture::CoreMemory memory;
  switch (scene.mutation) {
  case 1: memory.SetMenu(); break;
  case 2: memory.SetPlayingCharacterFullId(scene.character_id); break;
  case 3: memory.SetCharacterFullId(29829 + 0x01000000); break;
  case 4: memory.SetEntryPlayerId(1); break;
  case 5: memory.SetClock(kDate, 5, true); break;
  }
  current::CoreSnapshotPrefix raw{};
  Check(current::ReadCoreSnapshot(memory.Bindings(), raw) == scene.available,
      "actual .4 core reader result differs");
  if (scene.available) {
    Check(raw.clock.date_raw == kDate && raw.clock.speed == 5 && raw.clock.paused,
        "actual .4 clock prefix differs");
    Check(raw.has_played_character == scene.has_character &&
        raw.played_character_id == scene.character_id,
        "actual .4 complete CharacterID resolution differs");
  }

  auto adapter = xar::game::CreateCk3_12004AdapterFromBindings(memory.AdapterBindings());
  Check(adapter != nullptr && adapter->enabled(), "fixture adapter is unavailable");
  Check(adapter->supports_step(current::kCoreFrameStepV1) && !adapter->supports_snapshot(),
      "partial core capability advertised as complete Snapshot");
  current::CoreFrameMailboxContextV1 context{};
  context.game = adapter.get();

  const auto owner = GetCurrentThreadId();
  PumpFixture runtime(owner);
  auto environment = runtime.Environment();
  Check(environment.permitted_executor == &current::ExecuteCoreFrameMailboxV1 &&
      environment.snapshot_observer_callback == nullptr,
      "production registration differs from core-only dispatch");
  mailbox::MainThreadQueryMailboxV1 state{};
  Check(mailbox::InstallMainThreadQueryMailboxV1(state, environment),
      "fixture app-main mailbox installation failed");
  const auto boundary = current::ThreadRuntimeBuildProfile().pump_exact_return_rva;
  mailbox::ObserveMainThreadPumpAndDrainV1(state, boundary, owner);
  mailbox::ObserveMainThreadPumpAndDrainV1(state, boundary, owner);
  mailbox::MainThreadQueryTicketV1 ticket{};
  Check(mailbox::TrySubmitMainThreadQueryV1(state, environment.permitted_executor,
      &context, ticket) == mailbox::MainThreadQuerySubmitResultV1::submitted,
      "actual core executor was not accepted by registered mailbox");
  Check(mailbox::ObserveMainThreadPumpAndDrainV1(state, boundary, owner),
      "actual core executor did not run on the owned pump");
  Check(mailbox::WaitForMainThreadQueryV1(state, ticket, 1000) ==
      mailbox::MainThreadQueryWaitResultV1::completed,
      "actual core executor did not complete");
  Check(mailbox::ReclaimMainThreadQueryV1(state, ticket) ==
      mailbox::MainThreadQueryReclaimResultV1::reclaimed,
      "actual core executor result was not reclaimable");
  Check(mailbox::UninstallMainThreadQueryMailboxV1(state, 1000) ==
      mailbox::MainThreadQueryUninstallResultV1::uninstalled,
      "fixture app-main mailbox uninstall failed");
  Check(context.observation.core_available == scene.available &&
      context.observation.application_main_observed,
      "core-only observation availability differs");

  const auto wire = current::SerializeCoreFrameCommandResultV1(
      "core-frame-fixture", context.observation);
  Check(wire.find("\"type\":\"command_result\",\"protocol_version\":1") != std::string::npos &&
      wire.find("\"request_id\":\"core-frame-fixture\",\"ok\":true,\"result\":") != std::string::npos &&
      wire.find("\"schema\":\"ck3_12004_core_frame_v1\"") != std::string::npos &&
      wire.find("\"complete_snapshot\":false") != std::string::npos &&
      wire.find(current::kExecutableSha256) != std::string::npos,
      "whole command-result identity/partial metadata differs");
  if (scene.available) {
    Check(wire.find("\"status\":\"partial\"") != std::string::npos &&
        wire.find("\"played_character_id\":" + std::to_string(scene.character_id)) != std::string::npos,
        "raw full CharacterID was not published");
  } else {
    Check(wire.find("\"status\":\"unavailable\"") != std::string::npos &&
        wire.find("\"date_raw\":null") != std::string::npos &&
        wire.find("\"played_character_id\":null") != std::string::npos,
        "unavailable core prefix was serialized as zero values");
  }
  std::ofstream file(output / scene.filename, std::ios::binary);
  file << wire << '\n';
  Check(file.good(), "whole command-result output failed");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "usage: xar_ck3_12004_core_frame_v1_test <wire-output-dir>");
    const auto bound = current::BindCoreImage(kFixtureBase, current::kExecutableSha256);
    Check(bound.enabled && reinterpret_cast<std::uintptr_t>(bound.game_state_slot) ==
        kFixtureBase + current::kGameStateSlotRva &&
        reinterpret_cast<std::uintptr_t>(bound.jomini_state_slot) ==
        kFixtureBase + current::kJominiStateSlotRva &&
        reinterpret_cast<std::uintptr_t>(bound.character_storage_slot) ==
        kFixtureBase + current::kCharacterStorageSlotRva &&
        reinterpret_cast<std::uintptr_t>(bound.get_local_player) ==
        kFixtureBase + current::kGetLocalPlayerRva,
        "actual .4 core image address arithmetic differs");
    Check(!current::BindCoreImage(0, current::kExecutableSha256).enabled &&
        !current::BindCoreImage(kFixtureBase, xar::ck3_12003::kExecutableSha256).enabled &&
        !current::BindCoreImage(kFixtureBase, "wrong-sha").enabled,
        "actual .4 core binder accepted another image identity");
    const std::filesystem::path output(argv[1]);
    std::filesystem::create_directories(output);
    const std::array scenes{
        Scene{"core-frame-robert-paused.json", 0, true, true, 29829},
        Scene{"core-frame-menu.json", 1, true, false, -1},
        Scene{"core-frame-full-generation.json", 2, true, true, -2147453819},
        Scene{"core-frame-wrong-generation.json", 3, true, false, -1},
        Scene{"core-frame-mixed-player.json", 4, true, false, -1},
        Scene{"core-frame-invalid-clock.json", 5, false, false, -1}};
    for (const auto &scene : scenes) WriteScene(scene, output);
    std::cout << "core-frame fixture: six whole command-result wires\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
