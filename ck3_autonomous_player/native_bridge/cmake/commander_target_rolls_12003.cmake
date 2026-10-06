# FIRST whole-query qualification of candidate-specific current target bounds.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12003_commander_target_roll_test
    src/ck3_12002_army.cpp
    src/ck3_12003_army_replenishment_records.cpp
    src/ck3_12003_army_supply_timing.cpp
    src/ck3_12002_province.cpp
    src/ck3_12002_combat.cpp
    src/ck3_12003_commander.cpp
    src/ck3_12003_commander_target_roll.cpp
    src/ck3_12003_commander_mailbox.cpp
    src/ck3_12002_query_mailbox.cpp
    src/ck3_12003_abi_profile.cpp
    src/ck3_12003_commander_target_roll_test.cpp)
  target_include_directories(xar_ck3_12003_commander_target_roll_test PRIVATE include)
  target_compile_features(xar_ck3_12003_commander_target_roll_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_commander_target_roll_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_commander_target_roll_test PRIVATE
      /W4 /WX /permissive- /EHsc /Gy)
    target_link_options(xar_ck3_12003_commander_target_roll_test PRIVATE /OPT:REF)
  endif()
  target_link_libraries(xar_ck3_12003_commander_target_roll_test PRIVATE user32)
  file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/ck3_12003_commander_target_roll_wire")
  add_test(NAME xar_ck3_12003_commander_target_roll
    COMMAND xar_ck3_12003_commander_target_roll_test
      "${CMAKE_BINARY_DIR}/ck3_12003_commander_target_roll_wire")
endif()
