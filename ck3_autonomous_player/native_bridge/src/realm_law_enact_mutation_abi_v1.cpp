#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <bcrypt.h>

#include "xar_bridge/realm_law_enact_mutation_abi_v1.hpp"

#include <array>
#include <cstring>
#include <limits>
#include <vector>

#pragma comment(lib, "bcrypt.lib")

namespace xar::ck3_11906::private_law {
namespace {

struct SpanEvidence {
  const char *name;
  std::uintptr_t rva;
  std::size_t size;
  const char *sha256;
};

// Data vtables contain relocated pointers in a live image, so they are checked
// entry-by-entry below. Only relocation-stable instruction bytes are hashed.
constexpr std::array<SpanEvidence, 20> kSpans{{
    {"gui_law_enact_registration", 0x7DF870, 0xC4,
     "A3B429A8AE524E4957960D92A561D7558B8F3032DC7914DD235F05941B05626E"},
    {"gui_law_enact_reflection_callback", 0x3DE0880, 0x1C,
     "933D0540B343A2D3BA24F4DAB309A441DA0DE753E1F4515F623C37B8C7403683"},
    {"gui_law_can_enact_receiver", 0x3DDF770, 0xA9,
     "99878CBEA6C1F72BF956B042B3DC0EA99498B838401A3D118F9DA1C4F2F8F552"},
    {"engine_final_law_evaluator", 0x2C7D930, 0x16D,
     "19DF78424757D57F98B4AC0A3A4483B71A0262F61361E22DB9343D05FAFBB053"},
    {"engine_final_command_validator", 0x2C7DAA0, 0x135,
     "D626F7242CAA153AC91710BA570C3BE995CBA4DEE6EB4FCA081EFDCD3D1E44C9"},
    {"gui_law_enact_popup_builder", 0x3DDF8C0, 0xFC,
     "098E3CBFDF01914AF549211A7416C89A9649358CB948D7CE7DA7AB80E5A5F172"},
    {"popup_confirm_add_law_submit", 0x3DDEEC0, 0x5F,
     "A87F23F36C57F82856DB60676D5E8B3CA0B375DFF2FF446E44256A1384EA6278"},
    {"add_law_command_executor_leaf", 0x25E2640, 0x4B,
     "E1F214A62378DDEC95101BF8A5CBB96B2C3B77E444104938FC1B237668489B15"},
    {"add_law_command_validator_adapter_leaf", 0x25E2690, 0x4E,
     "A2324CCA52063F1D308DD4470CF1183574E972BC85E580EE0DE83C3DB4C6A6B0"},
    {"add_law_command_heap_clone", 0x25EC5B0, 0x7C,
     "39336CAFA6C9649B740C57C3396877699BDDAA958C15722AD79CFBF64AF8B204"},
    {"add_law_command_serializer", 0x25E26E0, 0x9F,
     "62EECCEB502016F098239A1C9FE7ADDB17AC02CE8EDBF5510060D611EE5A0EB8"},
    {"submit_command_clone_and_queue", 0x973E00, 0x6C,
     "DE559EA4ADE7CC7BA5AD44612C15B28FD66B59FC69F4B1BF6C52431E750537F8"},
    {"locked_command_queue", 0x341D990, 0xFA,
     "28AC1C7F76E546A569234B3B1C05ED2746F364EF2FC61450AC13A95681E5650A"},
    {"law_mutation_dispatch", 0x260ACB0, 0xBA,
     "86F49D059BBC84A1C26DAFB646F8446313505FB25221E74DD0D9F3DB0040A53B"},
    {"law_mutation_apply_logical_span", 0x25FF0F0, 0x1BC,
     "3B80175307D4CC5CDD860E75A6C0839324ECA78406DD0E37F5A9DA7EAA5AFCBB"},
    {"command_framework_execution_adjustor_leaf", 0x803620, 0x9,
     "610780A6CE279F49AC53E56DA78A854CF59B83D0D07B2850381DF5E048D444AD"},
    {"command_framework_dispatch_gate", 0x26B2750, 0xF9,
     "BA8BE78920AF57E57F057566D865B370A6CBD378D0922E92AD7B2860E0B46A97"},
    {"command_framework_secondary_callsite", 0x26B29BC, 0x9,
     "D5532554CC958F45E10A76FF2382F5AA0BC3FE0673C6D272E78B5326620F788C"},
    {"add_law_command_deserializer_logical_span", 0x25E2780, 0xC9,
     "6637A71F6B7E9B0C92BAB5AD863FF81112F17825C8222BB7CD61D19F24DAEDF0"},
    {"law_mutation_finalizer", 0x25FEFA0, 0x14E,
     "5F6F68BDAEB3FE7BDB3D159BFF2C59C4EAA06A7B3C14C2F4294347B18590D058"},
}};

struct RelativeEdgeEvidence {
  const char *name;
  std::uintptr_t instruction_rva;
  std::uint32_t instruction_size;
  std::uint32_t displacement_offset;
  std::uintptr_t target_rva;
};

constexpr std::array<RelativeEdgeEvidence, 13> kRelativeEdges{{
    {"registers_enact_callback", 0x7DF8DC, 7, 3, 0x3DE0880},
    {"reflection_calls_gui_enact", 0x3DE0889, 5, 1, 0x3DDF8C0},
    {"gui_enact_rechecks_can_enact", 0x3DDF8D3, 5, 1, 0x3DDF770},
    {"can_enact_calls_final_evaluator", 0x3DDF7FC, 5, 1, 0x2C7D930},
    {"popup_confirm_calls_submit", 0x3DDEF14, 5, 1, 0x973E00},
    {"submit_calls_locked_queue", 0x973E41, 5, 1, 0x341D990},
    {"validator_adapter_tailcalls_command_validator", 0x25E26D9, 5, 1,
     0x2C7DAA0},
    {"command_validator_reuses_final_evaluator", 0x2C7DBCE, 5, 1,
     0x2C7D930},
    {"executor_tailcalls_mutation_dispatch", 0x25E2686, 5, 1, 0x260ACB0},
    {"mutation_dispatch_calls_apply", 0x260AD4C, 5, 1, 0x25FF0F0},
    {"execution_adjustor_enters_framework_dispatch", 0x803624, 5, 1,
     0x26B2750},
    {"framework_dispatch_calls_secondary_router", 0x26B27D8, 5, 1,
     0x26B2890},
    {"mutation_dispatch_calls_finalizer", 0x260AD57, 5, 1, 0x25FEFA0},
}};

struct PointerEvidence {
  const char *name;
  std::uintptr_t pointer_rva;
  std::uintptr_t target_rva;
};

constexpr std::array<PointerEvidence, 14> kPointerEdges{{
    {"add_law_secondary_executor", 0x4323708, 0x25E2640},
    {"add_law_primary_destructor", 0x4323730, 0x963C60},
    {"add_law_primary_validator", 0x4323760, 0x25E2690},
    {"add_law_primary_clone", 0x4323770, 0x25EC5B0},
    {"add_law_primary_serializer", 0x43237B0, 0x25E26E0},
    {"add_law_primary_deserializer", 0x43237B8, 0x25E2780},
    {"popup_can_confirm", 0x4590F68, 0x3DDEF20},
    {"popup_confirm_submit", 0x4590F78, 0x3DDEEC0},
    {"gui_law_enact_initializer", 0x4013628, 0x7DF870},
    {"add_law_primary_execution_dispatch", 0x4323768, 0x803620},
    {"character_registry_name", 0x42B7C28, 0x4095758},
    {"law_registry_name", 0x42C2AD8, 0x40F87C4},
    {"add_law_registry_name", 0x42C2AE8, 0x429D240},
    {"law_changed_registry_name", 0x42C5078, 0x42A1180},
}};

struct AsciiEvidence {
  const char *name;
  std::uintptr_t rva;
  const char *value;
};

constexpr std::array<AsciiEvidence, 7> kAsciiEvidence{{
    {"gui_law_enact_method", 0x4590D34, "Enact"},
    {"add_law_command_rtti", 0x54C18D8, ".?AVCAddLawCommand@@"},
    {"enact_popup_rtti", 0x56FA7B0, ".?AVCEnactLawConfirmationPopup@@"},
    {"character_registry_literal", 0x4095758, "character"},
    {"law_registry_literal", 0x40F87C4, "law"},
    {"add_law_registry_literal", 0x429D240, "add_law"},
    {"law_changed_registry_literal", 0x42A1180, "law_changed"},
}};

struct NumericEvidence {
  const char *name;
  std::uintptr_t rva;
  std::uint64_t value;
};

constexpr std::array<NumericEvidence, 4> kNumericEvidence{{
    {"character_field_tag", 0x42B7C20, 0x6EC},
    {"law_field_tag", 0x42C2AD0, 0x2FF2},
    {"add_law_command_class_key", 0x42C2AE0, 0x2FF3},
    {"law_changed_notification_key", 0x42C5070, 0x328A},
}};

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

} // namespace xar::ck3_11906::private_law
