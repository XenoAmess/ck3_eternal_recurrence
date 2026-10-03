#include "xar_bridge/ck3_12003_succession_modal.hpp"

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
#include <utility>
#include <vector>

#if defined(XAR_CK3_SUCCESSION_FIXTURE_BRIDGE_WIRE)
std::string CurrentTimelineBlockerContextResultFrame(
    std::string_view, std::uint64_t, std::uint64_t,
    const xar::game::CurrentTimelineBlockerContextV1 &);
std::string DeathSuccessionModalContinueResultFrame(
    std::string_view, std::uint64_t,
    const xar::game::DeathSuccessionModalContinueReceiptV1 &);
#endif

namespace {
using namespace xar;
constexpr std::int32_t kActor = 38822;
constexpr std::int32_t kDate = 53239392;
constexpr std::uint64_t kRevision = 901;

void Require(bool condition, std::string_view message) {
  if (!condition) throw std::runtime_error(std::string(message));
}

template <typename T>
void Put(void *object, std::size_t offset, const T &value) {
  std::memcpy(static_cast<std::byte *>(object) + offset, &value, sizeof(value));
}

struct Widget {
  std::array<std::byte, 0x200> bytes{};
  std::string name;
  explicit Widget(std::string value) : name(std::move(value)) {
    const std::uintptr_t vtable = 0x777000;
    Put(bytes.data(), 0, vtable);
    Put(bytes.data(), ck3_11906::kZhongguoWidgetNameOffset, name);
  }
  void Flags(std::uint8_t flags) {
    Put(bytes.data(), ck3_11906::kZhongguoWidgetHiddenFlagsOffset, flags);
  }
};

struct Fixture;
Fixture *active = nullptr;

struct Fixture {
  std::byte *image = nullptr;
  ck3_12003::SuccessionModalBindings12003 bindings{};
  std::array<std::byte, 0x200> character{};
  std::array<std::byte, 0x40> storage{};
  std::vector<std::byte> slots = std::vector<std::byte>((kActor + 1ULL) * 0x10);
  std::array<std::byte, 0x30> idler_root{};
  std::array<std::byte, 0x10> idler{};
  std::array<std::byte, 0x100> ingame{};
  std::array<std::byte, 0x300> handler{};
  std::array<std::byte, 0x100> controller{};
  std::array<std::byte, 0x200> gui_first{};
  std::array<std::byte, 0x80> gui_second{};
  std::array<std::byte, 0x400> gui_third{};
  std::array<std::byte, 0x20> gui_host{};
  std::array<std::byte, 0xE0> gui_owner{};
  Widget root{"succession_event_window"};
  Widget bottom{"bottom"};
  Widget close{"close_button"};
  Widget menu{"menu_button"};
  std::array<void *, 3> children{};
  bool closed = false;
  std::uint32_t pause_reads = 0;
  std::uint32_t open_succession_reads = 0;
  std::uint32_t controller_resolutions = 0;
  std::uint32_t controller_open_reads = 0;
  std::uint32_t close_invocations = 0;
  std::uint32_t gui_lookups = 0;

