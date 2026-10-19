# Finite current-player ordinary-pious pilgrimage. Default OFF, no advertising.
option(XAR_CK3_ENABLE_G2_PLAYER_PILGRIMAGE_EXECUTION_PRIVATE_V1
  "Compile private exact4 ordinary pious pilgrimage execution (unqualified by default)" OFF)
if(XAR_CK3_ENABLE_G2_PLAYER_PILGRIMAGE_EXECUTION_PRIVATE_V1 AND
   XAR_CK3_ENABLE_G2_ACTIVITY_COST_SLOT12_PASSIVE_PRIVATE_V1)
  message(FATAL_ERROR "Pilgrimage and legacy Feast passive cost require separate cold profiles")
endif()

if(XAR_CK3_ENABLE_G2_PLAYER_PILGRIMAGE_EXECUTION_PRIVATE_V1)
  if(NOT WIN32)
    message(FATAL_ERROR "Private pilgrimage execution requires the exact Windows owner mailbox")
  endif()
  set(_pilgrimage_sources
    src/ck3_12004_player_pilgrimage_execution_private_v1.cpp
    src/activity_pilgrimage_planner_open_v1.cpp
    src/activity_pilgrimage_stage1_v1.cpp
    src/activity_pilgrimage_destination_v1.cpp
    src/activity_pilgrimage_planner_caller12004_v1.cpp
    src/activity_typed_full_cost_v1.cpp
    src/activity_typed_cost_serializer_v1.cpp
    src/activity_pilgrimage_cost_lifecycle_v1.cpp
    src/activity_pilgrimage_stage5_start_v1.cpp
    src/activity_pilgrimage_start_capture_v1.cpp
    src/activity_cost_slot12_passive_v1.cpp
    src/activity_planner_diag_v1.cpp
    src/activity_hosted_identity_v1.cpp
    src/activity_feast_resource_balance_v1.cpp)
  target_sources(xar_ck3_12002_runtime PRIVATE ${_pilgrimage_sources})
  # No PUBLIC feature macro and no inherited Feast Start/Gold/guest gate.
  set_property(SOURCE src/bridge.cpp src/ck3_12002_nonwar_router.cpp
    src/ck3_12002_nonwar_mailbox.cpp src/ck3_12002_feast_planner_native.cpp
    src/ck3_12004_player_pilgrimage_execution_private_v1.cpp
    APPEND PROPERTY COMPILE_DEFINITIONS
      XAR_CK3_ENABLE_G2_PLAYER_PILGRIMAGE_EXECUTION_PRIVATE_V1=1)
  set_property(SOURCE src/activity_pilgrimage_planner_open_v1.cpp
    src/activity_pilgrimage_stage1_v1.cpp src/activity_pilgrimage_destination_v1.cpp
    src/activity_pilgrimage_planner_caller12004_v1.cpp
    APPEND PROPERTY COMPILE_DEFINITIONS
      XAR_CK3_ENABLE_PILGRIMAGE_PIOUS_PLANNER_PRIVATE_V1=1)

  if(BUILD_TESTING)
    function(_pilgrimage_fixture target)
      add_executable(${target} EXCLUDE_FROM_ALL ${ARGN})
      target_compile_features(${target} PRIVATE cxx_std_20)
      target_include_directories(${target} PRIVATE include src research)
      target_compile_definitions(${target} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
      target_link_libraries(${target} PRIVATE $<LINK_ONLY:xar_ck3_12002_runtime>
        xar_bridge_protocol bcrypt user32)
      if(MSVC)
        target_compile_options(${target} PRIVATE /UNDEBUG /W4 /permissive- /EHsc)
      endif()
    endfunction()

    _pilgrimage_fixture(xar_ck3_12004_pilgrimage_execution_wire_fixture
      src/ck3_12004_pilgrimage_execution_wire_fixture.cpp)
    _pilgrimage_fixture(xar_ck3_12004_pilgrimage_start_safety_fixture
      src/activity_pilgrimage_stage5_start_fixture.cpp)
    _pilgrimage_fixture(xar_ck3_12004_pilgrimage_full10_fixture
      tests/activity_typed_full_cost_v1_test.cpp)
    _pilgrimage_fixture(xar_ck3_12004_pilgrimage_cold_lifecycle_fixture
      tests/activity_pilgrimage_cost_lifecycle_serializer_v1_test.cpp)
    _pilgrimage_fixture(xar_ck3_12004_pilgrimage_planner_caller_fixture
      tests/activity_pilgrimage_planner_caller12004_v1_test.cpp)
    target_compile_definitions(xar_ck3_12004_pilgrimage_planner_caller_fixture PRIVATE
      XAR_CK3_ENABLE_PILGRIMAGE_PIOUS_PLANNER_PRIVATE_V1=1)
    foreach(_part IN ITEMS planner_open stage1 destination)
      _pilgrimage_fixture(xar_ck3_12004_pilgrimage_${_part}_fixture
        tests/activity_pilgrimage_${_part}_v1_test.cpp)
      target_compile_definitions(xar_ck3_12004_pilgrimage_${_part}_fixture PRIVATE
        XAR_CK3_ENABLE_PILGRIMAGE_PIOUS_PLANNER_PRIVATE_V1=1)
    endforeach()

    _pilgrimage_fixture(xar_ck3_12004_pilgrimage_stage1_selection_fixture
      tests/activity_pilgrimage_stage1_selection_v1_test.cpp)
    target_compile_definitions(xar_ck3_12004_pilgrimage_stage1_selection_fixture PRIVATE
      XAR_CK3_ENABLE_PILGRIMAGE_PIOUS_PLANNER_PRIVATE_V1=1)

    # Real production TUs are recompiled per registration/classifier mode.
    # OFF is undefined; wrapper TUs avoid the original SOURCE flag properties.
    foreach(_mode IN ITEMS off on)
      set(_wrappers)
      foreach(_unit IN ITEMS ck3_12002_nonwar_router ck3_12002_nonwar_mailbox
          ck3_12004_player_pilgrimage_execution_private_v1)
        set(_wrapper "${CMAKE_CURRENT_BINARY_DIR}/pilgrimage-gates/${_mode}/${_unit}.cpp")
        file(GENERATE OUTPUT "${_wrapper}" CONTENT
          "#include \"${CMAKE_CURRENT_SOURCE_DIR}/src/${_unit}.cpp\"\n")
        list(APPEND _wrappers "${_wrapper}")
      endforeach()
      set(_objects xar_ck3_12004_pilgrimage_gate_${_mode}_objects)
      add_library(${_objects} OBJECT ${_wrappers})
      set_property(TARGET ${_objects} PROPERTY EXCLUDE_FROM_ALL TRUE)
      target_compile_features(${_objects} PRIVATE cxx_std_20)
      target_include_directories(${_objects} PRIVATE include src research)
      target_compile_definitions(${_objects} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
      if(MSVC)
        target_compile_options(${_objects} PRIVATE /W4 /permissive- /EHsc)
      endif()
      foreach(_test IN ITEMS gate mailbox)
        _pilgrimage_fixture(xar_ck3_12004_pilgrimage_execution_${_test}_${_mode}_fixture
          src/ck3_12004_pilgrimage_execution_${_test}_test.cpp $<TARGET_OBJECTS:${_objects}>)
      endforeach()
      if(_mode STREQUAL on)
        target_compile_definitions(${_objects} PRIVATE
          XAR_CK3_ENABLE_G2_PLAYER_PILGRIMAGE_EXECUTION_PRIVATE_V1=1)
        foreach(_test IN ITEMS gate mailbox)
          target_compile_definitions(xar_ck3_12004_pilgrimage_execution_${_test}_${_mode}_fixture PRIVATE
            XAR_CK3_ENABLE_G2_PLAYER_PILGRIMAGE_EXECUTION_PRIVATE_V1=1)
        endforeach()
      endif()
      if(XAR_CK3_ENABLE_G2_PLAYER_PILGRIMAGE_ACTIVITIES_PRIVATE_QUERY_V1)
        target_compile_definitions(${_objects} PRIVATE
          XAR_CK3_ENABLE_G2_PLAYER_PILGRIMAGE_ACTIVITIES_PRIVATE_QUERY_V1=1)
        foreach(_test IN ITEMS gate mailbox)
          target_compile_definitions(xar_ck3_12004_pilgrimage_execution_${_test}_${_mode}_fixture PRIVATE
            XAR_CK3_ENABLE_G2_PLAYER_PILGRIMAGE_ACTIVITIES_PRIVATE_QUERY_V1=1)
        endforeach()
      endif()
    endforeach()

    set(_off_wrappers)
    foreach(_unit IN ITEMS activity_pilgrimage_planner_open_v1 activity_pilgrimage_stage1_v1
        activity_pilgrimage_destination_v1)
      set(_wrapper "${CMAKE_CURRENT_BINARY_DIR}/pilgrimage-gates/default-off/${_unit}.cpp")
      file(GENERATE OUTPUT "${_wrapper}" CONTENT
        "#include \"${CMAKE_CURRENT_SOURCE_DIR}/src/${_unit}.cpp\"\n")
      list(APPEND _off_wrappers "${_wrapper}")
    endforeach()
    _pilgrimage_fixture(xar_ck3_12004_pilgrimage_planner_default_off_fixture
      tests/activity_pilgrimage_default_off_v1_test.cpp ${_off_wrappers})
    set(_caller_off "${CMAKE_CURRENT_BINARY_DIR}/pilgrimage-gates/default-off/caller.cpp")
    file(GENERATE OUTPUT "${_caller_off}" CONTENT
      "#include \"${CMAKE_CURRENT_SOURCE_DIR}/src/activity_pilgrimage_planner_caller12004_v1.cpp\"\n")
    _pilgrimage_fixture(xar_ck3_12004_pilgrimage_caller_default_off_fixture
      tests/activity_pilgrimage_planner_caller12004_v1_test.cpp "${_caller_off}")
  endif()
endif()
