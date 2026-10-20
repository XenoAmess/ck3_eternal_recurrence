option(XAR_CK3_ENABLE_PLAYER_INVENTORY_WINDOW_OPEN_PRIVATE_V1
  "Compile exact4 current-player inventory read/open/close/independent-post" OFF)
if(XAR_CK3_ENABLE_PLAYER_INVENTORY_WINDOW_OPEN_PRIVATE_V1)
  if(NOT WIN32)
    message(FATAL_ERROR "Inventory window provider requires the actual Windows application owner")
  endif()
  target_sources(xar_ck3_12002_runtime PRIVATE
    src/player_inventory_window12004_transport.cpp
    src/player_inventory_window12004_json.cpp
    src/ingame_ui_navigation_v1.cpp
    src/normal_exit_map_source_v1.cpp)
  set_property(SOURCE src/bridge.cpp src/player_inventory_window12004_transport.cpp
    src/ingame_ui_navigation_v1.cpp src/ck3_12002_nonwar_router.cpp
    src/ck3_12002_nonwar_mailbox.cpp APPEND PROPERTY COMPILE_DEFINITIONS
    XAR_CK3_ENABLE_PLAYER_INVENTORY_WINDOW_OPEN_PRIVATE_V1=1)
endif()
if(BUILD_TESTING)
  add_executable(xar_ck3_12004_player_inventory_open_post_owned_fixture EXCLUDE_FROM_ALL
    tests/player_inventory_open_post12004_owned_test.cpp)
  target_compile_features(xar_ck3_12004_player_inventory_open_post_owned_fixture PRIVATE cxx_std_20)
  target_include_directories(xar_ck3_12004_player_inventory_open_post_owned_fixture PRIVATE include)
  add_executable(xar_ck3_12004_player_inventory_window_wire_owned_fixture EXCLUDE_FROM_ALL
    tests/player_inventory_window12004_wire_owned_test.cpp src/player_inventory_window12004_json.cpp)
  target_compile_features(xar_ck3_12004_player_inventory_window_wire_owned_fixture PRIVATE cxx_std_20)
  target_include_directories(xar_ck3_12004_player_inventory_window_wire_owned_fixture PRIVATE include)
  add_executable(xar_ck3_12004_player_inventory_close_owned_fixture EXCLUDE_FROM_ALL
    tests/player_inventory_close_owned_test.cpp)
  target_compile_features(xar_ck3_12004_player_inventory_close_owned_fixture PRIVATE cxx_std_20)
  target_include_directories(xar_ck3_12004_player_inventory_close_owned_fixture PRIVATE include)
  add_executable(xar_ck3_12004_player_inventory_close_wire_owned_fixture EXCLUDE_FROM_ALL
    tests/player_inventory_close_wire_owned_test.cpp src/player_inventory_window12004_json.cpp)
  target_compile_features(xar_ck3_12004_player_inventory_close_wire_owned_fixture PRIVATE cxx_std_20)
  target_include_directories(xar_ck3_12004_player_inventory_close_wire_owned_fixture PRIVATE include)
  if(MSVC)
    foreach(_t xar_ck3_12004_player_inventory_open_post_owned_fixture xar_ck3_12004_player_inventory_window_wire_owned_fixture
        xar_ck3_12004_player_inventory_close_owned_fixture xar_ck3_12004_player_inventory_close_wire_owned_fixture)
      target_compile_options(${_t} PRIVATE /UNDEBUG /Od /GL- /EHsc /utf-8)
      target_compile_definitions(${_t} PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
    endforeach()
  endif()
endif()
