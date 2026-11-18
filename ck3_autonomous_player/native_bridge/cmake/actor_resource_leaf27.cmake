# Source-wired v2 resource DATA; explicit feature remains OFF until qualified.
option(XAR_CK3_ENABLE_1210_ACTOR_RESOURCE_LEAF_V2 "Enable strict paused actor resource leaf v2" OFF)
if(XAR_CK3_ENABLE_1210_ACTOR_RESOURCE_LEAF_V2)
  if(NOT XAR_CK3_ENABLE_1210_ACTOR_FOUNDATION_V1 OR NOT XAR_CK3_ENABLE_1210_PERSONAL_GOLD_V1)
    message(FATAL_ERROR "Florin resource leaf v2 requires exact actor foundation and personal Gold")
  endif()
  # Target-scoped: avoid enabling new leaf references in unrelated old tests
  # that independently compile the shared Actor mailbox translation unit.
  set_property(SOURCE src/ck3_1210_adapter.cpp src/ck3_1210_personal_gold_frame_v1.cpp
    APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_1210_ACTOR_RESOURCE_LEAF_V2=1>")
  set_property(SOURCE src/bridge.cpp APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_bridge>:XAR_CK3_ENABLE_1210_ACTOR_RESOURCE_LEAF_V2=1>")
endif()
if(BUILD_TESTING)
  add_executable(xar_ck3_1210_actor_resource_leaf_v2_test
    src/ck3_1210_actor_resource_leaf_v2.cpp src/ck3_1210_actor_resource_leaf_v2_test.cpp
    src/ck3_1210_actor_foundation_v1.cpp src/ck3_1210_personal_gold_v1.cpp src/ck3_1210_core.cpp)
  target_include_directories(xar_ck3_1210_actor_resource_leaf_v2_test PRIVATE include)
  target_compile_definitions(xar_ck3_1210_actor_resource_leaf_v2_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  if(MSVC)
    target_compile_options(xar_ck3_1210_actor_resource_leaf_v2_test PRIVATE /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_native_bridge_1210_actor_resource_leaf_v2 COMMAND xar_ck3_1210_actor_resource_leaf_v2_test)
endif()

option(XAR_CK3_ENABLE_1210_RESOURCE_OWNER_SOURCES_V3 "Enable internal main-owned renown/treasury source DATA" OFF)
if(XAR_CK3_ENABLE_1210_RESOURCE_OWNER_SOURCES_V3)
  if(NOT XAR_CK3_ENABLE_1210_ACTOR_RESOURCE_LEAF_V2)
    message(FATAL_ERROR "Internal noncash sources require strict actor resource v2 owner")
  endif()
  target_sources(xar_ck3_12002_runtime PRIVATE src/ck3_1210_non_cash_decoder_v1.cpp src/ck3_1210_non_cash_owner_sources_v3.cpp)
  set_property(SOURCE src/ck3_1210_personal_gold_frame_v1.cpp APPEND PROPERTY COMPILE_DEFINITIONS
    "$<$<STREQUAL:$<TARGET_PROPERTY:NAME>,xar_ck3_12002_runtime>:XAR_CK3_ENABLE_1210_RESOURCE_OWNER_SOURCES_V3=1>")
  if(BUILD_TESTING)
    add_executable(xar_ck3_1210_resource_module_drift_v3_test
      src/ck3_1210_resource_module_drift_v3_test.cpp src/ck3_1210_non_cash_owner_sources_v3.cpp
      src/ck3_1210_non_cash_decoder_v1.cpp src/ck3_1210_actor_resource_leaf_v2.cpp
      src/ck3_1210_actor_foundation_v1.cpp src/ck3_1210_personal_gold_v1.cpp src/ck3_1210_core.cpp)
    target_include_directories(xar_ck3_1210_resource_module_drift_v3_test PRIVATE include)
    target_compile_definitions(xar_ck3_1210_resource_module_drift_v3_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
    if(MSVC)
      target_compile_options(xar_ck3_1210_resource_module_drift_v3_test PRIVATE /W4 /WX /permissive- /EHsc)
    endif()
    add_test(NAME xar_ck3_native_bridge_1210_resource_module_drift_v3 COMMAND xar_ck3_1210_resource_module_drift_v3_test)
  endif()
endif()

if(BUILD_TESTING)
  add_executable(xar_ck3_1210_resource_precore_counterexample src/ck3_1210_resource_precore_counterexample.cpp
    src/ck3_1210_actor_resource_leaf_v2.cpp src/ck3_1210_actor_foundation_v1.cpp
    src/ck3_1210_personal_gold_v1.cpp fixtures/ck3_1210_personal_gold_frame_body_v1.cpp
    src/ck3_1210_core.cpp fixtures/ck3_1210_adapter_body_v1.cpp src/ck3_1210_core_frame_v1.cpp
    src/ck3_1210_thread_runtime.cpp src/game_adapter_capabilities.cpp)
  target_include_directories(xar_ck3_1210_resource_precore_counterexample PRIVATE include)
  target_compile_definitions(xar_ck3_1210_resource_precore_counterexample PRIVATE XAR_CK3_ENABLE_1210_ACTOR_RESOURCE_LEAF_V2=1
    XAR_CK3_ENABLE_1210_CORE_FRAME_V1=1 XAR_CK3_ENABLE_1210_PERSONAL_GOLD_V1=1 XAR_CK3_ENABLE_1210_ACTOR_FOUNDATION_V1=1)
  target_compile_definitions(xar_ck3_1210_resource_precore_counterexample PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  if(MSVC)
    target_compile_options(xar_ck3_1210_resource_precore_counterexample PRIVATE /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_native_bridge_1210_resource_precore_counterexample COMMAND xar_ck3_1210_resource_precore_counterexample)
endif()

if(BUILD_TESTING)
  target_compile_features(xar_ck3_1210_actor_resource_leaf_v2_test PRIVATE cxx_std_20)
  target_compile_features(xar_ck3_1210_resource_precore_counterexample PRIVATE cxx_std_20)
endif()

if(BUILD_TESTING)
  add_executable(xar_ck3_1210_scoped_image_roots_test tests/scoped1210_image_roots_test.cpp src/ck3_1210_core.cpp)
  target_include_directories(xar_ck3_1210_scoped_image_roots_test PRIVATE include)
  target_compile_definitions(xar_ck3_1210_scoped_image_roots_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  target_compile_features(xar_ck3_1210_scoped_image_roots_test PRIVATE cxx_std_20)
  if(MSVC)
    target_compile_options(xar_ck3_1210_scoped_image_roots_test PRIVATE /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_native_bridge_1210_scoped_image_roots COMMAND xar_ck3_1210_scoped_image_roots_test)
endif()
