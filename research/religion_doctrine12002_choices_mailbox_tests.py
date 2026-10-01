#!/usr/bin/env python3
"""Run the actual native knowledge provider, slot runtime and full JSON wrapper."""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess
from pathlib import Path

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--record-wire-fixtures',action='store_true')
    args=p.parse_args();root=Path(__file__).resolve().parent.parent
    native=root/'ck3_autonomous_player/native_bridge';output=args.output_dir.resolve();output.mkdir(parents=True,exist_ok=True)
    vswhere=Path(os.environ.get('ProgramFiles(x86)',r'C:\Program Files (x86)'))/'Microsoft Visual Studio/Installer/vswhere.exe'
    installed=subprocess.run([str(vswhere),'-latest','-products','*','-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64',
        '-property','installationPath'],capture_output=True,text=True,check=True).stdout.strip()
    vcvars=Path(installed)/'VC/Auxiliary/Build/vcvars64.bat'
    sources=[native/'src'/name for name in ('ck3_12002.cpp','ck3_12002_religion_context.cpp',
        'religion_doctrine12002_intrinsic.cpp','religion_doctrine12002_choices.cpp',
        'ck3_12002_query_mailbox.cpp','main_thread_query_mailbox_v1.cpp','protocol.cpp',
        'religion_doctrine12002_choices_mailbox.cpp','religion_doctrine12002_choices_mailbox_test.cpp')]
    headers=[native/'include/xar_bridge'/name for name in ('religion_doctrine12002_choices.hpp',
        'religion_doctrine12002_choices_mailbox.hpp','religion_doctrine12002_intrinsic.hpp',
        'ck3_12002_religion_context.hpp','ck3_12002_query_mailbox.hpp','main_thread_query_mailbox_v1.hpp')]
    pins=sources+headers;runs=[];all_packets={}
    names=['learned-current.json','lookup-known.json','lookup-not-known.json','lookup-absent.json',
           'lookup-registry-unavailable.json','learned-empty.json']
    for mode in ('Od','O2'):
        target=output/mode;target.mkdir(exist_ok=True);temp=target/'tmp';temp.mkdir(exist_ok=True)
        exe=target/'doctrine-knowledge-mailbox-test.exe'
        command=subprocess.list2cmdline(['cl.exe','/nologo','/std:c++20','/EHsc','/'+mode,'/W4','/WX','/utf-8',
            '/I'+str(native/'include'),'/DXAR_CK3_ENABLE_G2_PLAYER_RELIGION_DOCTRINE_KNOWLEDGE_PRIVATE_QUERY_V1=1',
            '/DXAR_DOCTRINE_KNOWLEDGE_MAILBOX_STANDALONE_ADAPTER=1',*map(str,sources),'/Fe:'+str(exe),'/link','user32.lib'])
        batch=target/'build.cmd';batch.write_text('@echo off\ncall "'+str(vcvars)+'" >nul\nif errorlevel 1 exit /b %errorlevel%\n'+
            command+'\nexit /b %errorlevel%\n',encoding='utf-8')
        env=dict(os.environ,TEMP=str(temp),TMP=str(temp))
        build=subprocess.run(['cmd.exe','/d','/c',str(batch)],cwd=target,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (target/'build.log').write_text(build.stdout+build.stderr,encoding='utf-8')
        if build.returncode:raise RuntimeError('Compile failed: '+str(target/'build.log'))
        run=subprocess.run([str(exe),str(target)],cwd=target,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
        (target/'test.log').write_text(run.stdout+run.stderr,encoding='utf-8')
        if run.returncode:raise RuntimeError('Fixture failed: '+str(target/'test.log'))
        packets={name:json.loads((target/name).read_text(encoding='utf-8')) for name in names}
        for name,packet in packets.items():
            result=packet['result'];value=result['player_religion_doctrine_knowledge']
            assert packet['type']=='command_result' and packet['protocol_version']==1 and packet['ok'] is True
            assert packet['request_id']=='doctrine"knowledge-fixture'
            assert result['step']=='query-player-religion-doctrine-knowledge-v1'
            assert result['domain_key']=='player_religion_doctrine_knowledge_v1'
            assert result['backend_id']=='ck3-1.20.0.2-native-player-religion-doctrine-knowledge-v1'
            assert result['accepted'] and result['private_build'] and result['read_only'] and result['advertised'] is False
            assert result['snapshot_revision']==709 and result['date_raw']==value['date_raw']==53175816
            assert value['capture_epoch']>0 and value['capture_epoch']!=result['snapshot_revision']
            assert value['played_character_id']==0x03000004
            assert result['status']==('observed' if value['available'] else 'unavailable')
            assert result['query_mode']==('learned_rows' if name.startswith('learned-') else 'by_key')
        learned=packets['learned-current.json']['result']['player_religion_doctrine_knowledge']
        assert learned['knowledge_source']=='character_extension'
        assert learned['learned_rows'][1]['doctrine_key']=='doc"信' and learned['learned_rows'][1]['native_knows_doctrine']
        unknown=packets['lookup-not-known.json']['result']['player_religion_doctrine_knowledge']
        assert unknown['definition_found'] and unknown['native_knows_doctrine'] is False
        absent=packets['lookup-absent.json']['result']['player_religion_doctrine_knowledge']
        assert absent['available'] and not absent['definition_found'] and absent['native_knows_doctrine'] is None
        missing=packets['lookup-registry-unavailable.json']['result']['player_religion_doctrine_knowledge']
        assert not missing['available'] and missing['unavailable_reason']=='definition_registry_unavailable'
        empty=packets['learned-empty.json']['result']['player_religion_doctrine_knowledge']
        assert empty['available'] and empty['learned_rows']==[]
        runs.append({'mode':mode,'stdout':run.stdout.strip(),'actual_wire_cases':len(packets),
            'executable_sha256':digest(exe),'wire_sha256':{name:digest(target/name) for name in names}})
        all_packets[mode]=packets;print(mode,run.stdout.strip())
    source_pins={str(path.relative_to(root)):digest(path) for path in pins}
    result={'status':'GREEN','readiness':'static-ready','live_verified':False,'local_ck3_touched':False,
        'actual_native_core':True,'actual_knowledge_provider':True,
        'actual_mailbox_submit_drain_wait_reclaim':True,'actual_command_result_serializer':True,
        'fixture_native_callbacks':'Owned fixture objects; canonical knowledge getter behavior',
        'fixture_adapter_unwrap':'Bare adapter identity only; production WorkerAdapter unwrapping not substituted',
        'fixture_executor_permit':'Existing primary fixture permit; central named knowledge permit pending',
        'compiler':'MSVC /W4 /WX /Od and /O2','runs':runs,'source_sha256':source_pins}
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    if args.record_wire_fixtures:
        fixture={'schema':'xar.ck3_12002.doctrine_knowledge_actual_cpp_wire_fixture.v1',
            'game_version':'1.20.0.2','executable_sha256':'ae1ba6ff060ba603842f6f4a2ded0af4b7d3666b3dd271f75fb01b0da8e81b2d',
            'readiness':'static-ready','live_verified':False,'producer':'Actual C++ mailbox and command-result serializer',
            'source_sha256':source_pins,'packets':all_packets['O2'],
            'actual_wire_sha256':runs[1]['wire_sha256']}
        (root/'research/religion_doctrine12002_choices_mailbox_wire_fixtures.json').write_text(
            json.dumps(fixture,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return 0
if __name__=='__main__':raise SystemExit(main())
