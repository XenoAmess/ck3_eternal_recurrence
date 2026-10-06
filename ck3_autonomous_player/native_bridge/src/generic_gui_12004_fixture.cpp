#include "xar_bridge/ck3_12004_adapter.hpp"
#include "xar_bridge/ck3_12004_family_relationships.hpp"
#include "xar_bridge/ck3_12004_ingame_ui.hpp"
#include "xar_bridge/ck3_12004_snapshot_foundation.hpp"
#include "xar_bridge/ck3_12004_thread_runtime.hpp"
#include "xar_bridge/frontend_gui_result_v1.hpp"
#include "xar_bridge/ingame_ui_mailbox_v1.hpp"
#include "xar_bridge/protocol.hpp"
#include "xar_bridge/state_snapshot_frame_v1.hpp"
#include "ck3_12004_foundation_fixture_support.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <initializer_list>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {
namespace current = xar::ck3_12004;
namespace ui = xar::ck3_11906;
namespace game = xar::game;
constexpr std::int32_t kRobert = 29829;
constexpr std::int32_t kDate = 45000000;
constexpr std::uint32_t kPublicUnit = 0x01000003;
constexpr std::uint32_t kNativeArmy = 0x02000004;
constexpr std::uint64_t kRevision = 1;
constexpr std::uintptr_t kImageSize = 0x61C5000;
constexpr std::uintptr_t kFixtureWidgetVtable = 0x10028;

