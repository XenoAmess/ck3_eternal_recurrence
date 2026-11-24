#pragma once
#include "xar_bridge/ck3_121003_core_route26785313_v1.hpp"
#include "xar_bridge/ck3_121003_living_inventory26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_living_ui26785313_owner_v1.hpp"
#include "xar_bridge/ck3_121003_living_entry26785313_owner_v1.hpp"
namespace xar::ck3_121003::build26785313 {
#if defined(XAR_CK3_ENABLE_121003_26785313_LIVING_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_INVENTORY_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_UI_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_UI_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_WEAPON_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_WEAPON_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_EVENT_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_EVENT_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_DETAIL_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_DETAIL_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LIVING_ENTRY_V1) && XAR_CK3_ENABLE_121003_26785313_LIVING_ENTRY_V1 && defined(XAR_CK3_ENABLE_121003_26785313_LYD_V1) && XAR_CK3_ENABLE_121003_26785313_LYD_V1
inline constexpr bool kLivingWholeCompiled267V1=true;
#else
inline constexpr bool kLivingWholeCompiled267V1=false;
#endif
inline bool VerifyLivingWholeImage267V1(std::uintptr_t image)noexcept{
 return kLivingWholeCompiled267V1&&VerifyLivingInventoryImage267V1(image)&&
  VerifyLivingEntryImage267V1(image)&&VerifyLivingManageImage267V1(image)&&VerifyLydImage267V1(image);
}
inline const game::AdapterDescriptor&LivingWholeDescriptor267V1(const game::AdapterDescriptor&base)noexcept{
 if(!kLivingWholeCompiled267V1||!game::IsCk3_121003Core26785313Descriptor(base))return base;
 return LivingEntryDescriptor267V1(LivingUiDescriptor267V1(LivingInventoryQueryDescriptor267V1(base)));
}
inline bool LivingWholeStepEnabled267V1(const game::AdapterDescriptor&d,std::string_view step)noexcept{
 if(!kLivingWholeCompiled267V1||!game::IsCk3_121003Core26785313Descriptor(d))return false;
 if(step==kLivingInventoryQueryStep267V1)return LivingInventoryQueryStepEnabled267V1(d,step);
 if(step==kLivingUiStep267V1)return LivingUiStepEnabled267V1(d,step);
 if(step==kLivingEntryStep267V1)return LivingEntryStepEnabled267V1(d,step);
 return false;
}
inline bool AttachLivingWholeExecutor267V1(ck3_11906::MainThreadQueryInstallEnvironmentV1&environment,
 std::uintptr_t image)noexcept{
 // Existing mechanical field only. No old12004 capability and no slot35.
 if(!kLivingWholeCompiled267V1||!VerifyLivingWholeImage267V1(image))return false;
 auto&slot=environment.permitted_executor_artifact_personal_read12004;
 if(slot&&slot!=&ExecuteLivingOnOwner267V1)return false;
 slot=&ExecuteLivingOnOwner267V1;return true;
}
}
