#pragma once

#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_11906::private_law {

inline constexpr std::string_view kRealmLawEnactMutationAbiV1 =
    "realm_law_enact_mutation_v1_abi";
inline constexpr std::string_view kRealmLawEnactMutationBuildV1 =
    "1.19.0.6";
inline constexpr std::string_view kRealmLawEnactMutationExeSha256V1 =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr std::string_view kRealmLawEnactMutationManifestSha256V1 =
    "C9D4D2347646A3A4A95C1F6D735F9582D57DBD55729BFF9337136B0808F5D16B";

inline constexpr std::uintptr_t kGuiLawCanEnactReceiverRvaV1 = 0x3DDF770;
inline constexpr std::uintptr_t kGuiLawEnactPopupBuilderRvaV1 = 0x3DDF8C0;
inline constexpr std::uintptr_t kEnactLawPopupConfirmRvaV1 = 0x3DDEEC0;
inline constexpr std::uintptr_t kRealmLawFinalEvaluatorRvaV1 = 0x2C7D930;
inline constexpr std::uintptr_t kAddLawCommandValidatorRvaV1 = 0x25E2690;
inline constexpr std::uintptr_t kAddLawCommandSerializerRvaV1 = 0x25E26E0;
inline constexpr std::uintptr_t kAddLawCommandExecutorRvaV1 = 0x25E2640;
inline constexpr std::uintptr_t kRealmLawMutationDispatchRvaV1 = 0x260ACB0;
inline constexpr std::uintptr_t kRealmLawMutationApplyRvaV1 = 0x25FF0F0;
inline constexpr std::uintptr_t kAddLawCommandPrimaryVtableRvaV1 =
    0x4323730;
inline constexpr std::uintptr_t kAddLawCommandSecondaryVtableRvaV1 =
    0x4323700;
inline constexpr std::uintptr_t kCommandManagerRvaV1 = 0x57621F0;

using RealmLawMutationAbiReadFunctionV1 = bool (*)(
    void *context, std::uintptr_t rva, void *destination,
    std::size_t size) noexcept;

struct RealmLawMutationAbiReaderV1 {
  void *context = nullptr;
  RealmLawMutationAbiReadFunctionV1 read = nullptr;
};

enum class RealmLawMutationAbiFailureV1 : std::uint32_t {
  none = 0,
  invalid_reader,
  read_failed,
  sha256_failed,
  instruction_span_mismatch,
  relative_edge_mismatch,
  absolute_pointer_mismatch,
  ascii_evidence_mismatch,
  numeric_evidence_mismatch,
};

struct RealmLawMutationAbiProofV1 {
  bool verified = false;
  RealmLawMutationAbiFailureV1 failure =
      RealmLawMutationAbiFailureV1::invalid_reader;
  const char *failed_evidence = "reader";
  std::string_view contract = kRealmLawEnactMutationAbiV1;
  std::string_view build = kRealmLawEnactMutationBuildV1;
  std::string_view executable_sha256 = kRealmLawEnactMutationExeSha256V1;
  std::string_view manifest_sha256 = kRealmLawEnactMutationManifestSha256V1;
};

// Reads only the supplied exact-build image view. module_base is used solely
// to validate relocated vtable entries; the reader itself is addressed by RVA.
RealmLawMutationAbiProofV1 VerifyRealmLawEnactMutationAbiV1(
    const RealmLawMutationAbiReaderV1 &reader,
    std::uintptr_t module_base) noexcept;

const char *RealmLawMutationAbiFailureNameV1(
    RealmLawMutationAbiFailureV1 failure) noexcept;

} // namespace xar::ck3_11906::private_law
