#pragma once

#include "xar_bridge/rite_creation_actions12004.hpp"

namespace xar::ck3_12004::religion::rite_creation_actions {
inline constexpr std::size_t maximum_wire_request_bytes = 32768;
inline constexpr std::string_view native_backend_id =
    "ck3-1.20.0.4-native-rite-creation-action-v1";

// Assertions are supplied by the driver. They are never a captured native Frame.
struct WireRequest {
  Request request{};
  std::string request_id;
  std::uint64_t expected_revision = 0;
  std::uint64_t expected_connection_generation = 0;
  std::int32_t expected_date_raw = 0;
  std::int32_t expected_player_character_id = -1;
};

// Parses the complete, flat ExecuteStep JSON document with an operation-specific
// whitelist. It accepts JSON-escaped UTF-8 text and rejects duplicate decoded
// keys, unknown fields, nested values, trailing input, and invalid Unicode.
bool ParseRequest12004(std::string_view, WireRequest&,
                                    std::string& reason) noexcept;

// Call on a freshly captured owner frame before any native action. This checks
// assertions only; TLS, pause, build, permission and modal admission remain the
// controller/router's responsibility. Never construct actual from the request.
// Prepare may precede assignment of owner pump capture_epoch, so that field is
// checked by formatting the actual result, not by this four-assertion match.
bool MatchRequestFrame(const WireRequest&, const Frame& actual,
                                     std::string& reason) noexcept;
bool MatchRequestFrame(const WireRequest&, const Frame& actual) noexcept;

// Serializes only actual Result data. Unknown optionals remain null. The
// FormatResult emits command_result.result. SerializeCommandResult emits the
// normal outer command_result packet and returns empty on a formatting failure.
// No mailbox sequence is invented from a request or a capture epoch.
bool FormatRiteCreationActionLeaf12004(const Result&, std::string& json,
                                     std::string& reason) noexcept;
bool FormatResult12004(const Result&, std::string& json,
                      std::string& reason) noexcept;
std::string SerializeCommandResult12004(const Result&,
                                      std::string_view request_id) noexcept;
}  // namespace xar::ck3_12004::religion::rite_creation_actions
