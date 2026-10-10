#include "xar_bridge/m4_factor_actor_context_12004.hpp"
#include "xar_bridge/ck3_12004.hpp"

#include <cstring>
#include <map>
#include <stdexcept>
#include <vector>

namespace xar::ck3_12004 {
namespace {
void RequireContext(bool condition, const char *message) {
  if (!condition) throw std::runtime_error(message);
}
template <typename T>
T LoadContext(const M4FactorActorContext12004 &context, std::size_t offset) {
  T value{};
  std::memcpy(&value, context.raw.data()+offset, sizeof(value));
  return value;
}
struct ContextFixture {
  static constexpr std::uintptr_t module = 0x140000000;
  static constexpr std::uintptr_t actor = 0x100000, storage = 0x200000, slots = 0x300000;
  static constexpr std::uint32_t full_id = 0x82000001;
  std::map<std::uintptr_t, std::vector<std::byte>> memory;
  unsigned reads = 0;
  M4FactorActorContextRequest12004 request{module, kExecutableSha256, actor, 71};
  M4FactorActorInnerInit12004 inner{};
  template <typename T> void Put(std::uintptr_t address, T value) {
    auto &bytes = memory[address]; bytes.resize(sizeof(value));
    std::memcpy(bytes.data(), &value, sizeof(value));
  }
  ContextFixture() {
    Put(actor+0x18, full_id);
    Put(module+kCharacterStorageSlotRva, storage);
    Put(module+0x5C67570, std::uintptr_t{0x400000});
    Put(storage+0x20, slots);
    Put(storage+0x2C, std::int32_t{2});
    Put(slots+0x18, actor);
    // Synthetic child overlay tests the join protocol only. Actual child48
    // source and projection have their own cases in the connected compound.
    inner.module_base = module;
    inner.executable_sha256 = kExecutableSha256;
    inner.frame_key = 71;
    inner.complete_source = true;
    inner.self_pointer_patches[0] = {0x10, 0x18};
    inner.self_pointer_patch_count = 1;
    for (std::size_t i=0x10; i<0x18; ++i) inner.defined_bytes[i] = 1;
    // Deliberate overlapping child write: actual outer post-call zero wins.
    for (std::size_t i=0xE8; i<0xF0; ++i) {
      inner.raw[i] = std::byte{0x99}; inner.defined_bytes[i] = 1;
    }
  }
  static bool Read(void *opaque, std::uintptr_t address, void *out,
                   std::size_t size) noexcept {
    auto &fixture = *static_cast<ContextFixture *>(opaque);
    ++fixture.reads;
    const auto it = fixture.memory.find(address);
    if (it == fixture.memory.end() || it->second.size() != size) return false;
    std::memcpy(out, it->second.data(), size); return true;
  }
  bool Execute(M4FactorActorContext12004 &out) {
    return ReadM4FactorActorContext12004({this, Read}, request, inner, out);
  }
  bool ExecuteProduction(M4FactorActorContext12004 &out) {
    return ReadM4FactorActorContext12004({this, Read}, request, out);
  }
};
} // namespace

// No main/standalone execution or native call. First run belongs to 03/10's
// one connected new-case compound after all participating source is closed.
int RunM4FactorActorContext12004NewCases() {
  int count = 0;
  {
    ContextFixture fixture; M4FactorActorContext12004 out;
    RequireContext(fixture.ExecuteProduction(out) && out.complete_source &&
        out.actor_identity_qualified && out.context_receiver == ContextFixture::actor &&
        out.frame_key == 71 && out.actor_full_id == ContextFixture::full_id &&
        LoadContext<std::uint64_t>(out, 8) == 0x82000001ULL &&
        LoadContext<std::uint32_t>(out, 0) == 4 &&
        LoadContext<std::uint32_t>(out, 0x10) == 0xFFFFFFFFU,
        "B17C70 actual factor receiver full generation ID zero-extends into tag4 scope");
    ++count;
    M4FactorActorContext12004 joined;
    RequireContext(fixture.Execute(joined), "B17C70 synthetic join overlay available");
    RequireContext(LoadContext<std::uintptr_t>(out, 0x28) ==
        reinterpret_cast<std::uintptr_t>(out.raw.data())+0x30 &&
        LoadContext<std::uintptr_t>(out, 0x18) ==
        reinterpret_cast<std::uintptr_t>(out.raw.data())+0x38 &&
        LoadContext<std::uint32_t>(out, 0x20) == 8 &&
        LoadContext<std::uint32_t>(out, 0x24) == 0 &&
        LoadContext<std::uint64_t>(joined, 0x100) == 0 &&
        LoadContext<std::uintptr_t>(out, 0x118) == ContextFixture::module+0x448D1F8 &&
        LoadContext<std::uintptr_t>(out, 0x158) == ContextFixture::module+0x54DE270 &&
        !out.defined_bytes[4] && !out.defined_bytes[0x14] && !out.defined_bytes[0x167],
        "B17C70 stable self pointer/outer-store order with source padding undefined");
    ++count;
  }
  {
    ContextFixture fixture; M4FactorActorContext12004 out;
    fixture.inner.complete_source = false;
    RequireContext(fixture.Execute(out) && out.actor_identity_qualified &&
        !out.complete_source && LoadContext<std::uint32_t>(out, 0) == 4,
        "B17C70 missing constructor child stays partial, never guessed full zero context");
    ++count;
  }
  {
    ContextFixture fixture; M4FactorActorContext12004 out;
    fixture.inner.frame_key = 72;
    RequireContext(fixture.Execute(out) && !out.complete_source,
        "B17C70 child input belongs to the same exact supplied frame");
    ++count;
  }
  {
    ContextFixture fixture; M4FactorActorContext12004 out;
    fixture.Put(ContextFixture::slots+0x18, std::uintptr_t{ContextFixture::actor+0x100});
    RequireContext(!fixture.Execute(out) && !out.actor_identity_qualified &&
        !out.complete_source, "B17C70 generation slot must resolve the original factor receiver");
    ++count;
  }
  {
    ContextFixture fixture; M4FactorActorContext12004 out;
    fixture.request.executable_sha256 = "other-build";
    RequireContext(!fixture.Execute(out) && !fixture.reads && !out.complete_source,
        "B17C70 unqualified image performs no source memory read");
    ++count;
  }
  return count;
}
} // namespace xar::ck3_12004
