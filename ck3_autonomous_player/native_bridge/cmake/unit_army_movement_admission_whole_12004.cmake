# One fresh CArmy admission whole producer. Root owns first build/run.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12004_unit_army_movement_admission_whole_test
    EXCLUDE_FROM_ALL
    tests/ck3_12004_unit_army_movement_admission_whole_test.cpp
    $<TARGET_OBJECTS:xar_ck3_bridge>)
  target_link_libraries(xar_ck3_12004_unit_army_movement_admission_whole_test PRIVATE
    xar_ck3_12002_runtime xar_bridge_protocol bcrypt
    $<TARGET_PROPERTY:xar_ck3_bridge,LINK_LIBRARIES>)
  target_include_directories(xar_ck3_12004_unit_army_movement_admission_whole_test PRIVATE include)
  target_compile_features(xar_ck3_12004_unit_army_movement_admission_whole_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_unit_army_movement_admission_whole_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    $<TARGET_PROPERTY:xar_ck3_bridge,COMPILE_DEFINITIONS>)
  if(MSVC)
    target_compile_options(xar_ck3_12004_unit_army_movement_admission_whole_test PRIVATE
      /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_12004_unit_army_movement_admission_whole_test
    COMMAND $<TARGET_FILE:xar_ck3_12004_unit_army_movement_admission_whole_test>
      --wire-dir ${CMAKE_CURRENT_BINARY_DIR}/wire/unit-army-movement-admission-12004)
endif()
