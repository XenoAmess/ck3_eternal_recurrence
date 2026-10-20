# Global current-player providers. No product host and no public capability.
option(XAR_CK3_ENABLE_G2_PLAYER_ARTIFACT_PERSONAL_USE_READONLY_V1
  "Compile private exact4 current-player personal artifact observation" OFF)
option(XAR_CK3_ENABLE_ARTIFACT_PERSONAL_USE_PRIVATE_V1
  "Compile private exact4 original personal inventory equip/unequip submission" OFF)
option(XAR_CK3_ENABLE_G2_PLAYER_GHW_PERMISSIONS_READONLY_V1
  "Compile private exact4 current-player GHW variables and independent object links" OFF)
if(XAR_CK3_ENABLE_ARTIFACT_PERSONAL_USE_PRIVATE_V1 AND
   NOT XAR_CK3_ENABLE_G2_PLAYER_ARTIFACT_PERSONAL_USE_READONLY_V1)
  message(FATAL_ERROR "Personal artifact actions require the independently enabled observation provider")
endif()
if(XAR_CK3_ENABLE_G2_PLAYER_ARTIFACT_PERSONAL_USE_READONLY_V1 OR
   XAR_CK3_ENABLE_ARTIFACT_PERSONAL_USE_PRIVATE_V1 OR
   XAR_CK3_ENABLE_G2_PLAYER_GHW_PERMISSIONS_READONLY_V1)
  if(NOT WIN32)
    message(FATAL_ERROR "Current-player native observers require the actual Windows owner mailbox")
  endif()
  target_sources(xar_ck3_12002_runtime PRIVATE
    src/current_player_observers12004.cpp
    src/current_player_observers12004_json.cpp
    src/artifact_personal_use12004.cpp
    src/artifact_personal_use12004_native.cpp
    src/ghw_permission_observer/ghw_variable_observer_12004.cpp
    src/ghw_permission_observer/ghw_variable_bindings_12004.cpp
    src/ghw_permission_observer/ghw_object_links_12004.cpp)
  foreach(_flag IN ITEMS
      XAR_CK3_ENABLE_G2_PLAYER_ARTIFACT_PERSONAL_USE_READONLY_V1
      XAR_CK3_ENABLE_ARTIFACT_PERSONAL_USE_PRIVATE_V1
      XAR_CK3_ENABLE_G2_PLAYER_GHW_PERMISSIONS_READONLY_V1)
    if(${_flag})
      set_property(SOURCE src/bridge.cpp src/current_player_observers12004.cpp
        src/ck3_12002_nonwar_router.cpp src/ck3_12002_nonwar_mailbox.cpp
        APPEND PROPERTY COMPILE_DEFINITIONS ${_flag}=1)
    endif()
  endforeach()
  if(XAR_CK3_ENABLE_ARTIFACT_PERSONAL_USE_PRIVATE_V1)
    set_property(SOURCE src/artifact_personal_use12004.cpp
      APPEND PROPERTY COMPILE_DEFINITIONS XAR_CK3_ENABLE_ARTIFACT_PERSONAL_USE_PRIVATE_V1=1)
  endif()
endif()

if(BUILD_TESTING AND WIN32)
  function(_current_player_finite target)
    add_executable(${target} EXCLUDE_FROM_ALL ${ARGN})
    target_compile_features(${target} PRIVATE cxx_std_20)
    target_include_directories(${target} PRIVATE include src src/ghw_permission_observer)
    target_compile_definitions(${target} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
    if(MSVC)
      target_compile_options(${target} PRIVATE /UNDEBUG /W4 /permissive- /EHsc /utf-8)
    endif()
  endfunction()
  # This owned fixture includes the actual core .cpp once. Do not compile the
  # core a second time or link a runtime archive that duplicates its producer.
  _current_player_finite(xar_ck3_12004_artifact_personal_use_owned_fixture
    tests/artifact_personal_use12004_owned_test.cpp)
  # This wrapper includes the core with its action macro absent, independently
  # of an ON runtime source property. It must touch no frame/native callback.
  _current_player_finite(xar_ck3_12004_artifact_personal_use_default_off_fixture
    tests/artifact_personal_use12004_default_off_test.cpp)
  _current_player_finite(xar_ck3_12004_artifact_personal_use_ledger_fixture
    tests/artifact_personal_use_ledger12004_test.cpp
    src/artifact_personal_use12004.cpp)
  _current_player_finite(xar_ck3_12004_ghw_variables_owned_fixture
    src/ghw_permission_observer/ghw_variable_observer_12004_fixture.cpp
    src/ghw_permission_observer/ghw_variable_observer_12004.cpp)
  _current_player_finite(xar_ck3_12004_ghw_object_links_owned_fixture
    src/ghw_permission_observer/ghw_object_links_12004_fixture.cpp
    src/ghw_permission_observer/ghw_object_links_12004.cpp)
  # Five real producer TUs, no full runtime/archive or fixture stubs. The JSON
  # TU also contains artifact action serialization and therefore calls the real
  # DesiredStateObserved implementation even though this fixture invokes GHW only.
  _current_player_finite(xar_ck3_12004_ghw_two_leaf_serializer_fixture
    tests/ghw_two_leaf_serializer12004_fixture.cpp
    src/current_player_observers12004_json.cpp
    src/ghw_permission_observer/ghw_variable_observer_12004.cpp
    src/ghw_permission_observer/ghw_object_links_12004.cpp
    src/artifact_personal_use12004.cpp)
  if(XAR_CK3_ENABLE_G2_PLAYER_GHW_PERMISSIONS_READONLY_V1)
    # Future normal runtime build only: unlike the five-TU body target this also
    # exercises the real address-only binder and its existing factory closure.
    _current_player_finite(xar_ck3_12004_ghw_factory_serializer_fixture
      tests/ghw_two_leaf_serializer12004_fixture.cpp)
    target_compile_definitions(xar_ck3_12004_ghw_factory_serializer_fixture PRIVATE
      XAR_GHW_INCLUDE_ADDRESS_ONLY_BINDER_REGRESSION=1)
    target_link_libraries(xar_ck3_12004_ghw_factory_serializer_fixture PRIVATE
      $<LINK_ONLY:xar_ck3_12002_runtime> xar_bridge_protocol user32 bcrypt)
  endif()
  if(XAR_CK3_ENABLE_G2_PLAYER_ARTIFACT_PERSONAL_USE_READONLY_V1 OR
     XAR_CK3_ENABLE_G2_PLAYER_GHW_PERMISSIONS_READONLY_V1)
    # This is one compiled profile's actual classifier/registrar; the separately
    # documented OFF/ON wrapper matrix must compile each production TU with its
    # actual macros. A test-only macro never qualifies another configuration.
    _current_player_finite(xar_ck3_12004_current_player_observer_gates_fixture
      tests/current_player_observer_gates12004_test.cpp)
    foreach(_flag IN ITEMS XAR_CK3_ENABLE_G2_PLAYER_ARTIFACT_PERSONAL_USE_READONLY_V1
        XAR_CK3_ENABLE_ARTIFACT_PERSONAL_USE_PRIVATE_V1
        XAR_CK3_ENABLE_G2_PLAYER_GHW_PERMISSIONS_READONLY_V1)
      if(${_flag})
        target_compile_definitions(xar_ck3_12004_current_player_observer_gates_fixture PRIVATE ${_flag}=1)
      endif()
    endforeach()
    target_link_libraries(xar_ck3_12004_current_player_observer_gates_fixture PRIVATE
      $<LINK_ONLY:xar_ck3_12002_runtime> xar_bridge_protocol user32 bcrypt)
  endif()
endif()
