#pragma once
#include "xar_bridge/ck3_1210_character_manager_v1.hpp"
#include "xar_bridge/game_adapter.hpp"
#include <string>
#include <string_view>

namespace xar::ck3_1210 {
inline constexpr char kCharacterManagerCandidateSchemaV1[] =
    "xar.ck3.character-manager-observation1210-candidate/v1";
inline constexpr char kCharacterManagerCandidateRoleV1[] = "internal_candidate_data";
inline constexpr char kCharacterManagerCandidateBackendV1[] =
    "ck3-1.21.0-native-headless-main-thread";
inline constexpr std::size_t kCharacterManagerCandidatePacketLimitV1 = 32 * 1024 * 1024;
// All three states remain distinct. This candidate formatter cannot construct
// available: source publication and application-main custody are unqualified.
enum class CharacterManagerCandidateRegistrationV1 : std::uint8_t {
  unregistered, registered_unavailable, available
};
using CharacterManagerCandidateFormatterV1 = bool (*)(
    const CharacterManagerObservationV1 &, std::string &, std::string_view &) noexcept;
using CharacterManagerCandidateReaderV1 = bool (*)(const CharacterManagerBindingsV1 &,
    const CoreSnapshotPrefix &, CharacterManagerObservationV1 &,
    CharacterManagerReadAccessV1) noexcept;
struct CharacterManagerCandidateDescriptorV1 {
  CharacterManagerCandidateRegistrationV1 state = CharacterManagerCandidateRegistrationV1::unregistered;
  CharacterManagerCandidateReaderV1 reader = nullptr;
  CharacterManagerCandidateFormatterV1 formatter = nullptr;
  bool public_available = false;
  bool application_main_observed = false;
  std::string_view unavailable_reason = "character_manager_candidate_descriptor_unregistered";
};
// Pure value formatter; never reads native memory or establishes custody.
// Validates the complete original shape before writing. Malformed input or
// exceptions clear output and return false with a nonempty format reason.
// Body available means copied DATA only; descriptor public_available is false.
bool SerializeCharacterManagerCandidateDataV1(const CharacterManagerObservationV1 &data,
    std::string &output, std::string_view &format_reason) noexcept;
// Exact adapter/version/SHA selects actual linked reader/formatter pointers,
// not caller-supplied names. No capability is installed or made available.
CharacterManagerCandidateDescriptorV1 DescribeCharacterManagerCandidateDataV1(
    const game::AdapterDescriptor &descriptor) noexcept;
bool FormatCharacterManagerCandidateDataForDescriptorV1(const game::AdapterDescriptor &descriptor,
    const CharacterManagerObservationV1 &data, std::string &output,
    std::string_view &format_reason) noexcept;
// Separate metadata keeps Java16's frozen candidate DATA exact-field grammar.
// No caller-provided descriptor-state booleans can be promoted by this function.
std::string SerializeCharacterManagerCandidateDescriptorV1(
    const game::AdapterDescriptor &descriptor);
} // namespace xar::ck3_1210
