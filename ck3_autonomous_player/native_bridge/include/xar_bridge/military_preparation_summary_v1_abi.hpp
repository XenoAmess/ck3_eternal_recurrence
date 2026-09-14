#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

namespace xar::bridge {

inline constexpr std::string_view kMilitaryPreparationSummaryPrivateKeyV1 =
    "g2_military_preparation_summary_v1";
inline constexpr std::string_view kMilitaryPreparationSummaryArtifactStemV1 =
    "g2-military-preparation-summary-v1";
inline constexpr std::string_view kMilitaryPreparationSummaryExecutableSha256V1 =
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86";
inline constexpr bool kMilitaryPreparationSummaryEnabledByDefaultV1 = false;
inline constexpr std::int64_t kMilitaryPreparationSummaryFixedPointScaleV1 =
    100000;
inline constexpr std::size_t kMilitaryPreparationSummaryFieldCountV1 = 10;

// CK3 1.19.0.6 exact-build anchors frozen by MIL2. The private core does not
// call them until a binding supplies the complete stock-order session teardown.
inline constexpr std::uintptr_t kMilitaryPreparationNamedValueDatabaseGetterRvaV1 =
    0x999AF0;
inline constexpr std::string_view
    kMilitaryPreparationNamedValueDatabaseGetterSha256V1 =
        "4E0246E4FB97D18607FA9CBF72F6030825B4FA0BF1340DABDC3FEBCBD0CA9AED";
inline constexpr std::uintptr_t kMilitaryPreparationNamedValueLookupRvaV1 =
    0x9999B0;
inline constexpr std::string_view kMilitaryPreparationNamedValueLookupSha256V1 =
    "B1BD5B25EB20D8B81D65BAE5942F3D233480910D40C2B11540BCC6E7A53D07E2";
inline constexpr std::uintptr_t kMilitaryPreparationNameHashRvaV1 = 0x3B8B000;
inline constexpr std::string_view kMilitaryPreparationNameHashSha256V1 =
    "E42410BF40CBE818FED8B771988E102AE129BCE08CD7F975EB7A1EB2E5CD70DD";

inline constexpr std::size_t kMilitaryPreparationRootScopeSizeV1 = 0x168;
inline constexpr std::uintptr_t kMilitaryPreparationRootScopeConstructorRvaV1 =
    0x81F190;
inline constexpr std::string_view
    kMilitaryPreparationRootScopeConstructorSha256V1 =
        "E119B49AA2F41C1E491435E90877DEB8F0DF42906226AAC2977F51A561443FA7";
inline constexpr std::uint32_t kMilitaryPreparationCharacterRootKindV1 = 4;
inline constexpr std::size_t kMilitaryPreparationRootKindOffsetV1 = 0x00;
inline constexpr std::size_t kMilitaryPreparationRootPayloadOffsetV1 = 0x08;

inline constexpr std::uintptr_t kMilitaryPreparationContextOwnerRvaV1 =
    0x337B210;
inline constexpr std::string_view kMilitaryPreparationContextOwnerSha256V1 =
    "CB13198F69D3B6478062F511DA9F4BC0319CFD2CEE8079E3E9E097BB29A70235";
inline constexpr std::uintptr_t
    kMilitaryPreparationSupportContainer118ConstructorRvaV1 = 0x3354330;
inline constexpr std::string_view
    kMilitaryPreparationSupportContainer118ConstructorSha256V1 =
        "8FF1EA95F300F3CA2F6FF20E267CD150DC95A72665F1A4CA8CC140B2146DA973";
inline constexpr std::uintptr_t
    kMilitaryPreparationSupportContainer2A8ConstructorRvaV1 = 0x3354280;
inline constexpr std::string_view
    kMilitaryPreparationSupportContainer2A8ConstructorSha256V1 =
        "CAAD6CC5E363916FE783AFDB299DFAF4FECBA51B5B649896059EE28ED371AA80";

inline constexpr std::uintptr_t kMilitaryPreparationFixedEvaluatorRvaV1 =
    0x3369820;
inline constexpr std::string_view kMilitaryPreparationFixedEvaluatorSha256V1 =
    "88C220FD822BE90E6E8DF71E1FC26214D62E5218493F5FCF1B64C2CD80A2DC04";
inline constexpr std::size_t kMilitaryPreparationDefinitionTreeOffsetV1 = 0x78;
inline constexpr std::size_t kMilitaryPreparationConstantRawOffsetV1 = 0x70;
inline constexpr std::size_t kMilitaryPreparationConstantPresentOffsetV1 = 0x83;

inline constexpr std::size_t kMilitaryPreparationRegistryDataOffsetV1 = 0xF08;
inline constexpr std::size_t kMilitaryPreparationRegistryCapacityOffsetV1 = 0xF10;
inline constexpr std::size_t kMilitaryPreparationRegistryCountOffsetV1 = 0xF14;
inline constexpr std::array<std::uint32_t, 5>
    kMilitaryPreparationStockFixedSlotsV1{0x34, 0x35, 0x36, 0x43, 0x44};

inline constexpr std::array<std::string_view,
                            kMilitaryPreparationSummaryFieldCountV1>
    kMilitaryPreparationSummaryDefinitionKeysV1{
        "xar_mcp_military_current_strength_final",
        "xar_mcp_military_max_strength_final",
        "xar_mcp_military_number_of_knights_final",
        "xar_mcp_military_max_number_of_knights_final",
        "xar_mcp_military_maa_gold_expense_relative_final",
        "ai_men_at_arms_expense_gold_min",
        "ai_men_at_arms_expense_gold_ideal",
        "ai_men_at_arms_expense_gold_max",
        "ai_men_at_arms_chance_expense_below_min",
        "ai_men_at_arms_chance_expense_below_ideal"};

inline constexpr std::array<std::uintptr_t, 5>
    kMilitaryPreparationBridgeWrapperLeafRvasV1{
        0x2849550, 0x28494C0, 0x19F4F00, 0x2868F40, 0x2873E20};
inline constexpr std::array<std::string_view, 5>
    kMilitaryPreparationBridgeWrapperLeafSha256V1{
        "88B396B98AA18C08795355D7C473F651D20F3DEB866C01A37C599114055484C2",
        "84874C3DCD57109D77E175C2B1880C5383C14C0BFB721708AA5E803D7D345D01",
        "609218A470B80A17521ACB19A767C30F2E6C393AF256BCA3898D03E5AFE9E3AD",
        "BD9F3C50F4D059647A385FE22C5CADDB3388E54BC7A2010888B5DD81E31C22E3",
        "48F87BC91325AB922B08ABE2020302944842121E0109C0029FD989540311F181"};

} // namespace xar::bridge
