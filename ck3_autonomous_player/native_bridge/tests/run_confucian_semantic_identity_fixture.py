"""Run one inert C++ fixture from exact production renderer/admission source spans.

This does not build the runtime DLL, load CK3, call Win32, or open a process.
The normal-exit fixture executes its production branch and common capability
lookup, without unrelated gameplay parsers or any normal-exit callback.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone

def ref(path):
    raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def block(source, marker):
    start=source.index(marker)
    opening=source.index('{',start)
    level=0;state='code';i=opening
    while i<len(source):
        ch=source[i];following=source[i:i+2]
        if state in ('string','char'):
            if ch=='\\':i+=2;continue
            if ch==('"'if state=='string'else"'"):state='code'
        elif state=='line':
            if ch=='\n':state='code'
        elif state=='comment':
            if following=='*/':state='code';i+=2;continue
        elif following=='//':state='line';i+=2;continue
        elif following=='/*':state='comment';i+=2;continue
        elif ch=='"':state='string'
        elif ch=="'":state='char'
        elif ch=='{':level+=1
        elif ch=='}':
            level-=1
            if level==0:return source[start:i+1]
        i+=1
    raise ValueError('unterminated production source block '+marker)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',required=True)
    parser.add_argument('--legacy-source-root',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--vcvars',required=True)
    args=parser.parse_args()
    current=Path(args.source_root).resolve();legacy=Path(args.legacy_source_root).resolve()
    output=Path(args.output).resolve();output.mkdir()
    sources=[]
    def source(root,relative):
        path=root/'ck3_autonomous_player/native_bridge'/relative
        data=path.read_text('utf-8-sig');sources.append(ref(path));return data
    def fragment(root,relative,marker):
        value=block(source(root,relative),marker)
        return value
    header='#include <string>\n#include <string_view>\n#include <span>\n#include <array>\n#include <utility>\n#include <fstream>\n#include <iterator>\n#include <iostream>\n#include <stdexcept>\n'
    for version in ('12002','12003','12004'):
        text=source(current,'include/xar_bridge/ck3_'+version+'.hpp')
        wanted=('kGameVersion','kAdapterId','kExecutableSha256')
        constants=[]
        for name in wanted:
            match=re.search(r'inline constexpr char '+name+r'\[\]\s*=\s*"[^"]*";',text)
            if match:constants.append(match.group())
        header+='namespace xar::ck3_'+version+'{\n'+'\n'.join(constants)+'\n}\n'
    descriptor=fragment(current,'include/xar_bridge/game_adapter.hpp','struct AdapterDescriptor')
    is_four=fragment(current,'src/ck3_12004_abi_profile.cpp','bool IsCk3_12004Descriptor(')
    header+='namespace xar::game{\n'+descriptor+';\n'+is_four+'\n}\n'
    renderer_two=fragment(current,'src/ck3_12002_query_mailbox.cpp','std::string RenderQueryBuildIdentity(')
    replace_two=fragment(current,'src/ck3_12002_query_mailbox.cpp','void ReplaceIdentity(')
    header+='namespace xar::ck3_12002{\n'+replace_two+'\n'+renderer_two+'\n}\n'
    normal=source(current,'include/xar_bridge/normal_exit_map_v1.hpp')
    constants=[]
    for name in ('kNormalExitMapV1Step','kNormalExitMapV1Capability'):
        match=re.search(r'inline constexpr std::string_view '+name+r'\s*=\s*"[^"]*";',normal)
        if not match:raise ValueError('missing exact normal-exit constant '+name)
        constants.append(match.group())
    header+='namespace xar::ck3_12003{\n'+'\n'.join(constants)+'\n}\n'
    spans=[]
    for label,root in [('original',legacy),('fixed',current)]:
        render=fragment(root,'src/ck3_12004_adapter.cpp','std::string Render12004BuildIdentity(')
        replace=fragment(root,'src/ck3_12004_adapter.cpp','void ReplaceIdentityToken(')
        admission_source=source(root,'src/game_adapter.cpp')
        branch=block(admission_source,'} else if (step == ck3_12003::kNormalExitMapV1Step)')
        branch_body=branch[branch.index('{')+1:]
        # The next optional grant branch opens its preprocessor condition
        # before this closing brace. It has no normal-exit statements.
        if '\n#if' in branch_body:
            statements,next_directive=branch_body.split('\n#if',1)
            if next_directive.strip()!='defined(XAR_CK3_ENABLE_GRANT_TITLE_PICKER_PRIVATE_V1)\n  }':
                raise ValueError('normal-exit extraction meets an unexpected conditional branch')
            branch_body=statements+'\n}'
        common=block(admission_source,'bool GameAdapter::supports(')
        method=block(admission_source,'bool GameAdapter::supports_step(')
        common_return=method[method.rfind('return '):method.rfind('}')].strip()
        if common_return!='return !capability.empty() && supports(capability);':raise ValueError('common capability admission differs')
        spans.append({'label':label,'renderer_sha256':hashlib.sha256(render.encode()).hexdigest(),
                      'normal_exit_branch_sha256':hashlib.sha256(branch.encode()).hexdigest(),
                      'common_supports_sha256':hashlib.sha256(common.encode()).hexdigest()})
        header+='namespace '+label+' {\nusing namespace xar;using namespace xar::game;\n'+replace+'\n'+render+'\n'
        header+='''class GameAdapter { AdapterDescriptor d_; bool enabled_; public:
explicit GameAdapter(AdapterDescriptor d, bool enabled=true):d_(d),enabled_(enabled){}
const AdapterDescriptor &descriptor() const noexcept { return d_; }
bool enabled() const noexcept { return enabled_; }
bool supports(std::string_view capability) const noexcept;
bool supports_step(std::string_view step) const noexcept;
};
'''+common+'\n'
        header+='bool GameAdapter::supports_step(std::string_view step) const noexcept { std::string_view capability;\nif (step == ck3_12003::kNormalExitMapV1Step) {\n'+branch_body+'else{return false;}\n'+common_return+'}\n}\n'
    program=header+'''int main(int argc,char**argv){
using namespace xar;using namespace xar::game;
constexpr std::array<std::string_view,1> cap{ck3_12003::kNormalExitMapV1Capability};
const AdapterDescriptor three{ck3_12003::kAdapterId,ck3_12003::kGameVersion,ck3_12003::kExecutableSha256,"",cap};
const AdapterDescriptor four{ck3_12004::kAdapterId,ck3_12004::kGameVersion,ck3_12004::kExecutableSha256,"",cap};
auto no_cap=four;no_cap.capabilities={};auto mixed=four;mixed.executable_sha256=ck3_12003::kExecutableSha256;
auto wrong_adapter=four;wrong_adapter.adapter_id=ck3_12003::kAdapterId;
const auto step=ck3_12003::kNormalExitMapV1Step;
if(!original::GameAdapter(three).supports_step(step)||original::GameAdapter(four).supports_step(step)||
 !fixed::GameAdapter(three).supports_step(step)||!fixed::GameAdapter(four).supports_step(step)||
 fixed::GameAdapter(no_cap).supports_step(step)||fixed::GameAdapter(mixed).supports_step(step)||
 fixed::GameAdapter(wrong_adapter).supports_step(step)||fixed::GameAdapter(four,false).supports_step(step))return 2;
std::cout<<"{\\"admission_checks\\":8,\\"cases\\":[";
for(int i=1;i<argc;++i){std::ifstream file(argv[i],std::ios::binary);std::string raw((std::istreambuf_iterator<char>(file)),{});
if(!file)return 3;if(i>1)std::cout<<',';
std::cout<<"{\\"original\\":"<<original::Render12004BuildIdentity(raw,four)<<",\\"fixed\\":"<<fixed::Render12004BuildIdentity(raw,four)<<'}';
if(fixed::Render12004BuildIdentity(raw,three)!=raw)return 4;}
std::cout<<"]}\\n";return 0;}
'''
    cpp=output/'fixture.cpp';cpp.write_text(program,encoding='utf-8',newline='\n')
    reader=current/'tools/lyd_i3b_checkpoint_readback'
    sys.dont_write_bytecode=True
    sys.path.insert(0,str(reader/'reader'));sys.path.insert(0,str(reader/'reader/dependencies'));sys.path.insert(0,str(reader/'tests'))
    import sdk_fixture_builders as fixtures
    import sdk_checkpoint_qualification as qualification
    binding=qualification.frame_binding(fixtures.frame())
    inputs=[]
    for op in ('assembly_predicates','religious_title'):
        dto=(fixtures.assembly if op=='assembly_predicates'else fixtures.title)(binding)
        dto.update(game_version='1.20.0.4',executable_sha256=qualification.sdk.CK3_12004.executable_sha256)
        if op=='religious_title':
            for name in ('title_properties_index_sha256','title_laws_index_sha256','head_getters_index_sha256'):
                dto['qualification'][name]=qualification.sdk.ACTUAL4_ABI_INDEX_SHA256
        wire=fixtures.envelope(op,binding,dto)
        wire.update(game_version='1.20.0.4',executable_sha256=qualification.sdk.CK3_12004.executable_sha256,
                    backend_id=qualification.sdk._operation_backend(qualification.sdk.OPERATIONS[op][2],qualification.sdk.CK3_12004))
        path=output/(op+'.inert.json');path.write_text(json.dumps(wire,separators=(',',':')),encoding='utf-8');inputs.append((path,op))
    graph=output/'challenger_graph.inert.json'
    graph.write_text('{"schema":"ck3_12003_confucian_challenger_graph_v1","game_version":"1.20.0.4"}',encoding='utf-8');inputs.append((graph,None))
    envscript=output/'compiler_environment.cmd'
    envscript.write_text('@echo off\ncall "'+str(Path(args.vcvars).resolve())+'" >nul\nif errorlevel 1 exit /b 1\nset PATH\nset INCLUDE\nset LIB\n',encoding='utf-8')
    env_result=subprocess.run(['cmd.exe','/d','/c',str(envscript)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if env_result.returncode:raise RuntimeError('MSVC environment setup failed')
    environment=os.environ.copy()
    for line in env_result.stdout.decode('utf-8','replace').splitlines():
        if '='in line:
            key,value=line.split('=',1)
            if key.upper()in ('PATH','INCLUDE','LIB','LIBPATH'):environment[key.upper()]=value
    records=[]
    def run(name,argv):
        start=datetime.now(timezone.utc).isoformat()
        result=subprocess.run(argv,cwd=output,env=environment,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        (output/(name+'.stdout.raw')).write_bytes(result.stdout);(output/(name+'.stderr.raw')).write_bytes(result.stderr)
        record={'argv':argv,'started_at':start,'ended_at':datetime.now(timezone.utc).isoformat(),'exit_code':result.returncode,
                'stdout_sha256':hashlib.sha256(result.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(result.stderr).hexdigest()}
        records.append(record)
        print(json.dumps({'phase':name,'exit_code':result.returncode,'stdout_bytes':len(result.stdout),
                          'stderr_bytes':len(result.stderr)}),flush=True)
        if result.returncode:raise RuntimeError(name+' failed')
        return result
    executable=output/'confucian_semantic_identity_fixture.exe'
    compiler=shutil.which('cl.exe',path=environment['PATH'])
    if compiler is None:raise RuntimeError('MSVC compiler was not resolved in the captured environment')
    run('compile',[compiler,'/nologo','/std:c++20','/EHsc','/W4','/WX','/O2','/MD',str(cpp),'/Fe:'+str(executable),'/Fo:'+str(output/'fixture.obj'),'/link','/INCREMENTAL:NO'])
    native_result=run('fixture',[str(executable)]+[str(path)for path,op in inputs])
    result=json.loads(native_result.stdout)
    for row,(path,op) in zip(result['cases'],inputs,strict=True):
        if op is None:
            assert row['fixed']['schema']=='ck3_12003_confucian_challenger_graph_v1'
            assert row['original']['schema']=='ck3_12004_confucian_challenger_graph_v1'
            continue
        try:qualification.sdk.project_native_query(row['original'],binding,op,qualification.sdk.CK3_12004)
        except ValueError as error:
            assert str(error)=='native payload exact build/schema differs'
        else:raise AssertionError('original native renderer was not rejected')
        public=qualification.sdk.project_native_query(row['fixed'],binding,op,qualification.sdk.CK3_12004)
        assert public['full_product_acceptance_credit']is False
    report={'schema':'lyd.r21.isolated-production-source-fragment-fixture.v1','status':'OFFLINE_FIXTURE_PASSED',
            'source_refs':sources,'exact_production_spans':spans,'cpp':ref(cpp),'executable':ref(executable),
            'compiler_and_fixture':records,'normal_exit_admission_checks':result['admission_checks'],
            'G2_G3_original_renderer_rejected_fixed_renderer_DTO_accepted':True,'G4_schema_only_checked':True,
            'runtime_DLL_built':False,'game_process_handles_SDK_or_saved_body_used':False,'live_acceptance_credit':None}
    (output/'RESULT.actual.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(ref(output/'RESULT.actual.json')),flush=True)

if __name__=='__main__':main()
