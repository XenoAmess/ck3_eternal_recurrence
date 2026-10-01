#pragma once

#include "xar_bridge/ck3_12002_actor_resources.hpp"
#include "xar_bridge/ck3_12002_religion_context.hpp"

namespace xar::ck3_12002::religion_conversion::outcome::actor {

struct Bindings {
  religion::Bindings current_religion{};
  ActorResourceReadMemory12002 read_memory = nullptr;
  void *memory_context = nullptr;
};
enum class Failure {
  none,
  bindings_unavailable,
  played_character_unavailable,
  frame_not_paused,
  current_religion_unavailable,
  resources_unavailable,
  state_changed,
};
struct Context {
  bool available = false;
  Failure failure = Failure::bindings_unavailable;
  std::uint64_t capture_epoch = 0;
  std::int32_t date_raw = 0;
  std::int32_t played_character_id = -1;
  religion::Context current_religion{};
  std::optional<std::int64_t> piety_raw;
  std::optional<std::int64_t> gold_raw;
  std::optional<std::int64_t> prestige_raw;
  static constexpr std::int64_t raw_scale = 100'000;
};

Bindings BindConversionOutcomeActorImage12002(std::uintptr_t module_base,
                                            std::string_view executable_sha256) noexcept;
// Independent current state only, from the existing paused application-main
// owner. No target, quotation, request ACK, command execution or delta input.
bool ReadPlayedConversionOutcomeActor12002(const Bindings &, std::uint64_t capture_epoch,
                                         Context &) noexcept;
const char *ConversionOutcomeActorFailureKey(Failure) noexcept;
std::string SerializeConversionOutcomeActor12002(const Context &);

} // namespace xar::ck3_12002::religion_conversion::outcome::actor
