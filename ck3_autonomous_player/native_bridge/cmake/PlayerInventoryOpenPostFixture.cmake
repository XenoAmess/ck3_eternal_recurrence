# Future source-only minimum fixture. This file has not been configured.
# The native opening TU is NOT compiled by this fixture; it only consumes the
# actual postcondition and process-life ledger policy headers.
function(xar_add_inventory_open_post_fixture selected_root)
  add_executable(xar_inventory_open_post12004_owned
    "${selected_root}/tests/player_inventory_open_post12004_owned_test.cpp")
  target_include_directories(xar_inventory_open_post12004_owned PRIVATE
    "${selected_root}/include")
  target_compile_features(xar_inventory_open_post12004_owned PRIVATE cxx_std_20)
  if(MSVC)
    target_compile_options(xar_inventory_open_post12004_owned PRIVATE /UNDEBUG /W4 /EHsc /utf-8)
  else()
    target_compile_options(xar_inventory_open_post12004_owned PRIVATE -UNDEBUG)
  endif()
  add_test(NAME xar_inventory_open_post12004_owned COMMAND xar_inventory_open_post12004_owned)
endfunction()
