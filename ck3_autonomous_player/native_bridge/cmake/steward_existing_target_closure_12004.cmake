# Existing standalone targets retain their original compile definitions.
if(TARGET xar_ck3_adapter_registry_test)
  target_sources(xar_ck3_adapter_registry_test PRIVATE
    src/ck3_12004_steward_develop_county.cpp)
endif()

foreach(target IN ITEMS
    xar_ck3_steward_develop_county_candidates_v1_test
    xar_ck3_steward_develop_county_candidates_v1_mailbox_test)
  if(TARGET ${target})
    target_sources(${target} PRIVATE src/ck3_12004_steward_develop_county.cpp)
    target_link_libraries(${target} PRIVATE $<LINK_ONLY:xar_ck3_12002_runtime>)
  endif()
endforeach()

if(TARGET xar_ck3_steward_develop_county_candidates_v1_serializer_test)
  target_sources(xar_ck3_steward_develop_county_candidates_v1_serializer_test PRIVATE
    src/ck3_12003_steward_develop_county.cpp
    src/ck3_12004_steward_develop_county.cpp
    src/council_composition_steward_candidates_reader_v1.cpp
    src/council_composition_candidates_public_v1.cpp
    src/council_composition_candidates_public_v1_serializer.cpp)
  target_link_libraries(xar_ck3_steward_develop_county_candidates_v1_serializer_test
    PRIVATE $<LINK_ONLY:xar_ck3_12002_runtime>)
endif()