  Fixture();
  ~Fixture() {
    if (image != nullptr) VirtualFree(image, 0, MEM_RELEASE);
    active = nullptr;
  }
  Fixture(const Fixture &) = delete;
  Fixture &operator=(const Fixture &) = delete;
};

bool __fastcall PausedBySuccession() {
  ++active->pause_reads;
  return !active->closed;
}

bool __fastcall HasOpenSuccession(void *character) {
  ++active->open_succession_reads;
  return character == active->character.data() && !active->closed;
}

void *__cdecl DynamicCast(void *source, long offset, void *source_type,
                         void *destination_type, int reference) {
  auto &fixture = *active;
  ++fixture.controller_resolutions;
  const auto base = reinterpret_cast<std::uintptr_t>(fixture.image);
  if (source != fixture.idler.data() || offset != 0 || reference != 0 ||
      reinterpret_cast<std::uintptr_t>(source_type) !=
          base + ck3_12003::kSuccessionIdlerBaseTypeDescriptorRva12003 ||
      reinterpret_cast<std::uintptr_t>(destination_type) !=
          base + ck3_12003::kSuccessionIngameIdlerTypeDescriptorRva12003) return nullptr;
  return fixture.ingame.data();
}

bool __fastcall ControllerOpen(void *controller) {
  ++active->controller_open_reads;
  return controller == active->controller.data() && !active->closed;
}

void __fastcall ControllerClose(void *controller) {
  if (controller != active->controller.data()) return;
  ++active->close_invocations;
  active->closed = true;
  active->root.Flags(ck3_11906::kZhongguoWidgetEffectiveHiddenMask);
}

void *__fastcall FindTopLevel(void *owner, const std::string *name) {
  ++active->gui_lookups;
  if (owner == active->gui_owner.data() && name != nullptr &&
      *name == "succession_event_window") return active->root.bytes.data();
  return nullptr;
}

bool ReadMemory(void *, const void *address, void *output,
                std::size_t size) noexcept {
  SIZE_T count = 0;
  return address != nullptr && output != nullptr && size != 0 &&
      ReadProcessMemory(GetCurrentProcess(), address, output, size, &count) != FALSE &&
      count == size;
}

void Jump(std::byte *destination, std::uintptr_t target) {
  std::array<std::byte, 12> machine{
      std::byte{0x48}, std::byte{0xB8}, std::byte{}, std::byte{},
      std::byte{}, std::byte{}, std::byte{}, std::byte{}, std::byte{},
      std::byte{}, std::byte{0xFF}, std::byte{0xE0}};
  std::memcpy(machine.data() + 2, &target, sizeof(target));
  std::memcpy(destination, machine.data(), machine.size());
  Require(FlushInstructionCache(GetCurrentProcess(), destination, machine.size()) != FALSE,
          "fixture local GUI callback trampoline unavailable");
}

Fixture::Fixture() {
  image = static_cast<std::byte *>(VirtualAlloc(nullptr, 0x5D00000,
      MEM_RESERVE | MEM_COMMIT, PAGE_EXECUTE_READWRITE));
  Require(image != nullptr, "fixture-owned image allocation failed");
  active = this;
  const auto base = reinterpret_cast<std::uintptr_t>(image);
  bindings = ck3_12003::BindSuccessionModalImage12003(base, ck3_12003::kExecutableSha256);
  Require(bindings.enabled && bindings.image_base == base, "actual .3 binder rejected exact image");
  Require(ck3_12003::kSuccessionHandlerPrimaryVtableRva12003 == 0x44BA890 &&
          bindings.handler_primary_vtable == base + 0x44BA890 &&
          bindings.controller_primary_vtable == base + 0x4522D90,
          "actual .3 binder did not use researched handler/controller vtables");
  Require(reinterpret_cast<std::uintptr_t>(bindings.controller_close) == base + 0x10D8900 &&
          reinterpret_cast<std::uintptr_t>(bindings.controller_open) == base + 0x10D8BC0 &&
          reinterpret_cast<std::uintptr_t>(bindings.is_paused_by_succession) == base + 0xA7C440 &&
          reinterpret_cast<std::uintptr_t>(bindings.has_open_succession) == base + 0xA7C4D0 &&
          reinterpret_cast<std::uintptr_t>(bindings.dynamic_cast_function) == base + 0x4260E94,
          "actual .3 binder did not map researched executable addresses");
  Require(bindings.gui.gui_abi_revision == ck3_11906::GuiAbiRevisionV1::crozier12003 &&
          reinterpret_cast<std::uintptr_t>(bindings.gui.gui_global_slot) == base + 0x5CB87F8 &&
          reinterpret_cast<std::uintptr_t>(bindings.gui.find_top_level_widget) == base + 0x3AAB100,
          "actual .3 binder did not select existing Crozier GUI ABI");
  Require(!ck3_12003::BindSuccessionModalImage12003(base,
              ck3_11906::kCurrentTimelineBlockerContextV1ExecutableSha256).enabled,
          "new adapter accepted old11906 executable identity");

  Put(character.data(), 0x18, kActor);
  Put(storage.data(), 0x20, slots.data());
  const std::int32_t capacity = kActor + 1;
  Put(storage.data(), 0x2C, capacity);
  Put(slots.data(), kActor * 0x10ULL + 8, character.data());
  Put(image, ck3_12003::kCharacterStorageSlotRva, storage.data());
  Put(image, ck3_12003::kSuccessionIdlerRootSlotRva12003, idler_root.data());
  Put(idler_root.data(), 0x10, idler.data());
  Put(ingame.data(), 0x88, handler.data());
  Put(handler.data(), 0, bindings.handler_primary_vtable);
  Put(handler.data(), 0x260, controller.data());
  Put(controller.data(), 0, bindings.controller_primary_vtable);
  bindings.dynamic_cast_function = &DynamicCast;
  bindings.is_paused_by_succession = &PausedBySuccession;
  bindings.has_open_succession = &HasOpenSuccession;
  bindings.controller_open = &ControllerOpen;
  bindings.controller_close = &ControllerClose;
  Put(image, ck3_12003::kSuccessionControllerPrimaryVtableRva12003 + 0x38,
      reinterpret_cast<std::uintptr_t>(&ControllerOpen));
  Put(image, ck3_12003::kSuccessionControllerPrimaryVtableRva12003 + 0x88,
      reinterpret_cast<std::uintptr_t>(&ControllerClose));

  Put(image, ck3_11906::kCrozierGuiGlobalSlotRva, gui_first.data());
  Put(gui_first.data(), ck3_11906::kZhongguoGuiChainFirstOffset, gui_second.data());
  Put(gui_second.data(), ck3_11906::kZhongguoGuiChainSecondOffset, gui_third.data());
  Put(gui_third.data(), ck3_11906::kZhongguoGuiContextOffset, gui_host.data());
  Put(gui_host.data(), ck3_11906::kZhongguoGuiOwnerOffset, gui_owner.data());
  Put(gui_owner.data(), ck3_11906::kZhongguoGuiOwnerRootWidgetOffset, root.bytes.data());
  children = {bottom.bytes.data(), close.bytes.data(), menu.bytes.data()};
  Put(root.bytes.data(), ck3_11906::kZhongguoWidgetChildrenOffset, children.data());
  const std::int32_t count = 3;
  Put(root.bytes.data(), ck3_11906::kZhongguoWidgetChildCountOffset, count);
  menu.Flags(ck3_11906::kZhongguoWidgetEffectiveHiddenMask);
  bindings.gui_access.read_memory = &ReadMemory;
  Jump(image + ck3_11906::kCrozierGuiFindTopLevelWidgetRva,
       reinterpret_cast<std::uintptr_t>(&FindTopLevel));
}

void Write(const std::filesystem::path &folder, const char *name,
           const std::string &value) {
  Require(!value.empty(), "actual production serializer returned empty packet");
  std::ofstream stream(folder / name, std::ios::binary);
  stream << value << '\n';
  Require(stream.good(), "native fixture packet could not be written");
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "usage: native-fixture PACKET_FOLDER");
    std::filesystem::create_directories(argv[1]);
    Fixture fixture;
    ck3_11906::CurrentTimelineBlockerReadRequestV1 read_request{kRevision, kDate, kActor, true};
    game::CurrentTimelineBlockerContextV1 modal{};
    Require(ck3_12003::ReadCurrentTimelineBlockerContextNative12003V1(
                fixture.bindings, read_request, modal) ==
                game::ReadCurrentTimelineBlockerContextResultV1::available,
            "new production .3 reader did not observe fixture-owned native GUI");
    Require(modal.identity == game::CurrentTimelineBlockerIdentityV1::death_succession_modal &&
            modal.blocks_simulation.available && modal.blocks_simulation.value &&
            modal.has_open_succession.available && modal.has_open_succession.value &&
            modal.can_continue.available && modal.can_continue.value,
            "new production reader lost actual GUI/predicate semantics");
    Require(fixture.pause_reads == 1 && fixture.open_succession_reads == 1 &&
            fixture.gui_lookups == 8, "reader did not invoke native predicate and eight GUI routes");
#if defined(XAR_CK3_SUCCESSION_FIXTURE_BRIDGE_WIRE)
    Write(argv[1], "modal-native-command-result.json",
          CurrentTimelineBlockerContextResultFrame("native-modal", 1, 100, modal));
#else
    Write(argv[1], "modal-native-context.json",
          ck3_11906::SerializeCurrentTimelineBlockerContextV1(modal));
#endif

