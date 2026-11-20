#pragma once
#include <cstdint>
namespace xar::ck3_1210::full111_rvas {
// Original operands are role keys only. Every nonzero value is current859F
// actual source/RTTI; there is no RVA delta and an unknown role returns zero.
inline constexpr std::uintptr_t Lookup(std::uintptr_t role) noexcept {
 switch(role) {
 case 0x8B27B0: return 0x8B2820; // daily_primary_bridge_function
 case 0x2E765F0: return 0x2E763E0; // daily_secondary_execute_function
 case 0x2E766C0: return 0x2E764B0; // daily_secondary_pre_function
 case 0x2E772A0: return 0x2E77090; // daily_final_function
 case 0x3E17850: return 0x3E17C00; // kQueueOwnedCommandRva
 case 0x3E1CD90: return 0x3E1D140; // command_worker_consumer
 case 0x3E1D180: return 0x3E1D530; // command_runner
 case 0x3E1D194: return 0x3E1D544; // command_scope_begin_guard
 case 0x3E1D286: return 0x3E1D636; // command_scope_end_guard
 case 0x3E64890: return 0x3E64C40; // worker_game_access_acquire
 case 0x3E64BA0: return 0x3E64F50; // worker_game_access_destructor
 case 0x3E653B0: return 0x3E65760; // kGetLocalPlayerRva
 case 0x3E65500: return 0x3E658B0; // pause_native_function
 case 0x3F5ADC0: return 0x3F5B170; // application_quit_function
 case 0x3F5AE85: return 0x3F5B235; // application_quit_flag_and_return_guard
 case 0x44FEA30: return 0x44FED60; // main_tls_getter
 case 0x4AFA620: return 0x4AFA650; // application_interface_dynamic_vtable
 case 0x4B3D998: return 0x4B3D9A0; // daily_secondary_vtable
 case 0x4B3D9B0: return 0x4B3D9B8; // daily_final_vtable_slot
 case 0x4B3D9D0: return 0x4B3D9D8; // daily_primary_vtable
 case 0x4B3DA68: return 0x4B3DA70; // kAutoSaveSecondaryVtableRva
 case 0x4B3DAA0: return 0x4B3DAA8; // kAutoSavePrimaryVtableRva
 case 0x4DC8568: return 0x4DC85C0; // application_game_dynamic_vtable
 case 0x4E8B7B8: return 0x4E8B860; // kSetSpeedSecondaryVtableRva
 case 0x4E8B7F0: return 0x4E8B898; // kSetSpeedPrimaryVtableRva
 case 0x4E8B958: return 0x4E8BA00; // kPauseSecondaryVtableRva
 case 0x4E8B990: return 0x4E8BA38; // kPausePrimaryVtableRva
 case 0x51B8AC8: return 0x51B8E40; // actual Daily BCA from CHD51BE370 DWORD3
 case 0x51BE070: return 0x51BE370; // daily_class_hierarchy_descriptor
 case 0x51C0470: return 0x51C0770; // daily_primary_COL
 case 0x51C0498: return 0x51C0798; // daily_secondary_COL
 case 0x5D3E3EC: return 0x0; // kGameSpeedCountRva
 case 0x60B11C8: return 0x60B12C8; // daily_type_descriptor
 case 0x68A8628: return 0x68A8928; // kCharacterStorageSlotRva
 case 0x68B1D58: return 0x68B2090; // kGameStateSlotRva
 case 0x68B3800: return 0x68B3B00; // kJominiStateSlotRva
 case 0x695910C: return 0x695940C; // main_tls_initialized_flag
 case 0x69DA8A0: return 0x69DABA0; // kCommandManagerRva
 case 0x6A640B8: return 0x6A643B8; // application_pointer_slot
 default:return 0;
 }
}
}
