if(BUILD_TESTING)
  add_executable(xar_ck3_war_declared_owner_tree_v1_test
    tests/war_declared_owner_tree_v1_test.cpp)
  target_include_directories(xar_ck3_war_declared_owner_tree_v1_test PRIVATE include)
  target_compile_features(xar_ck3_war_declared_owner_tree_v1_test PRIVATE cxx_std_20)
  if(MSVC)
    target_compile_options(xar_ck3_war_declared_owner_tree_v1_test PRIVATE
      /W4 /WX /permissive- /EHsc /utf-8 /UNDEBUG)
  endif()
  add_test(NAME xar_ck3_native_bridge_war_declared_owner_tree_v1
    COMMAND xar_ck3_war_declared_owner_tree_v1_test)
endif()
