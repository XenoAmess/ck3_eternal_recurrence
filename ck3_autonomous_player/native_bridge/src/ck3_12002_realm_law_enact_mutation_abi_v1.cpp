#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <bcrypt.h>

#include "xar_bridge/ck3_12002_realm_law_enact_mutation_abi_v1.hpp"

#include <array>
#include <cstring>
#include <limits>
#include <vector>

#pragma comment(lib, "bcrypt.lib")

namespace xar::ck3_12002::private_law {
namespace {

struct SpanEvidence {
  const char *name;
  std::uintptr_t rva;
  std::size_t size;
  const char *sha256;
};

// Data vtables contain relocated pointers in a live image, so they are checked
// entry-by-entry below. Only relocation-stable instruction bytes are hashed.
constexpr std::array<SpanEvidence, 17> kSpans{{
    {"popup_confirm_add_law_submit", 0x41d49c0, 0x57,
     "4A220AF435629A4640699DCCE8215331E49F380D7C885A1C278BFEFACC6D0E74"},
    {"popup_can_confirm", 0x41d4a20, 0x9b,
     "29E7686159CC2354945F09DB9B8480EB1F4CDEA4ACA113285D58CC3CA3A9D1DD"},
    {"engine_final_law_evaluator", 0x30b1b70, 0x16d,
     "B455916F55006AC77C69D4232383D6E0793B24883A7F26993A3F2E1490FADE91"},
    {"engine_final_command_validator", 0x30b1ce0, 0x135,
     "D15A328BC170FFF6B7BE0C2B8B8F084315DCC9354E5492F68C0B7D9A4EE741DF"},
    {"add_law_command_executor", 0x288d9b0, 0x89,
     "203CE00F45D17999F743520CF43A140A847151271D58805A66EFDC630D6C3B66"},
    {"add_law_command_validator_adapter", 0x288da40, 0x4e,
     "F8450F331DE36FFE76712F0FC483B83789EE2E00CB3BA0FAAABF99ECA2ACA6B8"},
    {"add_law_command_heap_clone", 0x2896230, 0x7c,
     "BCDB56996055EB07E5B949821A282A5C9D569401C2998EC5333CDDCB4C6C6BC3"},
    {"add_law_command_class_key", 0x28962b0, 0x6,
     "A3E5408F5F55BE0748CD4AAF0E6B33C439B4C69719D5DCE93911B1D4F40730B5"},
    {"add_law_command_serializer", 0x288da90, 0x9f,
     "F68077E743B70FDCEA711CEFA0468CE89531B2A62A4B611EFFE3BDEB747B7210"},
    {"add_law_command_deserializer", 0x288db30, 0xc9,
     "BE5BE1D997306E61D6E25AD4F0E324E69F3F133F74293DBA5FBA18A620301A17"},
    {"gui_submit_clone_and_queue_void_wrapper", 0x9e16b0, 0x78,
     "5048D599B10A65E292FC7C179CF2516943FEC8CBB30D29D73BEEA4844C828C18"},
    {"locked_command_queue", 0x37f06f0, 0xfa,
     "535C67B33DA7E1CDB8F1838476B2064A6DD4C09EF3EFCEDA33E5E9D28D34A2BE"},
    {"law_mutation_context_constructor", 0x28a94f0, 0x9f,
     "0EA47055418DBD8CB069FE99B499C2290C94FB3AD4972B0D8B60744335019296"},
    {"law_mutation_select_group", 0x28a96e0, 0xa8,
     "23825069C72071F85A263B8DA0BEEE6C93E5774DDA6DF1D9164EDAC53FB43C6E"},
    {"law_mutation_apply_logical_span", 0x28a9790, 0x1ba,
     "8994A58664734C4658DCE70139831356E37F21D72ED0C574D8C06F2032029B44"},
    {"law_mutation_finalizer", 0x28a9590, 0x14e,
     "F8BF78D21B620DA92594FAE6E0D0EE288DFA0A402FD93063A1061F68BEA42EE3"},
    {"add_law_command_destructor", 0x9d1560, 0x2b,
     "B366E6937D2ABABA61AAC02C64B2AE8373DB5D2CAE01E0119C700A11F27C9235"},
}};

struct RelativeEdgeEvidence {
  const char *name;
  std::uintptr_t instruction_rva;
  std::uint32_t instruction_size;
  std::uint32_t displacement_offset;
  std::uintptr_t target_rva;
};

constexpr std::array<RelativeEdgeEvidence, 12> kRelativeEdges{{
    {"confirm_primary_vtable", 0x41d49db, 7, 3, 0x47600f8},
    {"confirm_secondary_vtable", 0x41d49e7, 7, 3, 0x4760190},
    {"confirm_calls_void_wrapper", 0x41d4a0c, 5, 1, 0x9e16b0},
    {"wrapper_calls_locked_queue", 0x9e16f3, 5, 1, 0x37f06f0},
    {"wrapper_uses_manager", 0x9e16ec, 7, 3, 0x5cc1240},
    {"validator_reaches_final_command_evaluator", 0x288da89, 5, 1, 0x30b1ce0},
    {"command_validator_reaches_final_law_evaluator", 0x30b1e0e, 5, 1, 0x30b1b70},
    {"popup_reuses_final_law_evaluator", 0x41d4aab, 5, 1, 0x30b1b70},
    {"executor_constructs_mutation_context", 0x288da15, 5, 1, 0x28a94f0},
    {"executor_selects_same_group", 0x288da23, 5, 1, 0x28a96e0},
    {"executor_finalizes_mutation", 0x288da2e, 5, 1, 0x28a9590},
    {"selector_calls_apply", 0x28a9773, 5, 1, 0x28a9790},
}};

struct PointerEvidence {
  const char *name;
  std::uintptr_t pointer_rva;
  std::uintptr_t target_rva;
};

constexpr std::array<PointerEvidence, 8> kPointerEdges{{
    {"primary_destructor", 0x47600f8, 0x9d1560},
    {"primary_validator", 0x4760128, 0x288da40},
    {"primary_clone", 0x4760138, 0x2896230},
    {"primary_serializer", 0x4760178, 0x288da90},
    {"primary_deserializer", 0x4760180, 0x288db30},
    {"secondary_executor", 0x4760198, 0x288d9b0},
    {"popup_confirm", 0x49f20b8, 0x41d49c0},
    {"popup_can_confirm", 0x49f20a8, 0x41d4a20},
}};

struct AsciiEvidence {
  const char *name;
  std::uintptr_t rva;
  const char *value;
};

constexpr std::array<AsciiEvidence, 2> kAsciiEvidence{{
    {"add_law_command_rtti", 0x5a04f88, ".?AVCAddLawCommand@@"},
    {"enact_popup_rtti", 0x5c551c8, ".?AVCEnactLawConfirmationPopup@@"},
}};

struct NumericEvidence {
  const char *name;
  std::uintptr_t rva;
  std::uint64_t value;
};

constexpr std::array<NumericEvidence, 0> kNumericEvidence{};

RealmLawMutationAbiProofV1 Failure(RealmLawMutationAbiFailureV1 failure,
                                   const char *evidence) noexcept {
  RealmLawMutationAbiProofV1 proof{};
  proof.failure = failure;
  proof.failed_evidence = evidence;
  return proof;
}

bool Sha256(const std::vector<unsigned char> &input,
            std::array<unsigned char, 32> &output) noexcept {
  BCRYPT_ALG_HANDLE algorithm = nullptr;
  BCRYPT_HASH_HANDLE hash = nullptr;
  std::vector<unsigned char> object;
  bool success = false;
  if (BCryptOpenAlgorithmProvider(&algorithm, BCRYPT_SHA256_ALGORITHM, nullptr,
                                  0) < 0) {
    return false;
  }
  DWORD object_length = 0;
  DWORD result_length = 0;
  if (BCryptGetProperty(algorithm, BCRYPT_OBJECT_LENGTH,
                        reinterpret_cast<PUCHAR>(&object_length),
                        sizeof(object_length), &result_length, 0) < 0 ||
      result_length != sizeof(object_length)) {
    BCryptCloseAlgorithmProvider(algorithm, 0);
    return false;
  }
  try {
    object.resize(object_length);
  } catch (...) {
    BCryptCloseAlgorithmProvider(algorithm, 0);
    return false;
  }
  if (BCryptCreateHash(algorithm, &hash, object.data(), object_length, nullptr,
                       0, 0) >= 0 &&
      input.size() <= (std::numeric_limits<ULONG>::max)() &&
      BCryptHashData(hash, const_cast<PUCHAR>(input.data()),
                     static_cast<ULONG>(input.size()), 0) >= 0 &&
      BCryptFinishHash(hash, output.data(), static_cast<ULONG>(output.size()),
                       0) >= 0) {
    success = true;
  }
  if (hash != nullptr) {
    BCryptDestroyHash(hash);
  }
  BCryptCloseAlgorithmProvider(algorithm, 0);
  return success;
}

bool DigestMatches(const std::array<unsigned char, 32> &digest,
                   const char *expected) noexcept {
  static constexpr char kHex[] = "0123456789ABCDEF";
  for (std::size_t index = 0; index < digest.size(); ++index) {
    if (expected[index * 2] != kHex[digest[index] >> 4U] ||
        expected[index * 2 + 1] != kHex[digest[index] & 0x0FU]) {
      return false;
    }
  }
  return expected[64] == '\0';
}

} // namespace

RealmLawMutationAbiProofV1 VerifyRealmLawEnactMutationAbiV1(
    const RealmLawMutationAbiReaderV1 &reader,
    std::uintptr_t module_base) noexcept {
  if (reader.read == nullptr || module_base == 0) {
    return Failure(RealmLawMutationAbiFailureV1::invalid_reader, "reader");
  }
  try {
    for (const auto &span : kSpans) {
      std::vector<unsigned char> bytes(span.size);
      if (!reader.read(reader.context, span.rva, bytes.data(), bytes.size())) {
        return Failure(RealmLawMutationAbiFailureV1::read_failed, span.name);
      }
      std::array<unsigned char, 32> digest{};
      if (!Sha256(bytes, digest)) {
        return Failure(RealmLawMutationAbiFailureV1::sha256_failed, span.name);
      }
      if (!DigestMatches(digest, span.sha256)) {
        return Failure(RealmLawMutationAbiFailureV1::instruction_span_mismatch,
                       span.name);
      }
    }

    for (const auto &edge : kRelativeEdges) {
      std::int32_t displacement = 0;
      if (!reader.read(reader.context,
                       edge.instruction_rva + edge.displacement_offset,
                       &displacement, sizeof(displacement))) {
        return Failure(RealmLawMutationAbiFailureV1::read_failed, edge.name);
      }
      const auto actual = static_cast<std::intptr_t>(edge.instruction_rva) +
                          edge.instruction_size + displacement;
      if (actual != static_cast<std::intptr_t>(edge.target_rva)) {
        return Failure(RealmLawMutationAbiFailureV1::relative_edge_mismatch,
                       edge.name);
      }
    }

    for (const auto &edge : kPointerEdges) {
      std::uintptr_t pointer = 0;
      if (!reader.read(reader.context, edge.pointer_rva, &pointer,
                       sizeof(pointer))) {
        return Failure(RealmLawMutationAbiFailureV1::read_failed, edge.name);
      }
      if (pointer != module_base + edge.target_rva) {
        return Failure(RealmLawMutationAbiFailureV1::absolute_pointer_mismatch,
                       edge.name);
      }
    }

    for (const auto &evidence : kAsciiEvidence) {
      const std::size_t size = std::strlen(evidence.value) + 1;
      std::vector<char> actual(size);
      if (!reader.read(reader.context, evidence.rva, actual.data(), size)) {
        return Failure(RealmLawMutationAbiFailureV1::read_failed,
                       evidence.name);
      }
      if (std::memcmp(actual.data(), evidence.value, size) != 0) {
        return Failure(RealmLawMutationAbiFailureV1::ascii_evidence_mismatch,
                       evidence.name);
      }
    }

    for (const auto &evidence : kNumericEvidence) {
      std::uint64_t actual = 0;
      if (!reader.read(reader.context, evidence.rva, &actual, sizeof(actual))) {
        return Failure(RealmLawMutationAbiFailureV1::read_failed,
                       evidence.name);
      }
      if (actual != evidence.value) {
        return Failure(RealmLawMutationAbiFailureV1::numeric_evidence_mismatch,
                       evidence.name);
      }
    }
  } catch (...) {
    return Failure(RealmLawMutationAbiFailureV1::read_failed, "allocation");
  }

  RealmLawMutationAbiProofV1 proof{};
  proof.verified = true;
  proof.failure = RealmLawMutationAbiFailureV1::none;
  proof.failed_evidence = "";
  return proof;
}

const char *RealmLawMutationAbiFailureNameV1(
    RealmLawMutationAbiFailureV1 failure) noexcept {
  switch (failure) {
  case RealmLawMutationAbiFailureV1::none:
    return "none";
  case RealmLawMutationAbiFailureV1::invalid_reader:
    return "invalid_reader";
  case RealmLawMutationAbiFailureV1::read_failed:
    return "read_failed";
  case RealmLawMutationAbiFailureV1::sha256_failed:
    return "sha256_failed";
  case RealmLawMutationAbiFailureV1::instruction_span_mismatch:
    return "instruction_span_mismatch";
  case RealmLawMutationAbiFailureV1::relative_edge_mismatch:
    return "relative_edge_mismatch";
  case RealmLawMutationAbiFailureV1::absolute_pointer_mismatch:
    return "absolute_pointer_mismatch";
  case RealmLawMutationAbiFailureV1::ascii_evidence_mismatch:
    return "ascii_evidence_mismatch";
  case RealmLawMutationAbiFailureV1::numeric_evidence_mismatch:
    return "numeric_evidence_mismatch";
  }
  return "invalid_failure";
}

} // namespace xar::ck3_12002::private_law
