# Existing adopted .3 providers, independently rebound to the exact .4 image.
target_sources(xar_ck3_12002_runtime PRIVATE
  src/ck3_12004_religion_costs_eligibility_bindings.cpp
  src/ck3_12004_religion_draft_bindings.cpp
  src/ck3_12004_religion_adopted_observers.cpp)

if(BUILD_TESTING AND WIN32 AND
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1 AND
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_GROUPS_PRIVATE_QUERY_V1 AND
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_DOCTRINE_CHOICES_PRIVATE_QUERY_V1 AND
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_TENET_CHOICES_PRIVATE_QUERY_V1 AND
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_RESOURCE_COSTS_PRIVATE_QUERY_V1 AND
   XAR_CK3_ENABLE_G2_PLAYER_RELIGION_AI_REFORM_INPUTS_PRIVATE_QUERY_V1 AND
   XAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1 AND
   XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1)
  foreach(family IN ITEMS costs_eligibility draft_bindings adopted_observers)
    set(target "xar_ck3_12004_religion_${family}_mailbox_test")
    add_executable(${target}
      "src/ck3_12004_religion_${family}_mailbox_test.cpp")
    target_include_directories(${target} PRIVATE include)
    target_compile_features(${target} PRIVATE cxx_std_20)
    target_compile_definitions(${target} PRIVATE
      NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
      XAR_CK3_ENABLE_G2_PLAYER_RELIGION_REFORM_CONTEXT_PRIVATE_QUERY_V1=1
      XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_GROUPS_PRIVATE_QUERY_V1=1
      XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_DOCTRINE_CHOICES_PRIVATE_QUERY_V1=1
      XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_TENET_CHOICES_PRIVATE_QUERY_V1=1
      XAR_CK3_ENABLE_G2_PLAYER_RELIGION_DRAFT_RESOURCE_COSTS_PRIVATE_QUERY_V1=1
      XAR_CK3_ENABLE_G2_PLAYER_RELIGION_AI_REFORM_INPUTS_PRIVATE_QUERY_V1=1
      XAR_CK3_ENABLE_G2_PLAYER_RITE_GOVERNANCE_PRIVATE_QUERY_V1=1
      XAR_CK3_ENABLE_G2_PLAYER_RITE_MEMBERS_PRIVATE_QUERY_V1=1)
    target_link_libraries(${target} PRIVATE
      xar_bridge_protocol xar_ck3_12002_runtime user32 bcrypt)
    if(MSVC)
      target_compile_options(${target} PRIVATE
        /UNDEBUG /W4 /WX /permissive- /EHsc /utf-8 /Gy)
      target_link_options(${target} PRIVATE /OPT:REF)
    endif()
    add_test(NAME ${target} COMMAND ${target}
      "${CMAKE_CURRENT_BINARY_DIR}/religion-12004-adopted-wire")
  endforeach()
endif()
