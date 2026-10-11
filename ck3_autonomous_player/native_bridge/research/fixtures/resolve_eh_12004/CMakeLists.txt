cmake_minimum_required(VERSION 3.24)
project(lyd_b4_resolve_eh_fixture LANGUAGES CXX)
if(NOT WIN32 OR NOT MSVC OR NOT CMAKE_SIZEOF_VOID_P EQUAL 8)
  message(FATAL_ERROR "This fixture requires native Windows x64 MSVC")
endif()
add_executable(lyd_b4_resolve_eh_fixture_12004 resolve_eh_fixture.cpp)
target_compile_features(lyd_b4_resolve_eh_fixture_12004 PRIVATE cxx_std_20)
target_compile_options(lyd_b4_resolve_eh_fixture_12004 PRIVATE
  /O2 /Ob0 /EHsc /GS- /guard:cf- /W4 /Zi)
target_link_options(lyd_b4_resolve_eh_fixture_12004 PRIVATE /DEBUG /INCREMENTAL:NO)
set_target_properties(lyd_b4_resolve_eh_fixture_12004 PROPERTIES
  RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")
