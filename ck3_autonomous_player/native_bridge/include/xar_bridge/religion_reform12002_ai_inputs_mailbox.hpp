#pragma once

#include "xar_bridge/ck3_12002_query_mailbox.hpp"
#include "xar_bridge/religion_reform12002_ai_context.hpp"
#include "xar_bridge/religion_reform12002_schedule.hpp"

namespace xar::ck3_12002 {

inline constexpr std::string_view kPlayerReligionAIReformInputsPrivateStep12002 =
    "query-player-religion-ai-reform-inputs-v1";
inline constexpr std::string_view kPlayerReligionAIReformInputsDomainKey12002 =
    "player_religion_ai_reform_inputs_v1";
inline constexpr std::string_view kPlayerReligionAIReformInputsBackend12002 =
    "ck3-1.20.0.2-native-player-religion-ai-reform-inputs-v1";

struct PlayerReligionAIReformInputsBindings12002 {
  CoreBindings core{};
  religion_reform::AIContextBindings context{};
  religion_reform::ScheduleBindings schedule{};
};
struct PlayerReligionAIReformControllerInputs12002 {
  std::uint32_t context_index = 0;
  religion_reform::ScheduleInputs schedule{};
};
struct PlayerReligionAIReformInputsObservation12002 {
  bool available = false;
  std::string failure = "bindings_unavailable";
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  religion_reform::ActorAIContext context{};
  religion_reform::ScheduleInputs schedule_base{};
  std::vector<PlayerReligionAIReformControllerInputs12002> controller_inputs;
  bool gate_inputs_observation_complete = false;
};
struct PlayerReligionAIReformInputsMailboxContext12002 {
  QueryMailboxEnvelope envelope{};
  PlayerReligionAIReformInputsBindings12002 bindings{};
  PlayerReligionAIReformInputsObservation12002 observation{};
  bool completed = false;
  std::string failure;
};

bool IsPlayerReligionAIReformInputsPrivateStep12002(std::string_view step) noexcept;
bool ParsePlayerReligionAIReformInputsRevision12002(std::string_view payload,
                                                  std::uint64_t &expected_revision) noexcept;
bool ExecutePlayerReligionAIReformInputsMailbox12002(
    void *, const ck3_11906::MainThreadExecutionStampV1 &) noexcept;
std::string SerializePlayerReligionAIReformInputsResult12002(
    const PlayerReligionAIReformInputsMailboxContext12002 &, std::string_view request_id);

// Reads the actual controller table and each member's native schedule inputs.
// No controller priority, scheduler invocation, next reform time or action.
bool RunPlayerReligionAIReformInputsMailbox12002(PlayerReligionAIReformInputsMailboxContext12002 &,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;
bool HandlePlayerReligionAIReformInputsPrivate12002(const game::GameAdapter &,
    ck3_11906::MainThreadQueryMailboxV1 &, const game::Snapshot &published,
    std::uint64_t revision, std::string_view step, std::string_view payload,
    std::string_view request_id, std::string &serialized,
    std::string &failure) noexcept;

} // namespace xar::ck3_12002
