#include "army_pre_date_prepared_roster_12004.hpp"

#include <array>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>

namespace {
template<class T> void Store(void *p, std::size_t at, const T &value) {
  std::memcpy(static_cast<std::byte *>(p) + at, &value, sizeof value);
}
void Require(bool value, const char *reason) {
  if (!value) throw std::runtime_error(reason);
}
std::size_t permission_calls = 0, fresh_calls = 0;
void *fallback_receiver = nullptr;
bool Permission(void *p, void *chunk) {
  ++permission_calls;
  Require(chunk == static_cast<std::byte *>(p) + 0x18, "not physical chunk0");
  return p != fallback_receiver;
}
std::int64_t *Fresh(void *p, std::int64_t *out) {
  ++fresh_calls;
  std::uint32_t id{}; std::memcpy(&id, static_cast<std::byte *>(p) + 0x10, sizeof id);
  *out = id == 0x80000000U ? 1234 : 555;
  return out;
}
struct ReadContext { const void *reject = nullptr; };
bool Copy(void *context, const void *src, void *dst, std::size_t size) noexcept {
  if (static_cast<ReadContext *>(context)->reject == src) return false;
  std::memcpy(dst, src, size); return true;
}
} // namespace

int main(int argc, char **argv) {
  try {
    Require(argc == 2, "one fresh output directory required");
    const std::filesystem::path output(argv[1]);
    Require(!std::filesystem::exists(output), "fresh output directory already exists");
    std::filesystem::create_directories(output);
    using namespace xar::ck3_12004;
    constexpr std::string_view sha = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    const auto bound = BindArmyPreDatePreparedRoster12004(0x10000000, sha);
    Require(bound.enabled && reinterpret_cast<std::uintptr_t>(bound.persistent_fallback_slot) == 0x15D1EB58,
            "actual4 fallback binder");
    Require(!BindArmyPreDatePreparedRoster12004(0x10000000, "old").enabled, "old build admitted");
    std::array<std::byte, 0xD0> state{};
    std::vector<std::byte> data(0x2A5E0);
    std::array<std::byte, 0x40> registry{};
    std::array<std::byte, 0x20> table{};
    std::array<std::byte, 0x160> first{}, second{}, fallback{};
    std::array<std::byte, 0x40> definition{};
    void *state_ptr = state.data(), *registry_ptr = registry.data(), *fallback_ptr = fallback.data();
    fallback_receiver = fallback.data();
    const std::array<std::uint32_t, 6> ids = {0x12000001U, 0x12000001U, 0x34000001U,
                                            0xFFFFFFFFU, 0x80000000U, 0U};
    auto *manager = data.data() + 0x2A540;
    Store(state.data(), 8, std::uint64_t{53289912});
    Store(state.data(), 0x9C, std::uint32_t{6066});
    Store(state.data(), 0xA0, data.data()); Store(state.data(), 0xC0, std::uint8_t{0x82});
    Store(manager, 0x30, ids.data()); Store(manager, 0x3C, std::int32_t{6});
    Store(registry.data(), 0x20, table.data()); Store(registry.data(), 0x2C, std::uint32_t{2});
    Store(table.data(), 8, first.data()); Store(table.data(), 24, second.data());
    Store(first.data(), 0x10, std::uint32_t{0x80000000U});
    Store(first.data(), 0x118, definition.data()); Store(definition.data(), 0x38, std::uint32_t{1});
    Store(first.data(), 0x138, std::int32_t{0}); Store(first.data(), 0x148, std::int64_t{0});
    Store(second.data(), 0x10, std::uint32_t{0x12000001U});
    Store(second.data(), 0x138, std::int32_t{1}); Store(second.data(), 0x148, std::int64_t{77});
    Store(fallback.data(), 0x10, std::uint32_t{0xFFFFFFFFU});
    Store(fallback.data(), 0x138, std::int32_t{1}); Store(fallback.data(), 0x148, std::int64_t{66});
    ReadContext context{};
    ArmyPreDatePreparedRosterBindings12004 b{};
    b.enabled = true; b.game_state_slot = &state_ptr; b.persistent_registry_slot = &registry_ptr;
    b.persistent_fallback_slot = &fallback_ptr; b.read_memory = Copy; b.read_context = &context;
    b.can_fixed_chunk0_replenish = Permission; b.get_fresh_fraction = Fresh;
    const auto state_before = state; const auto data_before = data;
    const auto first_before = first, second_before = second, fallback_before = fallback;
    const auto r = ReadArmyPreDatePreparedRoster12004(b, {41, ArmyPreparedRosterStage12004::current_query});
    Require(r.raw_roster_ready && r.current_resolution_ready && r.current_cache_ready &&
            r.conditional_preparation_ready, "new complete roster preparation inputs");
    Require(r.current_c0_raw == std::uint8_t{0x82} && r.current_mask02_admitted == true, "rawC0 mask02");
    Require(r.occurrences.size() == 6 && r.occurrences[0].raw_full_id == r.occurrences[1].raw_full_id &&
            r.occurrences[1].stored_index == 1, "ordered repeats lost");
    Require(r.occurrences[2].candidate_full_id == 0x12000001U &&
            r.occurrences[2].resolved_full_id == 0xFFFFFFFFU && r.occurrences[2].used_fallback,
            "full-generation fallback lost");
    Require(r.occurrences[3].raw_full_id == 0xFFFFFFFFU && r.occurrences[5].raw_full_id == 0U,
            "raw sentinel or zero lost");
    Require(r.occurrences[4].current_cache148 == 0 &&
            r.occurrences[4].conditional_branch_cache148 == 1234,
            "current cache was substituted with fresh value");
    Require(r.occurrences[4].permission_required == false &&
            !r.occurrences[4].fixed_chunk0_permission && r.occurrences[2].conditional_branch_cache148 == 0,
            "guard bypass or denied preparation wrong");
    Require(permission_calls == 5 && fresh_calls == 3, "conditional native demand or repetitions wrong");
    Require(r.observed_frame.sequence == 41 && r.observed_frame.date_raw == std::uint64_t{53289912} &&
            r.observed_frame.absolute_day_raw == std::uint32_t{6066} && !r.observed_post_frame &&
            !r.actual_preparation_observed, "current sample backdated or postframe manufactured");
    Require(state == state_before && data == data_before && first == first_before &&
            second == second_before && fallback == fallback_before, "readonly leaf wrote native state");
    Store(definition.data(), 0x38, std::uint32_t{0x4744624F});
    const auto guarded = ReadArmyPreDatePreparedRoster12004(b, {45});
    Require(guarded.occurrences[4].guard138 == 0 &&
            guarded.occurrences[4].permission_required == true &&
            guarded.occurrences[4].fixed_chunk0_permission == true &&
            guarded.occurrences[4].conditional_branch_cache148 == 1234 &&
            permission_calls == 11 && fresh_calls == 6,
            "guard-zero ObDG did not use physical chunk0 permission");
    Store(definition.data(), 0x38, std::uint32_t{1});
    Store(state.data(), 0xC0, std::uint8_t{0x80});
    const auto skipped = ReadArmyPreDatePreparedRoster12004(b, {42, ArmyPreparedRosterStage12004::post_date});
    Require(skipped.conditional_preparation_ready && skipped.current_mask02_admitted == false &&
            skipped.occurrences[0].conditional_branch_cache148 == 77 &&
            permission_calls == 11 && fresh_calls == 6 && !skipped.actual_preparation_observed,
            "mask-off branch called preparation or conflated postdate frame");
    context.reject = ids.data() + 1;
    const auto partial = ReadArmyPreDatePreparedRoster12004(b, {43});
    Require(!partial.raw_roster_ready && partial.occurrences.size() == 6 &&
            !partial.occurrences[1].raw_full_id && partial.occurrences[2].raw_full_id == 0x34000001U,
            "unread occurrence was dropped or changed order");
    context.reject = nullptr; Store(manager, 0x3C, std::int32_t{0});
    const auto empty = ReadArmyPreDatePreparedRoster12004(b, {44});
    Require(empty.raw_roster_ready && empty.conditional_preparation_ready && empty.occurrences.empty(),
            "legitimate empty roster unavailable");
    std::ofstream(output / "RESULT.json") <<
      "{\"status\":\"GREEN\",\"family\":\"actual4_pre_date_prepared_roster\","
      "\"scenes\":5,\"ordered_occurrences\":6,\"actual_preparation_observed\":false,"
      "\"game_actions\":0,\"native_exe_callbacks_executed\":0}\n";
    std::cout << "GREEN: ordered raw FullIDs, repetition, generation fallback, physical chunk0, current/conditional cache148, frame separation\n";
    return 0;
  } catch (const std::exception &e) { std::cerr << e.what() << '\n'; return 1; }
}
