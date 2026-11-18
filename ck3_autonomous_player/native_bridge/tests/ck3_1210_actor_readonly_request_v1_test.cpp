// SOURCE ONLY. Pure closed-envelope parser; no Game, actor executor or action.
#include "xar_bridge/ck3_1210_actor_readonly_request_v1.hpp"
#include <bit>
#include <cstdlib>
#include <iostream>
#include <string>
using namespace xar::ck3_1210;
namespace {
constexpr std::string_view kStep = "query-character-manager-roster-v1";
void Need(bool value, const char *reason) {
  if (!value) { std::cerr << "FAIL " << reason << char(10); std::exit(1); }
}
std::string Request(std::string_view revision) {
  return R"({"type":"execute_step","protocol_version":1,"request_id":"rq-1","step":"query-character-manager-roster-v1","expected_revision":)" +
    std::string(revision) + '}';
}
std::string Replace(std::string source, std::string_view from, std::string_view to) {
  const auto at = source.find(from); Need(at != std::string::npos, "source fixture anchor");
  source.replace(at, from.size(), to); return source;
}
void Bad(std::string_view raw, ActorReadonlyRevisionV1 policy = ActorReadonlyRevisionV1::positive) {
  ActorReadonlyRequestV1 value{"retained", 999};
  Need(!ParseActorReadonlyRequestV1(raw, kStep, policy, value) &&
    value.request_id == "retained" && value.expected_revision == 999, "reject without partial output mutation");
}
} // namespace
int main() {
  ActorReadonlyRequestV1 value{};
  for (const auto revision : {"1", "9007199254740993", "18446744073709551615"}) {
    Need(ParseActorReadonlyRequestV1(Request(revision), kStep, ActorReadonlyRevisionV1::positive, value),
      "full uint64 NativeWire integer token accepted without float narrowing");
    Need(value.request_id == "rq-1", "original id retained");
    Bad(Request(revision), ActorReadonlyRevisionV1::zero);
  }
  Need(value.expected_revision == 18446744073709551615ULL, "uint64 maximum preserved");
  Need(ParseActorReadonlyRequestV1(Request("0"), kStep, ActorReadonlyRevisionV1::zero, value) &&
    value.expected_revision == 0, "zero-only policy distinct from positive");
  Bad(Request("0"));
  for (const auto token : {"-0", "-1", "+1", "01", "00", "1.0", "1e0", "true", "null",
      "18446744073709551616", "9999999999999999999999999999", "[]", "{}"}) Bad(Request(token));
  Bad(Request(std::string(1, char(34)) + "1" + char(34)));
  const auto base = Request("1");
  for (const auto extra : {R"(,"expected_revision":2)", R"(,"actor_full_id":0)",
      R"(,"expected_connection_generation":1)", R"(,"source":"arbitrary")", R"(,"native_address":1)",
      R"(,"protocol_version":1)", R"(,"request_id":"other")", R"(,"step":"other")"})
    Bad(base.substr(0, base.size() - 1) + extra + '}');
  Bad(base + "true"); Bad(base + "{}"); Bad(base.substr(0, base.size() - 1) + ",}");
  Bad(Replace(base, R"("type":"execute_step",)", ""));
  Bad(Replace(base, R"("protocol_version":1)", R"("protocol_version":true)"));
  Bad(Replace(base, R"("step":"query-character-manager-roster-v1")", R"("step":"other")"));
  Bad(Replace(base, "rq-1", "")); Bad(Replace(base, "rq-1", std::string(129, 'a')));
  // NativeWire.control permits original unescaped UTF-8/spaces. The existing
  // bridge may impose its own narrower outer request-id routing gate.
  std::string original = "rq "; original += std::bit_cast<char>(std::uint8_t{0xE4}); original += std::bit_cast<char>(std::uint8_t{0xB8}); original += std::bit_cast<char>(std::uint8_t{0xAD});
  Need(ParseActorReadonlyRequestV1(Replace(base, "rq-1", original), kStep,
    ActorReadonlyRevisionV1::positive, value) && value.request_id == original, "valid UTF-8 id retained byte-for-byte");
  for (const auto malformed : {std::string(1, std::bit_cast<char>(std::uint8_t{0x80})), std::string{std::bit_cast<char>(std::uint8_t{0xC0}), std::bit_cast<char>(std::uint8_t{0xAF})},
      std::string{std::bit_cast<char>(std::uint8_t{0xED}),std::bit_cast<char>(std::uint8_t{0xA0}),std::bit_cast<char>(std::uint8_t{0x80})}, std::string{std::bit_cast<char>(std::uint8_t{0xE4}),std::bit_cast<char>(std::uint8_t{0xB8})},
      std::string{std::bit_cast<char>(std::uint8_t{0xF4}),std::bit_cast<char>(std::uint8_t{0x90}),std::bit_cast<char>(std::uint8_t{0x80}),std::bit_cast<char>(std::uint8_t{0x80})}, std::string(1, char(1))})
    Bad(Replace(base, "rq-1", malformed));
  Bad(Replace(base, "expected_revision", std::string("expected_") + char(92) + "u0072evision"));
  Bad(Replace(base, "rq-1", std::string("rq") + char(92) + "u0031"));
  Bad(std::string(1025, ' '));
  Need(!ParseActorReadonlyRequestV1(base, "", ActorReadonlyRevisionV1::positive, value), "compiled step is required");
  const auto reordered = R"({"expected_revision":1,"step":"query-character-manager-roster-v1","request_id":"rq-1","protocol_version":1,"type":"execute_step"})";
  Need(ParseActorReadonlyRequestV1(reordered, kStep, ActorReadonlyRevisionV1::positive, value), "field order is not a selector");
  std::cout << "PASS strict five-field readonly request grammar; no owner or capability qualification" << char(10);
}
