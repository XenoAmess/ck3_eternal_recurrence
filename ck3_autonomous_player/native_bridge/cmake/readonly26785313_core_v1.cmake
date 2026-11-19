# Independent default-OFF current-image readonly implementation. No wire/Full/GUI capability.
option(XAR_CK3_ENABLE_121003_26785313_READONLY_V1 "Compile isolated exact26785313 Core/raw-resource owner reader" OFF)
if(XAR_CK3_ENABLE_121003_26785313_READONLY_V1)
  target_sources(xar_ck3_12002_runtime PRIVATE src/ck3_121003_readonly26785313_v1.cpp)
endif()
if(BUILD_TESTING)
  # Compile the actual production branch without the finite fixture macro.
  add_library(xar_ck3_121003_26785313_readonly_compile OBJECT
    src/ck3_121003_readonly26785313_v1.cpp)
  set_target_properties(xar_ck3_121003_26785313_readonly_compile PROPERTIES EXCLUDE_FROM_ALL TRUE)
  target_include_directories(xar_ck3_121003_26785313_readonly_compile PRIVATE include)
  target_compile_features(xar_ck3_121003_26785313_readonly_compile PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_121003_26785313_readonly_compile PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
  add_executable(xar_ck3_121003_26785313_core_static_test EXCLUDE_FROM_ALL
    src/ck3_121003_readonly26785313_static_test.cpp)
  target_include_directories(xar_ck3_121003_26785313_core_static_test PRIVATE include src)
  target_compile_features(xar_ck3_121003_26785313_core_static_test PRIVATE cxx_std_20)
  target_compile_definitions(xar_ck3_121003_26785313_core_static_test PRIVATE
    NOMINMAX WIN32_LEAN_AND_MEAN XAR_CK3_26785313_OFFLINE_FIXTURE=1)
  target_link_libraries(xar_ck3_121003_26785313_core_static_test PRIVATE bcrypt)
  if(MSVC)
    target_compile_options(xar_ck3_121003_26785313_readonly_compile PRIVATE /W4 /WX /permissive- /EHsc)
    target_compile_options(xar_ck3_121003_26785313_core_static_test PRIVATE /W4 /WX /permissive- /EHsc)
  endif()
  add_test(NAME xar_ck3_121003_26785313_core_synthetic
    COMMAND xar_ck3_121003_26785313_core_static_test --synthetic-image)
  # Actual disk qualification separately needs an explicit exact EXE path.
  # The default synthetic test supplies neither actual EXE nor live credit.
endif()
