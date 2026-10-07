#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <bcrypt.h>

#include "xar_bridge/ck3_12004_realm_law_enact_mutation_abi_v1.hpp"

#include <array>
#include <cstring>
#include <limits>
#include <vector>

#pragma comment(lib, "bcrypt.lib")

namespace xar::ck3_12004::private_law {
namespace {

struct SpanEvidence {
  const char *name;
  std::uintptr_t rva;
  std::size_t size;
  const char *sha256;
};

// Data vtables contain relocated pointers in a live image, so they are checked
// entry-by-entry below. Only relocation-stable instruction bytes are hashed.
constexpr std::array<SpanEvidence, 14> kSpans{{
    {"engine_final_law_evaluator", 0x30b1b50, 0x16d,
     "A6805E20505ECBFE00B1AC0435AE62AB5CAFAC144477AF62AEFA279E032F17A1"},
    {"engine_final_command_validator", 0x30b1cc0, 0x135,
     "45A94EBD0ED829FF51D11FC3B9FE21DC765029D154BBA8E4FEB6C759975B75A3"},
    {"add_law_command_executor", 0x288d990, 0x89,
     "9F942000F9EE50F8D1230DC2F0A4DAF29C967671A20D2B659DFAE02D5AD7B7EE"},
    {"add_law_command_validator_adapter", 0x288da20, 0x4e,
     "8D5E1094AF8B570F19FFF46CB0DCB4D0C71171590FF4FC8A7ADEBBEB9F7701C1"},
    {"add_law_command_heap_clone", 0x2896210, 0x7c,
     "FC29C46C27A33F62320F43499F012A5349F99849D7F39CA1D33FD29372026E21"},
    {"add_law_command_class_key", 0x2896290, 0x6,
     "A3E5408F5F55BE0748CD4AAF0E6B33C439B4C69719D5DCE93911B1D4F40730B5"},
    {"add_law_command_serializer", 0x288da70, 0x9f,
     "F68077E743B70FDCEA711CEFA0468CE89531B2A62A4B611EFFE3BDEB747B7210"},
    {"add_law_command_deserializer", 0x288db10, 0xc9,
     "8693B76160265D3EC142ED20538745BE5660C6979B7452DE21FA1870E779B92D"},
    {"locked_command_queue", 0x37f06d0, 0xfa,
     "35BE39318795009EF6176E9C135E9CD7ECDADE099F895515F3DD664949E34D0C"},
    {"law_mutation_context_constructor", 0x28a94d0, 0x9f,
     "453293DC9688406C0C388C4F4B2A0D4B498011651AE5DC52853E1A03DF76DF55"},
    {"law_mutation_select_group", 0x28a96c0, 0xa8,
     "2B2A8EFD1D61BA31DD29BD00FDFD972B5A0FFFFD2E53604F18F8C81D9361501B"},
    {"law_mutation_apply_logical_span", 0x28a9770, 0x1ba,
     "4F15B1E2431E41EBEA92C1C56D1EE054447BA627EAE9B7E50AC9ED893ECEA1E6"},
    {"law_mutation_finalizer", 0x28a9570, 0x14e,
     "AD264178B5B6F11C3676EC46B63C376058063187758BBB48FF37FCB09F1F95DA"},
    {"add_law_command_destructor", 0x9d1560, 0x2b,
     "30F2F57FE59FC3BC3C2B6C0C186D2C749325E8502A00404FBC1D6F13EE82E30F"},
}};

struct RelativeEdgeEvidence {
  const char *name;
  std::uintptr_t instruction_rva;
  std::uint32_t instruction_size;
  std::uint32_t displacement_offset;
  std::uintptr_t target_rva;
};

constexpr std::array<RelativeEdgeEvidence, 6> kRelativeEdges{{
    {"validator_reaches_final_command_evaluator", 0x288da69, 5, 1, 0x30b1cc0},
    {"command_validator_reaches_final_law_evaluator", 0x30b1dee, 5, 1, 0x30b1b50},
    {"executor_constructs_mutation_context", 0x288d9f5, 5, 1, 0x28a94d0},
    {"executor_selects_same_group", 0x288da03, 5, 1, 0x28a96c0},
    {"executor_finalizes_mutation", 0x288da0e, 5, 1, 0x28a9570},
    {"selector_calls_apply", 0x28a9753, 5, 1, 0x28a9770},
}};

struct PointerEvidence {
  const char *name;
  std::uintptr_t pointer_rva;
  std::uintptr_t target_rva;
};

constexpr std::array<PointerEvidence, 6> kPointerEdges{{
    {"primary_destructor", 0x4760108, 0x9d1560},
    {"primary_validator", 0x4760138, 0x288da20},
    {"primary_clone", 0x4760148, 0x2896210},
    {"primary_serializer", 0x4760188, 0x288da70},
    {"primary_deserializer", 0x4760190, 0x288db10},
    {"secondary_executor", 0x47601a8, 0x288d990},
}};

struct AsciiEvidence {
  const char *name;
  std::uintptr_t rva;
  const char *value;
};

constexpr std::array<AsciiEvidence, 1> kAsciiEvidence{{
    {"add_law_command_rtti", 0x5a04f58, ".?AVCAddLawCommand@@"},
}};

struct NumericEvidence {
  const char *name;
  std::uintptr_t rva;
  std::uint64_t value;
};

constexpr std::array<NumericEvidence, 0> kNumericEvidence{};

// Shared DTO defaults describe old2, so both success and failure must
// acquire actual4 identity here before the copied verification policy runs.
RealmLawMutationAbiProofV1 Actual4Proof() noexcept {
  RealmLawMutationAbiProofV1 proof{};
  proof.contract = kRealmLawEnactMutationAbi12004V1;
  proof.build = ck3_12004::kGameVersion;
  proof.executable_sha256 = ck3_12004::kExecutableSha256;
  proof.manifest_sha256 = kRealmLawEnactMutationManifestSha25612004V1;
  return proof;
}

RealmLawMutationAbiProofV1 Failure(RealmLawMutationAbiFailureV1 failure,
                                   const char *evidence) noexcept {
  auto proof = Actual4Proof();
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

RealmLawMutationAbiProofV1 VerifyRealmLawEnactMutationAbi12004V1(
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

  auto proof = Actual4Proof();
  proof.verified = true;
  proof.failure = RealmLawMutationAbiFailureV1::none;
  proof.failed_evidence = "";
  return proof;
}

} // namespace xar::ck3_12004::private_law
