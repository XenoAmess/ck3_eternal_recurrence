// Standalone closed-payload parser fixture. No GameAdapter, GUI or mailbox execution.
#include "xar_bridge/war_declared_overview_v1.hpp"

#include <cstdint>
#include <iostream>
#include <iterator>
#include <limits>
#include <string>
#include <string_view>
#include <vector>

namespace {
struct Case {
  std::string_view name;
  std::string_view payload;
  bool accepted;
  std::uint64_t revision;
};

constexpr char kEmbeddedNul[] = "{\"expected_revision\":1}\0trailing";
constexpr Case cases[] = {
    {"zero is syntactically unsigned; Prepare owns positive gate", R"({"expected_revision":0})", true, 0},
    {"one", R"({"expected_revision":1})", true, 1},
    {"uint32 high bit", R"({"expected_revision":2147483648})", true, 2147483648ULL},
    {"above uint32", R"({"expected_revision":4294967296})", true, 4294967296ULL},
    {"uint64 maximum", R"({"expected_revision":18446744073709551615})", true,
        std::numeric_limits<std::uint64_t>::max()},
    {"JSON ASCII whitespace", " \t\r\n{ \n\"expected_revision\" \t: \r42\n }\t\r\n ", true, 42},
    {"empty", "", false, 0},
    {"missing member", "{}", false, 0},
    {"non-object", "1", false, 0},
    {"top-level array", R"([{"expected_revision":1}])", false, 0},
    {"true", R"({"expected_revision":true})", false, 0},
    {"false", R"({"expected_revision":false})", false, 0},
    {"null", R"({"expected_revision":null})", false, 0},
    {"string", R"({"expected_revision":"1"})", false, 0},
    {"decimal", R"({"expected_revision":1.0})", false, 0},
    {"exponent", R"({"expected_revision":1e0})", false, 0},
    {"negative", R"({"expected_revision":-1})", false, 0},
    {"negative spaced", R"({"expected_revision":- 1})", false, 0},
    {"positive sign", R"({"expected_revision":+1})", false, 0},
    {"hex", R"({"expected_revision":0x1})", false, 0},
    {"leading zero", R"({"expected_revision":01})", false, 0},
    {"double zero", R"({"expected_revision":00})", false, 0},
    {"split digits", R"({"expected_revision":1 2})", false, 0},
    {"uint64 overflow", R"({"expected_revision":18446744073709551616})", false, 0},
    {"long overflow", R"({"expected_revision":9999999999999999999999999999999999999999})", false, 0},
    {"duplicate key", R"({"expected_revision":1,"expected_revision":2})", false, 0},
    {"extra target", R"({"expected_revision":1,"target":1})", false, 0},
    {"extra pointer", R"({"expected_revision":1,"address":4096})", false, 0},
    {"extra fixed window selector", R"({"expected_revision":1,"window_name":"war_declared_overview"})", false, 0},
    {"operation injection", R"({"operation":"close","expected_revision":1})", false, 0},
    {"nested value", R"({"expected_revision":{"expected_revision":1}})", false, 0},
    {"nested foreign object", R"({"foreign":{"expected_revision":1}})", false, 0},
    {"escaped member", R"({"ex\u0070ected_revision":1})", false, 0},
    {"wrong member case", R"({"Expected_revision":1})", false, 0},
    {"missing colon", R"({"expected_revision" 1})", false, 0},
    {"missing value", R"({"expected_revision":})", false, 0},
    {"missing close", R"({"expected_revision":1)", false, 0},
    {"trailing comma", R"({"expected_revision":1,})", false, 0},
    {"trailing object", R"({"expected_revision":1}{})", false, 0},
    {"trailing text", R"({"expected_revision":1}true)", false, 0},
    {"embedded NUL", std::string_view(kEmbeddedNul, sizeof(kEmbeddedNul)-1), false, 0},
    {"non-JSON whitespace", "\xC2\xA0{\"expected_revision\":1}", false, 0},
};

constexpr std::string_view kRequest = "unit-query-1";
constexpr std::string_view kQuery = "query-war-declared-overview-v1";
constexpr std::string_view kClose = "close-war-declared-overview-v1";

std::string Wire(std::string_view revision, std::string_view request=kRequest,
                 std::string_view step=kQuery) {
  return "{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\"" +
      std::string(request) + "\",\"step\":\"" + std::string(step) +
      "\",\"expected_revision\":" + std::string(revision) + "}";
}

struct WireCase {
  std::string name;
  std::string payload;
  std::string_view request = kRequest;
  std::string_view step = kQuery;
  bool accepted = false;
  std::uint64_t revision = 0;
};

std::vector<WireCase> WireCases() {
  const auto valid = Wire("17");
  std::vector<WireCase> tests{
      {"actual SDK query five-key envelope", valid, kRequest, kQuery, true, 17},
      {"actual SDK close five-key envelope", Wire("18",kRequest,kClose), kRequest,kClose,true,18},
      {"outer unsigned zero", Wire("0"), kRequest,kQuery,true,0},
      {"outer uint64 maximum", Wire("18446744073709551615"), kRequest,kQuery,true,
          std::numeric_limits<std::uint64_t>::max()},
      {"outer any key order", R"({"expected_revision":17,"step":"query-war-declared-overview-v1","request_id":"unit-query-1","protocol_version":1,"type":"execute_step"})",kRequest,kQuery,true,17},
      {"outer ASCII whitespace", " \t\n"+valid+"\r\n ",kRequest,kQuery,true,17},
      {"original one-key payload is not wire", R"({"expected_revision":17})"},
      {"request mismatch", valid, "another-request"},
      {"query-vs-close mismatch", valid, kRequest,kClose},
      {"foreign step even if expected matches", Wire("17",kRequest,"life-advance"),kRequest,"life-advance"},
      {"empty request", Wire("17",""),""},
      {"nested foreign injection", valid.substr(0,valid.size()-1)+R"(,"foreign":{"expected_revision":17}})"},
      {"extra key", valid.substr(0,valid.size()-1)+R"(,"address":4096})"},
      {"trailing second frame", valid+valid},
      {"trailing non-whitespace", valid+"true"},
      {"escaped request value", Wire("17",R"(unit-query-\u0031)")},
      {"escaped member name", R"({"ty\u0070e":"execute_step","protocol_version":1,"request_id":"unit-query-1","step":"query-war-declared-overview-v1","expected_revision":17})"},
      {"control request value", Wire("17","unit-query-\n1"),"unit-query-\n1"},
      {"non-ASCII request", Wire("17","unit-query-\xC3\xA9"),"unit-query-\xC3\xA9"},
  };
  const std::string fields[] = {
      R"("type":"execute_step")", R"("protocol_version":1)",
      R"("request_id":"unit-query-1")", R"("step":"query-war-declared-overview-v1")",
      R"("expected_revision":17)",
  };
  for (std::size_t missing=0; missing<std::size(fields); ++missing) {
    std::string payload = "{";
    for (std::size_t index=0; index<std::size(fields); ++index) {
      if (index==missing) continue;
      if (payload.size()>1) payload += ',';
      payload += fields[index];
    }
    tests.push_back({"missing mandatory field "+std::to_string(missing),payload+"}"});
    tests.push_back({"duplicate mandatory field "+std::to_string(missing),
        valid.substr(0,valid.size()-1)+","+fields[missing]+"}"});
  }
  const std::string revision_tokens[] = {"true","false","null","\"17\"","17.0","17e0",
      "-17","+17","017","17 2","18446744073709551616","{}","[]"};
  for (const auto &token:revision_tokens)
    tests.push_back({"outer invalid revision "+token,Wire(token)});
  const std::string bad_protocol[] = {"true","\"1\"","1.0","01","2","{}"};
  for (const auto &token:bad_protocol) {
    const auto pos = valid.find("\"protocol_version\":1");
    auto payload = valid;
    payload.replace(pos,std::string_view("\"protocol_version\":1").size(),"\"protocol_version\":"+token);
    tests.push_back({"outer invalid protocol "+token,payload});
  }
  auto wrong_type = valid;
  const auto type_pos = wrong_type.find("execute_step");
  wrong_type.replace(type_pos,std::string_view("execute_step").size(),"command_result");
  tests.push_back({"wrong message type",wrong_type});
  tests.push_back({"4096-byte complete frame",valid+std::string(4096-valid.size(),' '),kRequest,kQuery,true,17});
  tests.push_back({"4097-byte frame rejected",valid+std::string(4097-valid.size(),' ')});
  auto nul = valid;
  nul.push_back('\0');
  tests.push_back({"outer embedded NUL",nul});
  static const std::string request129(129,'a');
  static const std::string request128(128,'a');
  tests.push_back({"request length128",Wire("17",request128),request128,kQuery,true,17});
  tests.push_back({"request length129",Wire("17",request129),request129});
  return tests;
}
} // namespace

int main() {
  unsigned failures = 0;
  unsigned assertions = 0;
  for (const auto &test : cases) {
    std::uint64_t revision = 777;
    const bool accepted = xar::ck3_11906::ParseWarDeclaredExpectedRevisionV1(test.payload, revision);
    assertions += 2;
    if (accepted != test.accepted || revision != test.revision) {
      ++failures;
      std::cerr << "FAIL " << test.name << ": accepted=" << accepted
                << ", revision=" << revision << '\n';
    }
  }
  const auto wire_cases = WireCases();
  for (const auto &test:wire_cases) {
    std::uint64_t revision = 777;
    const bool accepted = xar::ck3_11906::ParseWarDeclaredRequestV1(
        test.payload,test.request,test.step,revision);
    assertions += 2;
    if (accepted != test.accepted || revision != test.revision) {
      ++failures;
      std::cerr << "FAIL " << test.name << ": accepted=" << accepted
                << ", revision=" << revision << '\n';
    }
  }
  std::cout << "cases=" << std::size(cases) << " assertions=" << assertions
            << " whole_wire_cases=" << wire_cases.size()
            << " failures=" << failures << " scope=internal_and_actual_whole_wire_parser_only\n";
  return failures ? 1 : 0;
}
