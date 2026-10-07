# AUTHORED_NOTRUN. One new collector/serializer fixture; Root owns FIRST.
# No whole Strength producer or additional production translation unit.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12004_army_four_leaf_pipeline_test
    src/army_four_leaf_pipeline_12004_fixture.cpp)
  target_include_directories(xar_ck3_12004_army_four_leaf_pipeline_test PRIVATE include)
  target_compile_features(xar_ck3_12004_army_four_leaf_pipeline_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12004_army_four_leaf_pipeline_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12004_army_four_leaf_pipeline_test PRIVATE
      /W4 /WX /permissive- /EHsc /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_12004_army_four_leaf_pipeline_test
    COMMAND $<TARGET_FILE:xar_ck3_12004_army_four_leaf_pipeline_test>
      "${CMAKE_CURRENT_BINARY_DIR}/army-four-leaf-native-bundle.json")
endif()
