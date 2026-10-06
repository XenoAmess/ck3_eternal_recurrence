#include "xar_bridge/ck3_12002_realm_law.hpp"
#include "xar_bridge/realm_law_12004_native.hpp"

namespace xar::ck3_12002 {
namespace {
struct CaptureContext {
  const private_law::RealmLawActiveCollectionAccess *access;
  const private_law::RealmLawFinalTerms12002Operations *operations;
  RealmLawReadback12002 *output;
  std::string_view actual_executable_sha256;
};
bool Observe(void *opaque, std::size_t group, std::size_t index,
    std::uintptr_t native_law,
    const private_law::RealmLawCandidateCollectionRow11906 &row) noexcept {
  auto &context = *static_cast<CaptureContext *>(opaque);
  auto &value = context.output->final[group][index];
  const private_law::RealmLawFinalTerms12002Input input{
      reinterpret_cast<const void *>(native_law),
      reinterpret_cast<const void *>(context.access->played_character_address),
      static_cast<std::uint32_t>(context.output->frame.actor_character_id)};
  value = context.actual_executable_sha256 == ck3_12004::kExecutableSha256
      ? ck3_12004::private_law::ReadRealmLawFinalTerms12004(input, *context.operations)
      : private_law::ReadRealmLawFinalTerms12002(input, *context.operations);
  using Status = private_law::RealmLawFinalTerms12002Status;
  if (!value.terms.cost_available || !value.native_reason_available ||
      value.terms.status == Status::unavailable ||
      row.active != (value.terms.status == Status::already_active)) {
    context.output->failure = "native_law_cost_active_or_reason_unavailable";
    return false;
  }
  if (group == 1 && context.output->succession_profiles_12003_observed) {
    context.output->succession_profiles_12003[index] =
        context.actual_executable_sha256 == ck3_12004::kExecutableSha256
            ? ck3_12004::private_law::ReadRealmLawSuccessionProfile12004(
                  *context.access, native_law, context.actual_executable_sha256)
            : ck3_12003::private_law::ReadRealmLawSuccessionProfile12003(
                  *context.access, native_law, context.actual_executable_sha256);
  }
  return true;
}
void AppendString(std::string &out, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  out += '"';
  for (const unsigned char c : value) {
    if (c == '"' || c == '\\') { out += '\\'; out += static_cast<char>(c); }
    else if (c < 0x20) {
      out += "\\u00"; out += hex[c >> 4]; out += hex[c & 15];
    } else out += static_cast<char>(c);
  }
  out += '"';
}
std::string_view Key(const private_law::RealmLawActiveKey &key) noexcept {
  return {key.bytes.data(), key.size};
}
std::string_view Status(private_law::RealmLawFinalTerms12002Status value) noexcept {
  using S = private_law::RealmLawFinalTerms12002Status;
  switch (value) {
  case S::candidate_kind_rejected: return "candidate_kind_rejected";
  case S::already_active: return "already_active";
  case S::engine_blocked: return "engine_blocked";
  case S::can_enact: return "can_enact";
  default: return "unavailable";
  }
}
}

bool CaptureRealmLawReadback12002(
    const private_law::RealmLawActiveCollectionAccess &access,
    std::uintptr_t module_base, const RealmLawReadbackFrame12002 &frame,
    const private_law::RealmLawFinalTerms12002Operations &operations,
    RealmLawReadback12002 &output,
    std::string_view actual_executable_sha256) noexcept {
  try {
    output = {};
    output.frame = frame;
    output.succession_profiles_12003_observed =
        actual_executable_sha256 == ck3_12003::kExecutableSha256 ||
        actual_executable_sha256 == ck3_12004::kExecutableSha256;
    if (frame.snapshot_revision == 0 || frame.actor_character_id <= 0 || module_base == 0) {
      output.failure = "native_law_frame_unavailable"; return false;
    }
    CaptureContext context{&access, &operations, &output,
        actual_executable_sha256};
    const bool collected = actual_executable_sha256 == ck3_12004::kExecutableSha256
        ? ck3_12004::private_law::ReadRealmLawCandidateCollectionWithObserver12004(
              access, module_base, &context, &Observe, output.collection)
        : private_law::ReadRealmLawCandidateCollectionWithObserver12002(
              access, module_base, &context, &Observe, output.collection);
    if (!collected) {
      if (output.failure.empty()) {
        output.failure = "native_law_collection_unavailable:";
        output.failure += private_law::RealmLawCandidateCollectionFailureName(output.collection.failure);
      }
      return false;
    }
    output.available = true;
    return true;
  } catch (...) {
    output.available = false;
    output.failure = "native_law_capture_exception";
    return false;
  }
}

std::string SerializeRealmLawReadback12002(const RealmLawReadback12002 &readback) {
  if (!readback.available || !readback.failure.empty()) return {};
  std::string out = "{\"schema\":\"realm-law-final-terms-private-read-v1\",\"snapshot_revision\":" +
      std::to_string(readback.frame.snapshot_revision) + ",\"date_raw\":" +
      std::to_string(readback.frame.date_raw) + ",\"actor_character_id\":" +
      std::to_string(readback.frame.actor_character_id) +
      ",\"cost_scale\":100000,\"cost_slots\":[\"gold\",\"prestige\",\"piety\",\"renown\",\"influence\",\"herd\",\"treasury\",\"treasury_or_gold\",\"merit\",\"barter_goods\"],\"groups\":[";
  for (std::size_t g = 0; g < readback.collection.groups.size(); ++g) {
    if (g != 0) out += ',';
    const auto &group = readback.collection.groups[g];
    out += "{\"group_key\":"; AppendString(out, Key(group.key));
    out += ",\"active_law_key\":";
    if (group.active_found) AppendString(out, Key(group.active_law_key)); else out += "null";
    out += ",\"candidates\":[";
    for (std::size_t i = 0; i < group.candidate_count; ++i) {
      if (i != 0) out += ',';
      const auto &row = group.candidates[i]; const auto &terms = readback.final[g][i];
      out += "{\"law_key\":"; AppendString(out, Key(row.key));
      out += ",\"active\":"; out += row.active ? "true" : "false";
      out += ",\"final_status\":"; AppendString(out, Status(terms.terms.status));
      out += ",\"final_can_enact\":";
      out += terms.terms.status == private_law::RealmLawFinalTerms12002Status::can_enact ? "true" : "false";
      out += ",\"native_reason\":"; AppendString(out, terms.native_reason);
      out += ",\"cost_raw\":[";
      for (std::size_t slot = 0; slot < terms.terms.cost_raw.size(); ++slot) {
        if (slot != 0) out += ','; out += std::to_string(terms.terms.cost_raw[slot]);
      }
      out += "]";
      if (g == 1 && readback.succession_profiles_12003_observed) {
        ck3_12003::private_law::AppendRealmLawSuccessionProfileFields12003(
            out, readback.succession_profiles_12003[i]);
      }
      out += "}";
    }
    out += "]}";
  }
  return out + "]}";
}
} // namespace xar::ck3_12002
