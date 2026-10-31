#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kFamilyMarriageSendOutgoingStepV2 =
    "query-family-marriage-send-outgoing-v1-private";
enum class FamilyMarriageOutgoingScopeV2 : std::uint8_t {
  action_preparation,
  post_submission
};
enum class FamilyMarriageOutgoingRouteV2 : std::uint8_t {
  first_heir,
  fulfill_betrothal,
  child_matrilineal,
  child_default,
  ruler
};
struct FamilyMarriageOutgoingRequestV2 {
  FamilyMarriageOutgoingScopeV2 scope =
      FamilyMarriageOutgoingScopeV2::action_preparation;
  FamilyMarriageOutgoingRouteV2 route = FamilyMarriageOutgoingRouteV2::ruler;
  std::uint32_t actor = 0;
  std::uint32_t subject = 0;
  std::uint32_t candidate = 0;
  std::optional<std::uint32_t> expected_recipient{};
  std::optional<std::uint32_t> sender{};
  bool request_matrilineal_option = false;
  bool require_matrilineal_option_off = false;
};
struct FamilyMarriageOutgoingFrameV2 {
  std::uint64_t revision = 0;
  std::int32_t date_raw = 0;
  std::uint32_t played_character_id = 0;
  bool paused = false;
  bool map_ready = false;
  bool player_alive = false;
  friend bool operator==(const FamilyMarriageOutgoingFrameV2 &,
                         const FamilyMarriageOutgoingFrameV2 &) = default;
};

// These APIs do not adapt a specific first-heir active/absent result into a
// complete storage inventory or claim that a local context was materialized.
bool ValidateFamilyMarriageOutgoingRequestV2(
    const FamilyMarriageOutgoingRequestV2 &,
    const FamilyMarriageOutgoingFrameV2 &) noexcept;

// Decodes nine canonical flat native fields; Bridge owns the execute envelope.
// No Game/memory access. Failure resets output and never guesses null roles.
bool ParseFamilyMarriageOutgoingNativeFieldsV2(
    std::string_view payload, FamilyMarriageOutgoingRequestV2 &output) noexcept;

// Produces the complete command_result envelope. The result is accepted but
// storage remains unavailable, and preparation has a typed NotPrepared value.
// Post-submission prepared_context is JSON null. Throws invalid_argument for
// an invalid request/frame, empty request id, or zero query sequence.
std::string FamilyMarriageOutgoingUnavailableResultV2(
    std::string_view request_id, const FamilyMarriageOutgoingRequestV2 &,
    const FamilyMarriageOutgoingFrameV2 &, std::uint64_t query_sequence);

using CaptureFamilyMarriageOutgoingFrameV2 = bool (*)(
    void *context, FamilyMarriageOutgoingFrameV2 &output) noexcept;
struct FamilyMarriageOutgoingReadAccessV2 {
  void *context = nullptr;
  CaptureFamilyMarriageOutgoingFrameV2 capture_frame = nullptr;
};
enum class FamilyMarriageOutgoingReadStatusV2 : std::uint8_t {
  completed_unavailable,
  invalid_request,
  frame_unavailable,
  frame_changed
};
// Captures actual before/after frames through the supplied adapter callback.
// No native context/command constructor, option setter or submit is invoked.
// Output is empty on every non-completed result. Allocation exceptions may
// propagate; the production Bridge has its ordinary command error boundary.
FamilyMarriageOutgoingReadStatusV2 ReadFamilyMarriageOutgoingUnavailableV2(
    const FamilyMarriageOutgoingReadAccessV2 &,
    std::string_view request_id, const FamilyMarriageOutgoingRequestV2 &,
    std::uint64_t expected_revision, std::uint64_t query_sequence,
    std::string &output);

}  // namespace xar::bridge
