#include "xar_bridge/negotiated_reply_reporter_null_path_12004.hpp"

#include <cstring>
#include <map>
#include <stdexcept>
#include <vector>

namespace xar::ck3_12004 {
namespace {
constexpr std::string_view kPin =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
using Reporter = NegotiatedReplyReporter12004;
using Status = NegotiatedReplyReporterNullPathStatus12004;
void RequireReporter(bool value, const char *message) {
  if (!value) throw std::runtime_error(message);
}
struct Fixture {
  std::map<std::uintptr_t, std::uintptr_t> memory{
      {0x1000, 0x2000}, {0x2000, 0}, {0x1008, 0x3000}, {0x3000, 0}};
  std::vector<std::uintptr_t> reads;
  bool exact_word_reads = true;
  NegotiatedReplyReporterRequest12004 request{Reporter::rva307B910, kPin, 0x1000, 0x100000001ULL};
  static bool Read(void *opaque, std::uintptr_t address, void *out, std::size_t size) noexcept {
    auto &fixture = *static_cast<Fixture *>(opaque);
    fixture.reads.push_back(address);
    fixture.exact_word_reads &= size == sizeof(std::uintptr_t);
    const auto it = fixture.memory.find(address);
    if (!fixture.exact_word_reads || it == fixture.memory.end()) return false;
    std::memcpy(out, &it->second, size); return true;
  }
  NegotiatedReplyReporterNullPath12004 Execute() {
    return ReadNegotiatedReplyReporterNullPath12004(request, Read, this);
  }
};
} // namespace

// No main, no active helper call. Run only in35->10's new connected quote
// compound; do not replay08c actor or previous qualification cases.
int RunNegotiatedReplyReporterNullPath12004NewCases() {
  int count = 0;
  {
    Fixture fixture; const auto out = fixture.Execute();
    RequireReporter(out.no_external_effects && out.null_path_source_closed &&
        out.status == Status::null_branch_no_external_effects &&
        out.slot0_address == 0x2000 && out.slot0_content == 0 &&
        out.slot1_address == 0x3000 && out.slot1_content == 0 &&
        out.frame_key == 0x100000001ULL &&
        fixture.reads == std::vector<std::uintptr_t>{0x1000,0x2000,0x1008,0x3000},
        "307B910 follows actual two-level null slots in original uint64 frame");
    ++count;
  }
  {
    Fixture fixture; fixture.request.reporter = Reporter::rva307BAF0;
    fixture.memory.erase(0x1008); fixture.memory.erase(0x3000);
    const auto out = fixture.Execute();
    RequireReporter(out.no_external_effects && !out.slot1_address && !out.slot1_content &&
        fixture.reads == std::vector<std::uintptr_t>{0x1000,0x2000},
        "307BAF0 null branch never reads second bundle slot");
    ++count;
  }
  for (const auto reporter : {Reporter::rva307B910, Reporter::rva307BAF0}) {
    Fixture fixture; fixture.request.reporter = reporter;
    fixture.memory[0x2000] = 0x4000;
    const auto out = fixture.Execute();
    RequireReporter(!out.no_external_effects && out.status == Status::nonnull_output_branch &&
        !out.slot1_address && fixture.reads.size() == 2,
        "nonnull first output is outside null contract, not guessed no-op");
    ++count;
  }
  {
    Fixture fixture; fixture.memory[0x3000] = 0x5000;
    const auto out = fixture.Execute();
    RequireReporter(!out.no_external_effects && out.status == Status::nonnull_output_branch &&
        out.slot1_content == 0x5000, "307B910 nonnull second output requires output work");
    ++count;
  }
  {
    Fixture fixture; fixture.memory[0x1000] = 0;
    const auto out = fixture.Execute();
    RequireReporter(!out.no_external_effects && out.status == Status::required_slot_address_zero &&
        !out.slot0_content && fixture.reads.size() == 1,
        "zero bundle entry is not a readable zero payload slot");
    ++count;
  }
  {
    Fixture fixture; fixture.memory.erase(0x2000);
    const auto out = fixture.Execute();
    RequireReporter(!out.no_external_effects &&
        out.status == Status::required_slot_content_unavailable,
        "unreadable required slot is unavailable, not fabricated null");
    ++count;
  }
  {
    Fixture fixture; fixture.request.executable_sha256 = "other-image";
    const auto out = fixture.Execute();
    RequireReporter(!out.no_external_effects && !out.null_path_source_closed &&
        fixture.reads.empty(), "unqualified image does not read bundle");
    ++count;
  }
  {
    Fixture fixture; fixture.request.reporter = static_cast<Reporter>(0);
    const auto out = fixture.Execute();
    RequireReporter(!out.no_external_effects && !out.null_path_source_closed &&
        fixture.reads.empty(), "unowned reporter is outside source contract");
    ++count;
  }
  {
    const NegotiatedReplyReporterSuppliedContents12004 input{
        Reporter::rva307B910,
        "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518",
        0x100000001ULL, std::uintptr_t{0}, std::uintptr_t{0}};
    const auto out = ProjectNegotiatedReplyReporterNullContents12004(input);
    RequireReporter(out.no_external_effects && out.contents_supplied &&
        out.output_bundle_receiver == 0 && !out.slot0_address && !out.slot1_address &&
        out.frame_key == input.frame_key,
        "caller source inputs project null effects without inventing native stack addresses");
    ++count;
  }
  {
    NegotiatedReplyReporterSuppliedContents12004 input{
        Reporter::rva307B910, kPin, 7, std::uintptr_t{0}, std::nullopt};
    const auto unavailable = ProjectNegotiatedReplyReporterNullContents12004(input);
    input.reporter = Reporter::rva307BAF0;
    const auto first_only = ProjectNegotiatedReplyReporterNullContents12004(input);
    RequireReporter(!unavailable.no_external_effects &&
        unavailable.status == Status::required_slot_content_unavailable &&
        first_only.no_external_effects && !first_only.slot1_content,
        "missing second content stays unavailable for307B910 and is unused for307BAF0");
    ++count;
  }
  return count;
}
} // namespace xar::ck3_12004
