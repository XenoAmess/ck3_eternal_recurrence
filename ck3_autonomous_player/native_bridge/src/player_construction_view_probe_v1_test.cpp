#include "player_construction_view_probe_v1.hpp"

#include <array>
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <utility>

namespace {

using namespace xar::ck3::shared;

struct Fixture final {
  static constexpr std::uintptr_t kModule = 0x10000000U;
  std::array<std::byte, 0xE0> handler{};
  std::array<std::byte, 0x140> view{};
  PlayerConstructionViewResolvedOwnerV1 owner{};
  bool visibility_readable = true;
  bool effective_visible = false;

  Fixture() {
    owner.root = 0x20000000U;
    owner.idler_base = 0x20000010U;
    owner.idler_gfx = 0x20000020U;
    owner.handler = reinterpret_cast<std::uintptr_t>(handler.data());
    owner.exact_idler_rtti_cast = true;
    Put(handler, 0U, kModule + 0x40AF630U);
    Put(handler, 0xD0U, reinterpret_cast<std::uintptr_t>(view.data()));
    Put(view, 0U, kModule + 0x4131618U);
    Put(view, 0xD0U, owner.handler);
    Put(view, 0x118U, std::uintptr_t{0U});
    Put(view, 0x120U, std::int32_t{0});
    Put(view, 0x124U, std::int32_t{0});
  }

  template <typename T, std::size_t N>
  static void Put(std::array<std::byte, N>& buffer, std::size_t offset,
                  const T& value) {
    assert(offset + sizeof(value) <= buffer.size());
    std::memcpy(buffer.data() + offset, &value, sizeof(value));
  }
};

bool Resolve(void* context, std::uintptr_t module,
             PlayerConstructionViewResolvedOwnerV1& owner) noexcept {
  auto& fixture = *static_cast<Fixture*>(context);
  if (module != Fixture::kModule) return false;
  owner = fixture.owner;
  return true;
}

bool Read(void* context, std::uintptr_t address, void* destination,
          std::size_t bytes) {
  const auto& fixture = *static_cast<Fixture*>(context);
  for (const auto& [begin, size] :
       std::array<std::pair<std::uintptr_t, std::size_t>, 2>{{
           {reinterpret_cast<std::uintptr_t>(fixture.handler.data()),
            fixture.handler.size()},
           {reinterpret_cast<std::uintptr_t>(fixture.view.data()),
            fixture.view.size()},
       }}) {
    if (address >= begin && address - begin <= size &&
        bytes <= size - (address - begin)) {
      std::memcpy(destination, reinterpret_cast<const void*>(address), bytes);
      return true;
    }
  }
  return false;
}

bool ReadVisibility(void* context, std::uintptr_t module,
                    bool& effective_visible) noexcept {
  const auto& fixture = *static_cast<Fixture*>(context);
  if (module != Fixture::kModule || !fixture.visibility_readable) {
    return false;
  }
  effective_visible = fixture.effective_visible;
  return true;
}

PlayerConstructionViewProbeResultV1 Probe(Fixture& fixture) {
  PlayerConstructionViewProbeAdmissionV1 admission{};
  admission.exact_build_admitted = true;
  admission.application_main_thread = true;
  admission.session_live = true;
  admission.module_base = Fixture::kModule;
  PlayerConstructionViewProbeSourceV1 source{};
  source.resolve_owner = &Resolve;
  source.owner_context = &fixture;
  source.read_memory = &Read;
  source.read_context = &fixture;
  source.read_holding_view_visibility = &ReadVisibility;
  source.visibility_context = &fixture;
  return ProbePlayerConstructionViewCacheV1(admission, source);
}

}  // namespace

int main() {
  Fixture fixture{};
  auto result = Probe(fixture);
  assert(result.status == PlayerConstructionViewProbeStatusV1::
                              view_candidate_cache_empty);
  assert(result.failure == PlayerConstructionViewProbeFailureV1::none);
  assert(result.view_present && result.cached_candidate_count == 0);
  assert(result.holding_view_visibility ==
         PlayerConstructionHoldingViewVisibilityV1::hidden);

  fixture.effective_visible = true;
  Fixture::Put(fixture.view, 0x118U, std::uintptr_t{0x30000000U});
  Fixture::Put(fixture.view, 0x120U, std::int32_t{3});
  Fixture::Put(fixture.view, 0x124U, std::int32_t{2});
  result = Probe(fixture);
  assert(result.status == PlayerConstructionViewProbeStatusV1::
                              view_candidate_cache_present);
  assert(result.cached_candidate_count == 2 &&
         result.candidate_capacity == 3);
  assert(result.holding_view_visibility ==
         PlayerConstructionHoldingViewVisibilityV1::visible);

  fixture.visibility_readable = false;
  result = Probe(fixture);
  assert(result.status == PlayerConstructionViewProbeStatusV1::
                              view_candidate_cache_present);
  assert(result.holding_view_visibility ==
         PlayerConstructionHoldingViewVisibilityV1::unavailable);
  fixture.visibility_readable = true;

  Fixture::Put(fixture.view, 0xD0U, std::uintptr_t{0xDEADBEEFU});
  result = Probe(fixture);
  assert(result.status == PlayerConstructionViewProbeStatusV1::unavailable);
  assert(result.failure == PlayerConstructionViewProbeFailureV1::view_identity);
  Fixture::Put(fixture.view, 0xD0U, fixture.owner.handler);

  Fixture::Put(fixture.view, 0x124U, std::int32_t{4});
  result = Probe(fixture);
  assert(result.status == PlayerConstructionViewProbeStatusV1::unavailable);
  assert(result.failure == PlayerConstructionViewProbeFailureV1::candidate_span);
}
