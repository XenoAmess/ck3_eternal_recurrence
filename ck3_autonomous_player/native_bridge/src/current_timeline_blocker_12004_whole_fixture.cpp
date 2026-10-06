#include "xar_bridge/ck3_12004_succession_modal.hpp"
#include "xar_bridge/ck3_12004_succession_modal_pins.hpp"
#include "ck3_12004_foundation_fixture_support.hpp"

#include <windows.h>

#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>

namespace {
using namespace xar;
constexpr std::int32_t kActor = ck3_12004::fixture::CoreMemory::kCharacterId;
constexpr std::int32_t kDate = 53'276'520;
constexpr std::uint64_t kRevision = 77;

void Require(bool value, std::string_view message) {
  if (!value) throw std::runtime_error(std::string(message));
}

template <typename T>
void Put(void *object, std::size_t offset, const T &value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}

struct Fixture;
Fixture *active = nullptr;

struct Fixture {
  std::byte *image = nullptr;
  ck3_12004::fixture::CoreMemory core{kDate, 0, true};
  ck3_12004::SuccessionModalBindings12004 bindings{};
  std::array<std::byte, 0x30> root{};
  std::array<std::byte, 0x10> idler{};
  std::array<std::byte, 0x100> ingame{};
  std::array<std::byte, 0x300> handler{};
  std::array<std::byte, 0x100> controller{};
  bool modal_visible = false;
  std::uint32_t widget_reads = 0;
  std::uint32_t predicate_reads = 0;
  std::uint32_t controller_resolutions = 0;
  std::uint32_t controller_open_reads = 0;
  std::uint32_t close_invocations = 0;

