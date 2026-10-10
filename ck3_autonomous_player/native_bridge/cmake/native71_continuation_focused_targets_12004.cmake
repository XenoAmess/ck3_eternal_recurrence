# Permanently tracked authored fixtures; only explicit target builds select them.
if(BUILD_TESTING AND WIN32)
  # The effective55 fixture is a two-TU DTO/serializer transport with active asserts.
  # It has no runtime/provider link; Root captures stdout for its Python strict focus.
  add_executable(xar_current_household_conception_wire_focus EXCLUDE_FROM_ALL
    tests/current_household_conception_wire_focus.cpp
    src/current_first_heir_relationship_v1.cpp)
  target_include_directories(xar_current_household_conception_wire_focus PRIVATE include)
  target_compile_features(xar_current_household_conception_wire_focus PRIVATE cxx_std_20)
  target_compile_definitions(xar_current_household_conception_wire_focus PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE
    XAR_CK3_ENABLE_G2_M5_ALLIANCE_PROJECTION_PRIVATE_QUERY_V1=1)
  if(MSVC)
    target_compile_options(xar_current_household_conception_wire_focus PRIVATE
      /EHsc /W4 /WX /utf-8 /UNDEBUG)
  endif()

  add_executable(knight_installed_transfer_consumption_12004_test EXCLUDE_FROM_ALL
    tests/knight_installed_transfer_consumption_12004_fixture.cpp)
  target_link_libraries(knight_installed_transfer_consumption_12004_test PRIVATE
    xar_ck3_12002_runtime)
  target_include_directories(knight_installed_transfer_consumption_12004_test PRIVATE include)
  target_compile_features(knight_installed_transfer_consumption_12004_test PRIVATE cxx_std_20)
  target_compile_definitions(knight_installed_transfer_consumption_12004_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(knight_installed_transfer_consumption_12004_test PRIVATE
      /W4 /WX /permissive- /EHsc /utf-8 /UNDEBUG)
  endif()
  add_test(NAME knight_installed_transfer_consumption_12004
    COMMAND $<TARGET_FILE:knight_installed_transfer_consumption_12004_test>
      "${CMAKE_CURRENT_BINARY_DIR}/knight-installed-transfer-consumption-wire")
endif()
