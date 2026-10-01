"""Necessary new CLI forwarding and bounded-run dispatch, using file-only fixtures."""
import contextlib
import io
from unittest import mock

import test_native_auto_run as fixtures
from xar_autoplayer import cli
import xar_autoplayer.native_auto_run as runtime


def test_explicit_nonwar_and_government_flags_reach_the_existing_cli_runner():
    fixture = fixtures.NativeAutoRunTests()
    fixture.setUp()
    try:
        argv = ["--bridge-mode", "native-headless", "--bridge-dll", str(fixture.dll_path),
                "--bridge-injector", str(fixture.injector_path), "native-auto-run", "--turns", "1"]
        defaults = cli.parser().parse_args(argv)
        assert defaults.nonwar_only is False
        assert defaults.allow_private_government_runtime_adapter_query is False
        with mock.patch.object(cli, "make_spec", return_value=fixture.spec), \
             mock.patch.object(cli, "configure_native_bridge_launch_environment", return_value=fixture.config), \
             mock.patch.object(runtime, "native_auto_run", return_value={"ok": False, "status": "blocked"}) as runner, \
             contextlib.redirect_stdout(io.StringIO()):
            cli.main(argv)
            assert "nonwar_only" not in runner.call_args.kwargs
            assert "allow_private_government_runtime_adapter_query" not in runner.call_args.kwargs
            cli.main(argv + ["--nonwar-only", "--allow-private-government-runtime-adapter-query"])
            assert runner.call_args.kwargs["nonwar_only"] is True
            assert runner.call_args.kwargs["allow_private_government_runtime_adapter_query"] is True
    finally:
        fixture.tearDown()


def test_bounded_production_runner_selects_nonwar_dispatch_and_sets_actual_driver_permission():
    fixture = fixtures.NativeAutoRunTests()
    fixture.setUp()
    original_run = runtime.native_auto_run
    existing_fake_auto = fixtures._FakeGameplayService.auto_turn
    dispatched = []

    def nonwar(service, *, before_submit=None):
        assert service.driver.nonwar_only is True
        assert service.driver.allow_private_government_runtime_adapter_query is True
        dispatched.append(before_submit)
        return existing_fake_auto(service, before_submit=before_submit)

    def bounded(*args, **kwargs):
        return original_run(*args, **kwargs, nonwar_only=True,
                            allow_private_government_runtime_adapter_query=True)

    try:
        with mock.patch.object(runtime, "native_auto_run", side_effect=bounded), \
             mock.patch.object(fixtures._FakeGameplayService, "auto_nonwar_turn", nonwar, create=True), \
             mock.patch.object(fixtures._FakeGameplayService, "auto_turn", side_effect=AssertionError("legacy planner was called")):
            report, harness = fixture._run(["advance"])
        assert len(dispatched) == 1
        assert report["auto_run"]["turns"][0]["selected_step"] == "life-advance"
        assert harness.driver.nonwar_only is True
        assert harness.driver.allow_private_government_runtime_adapter_query is True
    finally:
        fixture.tearDown()
