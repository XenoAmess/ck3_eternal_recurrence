#include "xar_bridge/ordinary_interaction_request_v1.hpp"

#include <array>
#include <cstddef>
#include <limits>
#include <utility>

namespace xar::ck3_12003 {
namespace {

constexpr std::size_t kMaximumStringBytes = 128;
constexpr std::uint32_t kInvalidCharacterId = 0xffffffffU;

bool IsKeyByte(char byte) noexcept {
  return (byte >= 'A' && byte <= 'Z') ||
         (byte >= 'a' && byte <= 'z') ||
         (byte >= '0' && byte <= '9') || byte == '_';
}

bool IsInteractionKey(std::string_view key) noexcept {
  if (key.empty() || key.size() > kMaximumStringBytes) {
    return false;
  }
  for (const char byte : key) {
    if (!IsKeyByte(byte)) {
      return false;
    }
  }
  return true;
}

class FlatJsonCursor final {
 public:
  explicit FlatJsonCursor(std::string_view json) noexcept : json_(json) {}

  bool Consume(char expected) noexcept {
    SkipWhitespace();
    if (position_ == json_.size() || json_[position_] != expected) {
      return false;
    }
    ++position_;
    return true;
  }

  bool ReadString(std::string_view &value) noexcept {
    if (!Consume('"')) {
      return false;
    }
    const std::size_t begin = position_;
    while (position_ < json_.size()) {
      const unsigned char byte =
          static_cast<unsigned char>(json_[position_]);
      if (byte == '"') {
        value = json_.substr(begin, position_ - begin);
        ++position_;
        return value.size() <= kMaximumStringBytes;
      }
      // These control fields deliberately share the existing protocol's
      // unescaped-string subset; do not decode escaped keys or values.
      if (byte < 0x20U || byte > 0x7fU || byte == '\\' ||
          position_ - begin == kMaximumStringBytes) {
        return false;
      }
      ++position_;
    }
    return false;
  }

  bool ReadUnsigned(std::uint64_t &value) noexcept {
    SkipWhitespace();
    if (position_ == json_.size() || json_[position_] < '0' ||
        json_[position_] > '9') {
      return false;
    }
    const bool begins_with_zero = json_[position_] == '0';
    const std::size_t begin = position_;
    std::uint64_t parsed = 0;
    while (position_ < json_.size() && json_[position_] >= '0' &&
           json_[position_] <= '9') {
      if (begins_with_zero && position_ != begin) {
        return false;
      }
      const std::uint64_t digit =
          static_cast<std::uint64_t>(json_[position_] - '0');
      if (parsed > (std::numeric_limits<std::uint64_t>::max() - digit) / 10U) {
        return false;
      }
      parsed = parsed * 10U + digit;
      ++position_;
    }
    value = parsed;
    return true;
  }

  bool AtEnd() noexcept {
    SkipWhitespace();
    return position_ == json_.size();
  }

 private:
  void SkipWhitespace() noexcept {
    while (position_ < json_.size()) {
      const char byte = json_[position_];
      if (byte != ' ' && byte != '\t' && byte != '\r' && byte != '\n') {
        break;
      }
      ++position_;
    }
  }

  std::string_view json_;
  std::size_t position_ = 0;
};

constexpr std::array<std::string_view, 10> kFieldNames{
    "type", "protocol_version", "request_id", "step", "interaction_key",
    "recipient_id", "expected_revision", "expected_player_character_id",
    "expected_game_pid", "expected_connection_generation"};

std::size_t FieldIndex(std::string_view key) noexcept {
  for (std::size_t index = 0; index < kFieldNames.size(); ++index) {
    if (key == kFieldNames[index]) {
      return index;
    }
  }
  return kFieldNames.size();
}

}  // namespace

bool OrdinaryInteractionRequestValidV1(
    const OrdinaryInteractionRequestV1 &request) noexcept {
  return IsInteractionKey(request.interaction_key) &&
         request.recipient_id != 0 &&
         request.recipient_id != kInvalidCharacterId &&
         request.expected_revision != 0 &&
         request.expected_player_character_id > 0 &&
         request.expected_game_pid != 0 &&
         request.expected_connection_generation != 0;
}

bool ParseOrdinaryInteractionRequestV1(
    std::string_view json, bool initiate,
    OrdinaryInteractionRequestV1 &output) noexcept {
  try {
    FlatJsonCursor cursor(json);
    OrdinaryInteractionRequestV1 parsed;
    std::uint16_t seen = 0;
    if (!cursor.Consume('{')) {
      return false;
    }
    for (std::size_t ordinal = 0; ordinal < kFieldNames.size(); ++ordinal) {
      if (ordinal != 0 && !cursor.Consume(',')) {
        return false;
      }
      std::string_view key;
      if (!cursor.ReadString(key) || !cursor.Consume(':')) {
        return false;
      }
      const std::size_t index = FieldIndex(key);
      if (index == kFieldNames.size()) {
        return false;
      }
      const auto field_bit = static_cast<std::uint16_t>(1U << index);
      if ((seen & field_bit) != 0) {
        return false;
      }
      seen = static_cast<std::uint16_t>(seen | field_bit);
      if (index == 0 || index == 2 || index == 3 || index == 4) {
        std::string_view value;
        if (!cursor.ReadString(value)) {
          return false;
        }
        switch (index) {
          case 0:
            if (value != "execute_step") {
              return false;
            }
            break;
          case 2:
            if (value.empty()) {
              return false;
            }
            break;
          case 3:
            if (value != (initiate ? kOrdinaryInteractionInitiateV1Step
                                  : kOrdinaryInteractionQueryV1Step)) {
              return false;
            }
            break;
          case 4:
            if (!IsInteractionKey(value)) {
              return false;
            }
            parsed.interaction_key.assign(value);
            break;
          default:
            return false;
        }
      } else {
        std::uint64_t value = 0;
        if (!cursor.ReadUnsigned(value)) {
          return false;
        }
        switch (index) {
          case 1:
            if (value != 1) {
              return false;
            }
            break;
          case 5:
            if (value == 0 || value >= kInvalidCharacterId) {
              return false;
            }
            parsed.recipient_id = static_cast<std::uint32_t>(value);
            break;
          case 6:
            parsed.expected_revision = value;
            break;
          case 7:
            if (value == 0 || value > static_cast<std::uint64_t>(
                                        std::numeric_limits<std::int32_t>::max())) {
              return false;
            }
            parsed.expected_player_character_id =
                static_cast<std::int32_t>(value);
            break;
          case 8:
            if (value == 0 || value >
                                  std::numeric_limits<std::uint32_t>::max()) {
              return false;
            }
            parsed.expected_game_pid = static_cast<std::uint32_t>(value);
            break;
          case 9:
            parsed.expected_connection_generation = value;
            break;
          default:
            return false;
        }
      }
    }
    if (seen != 0x03ffU || !cursor.Consume('}') || !cursor.AtEnd() ||
        !OrdinaryInteractionRequestValidV1(parsed)) {
      return false;
    }
    output = std::move(parsed);
    return true;
  } catch (...) {
    // Failure to allocate an exact key is an admission failure, never a
    // partially populated request and never an exception across the bridge.
    return false;
  }
}

}  // namespace xar::ck3_12003
