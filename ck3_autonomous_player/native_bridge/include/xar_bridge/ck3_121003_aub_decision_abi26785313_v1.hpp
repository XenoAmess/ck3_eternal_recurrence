#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <string_view>

// Current859 source ABI only. No binder, owner authorization, public capability,
// Native call, Full qualification or live behavior is granted by this header.
namespace xar::ck3_121003::build26785313::aub_decision_abi {
inline constexpr std::string_view kExecutableSha256="859f0d380098adcb130eb9d453458222749fcdf6d46126ad0ed99d78f9a0aa28";
inline constexpr std::uintptr_t kDecisionsViewVtable=0x4BFAB00;
inline constexpr std::uintptr_t kDecisionsViewSecondary10=0x4BFAAD8;
inline constexpr std::uintptr_t kDecisionDetailVtable=0x4BFB748;
inline constexpr std::uintptr_t kDecisionDetailSecondary10=0x4BFB720;
inline constexpr std::uintptr_t kDecisionTypeVtable=0x5000780;
inline constexpr std::uintptr_t kOptionControllerVtable=0x4C69570;
inline constexpr std::uintptr_t kDefaultControllerVtable=0x4C694A0;
inline constexpr std::uintptr_t kConstOptionEntryAnyObject=0x5D4D610;
inline constexpr std::uintptr_t kConstOptionEntryAnyVtable=0x4C68BD0;

inline constexpr std::size_t kWindowRoot=0x60,kWindowGuiContext=0x68;
inline constexpr std::size_t kWindowJomini=0x98,kWindowHandler=0xA0;
inline constexpr std::size_t kHandlerList=0x1B0,kHandlerDetail=0x1B8;
inline constexpr std::size_t kListGroups=0x260,kGroupDecisions=8;
inline constexpr std::size_t kDecisionGroupStride=0x20,kDecisionRowStride=0x20;
inline constexpr std::size_t kRowDefinition=0,kRowCharacterReference=0x10,kRowOwner=0x18;
inline constexpr std::size_t kDetailDecision=0xD0,kDetailActor=0xD8;
inline constexpr std::size_t kDetailController=0x2F0,kDetailWidgetState=0x309;
inline constexpr std::size_t kDecisionKey=0x18,kDecisionWidgetDefinition=0x13C8;
inline constexpr std::size_t kWidgetOptionsDefinition=0x40;
inline constexpr std::size_t kDefinitionsData=0x18,kDefinitionsCount=0x24,kDefinitionStride=0x1A0;
inline constexpr std::size_t kDefinitionKeyId=0,kDefinitionEnabledTrigger=0x80;
inline constexpr std::size_t kDefinitionDefault=0x178,kDefinitionFlatIcon=0x179;
inline constexpr std::size_t kControllerDetail=8,kControllerHandler=0x10,kControllerScope=0x18;
inline constexpr std::size_t kControllerEntries=0x20,kControllerCapacity=0x28,kControllerCount=0x2C,kControllerSelected=0x38;
inline constexpr std::size_t kEntryStride=0x208,kEntryDefinition=0,kEntryScope=8;
inline constexpr std::size_t kEntryName=0x178,kEntryTooltip=0x198,kEntryDescription=0x1B8,kEntryBlockerDescription=0x1D8;
inline constexpr std::size_t kEntryKeyId=0x200,kEntryFlatIcon=0x204,kEntrySelected=0x205;
inline constexpr std::uintptr_t kStringPool=0x6B14820,kStringPoolInitializationGuard=0x6B14818;
inline constexpr std::size_t kPoolRecords=0x30,kPoolCount=0x3C,kPoolLock=0x48,kPoolRecordStride=0x20;
inline constexpr std::uint32_t kPooledKeyIndexMask=0xFFFFFF;

inline constexpr std::uintptr_t kRowSelect=0x15E7DF0;
inline constexpr std::uintptr_t kPolicyOnSelect=0x1C0D6B0;
inline constexpr std::uintptr_t kPolicyUpdateScope=0x1C0D5D0;
inline constexpr std::uintptr_t kCanConfirm=0x1603C80;
inline constexpr std::uintptr_t kConfirm=0x1603CD0;
inline constexpr std::uintptr_t kToggleCustomWidgetState=0x16043A0;
inline constexpr std::uintptr_t kResetCustomWidgetState=0x16043C0;
inline constexpr std::uintptr_t kEntryEnabledTriggerEvaluator=0x3D47320;
inline constexpr std::uintptr_t kPolicyNameTyped=0x1C0FDE0,kPolicyTooltipTyped=0x1C0FF20;
inline constexpr std::uintptr_t kDecisionCanConfirmTyped=0x1606320,kDecisionConfirmTyped=0x1606400;
inline constexpr std::uintptr_t kDecisionConfirmTooltipTyped=0x16063C0,kDecisionConfirmTextTyped=0x1605F50;
inline constexpr std::uintptr_t kDecisionEffectDescriptionTyped=0x1606200;
inline constexpr std::uintptr_t kDecisionGroupsTyped=0x15E86F0,kGroupDecisionsTyped=0x15E9E10,kPolicyEntriesTyped=0x1C102A0;

inline constexpr std::array<std::string_view,6> kPolicyKeys={
 "aub_policy_treasury_only_pause_choice","aub_policy_treasury_only_continue_choice",
 "aub_policy_personal_only_pause_choice","aub_policy_personal_only_continue_choice",
 "aub_policy_treasury_first_pause_choice","aub_policy_treasury_first_continue_choice"};
inline constexpr std::string_view kDefaultPolicyKey="aub_policy_treasury_first_continue_choice";
#if defined(_MSC_VER)
// ABI aliases, not callable owner wrappers. Only fixed registered typed objects
// from a repeated exact-current model/source/Core read may reach these targets.
using RowSelectNative=void(__fastcall*)(void* actual_decision_row);
using PolicyOnSelectNative=void(__fastcall*)(void* actual_option_controller,const void* actual_entry);
using DetailCanConfirmNative=bool(__fastcall*)(const void* actual_detail);
using DetailConfirmNative=void(__fastcall*)(void* actual_detail);
using DetailToggleNative=void(__fastcall*)(void* actual_detail);
using EntryEnabledNative=bool(__fastcall*)(const void* actual_definition_plus80,const void* actual_entry_plus8_scope);
#endif
} // namespace xar::ck3_121003::build26785313::aub_decision_abi
