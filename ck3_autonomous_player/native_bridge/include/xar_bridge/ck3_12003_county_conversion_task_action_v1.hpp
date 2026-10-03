#pragma once

#include "xar_bridge/ck3_12003_county_conversion.hpp"
#include "xar_bridge/ck3_12002_commands.hpp"

#include <array>
#include <cstddef>
#include <optional>
#include <string>

namespace xar::ck3_12003::religion::county_conversion::action {

inline constexpr std::uintptr_t kPrimaryVtableRva = 0x476DC68;
inline constexpr std::uintptr_t kSecondaryVtableRva = 0x476DC38;
inline constexpr std::uint32_t kCommandChannel = 0x0E;

struct alignas(8) TaskScopes {
  std::int32_t incumbent_character_id = -1;
  std::int32_t owner_character_id = -1;
  std::uint16_t target_tag = 8;
  std::array<std::byte, 6> reserved{};
  std::int64_t province_id = -1;
  std::array<std::byte, 8> trailing{};
};
struct alignas(8) ChangeCouncilTaskCommand {
  std::uintptr_t primary_vtable = 0;
  std::uint8_t flags = 0;
  std::array<std::byte, 15> metadata{};
  std::uintptr_t secondary_vtable = 0;
  std::int32_t active_task_id = -1;
  std::uint32_t padding = 0;
  const void *task_type = nullptr;
  TaskScopes scopes;
};
static_assert(sizeof(TaskScopes) == 0x20);
static_assert(offsetof(TaskScopes, province_id) == 0x10);
static_assert(sizeof(ChangeCouncilTaskCommand) == 0x50);
static_assert(offsetof(ChangeCouncilTaskCommand, secondary_vtable) == 0x18);
static_assert(offsetof(ChangeCouncilTaskCommand, active_task_id) == 0x20);
static_assert(offsetof(ChangeCouncilTaskCommand, task_type) == 0x28);
static_assert(offsetof(ChangeCouncilTaskCommand, scopes) == 0x30);

struct Request {
  std::uint64_t expected_revision = 0;
  std::int32_t expected_active_task_id = -1;
  std::int32_t expected_incumbent_character_id = -1;
  std::int32_t province_id = -1;
  bool replace_existing_task = false;
  std::string action_id;
};
struct Access {
  Environment county;
  ck3_12002::CommandBindings commands;
  std::uintptr_t primary_vtable = 0;
  std::uintptr_t secondary_vtable = 0;
};
Access BindCountyConversionTaskActionImage12003(
    std::uintptr_t module_base, std::string_view executable_sha256) noexcept;

struct TaskState {
  bool available = false;
  std::string failure;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t owner_character_id = -1;
  std::optional<std::int32_t> incumbent_character_id;
  std::optional<std::int32_t> active_task_id;
  std::string task_key;
  std::optional<std::uint16_t> target_scope_tag;
  std::optional<std::int32_t> target_province_id;
  std::optional<std::int32_t> target_county_title_id;
  std::optional<std::int32_t> progress_kind;
  std::optional<std::int64_t> percentage_progress_raw;
};
enum class SubmitStatus { not_submitted, already_active_noop, queued_verification_pending };
struct Submission {
  SubmitStatus status = SubmitStatus::not_submitted;
  std::string failure;
  std::string request_id;
  Request request;
  std::uint64_t native_revision = 0;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  std::optional<std::int32_t> target_county_title_id;
  std::optional<bool> native_final_can_dispatch;
  bool native_submit_copy_called = false;
  std::uint32_t command_channel = kCommandChannel;
  TaskState before;
};
Submission SubmitCountyConversionTask12003(
    const Access &, const game::Snapshot &published,
    std::uint64_t public_revision, std::uint64_t native_revision,
    std::uint64_t pump_epoch, std::string_view request_id, const Request &);

struct IndependentResult {
  std::string request_id;
  std::string action_id;
  SubmitStatus submit_status = SubmitStatus::not_submitted;
  bool verification_pending = true;
  TaskState after;
  std::optional<bool> actual_task_id_unchanged;
  std::optional<bool> actual_task_assignment_matches;
  bool task_assignment_material_observed = false;
  bool county_conversion_completed = false;
};
IndependentResult ReadCountyConversionTaskResult12003(
    const Access &, const Submission &, std::uint64_t pump_epoch);

std::string SerializeCountyConversionTaskSubmission12003(const Submission &);
std::string SerializeCountyConversionTaskIndependentResult12003(const IndependentResult &);

} // namespace xar::ck3_12003::religion::county_conversion::action
