#include "xar_bridge/family_marriage_send_outgoing_v2.hpp"
#include <cstdint>
#include <optional>
#include <string>
#include <string_view>

namespace xar::bridge {

namespace {

constexpr std::uint32_t kMaxCharacterId = 0xFFFFFFFE;
constexpr std::uint32_t kMaxSignedCharacterId = 0x7FFFFFFF;

bool isValidCharacterId(std::uint32_t id) noexcept {
    return id >= 1 && id <= kMaxCharacterId;
}

bool isValidScope(FamilyMarriageOutgoingScopeV2 scope) noexcept {
    return scope == FamilyMarriageOutgoingScopeV2::action_preparation ||
           scope == FamilyMarriageOutgoingScopeV2::post_submission;
}

bool isValidRoute(FamilyMarriageOutgoingRouteV2 route) noexcept {
    return route == FamilyMarriageOutgoingRouteV2::first_heir ||
           route == FamilyMarriageOutgoingRouteV2::fulfill_betrothal ||
           route == FamilyMarriageOutgoingRouteV2::child_matrilineal ||
           route == FamilyMarriageOutgoingRouteV2::child_default ||
           route == FamilyMarriageOutgoingRouteV2::ruler;
}

bool validatePrivateRouteConstraints(const FamilyMarriageOutgoingRequestV2& request) noexcept {
    if (request.actor == request.subject) return false;
    if (!request.expected_recipient.has_value()) return false;
    if (!isValidCharacterId(request.expected_recipient.value())) return false;
    if (request.expected_recipient.value() > kMaxSignedCharacterId) return false;
    if (request.subject > kMaxSignedCharacterId) return false;
    if (request.candidate > kMaxSignedCharacterId) return false;

    if (request.route == FamilyMarriageOutgoingRouteV2::child_matrilineal) {
        if (!request.request_matrilineal_option || request.require_matrilineal_option_off) return false;
    } else if (request.route == FamilyMarriageOutgoingRouteV2::child_default) {
        if (request.request_matrilineal_option || !request.require_matrilineal_option_off) return false;
    } else {
        if (request.request_matrilineal_option || request.require_matrilineal_option_off) return false;
    }
    return true;
}

bool validateRulerRouteConstraints(const FamilyMarriageOutgoingRequestV2& request) noexcept {
    if (request.actor != request.subject) return false;
    if (request.expected_recipient.has_value()) return false;
    if (request.request_matrilineal_option || request.require_matrilineal_option_off) return false;
    return true;
}

bool validateSenderContract(const FamilyMarriageOutgoingRequestV2& request) noexcept {
    if (request.scope == FamilyMarriageOutgoingScopeV2::post_submission) {
        if (!request.sender.has_value()) return false;
        if (!isValidCharacterId(request.sender.value())) return false;
    } else {
        if (request.sender.has_value()) return false;
    }
    return true;
}

} // anonymous namespace

bool ValidateFamilyMarriageOutgoingRequestV2(
    const FamilyMarriageOutgoingRequestV2& request,
    const FamilyMarriageOutgoingFrameV2& frame) noexcept {

    if (!isValidScope(request.scope) || !isValidRoute(request.route)) {
        return false;
    }

    if (!isValidCharacterId(request.actor) || !isValidCharacterId(request.subject) || !isValidCharacterId(request.candidate)) {
        return false;
    }

    if (request.actor != frame.played_character_id) {
        return false;
    }

    if (request.subject == request.candidate) {
        return false;
    }

    if (!validateSenderContract(request)) {
        return false;
    }

    if (request.route == FamilyMarriageOutgoingRouteV2::ruler) {
        if (!validateRulerRouteConstraints(request)) return false;
    } else {
        if (!validatePrivateRouteConstraints(request)) return false;
    }

    if (request.scope == FamilyMarriageOutgoingScopeV2::action_preparation) {
        if (!frame.paused || !frame.map_ready || !frame.player_alive) {
            return false;
        }
    }

    return true;
}

FamilyMarriageOutgoingReadStatusV2 ReadFamilyMarriageOutgoingUnavailableV2(
    const FamilyMarriageOutgoingReadAccessV2& access,
    std::string_view request_id,
    const FamilyMarriageOutgoingRequestV2& request,
    std::uint64_t expected_revision,
    std::uint64_t query_sequence,
    std::string& output) {

    output.clear();

    if (request_id.empty() || query_sequence == 0) {
        return FamilyMarriageOutgoingReadStatusV2::invalid_request;
    }

    if (access.capture_frame == nullptr) {
        return FamilyMarriageOutgoingReadStatusV2::frame_unavailable;
    }

    FamilyMarriageOutgoingFrameV2 before_frame{};
    if (!access.capture_frame(access.context, before_frame)) {
        return FamilyMarriageOutgoingReadStatusV2::frame_unavailable;
    }

    if (before_frame.revision != expected_revision) {
        return FamilyMarriageOutgoingReadStatusV2::frame_changed;
    }

    if (!ValidateFamilyMarriageOutgoingRequestV2(request, before_frame)) {
        return FamilyMarriageOutgoingReadStatusV2::invalid_request;
    }

    FamilyMarriageOutgoingFrameV2 after_frame{};
    if (!access.capture_frame(access.context, after_frame)) {
        return FamilyMarriageOutgoingReadStatusV2::frame_unavailable;
    }

    if (!(before_frame == after_frame)) {
        return FamilyMarriageOutgoingReadStatusV2::frame_changed;
    }

    try {
        output = FamilyMarriageOutgoingUnavailableResultV2(request_id, request, before_frame, query_sequence);
    } catch (...) {
        output.clear();
        return FamilyMarriageOutgoingReadStatusV2::invalid_request;
    }

    return FamilyMarriageOutgoingReadStatusV2::completed_unavailable;
}

} // namespace xar::bridge
