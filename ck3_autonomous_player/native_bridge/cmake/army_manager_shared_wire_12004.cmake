# Lossless query-level ArmyManager transport; full runtime collector, synthetic world.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12004_army_manager_shared_wire_whole_test
    src/ck3_12004_army_manager_shared_wire_whole_test.cpp)
  target_link_libraries(xar_ck3_12004_army_manager_shared_wire_whole_test
    PRIVATE xar_ck3_12002_runtime)
  target_include_directories(xar_ck3_12004_army_manager_shared_wire_whole_test PRIVATE include)
  target_compile_features(xar_ck3_12004_army_manager_shared_wire_whole_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_army_manager_shared_wire_whole_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12004_army_manager_shared_wire_whole_test PRIVATE
      /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_ck3_12004_army_manager_shared_wire_whole_test PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_ck3_12004_army_manager_shared_wire_whole_test
    COMMAND xar_ck3_12004_army_manager_shared_wire_whole_test
      "${CMAKE_CURRENT_BINARY_DIR}/army-manager-shared-wire-12004")
endif()
