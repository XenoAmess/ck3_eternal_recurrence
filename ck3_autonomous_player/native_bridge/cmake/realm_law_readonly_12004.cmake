# The actual .4 helper is linked by the shared capture/provider translation
# unit. Root's mapped Core/descriptor/bootstrap source is supplied separately.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/realm_law_12004_native.cpp)

# This existing target also compiles the shared provider. Add its new link
# dependency without repeating the historical .3 qualification.
if(TARGET xar_ck3_12003_realm_law_succession_profile_wire_test)
  target_sources(xar_ck3_12003_realm_law_succession_profile_wire_test PRIVATE
    src/realm_law_12004_native.cpp)
endif()
