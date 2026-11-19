#pragma once
#include "xar_bridge/ck3_1210_opening_readonly56.hpp"
#include "xar_bridge/ck3_1210_personal_gold_frame_v1.hpp"
namespace xar::ck3_1210 {
struct OpeningMailboxContext56 {
 OpeningReadKind56 kind=OpeningReadKind56::government_scope;
 OpeningReadBindings56 bindings{};
 OpeningReadAccess56 read_access{}; // Only the explicit offline build may use a copy seam.
 const game::GameAdapter *native_full_adapter=nullptr;
 const std::uint64_t *current_published_revision=nullptr;
 std::uint64_t expected_native_revision=0;
 game::Snapshot expected_full{};
 OpeningReadObservation56 observation{};
 bool completed=false,application_main_observed=false,offline_fixture=false;
 std::uint64_t ticket_sequence=0,pump_epoch=0;
 std::uint32_t thread_id=0;
 std::size_t current_full_attempts=0;
};
bool ExecuteOpeningOnActorOwner56(PersonalGoldMailboxContextV1&,
 const ck3_11906::MainThreadExecutionStampV1&) noexcept;
std::string SerializeOpeningReadonlyData56(const OpeningMailboxContext56&);
std::string SerializeOpeningReadonlyCommand56(std::string_view,const OpeningMailboxContext56&);
}