  Fixture();
  ~Fixture() {
    if (image != nullptr) VirtualFree(image, 0, MEM_RELEASE);
    active = nullptr;
  }
  Fixture(const Fixture &) = delete;
  Fixture &operator=(const Fixture &) = delete;
};

bool ObserveWidget(void *opaque, ck3_11906::CurrentTimelineFixedWidgetV1 identity,
                   ck3_11906::CurrentTimelineWidgetObservationV1 &output) noexcept {
  auto &fixture = *static_cast<Fixture *>(opaque);
  ++fixture.widget_reads;
  output = {};
  if (identity == ck3_11906::CurrentTimelineFixedWidgetV1::succession_root ||
      identity == ck3_11906::CurrentTimelineFixedWidgetV1::succession_bottom ||
      identity == ck3_11906::CurrentTimelineFixedWidgetV1::succession_close) {
    output = {true, fixture.modal_visible, fixture.modal_visible};
  }
  return true;
}

bool __fastcall IsPaused() {
  ++active->predicate_reads;
  return active->modal_visible;
}

bool __fastcall HasOpen(void *character) {
  ++active->predicate_reads;
  return character == ck3_12004::ResolveCoreCharacter(active->bindings.core, kActor) &&
         active->modal_visible;
}

void *__cdecl Cast(void *source, long offset, void *source_type,
                   void *target_type, int reference) {
  auto &fixture = *active;
  ++fixture.controller_resolutions;
  const auto base = reinterpret_cast<std::uintptr_t>(fixture.image);
  return source == fixture.idler.data() && offset == 0 && reference == 0 &&
         reinterpret_cast<std::uintptr_t>(source_type) ==
             base + ck3_12004::kSuccessionIdlerBaseTypeDescriptorRva12004 &&
         reinterpret_cast<std::uintptr_t>(target_type) ==
             base + ck3_12004::kSuccessionIngameIdlerTypeDescriptorRva12004
             ? fixture.ingame.data() : nullptr;
}

bool __fastcall Open(void *controller) {
  ++active->controller_open_reads;
  return controller == active->controller.data() && active->modal_visible;
}

void __fastcall Close(void *controller) {
  if (controller == active->controller.data()) ++active->close_invocations;
  // Submission leaves the current observation intact. The independent later
  // fixture observation changes the state; a method return never clears it.
}

Fixture::Fixture() {
  Require(ck3_12004::kSuccessionModalNativePinsReady12004,
          "actual .4 modal mapping is still pending");
  image = static_cast<std::byte *>(VirtualAlloc(nullptr, 0x5D00000,
      MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE));
  Require(image != nullptr, "fixture-owned image allocation failed");
  active = this;
  const auto base = reinterpret_cast<std::uintptr_t>(image);
  const ck3_12004::SuccessionModalGuiProfile12004 gui{true, base, this, &ObserveWidget};
  bindings = ck3_12004::BindSuccessionModalImage12004(
      base, ck3_12004::kExecutableSha256, gui);
  Require(bindings.enabled && bindings.image_base == base,
          "independent exact .4 binder rejected fixture image");
  Require(reinterpret_cast<std::uintptr_t>(bindings.dynamic_cast_function) ==
              base + ck3_12004::kSuccessionRuntimeDynamicCastRva12004 &&
          reinterpret_cast<std::uintptr_t>(bindings.controller_open) ==
              base + ck3_12004::kSuccessionControllerOpenRva12004 &&
          reinterpret_cast<std::uintptr_t>(bindings.controller_close) ==
              base + ck3_12004::kSuccessionControllerCloseRva12004,
          "binder did not select actual .4 native callback pins");
  Require(!ck3_12004::BindSuccessionModalImage12004(base,
      "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6", gui).enabled,
      ".4 binder admitted the historical .3 executable");
  Require(!ck3_12004::BindSuccessionModalImage12004(
      base, ck3_12004::kExecutableSha256, {}).enabled,
      ".4 binder admitted an unavailable GUI profile");

  bindings.core = core.Bindings();
  Put(image, ck3_12004::kJominiStateSlotRva, root.data());
  Put(root.data(), ck3_12004::kSuccessionIdlerBaseOffset12004, idler.data());
  Put(ingame.data(), ck3_12004::kSuccessionIngameHandlerOffset12004, handler.data());
  Put(handler.data(), 0, bindings.handler_primary_vtable);
  Put(handler.data(), ck3_12004::kSuccessionHandlerControllerOffset12004,
      controller.data());
  Put(controller.data(), 0, bindings.controller_primary_vtable);
  bindings.dynamic_cast_function = &Cast;
  bindings.is_paused_by_succession = &IsPaused;
  bindings.has_open_succession = &HasOpen;
  bindings.controller_open = &Open;
  bindings.controller_close = &Close;
  Put(image, ck3_12004::kSuccessionControllerPrimaryVtableRva12004 +
      ck3_12004::kSuccessionControllerOpenVslot12004,
      reinterpret_cast<std::uintptr_t>(&Open));
  Put(image, ck3_12004::kSuccessionControllerPrimaryVtableRva12004 +
      ck3_12004::kSuccessionControllerCloseVslot12004,
      reinterpret_cast<std::uintptr_t>(&Close));
}

std::string Boolean(bool value) { return value ? "true" : "false"; }

std::string ReceiptJson(const game::DeathSuccessionModalContinueReceiptV1 &receipt) {
  std::string output = "{\"status\":\"submitted\",\"snapshot_revision\":" +
      std::to_string(receipt.snapshot_revision) + ",\"date_raw\":" +
      std::to_string(receipt.date_raw) + ",\"played_character_id\":" +
      std::to_string(receipt.played_character_id);
  const auto field = [&output](std::string_view key, bool value) {
    output += ",\"";
    output += key;
    output += "\":" + Boolean(value);
  };
  field("identity_verified", receipt.identity_verified);
  field("can_continue_verified", receipt.can_continue_verified);
  field("paused_by_succession_verified", receipt.paused_by_succession_verified);
  field("has_open_succession_verified", receipt.has_open_succession_verified);
  field("controller_vtable_verified", receipt.controller_vtable_verified);
  field("controller_open_verified", receipt.controller_open_verified);
  output += ",\"close_invocations\":" + std::to_string(receipt.close_invocations) +
            ",\"material_result_verified\":false}";
  return output;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: native-fixture OUTPUT_JSON");
    Fixture fixture;
    ck3_11906::CurrentTimelineBlockerReadRequestV1 request{kRevision, kDate, kActor, true};
    const auto read = [&fixture, &request](game::CurrentTimelineBlockerContextV1 &output) {
      return ck3_12004::ReadCurrentTimelineBlockerContextNative12004V1(
          fixture.bindings, request, output);
    };
    game::CurrentTimelineBlockerContextV1 no_modal{};
    Require(read(no_modal) == game::ReadCurrentTimelineBlockerContextResultV1::available &&
        no_modal.identity == game::CurrentTimelineBlockerIdentityV1::none &&
        no_modal.blocks_simulation.available && !no_modal.blocks_simulation.value &&
        no_modal.has_open_succession.available && !no_modal.has_open_succession.value &&
        !no_modal.can_continue.available &&
        no_modal.can_continue.unavailable_reason == "no_supported_timeline_surface_visible",
        "living .4 frame lost its legal unavailable/null can_continue");

    fixture.modal_visible = true;
    game::CurrentTimelineBlockerContextV1 modal{};
    Require(read(modal) == game::ReadCurrentTimelineBlockerContextResultV1::available &&
        modal.identity == game::CurrentTimelineBlockerIdentityV1::death_succession_modal &&
        modal.can_continue.available && modal.can_continue.value,
        ".4 native reader failed the supported fixture modal");
    ck3_11906::DeathSuccessionModalContinueRequestV1 close{kRevision, kDate, kActor};
    game::DeathSuccessionModalContinueReceiptV1 receipt{};
    Require(ck3_12004::ExecuteDeathSuccessionModalContinueNative12004V1(
        fixture.bindings, close, modal, receipt) ==
        game::DeathSuccessionModalContinueStatusV1::submitted &&
        receipt.close_invocations == 1 && fixture.close_invocations == 1 &&
        fixture.controller_resolutions == 1 && fixture.controller_open_reads == 1,
        ".4 controller acquisition/Open/Close pipeline failed");
    game::CurrentTimelineBlockerContextV1 after_ack{};
    Require(read(after_ack) == game::ReadCurrentTimelineBlockerContextResultV1::available &&
        after_ack.has_open_succession.value,
        "method ACK was mistaken for a cleared succession row");
    fixture.modal_visible = false;
    game::CurrentTimelineBlockerContextV1 cleared{};
    Require(read(cleared) == game::ReadCurrentTimelineBlockerContextResultV1::available &&
        cleared == no_modal && fixture.close_invocations == 1,
        "independent later .4 read failed to observe clearance");
    Require(fixture.widget_reads == 4 * ck3_11906::kCurrentTimelineFixedWidgetCountV1 &&
        fixture.predicate_reads == 8, "native query skipped a fixed widget or predicate");

    const std::filesystem::path output(argv[1]);
    if (!output.parent_path().empty()) std::filesystem::create_directories(output.parent_path());
    std::ofstream stream(output, std::ios::binary);
    stream << "{\"schema\":\"xar.death-succession-12004.whole-fixture.v1\","
              "\"status\":\"GREEN\",\"synthetic\":true,\"live_queries\":0,"
              "\"game_actions\":0,\"build\":{\"version\":\""
           << ck3_12004::kGameVersion << "\",\"exe_sha256\":\""
           << ck3_12004::kExecutableSha256 << "\",\"adapter_id\":\""
           << ck3_12004::kAdapterId << "\"},\"played_character_id\":" << kActor
           << ",\"snapshot_revision\":" << kRevision << ",\"date_raw\":" << kDate
           << ",\"no_modal\":" << ck3_11906::SerializeCurrentTimelineBlockerContextV1(no_modal)
           << ",\"modal\":" << ck3_11906::SerializeCurrentTimelineBlockerContextV1(modal)
           << ",\"close_receipt\":" << ReceiptJson(receipt)
           << ",\"after_ack\":" << ck3_11906::SerializeCurrentTimelineBlockerContextV1(after_ack)
           << ",\"cleared\":" << ck3_11906::SerializeCurrentTimelineBlockerContextV1(cleared)
           << "}\n";
    Require(stream.good(), "whole native fixture output could not be written");
    std::cout << "GREEN: synthetic actual-.4 binder/query/controller/serializer fixture\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
