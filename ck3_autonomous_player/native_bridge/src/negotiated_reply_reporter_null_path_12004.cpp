#include "xar_bridge/negotiated_reply_reporter_null_path_12004.hpp"

#include <limits>

namespace xar::ck3_12004 {
namespace {
constexpr std::string_view kActualExecutableSha256 =
    "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
constexpr std::string_view kActualExecutableSha256Lower =
    "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518";
using Status = NegotiatedReplyReporterNullPathStatus12004;

bool SourceReady(NegotiatedReplyReporter12004 reporter, std::string_view sha) noexcept {
  return (sha == kActualExecutableSha256 || sha == kActualExecutableSha256Lower) &&
      (reporter == NegotiatedReplyReporter12004::rva307B910 ||
       reporter == NegotiatedReplyReporter12004::rva307BAF0);
}

bool ReadWord(NegotiatedReplyReporterReadMemory12004 read, void *context,
              std::uintptr_t address, std::uintptr_t &out) noexcept {
  return address && address <= (std::numeric_limits<std::uintptr_t>::max)() - sizeof(out) &&
      read && read(context, address, &out, sizeof(out));
}

bool Slot(const NegotiatedReplyReporterRequest12004 &request,
          NegotiatedReplyReporterReadMemory12004 read, void *context,
          std::size_t offset, std::optional<std::uintptr_t> &address,
          std::optional<std::uintptr_t> &content,
          NegotiatedReplyReporterNullPath12004 &out) noexcept {
  if (!request.output_bundle_receiver || offset >
      (std::numeric_limits<std::uintptr_t>::max)() - request.output_bundle_receiver) {
    out.status = Status::bundle_unavailable; return false;
  }
  std::uintptr_t pointer = 0;
  if (!ReadWord(read, context, request.output_bundle_receiver+offset, pointer)) {
    out.status = Status::bundle_unavailable; return false;
  }
  address = pointer;
  if (!pointer) {
    out.status = Status::required_slot_address_zero; return false;
  }
  std::uintptr_t value = 0;
  if (!ReadWord(read, context, pointer, value)) {
    out.status = Status::required_slot_content_unavailable; return false;
  }
  content = value;
  return true;
}
} // namespace

NegotiatedReplyReporterNullPath12004 ReadNegotiatedReplyReporterNullPath12004(
    const NegotiatedReplyReporterRequest12004 &request,
    NegotiatedReplyReporterReadMemory12004 read, void *context) noexcept {
  NegotiatedReplyReporterNullPath12004 out;
  out.reporter = request.reporter;
  out.output_bundle_receiver = request.output_bundle_receiver;
  out.frame_key = request.frame_key;
  if (!SourceReady(request.reporter, request.executable_sha256)) return out;
  out.null_path_source_closed = true;
  if (!Slot(request, read, context, 0, out.slot0_address, out.slot0_content, out))
    return out;
  if (*out.slot0_content) {
    out.status = Status::nonnull_output_branch; return out;
  }
  if (request.reporter == NegotiatedReplyReporter12004::rva307B910) {
    if (!Slot(request, read, context, 8, out.slot1_address, out.slot1_content, out))
      return out;
    if (*out.slot1_content) {
      out.status = Status::nonnull_output_branch; return out;
    }
  }
  out.status = Status::null_branch_no_external_effects;
  out.no_external_effects = true;
  return out;
}

NegotiatedReplyReporterNullPath12004 ProjectNegotiatedReplyReporterNullContents12004(
    const NegotiatedReplyReporterSuppliedContents12004 &input) noexcept {
  NegotiatedReplyReporterNullPath12004 out;
  out.reporter = input.reporter;
  out.frame_key = input.frame_key;
  out.contents_supplied = true;
  if (!SourceReady(input.reporter, input.executable_sha256)) return out;
  out.null_path_source_closed = true;
  out.slot0_content = input.slot0_content;
  if (!input.slot0_content) {
    out.status = Status::required_slot_content_unavailable; return out;
  }
  if (*input.slot0_content) {
    out.status = Status::nonnull_output_branch; return out;
  }
  if (input.reporter == NegotiatedReplyReporter12004::rva307B910) {
    out.slot1_content = input.slot1_content;
    if (!input.slot1_content) {
      out.status = Status::required_slot_content_unavailable; return out;
    }
    if (*input.slot1_content) {
      out.status = Status::nonnull_output_branch; return out;
    }
  }
  out.status = Status::null_branch_no_external_effects;
  out.no_external_effects = true;
  return out;
}
} // namespace xar::ck3_12004
