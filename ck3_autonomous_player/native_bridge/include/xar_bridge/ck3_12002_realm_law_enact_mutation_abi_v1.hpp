#pragma once

#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::ck3_12002::private_law {

inline constexpr std::string_view kRealmLawEnactMutationAbiV1 =
    "ck3_12002_realm_law_enact_mutation_v1_abi";
inline constexpr std::string_view kRealmLawEnactMutationBuildV1 =
    "1.20.0.2";
inline constexpr std::string_view kRealmLawEnactMutationExeSha256V1 =
    "AE1BA6FF060BA603842F6F4A2DED0AF4B7D3666B3DD271F75FB01B0DA8E81B2D";
inline constexpr std::string_view kRealmLawEnactMutationManifestSha256V1 =
    "BD2000808A4CB293610C5CFF6D5B067AC1BEDDFC863600B8E7C99E68F27A4537";

inline constexpr std::uintptr_t kEnactLawPopupCanConfirmRvaV1 = 0x41D4A20;
inline constexpr std::uintptr_t kEnactLawPopupConfirmRvaV1 = 0x41D49C0;
inline constexpr std::uintptr_t kRealmLawFinalEvaluatorRvaV1 = 0x30B1B70;
inline constexpr std::uintptr_t kAddLawCommandValidatorRvaV1 = 0x288DA40;
inline constexpr std::uintptr_t kAddLawCommandSerializerRvaV1 = 0x288DA90;
inline constexpr std::uintptr_t kAddLawCommandExecutorRvaV1 = 0x288D9B0;
inline constexpr std::uintptr_t kRealmLawMutationSelectGroupRvaV1 = 0x28A96E0;
inline constexpr std::uintptr_t kRealmLawMutationApplyRvaV1 = 0x28A9790;
inline constexpr std::uintptr_t kAddLawCommandPrimaryVtableRvaV1 =
    0x47600F8;
inline constexpr std::uintptr_t kAddLawCommandSecondaryVtableRvaV1 =
    0x4760190;
inline constexpr std::uintptr_t kCommandManagerRvaV1 = 0x5CC1240;

inline constexpr std::uintptr_t kAddLawCommandCloneRvaV1 = 0x2896230;
inline constexpr std::uintptr_t kAddLawCommandDestructorRvaV1 = 0x9D1560;
inline constexpr std::uintptr_t kRealmLawLockedQueueRvaV1 = 0x37F06F0;

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

} // namespace xar::ck3_12002::private_law
