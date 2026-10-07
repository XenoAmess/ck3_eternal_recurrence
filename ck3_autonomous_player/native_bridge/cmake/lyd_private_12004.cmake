# Actual .4 LYD profiles reuse the original private options and DTO entrypoints.
# These source fixtures grant no native-game or business acceptance.
if(BUILD_TESTING AND WIN32)
  add_executable(xar_ck3_ingame_private_gui12004_profile_v1_test
    tests/ingame_private_gui_12004_profile_v1_test.cpp)
  target_include_directories(xar_ck3_ingame_private_gui12004_profile_v1_test PRIVATE include)
  target_compile_features(xar_ck3_ingame_private_gui12004_profile_v1_test PRIVATE cxx_std_20)
  if(MSVC)
    target_compile_options(xar_ck3_ingame_private_gui12004_profile_v1_test PRIVATE
      /W4 /WX /permissive- /EHsc /utf-8)
  endif()
  add_test(NAME ingame_private_gui12004_profile_v1
    COMMAND xar_ck3_ingame_private_gui12004_profile_v1_test)

  if(XAR_CK3_ENABLE_CONFUCIAN_ASSEMBLY_PREDICATES_PRIVATE_QUERY_V1)
    add_executable(xar_ck3_12004_confucian_assembly_bindings_test
      src/ck3_12004_confucian_assembly_bindings_test.cpp)
    target_link_libraries(xar_ck3_12004_confucian_assembly_bindings_test PRIVATE
      xar_ck3_12002_runtime)
    target_include_directories(xar_ck3_12004_confucian_assembly_bindings_test PRIVATE include)
    target_compile_features(xar_ck3_12004_confucian_assembly_bindings_test PRIVATE cxx_std_20)
    if(MSVC)
      target_compile_options(xar_ck3_12004_confucian_assembly_bindings_test PRIVATE
        /W4 /WX /permissive- /EHsc /utf-8)
    endif()
    add_test(NAME xar_ck3_12004_confucian_assembly_bindings_test
      COMMAND xar_ck3_12004_confucian_assembly_bindings_test)
  endif()

  if(XAR_CK3_ENABLE_CONFUCIAN_RELIGIOUS_TITLE_PRIVATE_QUERY_V1 AND
     XAR_CK3_ENABLE_CONFUCIAN_CHALLENGER_GRAPH_PRIVATE_QUERY_V1)
    add_executable(xar_ck3_12004_confucian_title_binding_first
      tests/ck3_12004_confucian_title_binding_first.cpp)
    target_link_libraries(xar_ck3_12004_confucian_title_binding_first PRIVATE
      xar_ck3_12002_runtime)
    target_include_directories(xar_ck3_12004_confucian_title_binding_first PRIVATE include)
    target_compile_features(xar_ck3_12004_confucian_title_binding_first PRIVATE cxx_std_20)
    if(MSVC)
      target_compile_options(xar_ck3_12004_confucian_title_binding_first PRIVATE
        /W4 /WX /permissive- /EHsc /utf-8)
    endif()
    add_test(NAME xar_ck3_12004_confucian_title_binding_first
      COMMAND xar_ck3_12004_confucian_title_binding_first)
  endif()
endif()
