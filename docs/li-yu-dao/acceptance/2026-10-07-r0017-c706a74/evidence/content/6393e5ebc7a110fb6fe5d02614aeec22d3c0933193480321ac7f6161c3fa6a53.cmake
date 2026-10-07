# Same-query preparation operands join each production Strength reader.
get_property(fixed_chunk0_targets DIRECTORY PROPERTY BUILDSYSTEM_TARGETS)
foreach(fixed_chunk0_target IN LISTS fixed_chunk0_targets)
  get_target_property(fixed_chunk0_sources ${fixed_chunk0_target} SOURCES)
  if("src/ck3_12002_army.cpp" IN_LIST fixed_chunk0_sources OR
     "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12002_army.cpp" IN_LIST fixed_chunk0_sources)
    if(NOT "src/ck3_12003_fixed_chunk0_preparation.cpp" IN_LIST fixed_chunk0_sources AND
       NOT "${CMAKE_CURRENT_SOURCE_DIR}/src/ck3_12003_fixed_chunk0_preparation.cpp" IN_LIST fixed_chunk0_sources)
      target_sources(${fixed_chunk0_target} PRIVATE src/ck3_12003_fixed_chunk0_preparation.cpp)
    endif()
  endif()
endforeach()

if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12003_fixed_chunk0_preparation_test
    src/ck3_12003_fixed_chunk0_preparation_test.cpp
    src/ck3_12003_fixed_chunk0_preparation.cpp
    src/ck3_12003_army_replenishment_records.cpp)
  target_include_directories(xar_ck3_12003_fixed_chunk0_preparation_test PRIVATE include)
  target_compile_features(xar_ck3_12003_fixed_chunk0_preparation_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_fixed_chunk0_preparation_test PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  if(MSVC)
    target_compile_options(xar_ck3_12003_fixed_chunk0_preparation_test PRIVATE /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_12003_fixed_chunk0_preparation_test
    COMMAND xar_ck3_12003_fixed_chunk0_preparation_test
      "${CMAKE_CURRENT_BINARY_DIR}/ck3_12003_fixed_chunk0_preparation_wire")
endif()
