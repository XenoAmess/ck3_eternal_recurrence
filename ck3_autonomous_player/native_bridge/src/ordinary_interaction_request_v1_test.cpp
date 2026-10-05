#include "xar_bridge/ordinary_interaction_request_v1.hpp"

#include <algorithm>
#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <string>
#include <string_view>

namespace {
using xar::ck3_12003::OrdinaryInteractionRequestV1;
using xar::ck3_12003::ParseOrdinaryInteractionRequestV1;

using Fields = std::array<std::string, 10>;
std::size_t checks = 0;
std::size_t failures = 0;

Fields BaseFields(bool initiate) {
  const std::string_view step =
      initiate ? xar::ck3_12003::kOrdinaryInteractionInitiateV1Step
               : xar::ck3_12003::kOrdinaryInteractionQueryV1Step;
  return {"\"type\":\"execute_step\"", "\"protocol_version\":1",
          "\"request_id\":\"python-execute-17\"",
          "\"step\":\"" + std::string(step) + "\"",
          "\"interaction_key\":\"Ask_Confucian_Review_17\"",
          "\"recipient_id\":2147483650", "\"expected_revision\":41",
          "\"expected_player_character_id\":16777219",
          "\"expected_game_pid\":10992",
          "\"expected_connection_generation\":9"};
}

std::string Object(const Fields &fields) {
  std::string json = "{";
  for (std::size_t index = 0; index < fields.size(); ++index) {
    if (index != 0) {
      json += ',';
    }
    json += fields[index];
  }
  return json + '}';
}

std::string WithValue(bool initiate, std::size_t index, std::string_view value) {
  Fields fields = BaseFields(initiate);
  fields[index].resize(fields[index].find(':') + 1U);
  fields[index] += value;
  return Object(fields);
}

void Check(bool passed, std::string_view name) {
  ++checks;
  if (!passed) {
    ++failures;
    std::cerr << "FAIL " << name << '\n';
  }
}

bool Same(const OrdinaryInteractionRequestV1 &a,
          const OrdinaryInteractionRequestV1 &b) {
  return a.interaction_key == b.interaction_key &&
         a.recipient_id == b.recipient_id &&
         a.expected_revision == b.expected_revision &&
         a.expected_player_character_id == b.expected_player_character_id &&
         a.expected_game_pid == b.expected_game_pid &&
         a.expected_connection_generation == b.expected_connection_generation;
}

void Reject(std::string_view name, std::string_view json, bool initiate) {
  OrdinaryInteractionRequestV1 output{"Unchanged", 2, 3, 4, 5, 6};
  const OrdinaryInteractionRequestV1 before = output;
  Check(!ParseOrdinaryInteractionRequestV1(json, initiate, output), name);
  Check(Same(output, before), std::string(name) + ":transactional output");
}

void Accept(std::string_view name, std::string_view json, bool initiate,
            std::uint32_t expected_id = 0x80000002U) {
  OrdinaryInteractionRequestV1 output;
  Check(ParseOrdinaryInteractionRequestV1(json, initiate, output), name);
  Check(output.recipient_id == expected_id,
        std::string(name) + ":full recipient preserved");
  Check(output.interaction_key == "Ask_Confucian_Review_17",
        std::string(name) + ":exact key preserved");
}

void TestStep(bool initiate) {
  const std::string label = initiate ? "initiate:" : "query:";
  const Fields base = BaseFields(initiate);
  const std::string canonical = Object(base);
  Accept(label + "production compact request", canonical, initiate);

  Fields reverse = base;
  std::reverse(reverse.begin(), reverse.end());
  Accept(label + "arbitrary field order", Object(reverse), initiate);
  std::string whitespace = " \r\n{\t";
  for (std::size_t index = 0; index < base.size(); ++index) {
    if (index != 0) {
      whitespace += " ,\r\n";
    }
    std::string field = base[index];
    field.insert(field.find(':') + 1U, " \t");
    whitespace += field;
  }
  whitespace += " \n}\r\n ";
  Accept(label + "all standard JSON whitespace", whitespace, initiate);

  Accept(label + "recipient generation FE",
         WithValue(initiate, 5, "4261412866"), initiate, 0xfe000002U);
  Accept(label + "recipient maximum",
         WithValue(initiate, 5, "4294967294"), initiate, 0xfffffffeU);
  Accept(label + "recipient minimum", WithValue(initiate, 5, "1"), initiate, 1);
  OrdinaryInteractionRequestV1 generation_a;
  OrdinaryInteractionRequestV1 generation_b;
  Check(ParseOrdinaryInteractionRequestV1(canonical, initiate, generation_a) &&
            ParseOrdinaryInteractionRequestV1(
                WithValue(initiate, 5, "4261412866"), initiate, generation_b) &&
            (generation_a.recipient_id & 0x00ffffffU) ==
                (generation_b.recipient_id & 0x00ffffffU) &&
            generation_a.recipient_id != generation_b.recipient_id,
        label + "equal low24 preserves different generations");

  Fields maximums = base;
  maximums[6] = "\"expected_revision\":18446744073709551615";
  maximums[7] = "\"expected_player_character_id\":2147483647";
  maximums[8] = "\"expected_game_pid\":4294967295";
  maximums[9] = "\"expected_connection_generation\":18446744073709551615";
  OrdinaryInteractionRequestV1 output;
  Check(ParseOrdinaryInteractionRequestV1(Object(maximums), initiate, output) &&
            output.expected_revision == std::numeric_limits<std::uint64_t>::max() &&
            output.expected_player_character_id ==
                std::numeric_limits<std::int32_t>::max() &&
            output.expected_game_pid == std::numeric_limits<std::uint32_t>::max() &&
            output.expected_connection_generation ==
                std::numeric_limits<std::uint64_t>::max(),
        label + "numeric upper bounds exact");

  for (std::size_t index = 0; index < base.size(); ++index) {
    std::string missing = "{";
    for (std::size_t field = 0; field < base.size(); ++field) {
      if (field == index) {
        continue;
      }
      if (missing.size() != 1) {
        missing += ',';
      }
      missing += base[field];
    }
    missing += '}';
    Reject(label + "missing field " + std::to_string(index), missing, initiate);
    Fields duplicate = base;
    duplicate[(index + 1U) % base.size()] = base[index];
    Reject(label + "duplicate among ten fields " + std::to_string(index),
           Object(duplicate), initiate);
  }

  Reject(label + "eleventh address field",
         canonical.substr(0, canonical.size() - 1U) +
             ",\"native_address\":123456}", initiate);
  Fields unknown = base;
  unknown[6] = "\"revision_alias\":41";
  Reject(label + "unknown substituted field", Object(unknown), initiate);
  unknown[6] = "\"expected_\\u0072evision\":41";
  Reject(label + "escaped field name", Object(unknown), initiate);
  Reject(label + "wrong step selection", canonical, !initiate);
  Reject(label + "wrong type", WithValue(initiate, 0, "\"hello\""), initiate);
  Reject(label + "wrong protocol", WithValue(initiate, 1, "2"), initiate);

  constexpr std::array<std::size_t, 6> numeric_fields{1, 5, 6, 7, 8, 9};
  constexpr std::array<std::string_view, 22> bad_numbers{
      "true", "false", "null", "\"1\"", "[]", "{}", "-1", "+1", "01",
      "00", "1.0", "1e0", "1E+0", ".1", "0x1", "NaN", "Infinity",
      "1 1", "1/**/", "1a", "18446744073709551616", ""};
  for (const std::size_t field : numeric_fields) {
    Reject(label + "zero field " + std::to_string(field),
           WithValue(initiate, field, "0"), initiate);
    for (const std::string_view bad : bad_numbers) {
      Reject(label + "numeric lexical field " + std::to_string(field) +
                 " value=" + std::string(bad),
             WithValue(initiate, field, bad), initiate);
    }
  }
  Reject(label + "recipient sentinel", WithValue(initiate, 5, "4294967295"), initiate);
  Reject(label + "recipient uint32 overflow", WithValue(initiate, 5, "4294967296"), initiate);
  Reject(label + "actor signed overflow", WithValue(initiate, 7, "2147483648"), initiate);
  Reject(label + "pid uint32 overflow", WithValue(initiate, 8, "4294967296"), initiate);

  constexpr std::array<std::size_t, 4> string_fields{0, 2, 3, 4};
  constexpr std::array<std::string_view, 8> bad_strings{
      "true", "1", "null", "[]", "{}", "'a'", "\"\\u0041\"", "\"A\\\"B\""};
  for (const std::size_t field : string_fields) {
    for (const std::string_view bad : bad_strings) {
      Reject(label + "string lexical field " + std::to_string(field),
             WithValue(initiate, field, bad), initiate);
    }
  }
  Reject(label + "empty request id", WithValue(initiate, 2, "\"\""), initiate);
  Reject(label + "request id over bound",
         WithValue(initiate, 2, '"' + std::string(129, 'x') + '"'), initiate);
  Accept(label + "request id exact bound",
         WithValue(initiate, 2, '"' + std::string(128, 'x') + '"'), initiate);
  Reject(label + "request id raw newline",
         WithValue(initiate, 2, "\"line\nbreak\""), initiate);
  Reject(label + "request id non ASCII",
         WithValue(initiate, 2, "\"\xc3\xa9\""), initiate);
  for (const std::string_view bad_key : {"", "with-space", "with space", "dot.key",
                                        "slash/key", "colon:key", "a\\b"}) {
    Reject(label + "invalid key " + std::string(bad_key),
           WithValue(initiate, 4, '"' + std::string(bad_key) + '"'), initiate);
  }
  Reject(label + "key non ASCII", WithValue(initiate, 4, "\"\xe4\xb8\xad\""), initiate);
  Reject(label + "key over bound",
         WithValue(initiate, 4, '"' + std::string(129, 'A') + '"'), initiate);
  Check(ParseOrdinaryInteractionRequestV1(
            WithValue(initiate, 4, '"' + std::string(128, 'A') + '"'), initiate, output) &&
            output.interaction_key == std::string(128, 'A'), label + "key exact bound");

  Reject(label + "empty document", "", initiate);
  Reject(label + "array envelope", '[' + canonical + ']', initiate);
  Reject(label + "empty object", "{}", initiate);
  Reject(label + "trailing comma", canonical.substr(0, canonical.size() - 1U) + ",}", initiate);
  Reject(label + "trailing object", canonical + "{}", initiate);
  Reject(label + "trailing garbage", canonical + "x", initiate);
  Reject(label + "missing final brace", canonical.substr(0, canonical.size() - 1U), initiate);
  std::string bad = canonical;
  bad[bad.find(':')] = '=';
  Reject(label + "bad colon", bad, initiate);
  bad = canonical;
  bad.erase(bad.find(','), 1);
  Reject(label + "missing comma", bad, initiate);
  bad = canonical;
  bad.insert(1, "\v");
  Reject(label + "non JSON whitespace", bad, initiate);
  bad = canonical;
  bad.push_back('\0');
  Reject(label + "embedded trailing NUL", bad, initiate);
}

int ParseFile(std::string_view mode, const char *path) {
  if (mode != "query" && mode != "initiate") {
    std::cerr << "mode must be query or initiate\n";
    return 2;
  }
  std::ifstream stream(path, std::ios::binary);
  if (!stream) {
    std::cerr << "request file could not be opened\n";
    return 2;
  }
  const std::string json((std::istreambuf_iterator<char>(stream)),
                         std::istreambuf_iterator<char>());
  OrdinaryInteractionRequestV1 output;
  if (!ParseOrdinaryInteractionRequestV1(json, mode == "initiate", output)) {
    std::cout << "{\"accepted\":false,\"reason\":\"invalid_closed_request\"}\n";
    return 1;
  }
  std::cout << "{\"accepted\":true,\"interaction_key\":\"" << output.interaction_key
            << "\",\"recipient_id\":" << output.recipient_id
            << ",\"expected_revision\":" << output.expected_revision
            << ",\"expected_player_character_id\":" << output.expected_player_character_id
            << ",\"expected_game_pid\":" << output.expected_game_pid
            << ",\"expected_connection_generation\":" << output.expected_connection_generation
            << "}\n";
  return 0;
}
}  // namespace

int main(int argc, char **argv) {
  if (argc == 4 && std::string_view(argv[1]) == "--parse-file") {
    return ParseFile(argv[2], argv[3]);
  }
  if (argc != 1) {
    std::cerr << "usage: ordinary-parser.exe [--parse-file query|initiate REQUEST.json]\n";
    return 2;
  }
  TestStep(false);
  TestStep(true);
  OrdinaryInteractionRequestV1 invalid;
  Check(!xar::ck3_12003::OrdinaryInteractionRequestValidV1(invalid), "default DTO invalid");
  std::cout << "ordinary interaction production parser: " << checks << " checks, "
            << failures << " failures\n";
  return failures == 0 ? 0 : 1;
}
