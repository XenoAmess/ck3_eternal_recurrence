#pragma once
#include "council_observation65.hpp"
#include "xar_bridge/ck3_1210_personal_gold_frame_v1.hpp"
#include "xar_bridge/ck3_1210_hotfix26757580_v1.hpp"
namespace xar::ck3_1210::council67 {
inline constexpr char kStep[]="query-council-owned-task-observation-26757580-private-v1";
inline constexpr char kSchema[]="xar.ck3.council-owned-task-observation.26757580.v1";
inline constexpr char kContractId[]="council-owned-task-readonly-26757580-v1";
inline constexpr char kPermissionKey[]="council-owned-task-observation-private-26757580";
// Private source-qualified query: there is deliberately no advertised cap.
struct Bindings {
 CoreBindings core{};
 xar::council_observation65::Bindings memory{};
 bool exact_build_admitted=false;
};
Bindings BindImage(std::uintptr_t,std::string_view) noexcept;
struct ReadAccess {
 void* context=nullptr;
 bool(*copy)(void*,std::uintptr_t,void*,std::size_t)noexcept=nullptr;
};
struct MailboxContext {
 Bindings bindings{};
 const game::GameAdapter* native_full_adapter=nullptr;
 const std::uint64_t* current_published_revision=nullptr;
 std::uint64_t expected_native_revision=0;
 game::Snapshot expected_full{};
 xar::council_observation65::Observation observation{};
 // Only an explicitly compiled offline Frame can accept a copy override.
 ReadAccess read_access{};
 bool completed=false,data_ready=false,application_main_observed=false,offline_fixture=false;
 std::uint64_t ticket_sequence=0,pump_epoch=0;
 std::uint32_t thread_id=0;
 std::size_t current_full_attempts=0;
};
bool ExecuteOnActor(PersonalGoldMailboxContextV1&,const ck3_11906::MainThreadExecutionStampV1&)noexcept;
std::string SerializeData(const MailboxContext&);
std::string SerializeCommand(std::string_view,const MailboxContext&);
} // namespace xar::ck3_1210::council67
