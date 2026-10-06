#pragma once

#include "xar_bridge/ck3_12003_readonly_revision.hpp"

#include <cstdint>
#include <limits>
#include <string>
#include <string_view>

// Proposed source only. Include in the existing focused fixture and call
// source_tests::VerifyRevisionParsing(&Check) before invoking its native reader.
namespace xar::ck3_12003::readonly_query::source_tests {

template <typename Check> bool VerifyRevisionParsing(Check check) {
  struct Case { std::string_view json; bool valid; std::uint64_t value; const char *name; };
  constexpr Case cases[] = {
    {R"({"expected_snapshot_revision":1})", true, 1, "canonical revision"},
    {R"({"expected_revision":2})", true, 2, "revision alias"},
    {" \n{\t\"expected_snapshot_revision\" : 42, \"expected_revision\"\r:\t42}\n", true, 42, "whitespace and agreeing aliases"},
    {R"({"expected_revision":18446744073709551615})", true, (std::numeric_limits<std::uint64_t>::max)(), "uint64 maximum"},
    {R"({"expected\u005frevision":9})", true, 9, "escaped equivalent revision key"},
    {R"({"expected_snapshot_revision":7,"other":{"expected_revision":99},"array":[true,false,null,"s",-1.25e+2]})", true, 7, "complete unrelated envelope values"},
    {R"({"other":{"expected_snapshot_revision":9},"expected_revision":3})", true, 3, "nested revision cannot override top-level"},
    {R"({"expected_revision":1,"other":"\uD83D\uDE00"})", true, 1, "paired surrogate in unrelated value"},
    {R"({"expected_revision":1,"other":"\"\\\/\b\f\n\r\t"})", true, 1, "JSON string escapes"},
    {R"({})", false, 0, "missing revision"},
    {R"({"expected_revision":0})", false, 0, "zero revision"},
    {R"({"expected_snapshot_revision":0,"expected_revision":1})", false, 0, "zero canonical cannot fall back to alias"},
    {R"({"expected_revision":-1})", false, 0, "negative revision"},
    {R"({"expected_revision":1.0})", false, 0, "fraction is not uint64 lexical form"},
    {R"({"expected_revision":1e0})", false, 0, "exponent is not uint64 lexical form"},
    {R"({"expected_revision":"1"})", false, 0, "quoted revision"},
    {R"({"expected_revision":null})", false, 0, "null revision"},
    {R"({"expected_snapshot_revision":4,"expected_revision":5})", false, 0, "alias mismatch"},
    {R"({"expected_snapshot_revision":4,"expected_snapshot_revision":4})", false, 0, "duplicate canonical even when equal"},
    {R"({"expected_revision":4,"expected_revision":5})", false, 0, "duplicate alias"},
    {R"({"expected_revision":4,"expected\u005frevision":4})", false, 0, "escaped duplicate alias"},
    {R"({"expected_snapshot_revision":4,"expected_snapshot\u005frevision":4})", false, 0, "escaped duplicate canonical"},
    {R"({"other":{"expected_snapshot_revision":4}})", false, 0, "nested-only canonical"},
    {R"({"other":[{"expected_revision":4}]})", false, 0, "nested-only alias in array"},
    {R"({"expected_revision":18446744073709551616})", false, 0, "uint64 overflow"},
    {R"({"expected_revision":01})", false, 0, "leading zero"},
    {R"({"expected_revision":1)", false, 0, "truncated root"},
    {R"({"expected_revision":1,"other":"unfinished})", false, 0, "truncated string"},
    {R"({"expected_revision":1,"other":[1,2})", false, 0, "mismatched array close"},
    {R"({"expected_revision":1,"other":nul})", false, 0, "invalid literal"},
    {R"({"expected_revision":1,"other":1e+})", false, 0, "truncated exponent"},
    {R"({"expected_revision":1,"other":+2})", false, 0, "invalid number sign"},
    {R"({"expected_revision":1,"other":"\x41"})", false, 0, "invalid string escape"},
    {R"({"expected_revision":1,"other":"\uD800"})", false, 0, "unpaired surrogate"},
    {R"({"expected_revision":1,})", false, 0, "trailing object comma"},
    {R"({"expected_revision":1,"other":[0,]})", false, 0, "trailing array comma"},
    {R"({expected_revision:1})", false, 0, "unquoted key"},
    {R"([{"expected_revision":1}])", false, 0, "root must be object"},
    {R"({"expected_revision":1} {})", false, 0, "trailing JSON object"},
  };
  for (const auto &row : cases) {
    std::uint64_t revision = 999;
    const bool valid = ParseUniqueTopLevelRevision(row.json, revision);
    if (!check(valid == row.valid && revision == row.value, row.name)) return false;
  }
  for (unsigned arrays = 63; arrays != 65; ++arrays) {
    std::string json = "{\"expected_revision\":1,\"other\":";
    json.append(arrays, '['); json += '0'; json.append(arrays, ']'); json += '}';
    std::uint64_t revision = 999;
    const bool valid = ParseUniqueTopLevelRevision(json, revision);
    if (!check(valid == (arrays == 63U) && revision == (arrays == 63U ? 1U : 0U),
        arrays == 63U ? "64-container depth accepted" : "65-container depth rejected")) return false;
  }
  std::string control = "{\"expected_revision\":1,\"other\":\"";
  control += '\n'; control += "\"}";
  std::uint64_t revision = 999;
  if (!check(!ParseUniqueTopLevelRevision(control, revision) && revision == 0,
      "raw string control rejected")) return false;
  std::string utf8 = "{\"expected_revision\":1,\"other\":\"";
  utf8 += static_cast<char>(0xC0); utf8 += static_cast<char>(0xAF); utf8 += "\"}";
  revision = 999;
  return check(!ParseUniqueTopLevelRevision(utf8, revision) && revision == 0,
      "overlong UTF-8 rejected");
}

} // namespace xar::ck3_12003::readonly_query::source_tests
