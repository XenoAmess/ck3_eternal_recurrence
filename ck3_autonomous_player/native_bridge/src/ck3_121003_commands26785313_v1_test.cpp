#include "xar_bridge/ck3_121003_commands26785313_v1.hpp"
#include "xar_bridge/ck3_1210_hotfix26757580_v1.hpp"
#include <array>
#include <cstddef>
#include <cstring>
#include <exception>
#include <iostream>
#include <limits>
#include <string>
#include <vector>

namespace {
namespace cur = xar::ck3_121003::build26785313;
namespace old = xar::ck3_1210;
#define REQUIRE(value) do { if (!(value)) { std::cerr << "failed line " << __LINE__ << ": " #value "\n"; return false; } } while (false)
constexpr std::uintptr_t kSyntheticBase = 0x180000000ULL;
const cur::CommandIdentityV1 identity{cur::kGameVersion, cur::kSteamBuildId, cur::kExecutableSha256};
struct Segment { std::uintptr_t address = 0; std::vector<unsigned char> bytes; };
struct Image {
  std::vector<Segment> segments;
  std::uintptr_t unreadable = 0;
  std::size_t reads = 0;
  template <class T> void Put(std::uintptr_t rva, T value) {
    PutBytes(rva, reinterpret_cast<const unsigned char *>(&value), sizeof(value));
  }
  void PutBytes(std::uintptr_t rva, const unsigned char *value, std::size_t size) {
    const auto address = kSyntheticBase + rva;
    for (auto &s : segments) {
      if (address >= s.address && address - s.address <= s.bytes.size() &&
          size <= s.bytes.size() - (address - s.address)) {
        std::memcpy(s.bytes.data() + (address - s.address), value, size); return;
      }
    }
    segments.push_back({address, std::vector<unsigned char>(value, value + size)});
  }
  static bool Read(void *opaque, std::uintptr_t from, void *to, std::size_t size) noexcept {
    auto &image = *static_cast<Image *>(opaque); ++image.reads;
    if (!to || !size || (image.unreadable && from <= image.unreadable &&
        image.unreadable - from < size)) return false;
    for (const auto &s : image.segments) {
      if (from >= s.address && from - s.address <= s.bytes.size() &&
          size <= s.bytes.size() - (from - s.address)) {
        std::memcpy(to, s.bytes.data() + (from - s.address), size); return true;
      }
    }
    return false;
  }
  cur::CommandImageReadV1 Access() { return {this, &Read}; }
};
Image CompleteImage() {
  Image result{};
  const std::array<unsigned char, 0x900> header{};
  result.PutBytes(0, header.data(), header.size());
  constexpr std::uint32_t pe = 0x100;
  result.Put(0, std::uint16_t{0x5A4D}); result.Put(0x3C, pe);
  result.Put(pe, std::uint32_t{0x4550}); result.Put(pe + 4, std::uint16_t{0x8664});
  result.Put(pe + 8, cur::kPeTimestamp); result.Put(pe + 24, std::uint16_t{0x20B});
  result.Put(pe + 48, std::uint64_t{kSyntheticBase});
  result.Put(pe + 80, static_cast<std::uint32_t>(cur::kImageSize));
  for (const auto &p : cur::CommandCodePinsV1()) result.PutBytes(p.rva, p.bytes.data(), p.bytes.size());
  for (const auto &p : cur::CommandMetadataPinsV1()) result.PutBytes(p.rva, p.bytes.data(), p.bytes.size());
  for (const auto &p : cur::CommandPointerPinsV1()) result.Put(p.rva, kSyntheticBase + p.target_rva);
  return result;
}
bool Verify(Image &image, const cur::CommandIdentityV1 &id = identity) {
  return cur::VerifyCurrentCommandImageV1(kSyntheticBase, id, image.Access());
}
bool CheckExactImage() {
  static_assert(sizeof(std::uintptr_t) == 8);
  auto image = CompleteImage();
  REQUIRE(cur::CommandCodePinsV1().size() == 17);
  REQUIRE(cur::CommandMetadataPinsV1().size() == 9);
  REQUIRE(cur::CommandPointerPinsV1().size() == 54);
  REQUIRE(Verify(image));
  std::string lower = cur::kExecutableSha256;
  for (auto &c : lower) if (c >= 'A' && c <= 'F') c = static_cast<char>(c - 'A' + 'a');
  REQUIRE(Verify(image, {cur::kGameVersion, cur::kSteamBuildId, lower}));
  const auto original_reads = image.reads;
  REQUIRE(!Verify(image, {"1.21.0", cur::kSteamBuildId, cur::kExecutableSha256}));
  REQUIRE(!Verify(image, {cur::kGameVersion, "26757580", cur::kExecutableSha256}));
  REQUIRE(!Verify(image, {cur::kGameVersion, cur::kSteamBuildId, old::kExecutableSha256}));
  REQUIRE(!Verify(image, {}));
  REQUIRE(image.reads == original_reads);
  REQUIRE(!cur::VerifyCurrentCommandImageV1(0, identity, image.Access()));
  REQUIRE(!cur::VerifyCurrentCommandImageV1((std::numeric_limits<std::uintptr_t>::max)(), identity, image.Access()));
  REQUIRE(!cur::VerifyCurrentCommandImageV1(kSyntheticBase, identity, {&image, nullptr}));
  REQUIRE(old::ImageBuildForSha(cur::kExecutableSha256) == old::ImageBuildV1::unknown);
  REQUIRE(!old::BindCommandImage(kSyntheticBase, cur::kExecutableSha256).enabled);
  REQUIRE(old::BindCommandImage(kSyntheticBase, old::kExecutableSha256).enabled);
  REQUIRE(old::BindCommandImage(kSyntheticBase, old::hotfix26757580::kExecutableSha256).enabled);

  for (const auto &p : cur::CommandCodePinsV1()) {
    auto damaged = CompleteImage(); const unsigned char bad = static_cast<unsigned char>(p.bytes[0] ^ 1);
    damaged.Put(p.rva, bad); REQUIRE(!Verify(damaged));
  }
  for (const auto &p : cur::CommandMetadataPinsV1()) {
    auto damaged = CompleteImage(); const unsigned char bad = static_cast<unsigned char>(p.bytes[0] ^ 1);
    damaged.Put(p.rva, bad); REQUIRE(!Verify(damaged));
  }
  for (const auto &p : cur::CommandPointerPinsV1()) {
    auto damaged = CompleteImage();
    damaged.Put(p.rva, kSyntheticBase + p.target_rva + 1); REQUIRE(!Verify(damaged));
    // The preferred on-disk VA must fail under this deliberately different base.
    damaged.Put(p.rva, std::uintptr_t{0x140000000ULL} + p.target_rva); REQUIRE(!Verify(damaged));
  }
  image = CompleteImage(); image.Put(0x130, std::uint64_t{0x140000000ULL}); REQUIRE(!Verify(image)); // preferred disk header cannot qualify a loaded ASLR header
  image = CompleteImage(); image.Put(0x3C, std::uint32_t{0xFFFFFFFF}); REQUIRE(!Verify(image));
  image = CompleteImage(); image.Put(0x108, cur::kPeTimestamp + 1); REQUIRE(!Verify(image));
  image = CompleteImage(); image.Put(0x118, std::uint16_t{0x10B}); REQUIRE(!Verify(image));
  image = CompleteImage(); image.Put(0x150, std::uint32_t{0x6FE6000}); REQUIRE(!Verify(image));
  image = CompleteImage(); image.unreadable = kSyntheticBase + cur::CommandCodePinsV1().back().rva; REQUIRE(!Verify(image));
  image = CompleteImage(); image.segments.pop_back(); REQUIRE(!Verify(image));
  return true;
}
bool CheckBindingSwitch() {
  auto image = CompleteImage();
  const auto bound = cur::BindCurrentCommandFixtureV1(kSyntheticBase, identity, image.Access());
#if XAR_CK3_ENABLE_121003_26785313_COMMAND_BINDINGS_V1 == 1
  REQUIRE(bound.current_image_verified && bound.offline_fixture && bound.commands.enabled);
  REQUIRE(cur::CurrentCommandTargetsMatchV1(bound));
  REQUIRE(bound.module_base == kSyntheticBase);
  REQUIRE(bound.commands.pause_primary_vtable == kSyntheticBase + cur::kPausePrimaryVtableRvaV1);
  REQUIRE(bound.commands.auto_save_secondary_vtable == kSyntheticBase + cur::kAutoSaveSecondaryVtableRvaV1);
  auto drift = bound; drift.commands.queue_owned_command = nullptr; REQUIRE(!cur::CurrentCommandTargetsMatchV1(drift));
  drift = bound; drift.commands.game_speed_count = nullptr; REQUIRE(!cur::CurrentCommandTargetsMatchV1(drift));
  drift = bound; drift.commands.pause_secondary_vtable += 8; REQUIRE(!cur::CurrentCommandTargetsMatchV1(drift));
  drift = bound; drift.commands.auto_save_primary_vtable += 8; REQUIRE(!cur::CurrentCommandTargetsMatchV1(drift));
  image.Put(cur::CommandPointerPinsV1()[0].rva, std::uintptr_t{});
  REQUIRE(!cur::BindCurrentCommandFixtureV1(kSyntheticBase, identity, image.Access()).current_image_verified);
#else
  REQUIRE(!bound.current_image_verified && !bound.commands.enabled);
  REQUIRE(!cur::BindCurrentCommandImageV1(kSyntheticBase, identity).current_image_verified);
#endif
  // No field of 'bound' is ever dereferenced or called: its addresses are RVAs
  // in a sparse fake reader, not mapped executable memory or a loaded game.
  return true;
}

struct Table { std::array<std::uintptr_t, 9> slots{}; std::size_t size = 0; };
enum class CloneMode { ordinary, empty, allocate_then_fail };
enum class QueueMode { accept_consume, accept_retain, reject_consume, reject_retain };
struct Manager {
  QueueMode mode = QueueMode::accept_consume;
  std::size_t calls = 0; std::uint32_t channel = 0; std::vector<std::byte> copied;
};
std::size_t clones = 0, deletes = 0, gates = 0;
CloneMode clone_mode = CloneMode::ordinary;
void *Delete(void *p, std::uint32_t flag) {
  if (flag != 1) std::terminate();
  ++deletes; delete[] static_cast<std::byte *>(p); return nullptr;
}
void **Clone(const void *p, void **storage) {
  if (clone_mode == CloneMode::empty) { *storage = nullptr; return storage; }
  const Table *table = nullptr; std::memcpy(&table, p, sizeof(table));
  auto *copy = new std::byte[table->size]; std::memcpy(copy, p, table->size); *storage = copy; ++clones;
  return clone_mode == CloneMode::allocate_then_fail ? nullptr : storage;
}
bool Queue(void *opaque, void **owned, std::uint32_t channel) {
  auto &m = *static_cast<Manager *>(opaque); ++m.calls; m.channel = channel;
  const Table *table = nullptr; std::memcpy(&table, *owned, sizeof(table));
  const auto *begin = static_cast<const std::byte *>(*owned); m.copied.assign(begin, begin + table->size);
  const std::uint32_t metadata = 0x12345678;
  std::memcpy(static_cast<std::byte *>(*owned) + 0x0C, &metadata, sizeof(metadata));
  const bool consume = m.mode == QueueMode::accept_consume || m.mode == QueueMode::reject_consume;
  if (consume) { Delete(*owned, 1); *owned = nullptr; }
  return m.mode == QueueMode::accept_consume || m.mode == QueueMode::accept_retain;
}
bool RejectBeforeQueue(void *) noexcept { ++gates; return false; }
Table MakeTable(std::size_t size) {
  Table result{}; result.size = size;
  result.slots[0] = reinterpret_cast<std::uintptr_t>(&Delete);
  result.slots[8] = reinterpret_cast<std::uintptr_t>(&Clone); return result;
}
template <class T> T Observed(const Manager &m) {
  T result{}; if (m.copied.size() == sizeof(result)) std::memcpy(&result, m.copied.data(), sizeof(result)); return result;
}
bool CheckLayoutsAndExistingOwnership() {
  static_assert(sizeof(old::TimeCommand) == 0x28 && sizeof(old::AutoSaveCommand) == 0x40);
  static_assert(offsetof(old::TimeCommand, secondary_vtable) == 0x18 && offsetof(old::TimeCommand, value) == 0x20);
  static_assert(offsetof(old::TimeCommand, paused) == 0x24 && offsetof(old::AutoSaveCommand, save_name) == 0x20);
  auto time_table = MakeTable(sizeof(old::TimeCommand)); auto save_table = MakeTable(sizeof(old::AutoSaveCommand));
  Manager manager{}; old::CommandBindings bindings{}; bindings.enabled = true;
  bindings.command_manager = &manager; bindings.queue_owned_command = &Queue;
  bindings.pause_primary_vtable = reinterpret_cast<std::uintptr_t>(&time_table);
  bindings.set_speed_primary_vtable = bindings.pause_primary_vtable;
  bindings.auto_save_primary_vtable = reinterpret_cast<std::uintptr_t>(&save_table);
  bindings.pause_secondary_vtable = 0x1122; bindings.set_speed_secondary_vtable = 0x2233; bindings.auto_save_secondary_vtable = 0x3344;
  const auto pause = old::MakePauseCommand(bindings, 44333, true);
  const auto original = pause;
  REQUIRE(pause.flags == 8 && pause.value == 44333 && pause.paused == 1 && pause.secondary_vtable == 0x1122);
  REQUIRE(old::MakePauseCommand(bindings, 44333, false).paused == 0);
  for (int speed = 1; speed <= 5; ++speed) {
    const auto c = old::MakeSetSpeedCommand(bindings, speed); REQUIRE(c.flags == 0 && c.value == speed - 1 && c.secondary_vtable == 0x2233);
  }
  const auto save = old::MakeSaveCheckpointCommand(bindings);
  REQUIRE(save.flags == 0x20 && save.secondary_vtable == 0x3344 && save.save_name.size == 14 && save.save_name.capacity == 15);
  REQUIRE(std::string_view(save.save_name.buffer.data(), 14) == old::kCheckpointSaveName);
  REQUIRE(save.save_name.buffer[14] == '\0' && save.save_name.buffer[15] == '\0');
  for (const auto mode : {QueueMode::accept_consume, QueueMode::accept_retain, QueueMode::reject_consume, QueueMode::reject_retain}) {
    manager.mode = mode; const auto before_clone = clones, before_delete = deletes;
    const bool accepted = mode == QueueMode::accept_consume || mode == QueueMode::accept_retain;
    REQUIRE(old::SubmitCommandCopy(bindings, &pause) == (accepted ? old::CommandSubmitResult::submitted : old::CommandSubmitResult::rejected));
    REQUIRE(manager.channel == 7 && clones == before_clone + 1 && deletes == before_delete + 1);
    REQUIRE(Observed<old::TimeCommand>(manager).value == 44333);
    REQUIRE(std::memcmp(&pause, &original, sizeof(pause)) == 0);
  }
  manager.mode = QueueMode::accept_consume;
  REQUIRE(old::SubmitCommandCopy(bindings, &save) == old::CommandSubmitResult::submitted);
  REQUIRE(Observed<old::AutoSaveCommand>(manager).save_name.size == 14 && manager.channel == 7);
  const auto before_gate = manager.calls, before_clones = clones;
  REQUIRE(old::SubmitCommandCopy(bindings, &pause, 7, &RejectBeforeQueue, nullptr) == old::CommandSubmitResult::unavailable);
  REQUIRE(gates == 1 && manager.calls == before_gate && clones == before_clones + 1 && clones == deletes);
  clone_mode = CloneMode::empty;
  REQUIRE(old::SubmitCommandCopy(bindings, &pause) == old::CommandSubmitResult::unavailable && manager.calls == before_gate);
  clone_mode = CloneMode::allocate_then_fail;
  REQUIRE(old::SubmitCommandCopy(bindings, &pause) == old::CommandSubmitResult::unavailable && clones == deletes && manager.calls == before_gate);
  clone_mode = CloneMode::ordinary; bindings.enabled = false;
  const auto terminal_clones = clones;
  REQUIRE(old::SubmitCommandCopy(bindings, &pause) == old::CommandSubmitResult::unavailable && clones == terminal_clones);
  return true;
}
} // namespace
int main() {
  if (!CheckExactImage() || !CheckBindingSwitch() || !CheckLayoutsAndExistingOwnership()) return 1;
  std::cout << "Current267 command image/layout/ownership NoGame source test passed; feature="
            << XAR_CK3_ENABLE_121003_26785313_COMMAND_BINDINGS_V1 << "; clones=" << clones << "; deletes=" << deletes
            << "; synthetic sparse reader only; no game/RVA function calls\n";
  return 0;
}