void Check(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
template <class T> void Store(void *base, std::size_t offset, const T &value) noexcept {
  std::memcpy(static_cast<std::byte *>(base) + offset, &value, sizeof(value));
}
template <class T> T Load(const void *base, std::size_t offset) noexcept {
  T value{};
  std::memcpy(&value, static_cast<const std::byte *>(base) + offset, sizeof(value));
  return value;
}
void Write(const std::filesystem::path &path, std::string_view wire) {
  std::ofstream output(path, std::ios::binary);
  output << wire << '\n';
  Check(output.good(), "whole native frame output failed");
}

// Reserve an owned address space with the actual image's extent. Only pages
// reached by the fixed production GUI readers are committed; no EXE is loaded.
class SparseImage {
public:
  SparseImage() {
    memory_ = VirtualAlloc(nullptr, kImageSize, MEM_RESERVE, PAGE_NOACCESS);
    Check(memory_ != nullptr, "synthetic image reservation failed");
  }
  ~SparseImage() { if (memory_) VirtualFree(memory_, 0, MEM_RELEASE); }
  SparseImage(const SparseImage &) = delete;
  SparseImage &operator=(const SparseImage &) = delete;
  std::uintptr_t Base() const noexcept { return reinterpret_cast<std::uintptr_t>(memory_); }
  void *At(std::uintptr_t rva, std::size_t bytes = sizeof(void *)) {
    Check(rva < kImageSize && bytes <= kImageSize - rva, "synthetic image RVA exceeds extent");
    const auto first = rva & ~std::uintptr_t{4095};
    const auto last = (rva + bytes - 1) & ~std::uintptr_t{4095};
    for (auto page = first; page <= last; page += 4096) {
      bool committed = false;
      for (const auto existing : pages_) if (existing == page) committed = true;
      if (!committed) {
        Check(VirtualAlloc(reinterpret_cast<void *>(Base() + page), 4096,
            MEM_COMMIT, PAGE_READWRITE) != nullptr, "synthetic image page commit failed");
        pages_.push_back(page);
      }
    }
    return reinterpret_cast<void *>(Base() + rva);
  }
  template <class T> void Put(std::uintptr_t rva, const T &value) {
    Store(At(rva, sizeof(T)), 0, value);
  }
  template <class F> void Forward(std::uintptr_t rva, F callback) {
    // x64 mov rax,<owned callback>; jmp rax. The normal binder still supplies
    // base+RVA and normal production function-address admission still runs.
    std::array<std::uint8_t, 12> code{0x48, 0xB8, 0, 0, 0, 0, 0, 0, 0, 0, 0xFF, 0xE0};
    const auto target = reinterpret_cast<std::uintptr_t>(callback);
    std::memcpy(code.data() + 2, &target, sizeof(target));
    auto *entry = At(rva, code.size());
    std::memcpy(entry, code.data(), code.size());
    DWORD previous = 0;
    Check(VirtualProtect(entry, code.size(), PAGE_EXECUTE_READ, &previous) != FALSE,
        "synthetic native forward page was not executable");
    Check(FlushInstructionCache(GetCurrentProcess(), entry, code.size()) != FALSE,
        "synthetic native forward cache flush failed");
  }
private:
  void *memory_ = nullptr;
  std::vector<std::uintptr_t> pages_;
};

struct SnapshotMemory;
SnapshotMemory *g_snapshot = nullptr;
struct SnapshotMemory {
  current::fixture::CoreMemory original_core{kDate, 4, true};
  current::CoreBindings core = original_core.Bindings();
  std::vector<std::byte> data{current::kEventManagerOffset12004 + 16};
  std::array<std::byte, 0x400> actor{};
  std::array<std::byte, 0x30> characters{};
  std::vector<std::byte> character_rows{
      static_cast<std::size_t>(kRobert + 1) * current::kCharacterStorageSlotStride};
  std::array<std::byte, 0x30> family{};
  std::array<std::byte, 0x300> resources{};
  std::array<std::byte, 0x30> pending_storage{}, unit_storage{}, war_storage{};
  std::array<std::byte, 0x20> globals{}, ready_entry{};
  std::array<std::byte, 1> identifier_table{};
  std::array<std::uintptr_t, 1> reply_primary{}, reply_secondary{};
  void *character_slot = characters.data();
  void *pending_slot = pending_storage.data();
  void *unit_slot = unit_storage.data();
  xar::ck3_12002::SettlementGlobalAccessor global_accessor = &GetGlobals;
  std::size_t event_reads = 0, settlement_reads = 0, unexpected_reads = 0;

  SnapshotMemory() {
    g_snapshot = this;
    const auto old_data = Load<void *>(*core.game_state_slot, current::kGameStateDataOffset);
    std::memcpy(data.data(), old_data,
        current::kPlayerCharacterManagerOffset + current::kPlayerManagerCountOffset + 4);
    Store(*core.game_state_slot, current::kGameStateDataOffset, data.data());
    Store(characters.data(), current::kCharacterStorageSlotsOffset, character_rows.data());
    Store(characters.data(), current::kCharacterStorageCapacityOffset, kRobert + 1);
    Store(character_rows.data(), static_cast<std::size_t>(kRobert) *
        current::kCharacterStorageSlotStride + current::kCharacterStorageObjectOffset, actor.data());
    Store(actor.data(), current::kCharacterFullIdOffset, kRobert);
    core.character_storage_slot = &character_slot;
    using namespace current::family_relationships_abi;
    Store(actor.data(), kCharacterFamilyOffset, family.data());
    Store(family.data(), kBetrothedIdOffset, std::int32_t{-1});
    Store(family.data(), kPrimarySpouseIdOffset, std::int32_t{-1});
    Store(actor.data(), 0x1B0, resources.data());
    Store(resources.data(), 0x100, std::int64_t{1234567});
    Store(resources.data(), 0x130, std::int64_t{2345678});
    Store(resources.data(), 0x110, std::int64_t{3456789});
    // The actual .4 Snapshot reader follows actor + 0x1B0 before reading stress.
    Store(resources.data(), 0x2F8, std::int32_t{7});
    // Empty, enabled World registries are read by the full production reader.
    Store(data.data(), xar::ck3_12002::kWorldWarManagerOffset + 0x20, war_storage.data());
    Store(globals.data(), 0x10, ready_entry.data());
    Store(globals.data(), 0x1C, std::int32_t{1});
    Store(ready_entry.data(), 0x08, std::int32_t{17});
    Store(ready_entry.data(), 0x10, std::uint16_t{1});
  }
  ~SnapshotMemory() { g_snapshot = nullptr; }
  SnapshotMemory(const SnapshotMemory &) = delete;
  SnapshotMemory &operator=(const SnapshotMemory &) = delete;
  game::Ck3_12004AdapterBindings Bindings() {
    game::Ck3_12004AdapterBindings out{};
    out.core = core;
    out.read_core_snapshot = current::ReadCoreSnapshot;
    out.armies.enabled = true;
    out.armies.game_state_slot = core.game_state_slot;
    out.armies.unit_storage_slot = &unit_slot;
    out.armies.get_unit_state = &UnexpectedUnitState;
    out.world.enabled = true;
    out.world.game_state_slot = core.game_state_slot;
    out.world.character_storage_slot = core.character_storage_slot;
    out.world.contains_war_participant = &UnexpectedContainsParticipant;
    out.world.get_war_score = &UnexpectedWarScore;
    out.provinces.enabled = true;
    current::SnapshotFoundationBindings foundation{};
    foundation.core = core;
    foundation.events = {core, &GetEvent, &pending_slot, &UnexpectedPending,
        &UnexpectedReply, reinterpret_cast<std::uintptr_t>(reply_primary.data()),
        reinterpret_cast<std::uintptr_t>(reply_secondary.data())};
    foundation.settlement = {true, &global_accessor, &GetIdentifierTable, &LookupIdentifier};
    out.snapshot_foundation12004 =
        std::make_shared<const current::SnapshotFoundationBindings>(foundation);
    return out;
  }
  static void *GetEvent(void *manager) {
    ++g_snapshot->event_reads;
    if (manager != g_snapshot->data.data() + current::kEventManagerOffset12004)
      ++g_snapshot->unexpected_reads;
    return nullptr;
  }
  static bool UnexpectedPending(void *, void *) { ++g_snapshot->unexpected_reads; return false; }
  static bool UnexpectedReply(void *) { ++g_snapshot->unexpected_reads; return false; }
  static std::int32_t UnexpectedUnitState(void *) { ++g_snapshot->unexpected_reads; return 0; }
  static bool UnexpectedContainsParticipant(const void *, std::int32_t) {
    ++g_snapshot->unexpected_reads; return false;
  }
  static std::int32_t UnexpectedWarScore(const void *, void *) {
    ++g_snapshot->unexpected_reads; return 0;
  }
  static void *GetGlobals() { return g_snapshot->globals.data(); }
  static void *GetIdentifierTable() { return g_snapshot->identifier_table.data(); }
  static std::int32_t *LookupIdentifier(void *table, std::int32_t *output, const void *view) {
    auto &memory = *g_snapshot;
    ++memory.settlement_reads;
    const auto name = Load<const char *>(view, 0);
    const auto size = Load<std::int32_t>(view, sizeof(void *));
    if (table != memory.identifier_table.data() || !name || size < 0) return nullptr;
    *output = std::string_view(name, static_cast<std::size_t>(size)) == "xa_settlement_ready" ? 17 : -1;
    return output;
  }
};

struct Widget {
  std::array<std::byte, 0x200> object{};
  std::string name;
  std::vector<void *> children;
  Widget(std::uintptr_t vtable, const char *runtime_name) : name(runtime_name) {
    Store(object.data(), 0, vtable);
    // Exact MSVC small-string layout consumed by the normal GUI name reader.
    if (name.size() < 16) {
      std::memcpy(object.data() + ui::kZhongguoWidgetNameOffset, name.data(), name.size());
      Store(object.data(), ui::kZhongguoWidgetNameOffset + 0x18, std::uint64_t{15});
    } else {
      Store(object.data(), ui::kZhongguoWidgetNameOffset, name.data());
      Store(object.data(), ui::kZhongguoWidgetNameOffset + 0x18, std::uint64_t{name.size()});
    }
    Store(object.data(), ui::kZhongguoWidgetNameOffset + 0x10, std::uint64_t{name.size()});
  }
  void Children(std::initializer_list<Widget *> widgets) {
    for (auto *child : widgets) {
      children.push_back(child->object.data());
      Store(child->object.data(), ui::kZhongguoWidgetParentOffset, object.data());
    }
    Store(object.data(), ui::kZhongguoWidgetChildrenOffset, children.data());
    Store(object.data(), ui::kZhongguoWidgetChildCountOffset, static_cast<std::int32_t>(children.size()));
  }
  void Visible(bool visible) noexcept {
    Store(object.data(), ui::kZhongguoWidgetHiddenFlagsOffset,
        visible ? std::uint8_t{0} : ui::kZhongguoWidgetEffectiveHiddenMask);
  }
};

struct GuiMemory;
GuiMemory *g_gui = nullptr;
struct GuiMemory {
  SparseImage image;
  std::array<std::byte, 0x1C0> app{};
  std::array<std::byte, 0x60> host{};
  std::array<std::byte, 0x3D8> context{};
  std::array<std::byte, 0x10> lookup_host{};
  std::array<std::byte, 0xD8> owner{};
  std::array<std::byte, 0x18> idler_root{};
  std::array<std::byte, 0x90> idler{};
  std::array<std::byte, 0xD0> handler{};
  std::array<std::byte, 0xD0> window{};
  std::array<std::byte, 0x30> army_storage{}, unit_storage{};
  std::array<std::byte, 5 * 16> army_rows{};
  std::array<std::byte, 4 * 16> unit_rows{};
  std::array<std::byte, 0x128> army{};
  std::array<std::byte, 0x180> unit{};
  Widget root{image.Base() + kFixtureWidgetVtable, "_root_"};
  Widget army_root{image.Base() + kFixtureWidgetVtable, "army_window"};
  Widget army_child{image.Base() + kFixtureWidgetVtable, "army_details"};
  Widget main_menu{image.Base() + kFixtureWidgetVtable, "mainmenu_panel_bottom"};
  Widget new_game{image.Base() + kFixtureWidgetVtable, "new_game"};
  Widget ruler{image.Base() + kFixtureWidgetVtable, "ruler_designer"};
  Widget coa_page{image.Base() + kFixtureWidgetVtable, "coat_of_arms_page"};
  Widget coa_preview{image.Base() + kFixtureWidgetVtable, "coat_of_arms_preview"};
  std::size_t cast_calls = 0, find_calls = 0;

  GuiMemory() {
    g_gui = this;
    const auto revision = ui::GuiAbiRevisionV1::crozier12004;
    image.Put(ui::GuiGlobalSlotRvaV1(revision), app.data());
    Store(app.data(), ui::kZhongguoGuiChainFirstOffset, host.data());
    Store(host.data(), ui::kZhongguoGuiChainSecondOffset, context.data());
    Store(context.data(), ui::kZhongguoGuiContextOffset, lookup_host.data());
    Store(lookup_host.data(), ui::kZhongguoGuiOwnerOffset, owner.data());
    Store(owner.data(), ui::kZhongguoGuiOwnerRootWidgetOffset, root.object.data());
    root.Children({&army_root, &main_menu, &ruler});
    army_root.Children({&army_child});
    main_menu.Children({&new_game});
    ruler.Children({&coa_page});
    coa_page.Children({&coa_preview});
    MainMenuScene();
    image.Forward(ui::GuiFindTopLevelWidgetRvaV1(revision), &FindTopLevel);
    image.Put(current::kUiIdlerRootSlotRva12004V1, idler_root.data());
    Store(idler_root.data(), 0x10, idler.data());
    Store(idler.data(), 0x88, handler.data());
    Store(handler.data(), 0, image.Base() + current::kUiHandlerPrimaryVtable12004V1);
    Store(handler.data(), current::kUiArmyWindowHandlerSlot12004V1, window.data());
    image.Forward(current::kUiRuntimeDynamicCastRva12004V1, &DynamicCast);
    image.Put(current::kUiArmyWindowPrimaryVtable12004V1 - 8,
        image.Base() + current::kUiArmyWindowCol12004V1);
    auto *col = image.At(current::kUiArmyWindowCol12004V1, 24);
    Store(col, 0, std::uint32_t{1});
    Store(col, 12, static_cast<std::uint32_t>(current::kUiArmyWindowTypeDescriptor12004V1));
    Store(col, 20, static_cast<std::uint32_t>(current::kUiArmyWindowCol12004V1));
    Store(window.data(), 0, image.Base() + current::kUiArmyWindowPrimaryVtable12004V1);
    Store(window.data(), current::kUiArmyWindowGuiRootOffset12004V1, army_root.object.data());
    Store(window.data(), current::kUiArmyWindowHandlerOffset12004V1, handler.data());
    Store(window.data(), current::kUiArmyWindowSubjectOffset12004V1, kNativeArmy);
    Store(army_storage.data(), 0x20, army_rows.data());
    Store(army_storage.data(), 0x2C, std::uint32_t{5});
    Store(unit_storage.data(), 0x20, unit_rows.data());
    Store(unit_storage.data(), 0x2C, std::uint32_t{4});
    Store(army_rows.data(), 4 * 16 + 8, army.data());
    Store(unit_rows.data(), 3 * 16 + 8, unit.data());
    Store(army.data(), 0x10, kNativeArmy);
    Store(army.data(), 0x124, kPublicUnit);
    Store(unit.data(), 0x10, kPublicUnit);
    Store(unit.data(), 0x174, kRobert);
    Store(unit.data(), 0x178, kNativeArmy);
    image.Put(current::kUiArmyStorage12004V1, army_storage.data());
    image.Put(current::kUiUnitStorage12004V1, unit_storage.data());
  }
  ~GuiMemory() { g_gui = nullptr; }
  GuiMemory(const GuiMemory &) = delete;
  GuiMemory &operator=(const GuiMemory &) = delete;
  void MainMenuScene() noexcept {
    main_menu.Visible(true);
    new_game.Visible(true);
    ruler.Visible(false);
    coa_page.Visible(false);
    coa_preview.Visible(false);
  }
  void CoatOfArmsScene() noexcept {
    main_menu.Visible(false);
    new_game.Visible(false);
    ruler.Visible(true);
    coa_page.Visible(true);
    coa_preview.Visible(true);
  }
  static void *__fastcall FindTopLevel(void *native_owner, const std::string *) {
    ++g_gui->find_calls;
    // Force the existing normal registered-root fallback and descendant walk.
    if (native_owner != g_gui->owner.data()) return nullptr;
    return nullptr;
  }
  static void *__fastcall DynamicCast(void *object, long offset,
      const void *source, const void *target, int reference) {
    auto &memory = *g_gui;
    ++memory.cast_calls;
    return object == memory.idler.data() && offset == 0 && reference == 0 &&
        reinterpret_cast<std::uintptr_t>(source) == memory.image.Base() + current::kUiIdlerBaseTypeDescriptor12004V1 &&
        reinterpret_cast<std::uintptr_t>(target) == memory.image.Base() + current::kUiIngameIdlerTypeDescriptor12004V1
        ? memory.idler.data() : nullptr;
  }
};

void *g_tls_context = nullptr;
BOOL WINAPI FakePeek(LPMSG, HWND, UINT, UINT, UINT) { return FALSE; }
void *__fastcall FakeTls() noexcept { return g_tls_context; }
struct PumpFixture {
  std::array<std::byte, 0x18> rng{};
  std::uintptr_t rng_wrapper = 0, rng_slot = 0;
  std::uint8_t tls_initialized = 1;
  std::array<std::byte, 0x28> tls{};
  void *peek_slot = reinterpret_cast<void *>(&FakePeek);
  DWORD protection = PAGE_READONLY;
  ui::MainThreadQueryMailboxV1 mailbox{};
  bool installed = false;

  PumpFixture(std::uintptr_t base, const current::CoreBindings &core) {
    const auto thread = GetCurrentThreadId();
    Store(rng.data(), 0x10, thread);
    rng_wrapper = reinterpret_cast<std::uintptr_t>(rng.data());
    rng_slot = reinterpret_cast<std::uintptr_t>(&rng_wrapper);
    tls[0x20] = std::byte{1};
    g_tls_context = tls.data();
    const std::array<ui::MainThreadQueryExecutorV1, 1> executors{&ui::ExecuteFrontendGuiRouteMailboxV1};
    auto environment = current::BindThreadRuntimeImage(base, current::kExecutableSha256, executors);
    // This supported mailbox fixture API supplies owned IAT/TLS/clock storage.
    // The GUI query environment itself never enables function overrides.
    environment.offline_fixture = true;
    environment.peek_message_iat_slot_override = &peek_slot;
    environment.resolved_peek_message_override = &FakePeek;
    environment.global_rng_wrapper_slot_override = reinterpret_cast<std::uintptr_t>(&rng_slot);
    environment.jomini_state_slot_override = reinterpret_cast<std::uintptr_t>(core.jomini_state_slot);
    environment.game_state_slot_override = reinterpret_cast<std::uintptr_t>(core.game_state_slot);
    environment.tls_initialized_flag_override = reinterpret_cast<std::uintptr_t>(&tls_initialized);
    environment.tls_context_getter_override = &FakeTls;
    environment.memory_protection_context = this;
    environment.memory_query_override = &Query;
    environment.memory_protect_override = &Protect;
    environment.system_page_size_override = 4096;
    Check(ui::InstallMainThreadQueryMailboxV1(mailbox, environment), "actual .4 frontend mailbox install failed");
    installed = true;
    const auto boundary = current::ThreadRuntimeBuildProfile().pump_exact_return_rva;
    ui::ObserveMainThreadPumpAndDrainV1(mailbox, boundary, thread);
    ui::ObserveMainThreadPumpAndDrainV1(mailbox, boundary, thread);
  }
  ~PumpFixture() {
    if (installed) ui::UninstallMainThreadQueryMailboxV1(mailbox, 1000);
    g_tls_context = nullptr;
  }
  static bool Query(void *opaque, const void *address, MEMORY_BASIC_INFORMATION &information) noexcept {
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
  static bool Protect(void *opaque, void *, std::size_t bytes, DWORD requested, DWORD &previous) noexcept {
    auto &runtime = *static_cast<PumpFixture *>(opaque);
    if (bytes != 4096) return false;
    previous = runtime.protection;
    runtime.protection = requested;
    return true;
  }
  void Run(ui::FrontendGuiRouteMailboxContextV1 &query) {
    Check(query.mailbox == &mailbox, "production query constructor lost mailbox");
    Check(ui::TrySubmitMainThreadQueryV1(mailbox, &ui::ExecuteFrontendGuiRouteMailboxV1,
        &query, query.ticket) == ui::MainThreadQuerySubmitResultV1::submitted,
        "normal frontend executor registration rejected query");
    Check(ui::ObserveMainThreadPumpAndDrainV1(mailbox,
        current::ThreadRuntimeBuildProfile().pump_exact_return_rva, GetCurrentThreadId()),
        "registered query did not run on owned paused application pump");
    Check(ui::WaitForMainThreadQueryV1(mailbox, query.ticket, 1000) ==
        ui::MainThreadQueryWaitResultV1::completed, "normal frontend query did not complete");
    Check(ui::ReclaimMainThreadQueryV1(mailbox, query.ticket) ==
        ui::MainThreadQueryReclaimResultV1::reclaimed, "normal frontend query was not reclaimed");
  }
  void Close() {
    Check(ui::UninstallMainThreadQueryMailboxV1(mailbox, 1000) ==
        ui::MainThreadQueryUninstallResultV1::uninstalled, "owned mailbox uninstall failed");
    installed = false;
  }
};

void CheckSnapshot(const game::Snapshot &snapshot) {
  Check(snapshot.paused && snapshot.map_ready && snapshot.date_raw == kDate &&
      snapshot.player_id == 0 && snapshot.has_played_character &&
      snapshot.played_character_id == kRobert && snapshot.played_character_alive,
      "actual .4 full Snapshot does not contain paused Robert");
  Check(snapshot.played_character_gold == game::FixedPointValue{1234567, 100000} &&
      snapshot.played_character_stress_points == 7, "actual .4 Snapshot resource reader was not reached");
}

ui::FrontendGuiRouteMailboxContextV1 FrontendQuery(
    PumpFixture &pump, const GuiMemory &gui, ui::FrontendGuiRouteOperationV1 operation) {
  // These readonly frontend requests carry the same expected_revision=0
  // admission and normal context construction as the production worker.
  std::uint64_t revision = 1;
  Check(xar::bridge::JsonUnsignedField("{\"expected_revision\":0}",
      "expected_revision", revision) && revision == 0,
      "normal frontend revision qualification failed");
  ui::FrontendGuiRouteMailboxContextV1 query{};
  query.mailbox = &pump.mailbox;
  query.operation = operation;
  query.environment = ui::BindZhongguoScoreboardNativeEnvironmentV1(
      gui.image.Base(), true, ui::GuiAbiRevisionV1::crozier12004,
      current::kExecutableSha256);
  Check(query.environment.exact_build_admitted && !query.environment.offline_fixture_function_overrides &&
      reinterpret_cast<std::uintptr_t>(query.environment.gui_global_slot) ==
          gui.image.Base() + current::kGuiGlobalSlotRva12004V1 &&
      reinterpret_cast<std::uintptr_t>(query.environment.find_top_level_widget) ==
          gui.image.Base() + current::kGuiFindTopLevelWidgetRva12004V1,
      "normal actual .4 frontend environment did not use the source-bound image profile");
  return query;
}

void FrontendFrames(const std::filesystem::path &output, GuiMemory &gui, PumpFixture &pump) {
  gui.MainMenuScene();
  auto main_route = FrontendQuery(pump, gui, ui::FrontendGuiRouteOperationV1::query);
  pump.Run(main_route);
  Check(main_route.result.route == ui::FrontendGuiRouteV1::main_menu &&
      !main_route.result.dispatch_invoked, "normal actual .4 main-menu route differs");
  Write(output / "mainmenu-route.json", ui::GenericGuiCommandResultFrameV1(
      "mainmenu-route", ui::kFrontendGuiRouteV1Step, true,
      ui::FrontendGuiRouteNameV1(main_route.result.route)));
  auto main_tree = FrontendQuery(pump, gui, ui::FrontendGuiRouteOperationV1::inspect_tree);
  pump.Run(main_tree);
  const auto &main = main_tree.result.tree_inspection;
  Check(main_tree.result.route == ui::FrontendGuiRouteV1::main_menu && main.root_available &&
      !main.truncated && main.scope_root_name == "mainmenu_panel_bottom" && main.widget_count == 2 &&
      main.widgets[0].runtime_name == "mainmenu_panel_bottom" &&
      main.widgets[1].runtime_name == "new_game" && !main_tree.result.dispatch_invoked,
      "normal actual .4 active main-menu subtree differs");
  Write(output / "mainmenu-tree.json", ui::FrontendGuiTreeInspectionResultFrameV1(
      "mainmenu-tree", ui::kFrontendGuiTreeInspectionV1Step, main));

  // Independent owned-memory scene, not a dispatch or transition assertion.
  gui.CoatOfArmsScene();
  auto coa_route = FrontendQuery(pump, gui, ui::FrontendGuiRouteOperationV1::query);
  pump.Run(coa_route);
  Check(coa_route.result.route == ui::FrontendGuiRouteV1::coat_of_arms_designer &&
      !coa_route.result.dispatch_invoked, "normal actual .4 coat-of-arms route differs");
  Write(output / "coa-route.json", ui::GenericGuiCommandResultFrameV1(
      "coa-route", ui::kFrontendGuiRouteV1Step, true,
      ui::FrontendGuiRouteNameV1(coa_route.result.route)));
  auto coa_tree = FrontendQuery(pump, gui, ui::FrontendGuiRouteOperationV1::inspect_coat_of_arms_tree);
  pump.Run(coa_tree);
  const auto &coa = coa_tree.result.tree_inspection;
  Check(coa_tree.result.route == ui::FrontendGuiRouteV1::coat_of_arms_designer && coa.root_available &&
      !coa.truncated && coa.scope_root_name == "coat_of_arms_page" && coa.widget_count == 2 &&
      coa.widgets[0].runtime_name == "coat_of_arms_page" &&
      coa.widgets[1].runtime_name == "coat_of_arms_preview" && !coa_tree.result.dispatch_invoked,
      "normal actual .4 coat-of-arms subtree differs");
  Write(output / "coa-tree.json", ui::FrontendGuiTreeInspectionResultFrameV1(
      "coa-tree", ui::kFrontendCoatOfArmsTreeInspectionV1Step, coa));
}
} // namespace

int main(int argc, char **argv) {
  try {
    Check(argc == 2, "usage: xar_generic_gui_12004_fixture <wire-output-dir>");
    const std::filesystem::path output(argv[1]);
    std::filesystem::create_directories(output);
    SnapshotMemory snapshot_memory;
    auto adapter = game::CreateCk3_12004AdapterFromBindings(snapshot_memory.Bindings());
    Check(adapter && adapter->enabled() && adapter->supports_snapshot() &&
        game::IsCk3_12004Descriptor(adapter->descriptor()), "actual .4 full Snapshot adapter unavailable");
    game::Snapshot before{};
    Check(game::ReadSnapshot(*adapter, before), "production full Snapshot before query failed");
    CheckSnapshot(before);
    Write(output / "state-snapshot-before.json", xar::bridge::SerializeStateSnapshotFrameV1(before, kRevision));

    GuiMemory gui;
    PumpFixture pump(gui.image.Base(), snapshot_memory.core);
    ui::FrontendGuiRouteMailboxContextV1 query{};
    const auto failure = ui::PrepareIngameUiMailboxV1(*adapter, &before,
        "{\"expected_revision\":1,\"window_kind\":\"army\",\"subject_id\":0}",
        ui::kIngameUiWindowQueryV1Step, kRevision, 1, gui.image.Base(), pump.mailbox, query);
    Check(failure.empty(), "normal typed army request qualification failed");
    Check(query.environment.gui_abi_revision == ui::GuiAbiRevisionV1::crozier12004 &&
        query.environment.exact_build_admitted && !query.environment.offline_fixture_function_overrides &&
        query.environment.executable_sha256 == current::kExecutableSha256,
        "normal exact .4 GUI environment was changed to fixture overrides");
    pump.Run(query);
    const auto &result = query.ingame_result;
    Check(result.available && result.status == "observed" && result.unavailable_reason.empty() &&
        result.window_exists && result.effective_visible && result.enabled &&
        result.subject_id_available && result.current_subject_id == kPublicUnit &&
        result.native_army_id == kNativeArmy && result.owner_character_id_available &&
        result.owner_character_id == static_cast<std::uint32_t>(kRobert),
        "normal production Army query did not observe the complete native/public Unit chain");
    Check(result.application_owner_thread_verified && result.gui_owner_binding_verified &&
        result.paused && result.date_raw == kDate && result.played_character_id == kRobert &&
        result.pump_epoch >= 3 && result.thread_id == GetCurrentThreadId() &&
        !result.dispatch_invoked && !result.verification_pending,
        "normal paused application-owner query admission differs");
    Check(result.tree.root_available && result.tree.widget_count == 2 &&
        result.tree.widgets[0].runtime_name == "army_window" &&
        result.tree.widgets[1].runtime_name == "army_details" &&
        gui.cast_calls != 0 && gui.find_calls != 0,
        "normal native RTTI handler and registered GUI traversal were not reached");
    Write(output / "army-query.json", ui::IngameUiCommandResultFrameV1(
        "army-query", query.ingame_request, result, kRevision));
    game::Snapshot after{};
    Check(game::ReadSnapshot(*adapter, after) && after == before,
        "read-only query changed the following production Snapshot");
    CheckSnapshot(after);
    Check(snapshot_memory.event_reads >= 5 && snapshot_memory.settlement_reads >= 5 &&
        snapshot_memory.unexpected_reads == 0, "normal complete Snapshot admission readers were not exercised");
    Write(output / "state-snapshot-after.json", xar::bridge::SerializeStateSnapshotFrameV1(after, kRevision));
    FrontendFrames(output, gui, pump);
    pump.Close();
    std::cout << "actual .4 whole native Army/frontend/CoA and full Snapshot fixture passed; offline owned memory only\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
