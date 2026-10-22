"""Actual guard -> registered MCP -> host error -> product GUI consumer."""
from __future__ import annotations
import argparse
import asyncio
import importlib
import importlib.util
from pathlib import Path
import sys
import tempfile
from typing import Protocol,runtime_checkable
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'ck3_autonomous_player/src'))
from acceptance_contract import Object,mapping
import acceptance_adapter as adapter
from inventory_gui_contract import REFUSAL
from startup_actor_binding import StartupActorBinding
from test_acceptance_adapter import GuiPort

@runtime_checkable
class HostPort(Protocol):
    async def call(self,name: str,arguments: dict[str,object] | None=None) -> object: ...

class RefusedDriver:
    allow_private_player_inventory_window_open=True
    normal_exit_managed_profile: None=None
    native_calls=0

    def capabilities(self) -> dict[str,object]:
        return {'backend':'unit-no-native-io'}

    def take_snapshot(self) -> dict[str,object]:
        self.native_calls+=1
        raise AssertionError('Pre-intent rejection must precede native reads')

    def execute_step(self,step: str,*,expected_revision: int | None=None) -> dict[str,object]:
        self.native_calls+=1
        raise AssertionError('Pre-intent rejection must precede native writes')

    def wait_for_change(self,after_revision: int,*,timeout_seconds: float) -> dict[str,object]:
        self.native_calls+=1
        raise AssertionError('No native waits in an admission refusal')

    def open_player_inventory_window_private_v1(self,*,expected_revision: int) -> dict[str,object]:
        transport=importlib.import_module('xar_autoplayer.bridge.player_inventory_window_private_transport_v1')
        # Narrow dynamic boundary to the historical untyped native transport.
        operation: object=getattr(transport,'open_player_inventory_window_private_v1')
        if not callable(operation):raise AssertionError('Actual transport missing')
        returned: object=operation(self,expected_revision=expected_revision)
        return mapping(returned,'actual transport response')

class InventoryMcpRefusalTest(unittest.TestCase):
    def test_actual_mcp_refusal_reaches_original_product_consumer(self) -> None:
        from mcp import Client
        from mcp.server import MCPServer
        mcp_server=importlib.import_module('xar_autoplayer.bridge.mcp_server')
        create: object=getattr(mcp_server,'create_server')
        if not callable(create):raise AssertionError('Actual server factory missing')
        driver=RefusedDriver();server: object=create(driver)
        if not isinstance(server,MCPServer):raise AssertionError('Actual MCP server required')
        host_path=ROOT/'ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py'
        spec=importlib.util.spec_from_file_location('_living_inventory_refusal_host',host_path)
        if spec is None or spec.loader is None:raise AssertionError('Actual host loader missing')
        host=importlib.util.module_from_spec(spec);sys.modules[spec.name]=host
        spec.loader.exec_module(host)
        factory: object=getattr(host,'PlanClient')
        if not callable(factory):raise AssertionError('Actual PlanClient missing')
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)
            async def produce() -> str:
                async with Client(server) as session:
                    candidate: object=factory(session,argparse.Namespace(output=output/'report.json',command_timeout=10),{},lambda:None)
                    if not isinstance(candidate,HostPort):raise AssertionError('Actual host interface missing')
                    try:await candidate.call(adapter.OPEN,{'expected_revision':1})
                    except RuntimeError as error:return 'RuntimeError: '+str(error)
                    raise AssertionError('Actual guard did not reject')
            actual_error=asyncio.run(produce())
            self.assertEqual(actual_error,REFUSAL)
            self.assertEqual(driver.native_calls,0)
            port=GuiPort(output/'consumer',error=actual_error)
            session=adapter.Session({'run_id':'unit-run'},port,adapter.Contract(72,420,60,(),()))
            session.startup_actor=StartupActorBinding(29829,123,'1',24000,25,'a'*64,'b'*64)
            session.open_inventory('16777217')
            self.assertEqual(port.calls,[adapter.ITEM,adapter.OPEN,adapter.ITEM])
            self.assertEqual(len(port.gui_requests),1)
            self.assertFalse(session.original_action_unknown)

if __name__=='__main__':unittest.main()
