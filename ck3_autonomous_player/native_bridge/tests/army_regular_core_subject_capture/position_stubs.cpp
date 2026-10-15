#include "xar_bridge/army_regular_core_readonly_access_12004.hpp"
#include <cstdlib>

// Fixture-only link boundary. The mock seven slots point to an invalid ArRg;
// therefore political predicates must never execute. An accidental call aborts
// the fixture instead of substituting successful production predicate behavior.
namespace xar::ck3_12004 {
ArmyRegularCoreReadonlyPredicate12004 ReadArmyPosition2C090D012004(const ArmyRegularCoreReadonlyAccess12004 &,std::uintptr_t,std::uintptr_t,std::uintptr_t)noexcept{std::abort();}
ArmyRegularCoreReadonlyPredicate12004 ReadArmyPosition2C0928012004(const ArmyRegularCoreReadonlyAccess12004 &,std::uintptr_t,std::uintptr_t,std::uintptr_t)noexcept{std::abort();}
ArmyRegularCoreReadonlyPredicate12004 ReadArmyPosition2C0941012004(const ArmyRegularCoreReadonlyAccess12004 &,std::uintptr_t,std::uintptr_t,std::uintptr_t)noexcept{std::abort();}
ArmyRegularCoreReadonlyPredicate12004 ReadArmyPosition2494B4012004(const ArmyRegularCoreReadonlyAccess12004 &,std::uintptr_t,std::int32_t)noexcept{std::abort();}
ArmyRegularCoreReadonlyPredicate12004 ReadArmyPosition28B280012004(const ArmyRegularCoreReadonlyAccess12004 &,std::uintptr_t,std::int32_t)noexcept{std::abort();}
ArmyRegularCoreReadonlyPredicate12004 ReadArmyPosition2C3A0E012004(const ArmyRegularCoreReadonlyAccess12004 &,std::uintptr_t,std::uintptr_t)noexcept{std::abort();}
}
