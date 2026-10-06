# Root's shared CMake owner includes this after registering the actual .4
# Government TU in xar_ck3_12002_runtime. This declares a fresh fixture only.
add_executable(xar_ck3_12004_government_whole_first
  ${CMAKE_CURRENT_LIST_DIR}/../src/ck3_12004_government_whole_first.cpp)
target_link_libraries(xar_ck3_12004_government_whole_first PRIVATE xar_ck3_12002_runtime)
target_compile_features(xar_ck3_12004_government_whole_first PRIVATE cxx_std_20)
target_compile_definitions(xar_ck3_12004_government_whole_first PRIVATE
  NOMINMAX WIN32_LEAN_AND_MEAN UNICODE _UNICODE)