    game::DeathSuccessionModalContinueReceiptV1 receipt{};
    ck3_11906::DeathSuccessionModalContinueRequestV1 close_request{kRevision, kDate, kActor};
    Require(ck3_12003::ExecuteDeathSuccessionModalContinueNative12003V1(
                fixture.bindings, close_request, modal, receipt) ==
                game::DeathSuccessionModalContinueStatusV1::submitted,
            "new production .3 executor did not invoke actual controller path");
    Require(fixture.controller_resolutions == 1 && fixture.controller_open_reads == 1 &&
            fixture.close_invocations == 1 && receipt.close_invocations == 1,
            "actual production controller resolution/Open/Close count changed");
#if defined(XAR_CK3_SUCCESSION_FIXTURE_BRIDGE_WIRE)
    Write(argv[1], "close-native-command-result.json",
          DeathSuccessionModalContinueResultFrame("native-close", 101, receipt));
#endif

    game::CurrentTimelineBlockerContextV1 cleared{};
    Require(ck3_12003::ReadCurrentTimelineBlockerContextNative12003V1(
                fixture.bindings, read_request, cleared) ==
                game::ReadCurrentTimelineBlockerContextResultV1::available &&
            cleared.identity == game::CurrentTimelineBlockerIdentityV1::none &&
            cleared.blocks_simulation.available && !cleared.blocks_simulation.value &&
            cleared.has_open_succession.available && !cleared.has_open_succession.value,
            "new production reader did not independently observe cleared GUI/predicates");
    Require(fixture.pause_reads == 2 && fixture.open_succession_reads == 2 &&
            fixture.gui_lookups == 16 && fixture.close_invocations == 1,
            "independent clear read did not retain a single Close");
#if defined(XAR_CK3_SUCCESSION_FIXTURE_BRIDGE_WIRE)
    Write(argv[1], "clear-native-command-result.json",
          CurrentTimelineBlockerContextResultFrame("native-clear", 2, 102, cleared));
#else
    Write(argv[1], "clear-native-context.json",
          ck3_11906::SerializeCurrentTimelineBlockerContextV1(cleared));
#endif
    std::cout << "GREEN: exact .3 binder and production native reader/controller/serializer pipeline\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
