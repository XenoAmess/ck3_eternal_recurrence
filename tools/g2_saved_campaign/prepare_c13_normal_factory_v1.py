"""Exact six-constant C12->C13 normal-warm port; create-only Z review."""
import argparse,ast,hashlib,json
from datetime import datetime,timezone
from pathlib import Path

BASE_SHA='901fae6d94b7a5a7d72803a0c761f8ca0e57c40b73ef254e5e88c9178d2365b1'
PORTS=(
 ('root_p37c12_sdk_queue.py','root_p37c13_sdk_queue.py'),
 ('root_p37c12_mcp_entry.py','root_p37c13_mcp_entry.py'),
 ('root_native_build_binding_p37c12.py','root_native_build_binding_p37c13.py'),
 ('ROOT-FINAL-SDK-FREEZE-P37C12.json','ROOT-FINAL-SDK-FREEZE-P37C13.json'),
 ('ROOT-CAMPAIGN-MAP-ADMITTED-C12.json','ROOT-CAMPAIGN-MAP-ADMITTED-C13.json'),
 ('ROOT-C12-NORMAL-SOURCE-WARM-BOUND.json','ROOT-C13-NORMAL-SOURCE-WARM-BOUND.json'))
MASK="            self.flags = [flag for flag in self.flags if flag != '--private-active-scheme-sway-completion-execution-query']\n"

def require(ok,why):
 if not ok:raise ValueError(why)

def transform(raw):
 require(hashlib.sha256(raw).hexdigest()==BASE_SHA,'exact adopted C12 factory required')
 source=raw.decode('utf8');result=source
 for old,new in PORTS:
  require(result.count(old)==1 and new not in result,'single exact current-view constant required')
  result=result.replace(old,new)
 inverse=result
 for old,new in PORTS:inverse=inverse.replace(new,old)
 require(inverse==source,'non-namespace byte changed')
 mapping=dict(PORTS)
 class Constants(ast.NodeTransformer):
  def visit_Constant(self,node):
   if isinstance(node.value,str) and node.value in mapping:
    return ast.copy_location(ast.Constant(mapping[node.value]),node)
   return node
 expected=Constants().visit(ast.parse(source))
 require(ast.dump(ast.parse(result),include_attributes=False)==ast.dump(expected,include_attributes=False),
         'changes exceed six exact AST constants')
 require(result.count(MASK)==source.count(MASK)==1,'inherited unsupported execution-query mask differs')
 require("MACHINE='xenoamess-full-tower-eb9d2c1186'" in result,'machine identity changed')
 require('--private-war-daily-watch-speed2-trial' not in result,'trial opt-in must remain absent')
 compile(result,'root_p37c13_warm_resume.py','exec')
 return result.encode()

def pin(path):
 raw=Path(path).read_bytes()
 return dict(path=str(Path(path).resolve()),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--base',type=Path,required=True)
 parser.add_argument('--output',type=Path,required=True)
 args=parser.parse_args();result=transform(args.base.read_bytes())
 out=args.output.resolve();repo=Path(__file__).resolve().parents[2]
 require(out.is_relative_to(repo/'_runtime') and not out.exists(),'new repo _runtime review root required')
 out.mkdir(parents=True,exist_ok=False)
 target=out/'root_p37c13_warm_resume.py'
 with target.open('xb') as stream:stream.write(result)
 proof=dict(schema='xar.C13-normal-source-factory-exact-port/v1',machine_id='xenoamess-full-tower-eb9d2c1186',
  observed_at_utc=datetime.now(timezone.utc).isoformat(),status='SOURCE_READY_NO_CONSTRUCTOR_CREDIT',
  producer=pin(__file__),base=pin(args.base),factory=pin(target),exact_AST_constant_ports=list(PORTS),
  inverse_all_other_bytes_equal=True,execution_query_mask_preserved=True,trial_opt_in=False,
  physical_C11_imports_and_machine_episode_hash_constants_unchanged=True,
  admission_schema='xar.normal-clean-source-warm/v1',boundary='Actual clean seed/postclose:3033/raw53202696/current40526/episode/minNative1279/NEXT6345; not embedded in factory.',
  existing_startup_MET_caps_guards_unchanged=True,actual_Runtime_Game_RPC_calls=0)
 with (out/'QUALIFICATION.json').open('x',encoding='utf8') as stream:json.dump(proof,stream,indent=2);stream.write('\n')
 print(json.dumps(dict(factory=pin(target),qualification=pin(out/'QUALIFICATION.json'))))

if __name__=='__main__':main()
