# Exact-build observed-current ordered candidate mapper inputs; new fixture only.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_12003_current_candidate_detachment_mapper src/ck3_12003_current_candidate_detachment_mapper_test.cpp)
  target_link_libraries(xar_ck3_12003_current_candidate_detachment_mapper PRIVATE xar_ck3_12002_runtime)
  target_include_directories(xar_ck3_12003_current_candidate_detachment_mapper PRIVATE include)
  target_compile_features(xar_ck3_12003_current_candidate_detachment_mapper PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_12003_current_candidate_detachment_mapper PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
  if(MSVC)
    target_compile_options(xar_ck3_12003_current_candidate_detachment_mapper PRIVATE /W4 /WX /permissive- /EHsc /Gy /O2 /UNDEBUG)
    target_link_options(xar_ck3_12003_current_candidate_detachment_mapper PRIVATE /OPT:REF)
  endif()
  add_test(NAME xar_ck3_12003_current_candidate_detachment_mapper COMMAND xar_ck3_12003_current_candidate_detachment_mapper
    "${CMAKE_CURRENT_BINARY_DIR}/current-candidate-detachment-mapper-wire")
endif()
