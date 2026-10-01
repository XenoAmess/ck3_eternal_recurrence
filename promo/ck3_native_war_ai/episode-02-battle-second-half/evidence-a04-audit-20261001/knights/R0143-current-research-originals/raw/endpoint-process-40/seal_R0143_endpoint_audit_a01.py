from pathlib import Path
import hashlib,json,sys
B=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001');O=B/'R0143-four-save-endpoint-audit-reinforcement-a01'
def ident(p):
 p=Path(p).resolve()
 with p.open('rb')as f:d=hashlib.file_digest(f,'sha256').hexdigest().upper()
 return {'path':str(p),'bytes':p.stat().st_size,'sha256':d}
def main():
 sys.stdout.reconfigure(encoding='utf-8');receipt=O/'R0143-final-readonly-endpoint-receipt-a01.json';facts=O/'R0143-actual-endpoint-semantic-facts-a01.json'
 copies=[]
 for n in ['R0143-final-facts-a01.stdout.bin','R0143-final-facts-a01.stderr.bin','R0143-final-facts-a01-intent.json','R0143-final-facts-a01-process.json','seal_R0143_endpoint_audit_a01.py']:
  src=B/n;dst=O/'exact-copies'/n;before=ident(src)
  with dst.open('xb')as f:f.write(src.read_bytes())
  assert ident(src)==before and ident(dst)['sha256']==before['sha256'];copies.append({'original':before,'exact_copy':ident(dst)})
 verification=json.loads((O/'R0143-four-save-endpoint-verification.json').read_text(encoding='utf-8'))
 for state in verification['saved_states']:assert ident(state['immutable']['path'])==state['immutable']
 content='''# R0143 原版四存档端点核对

本目录只读取 R0143：runtime 419cac1a956c7be356d886256c7bc689cda5327d，PID17420，native-29829-a5224cf6dfcc。四份原版 immutable 存档逐 SHA 对原 native checkpoint 绑定，实际使用 Rakaly0.8.19 解码；raw exact copies、解码全文、角色/战斗/家族/荣誉全块差分和实际 argv/stdout/stderr 均保留。

新增端点证据：33437 在 1066.12.30 保存为死亡，reason death_battle、killer34120，军团65脱离；34120 的 prestige currency 和 accumulated 各+150、kills新增33437、signature_weapon新增axe。Army18 defender regiment14→13；原版UI getter left11→10只移除33437/right19不变。两个UI窗口的保存态顶层 RNG 端点相等，推进日 random_count +948。

UI 原图与前后 paused snapshot/subject/PID/GUI thread/context/owner 已核 SHA 和原件绑定；root 人工审图回执原样保留，本报告不制造新的视觉审批。上述存档及 getter 是端点证据：daily trace export容量失败，DTO未发布；monitor accepted=false/status failed/flags8/truncated128/uninstalledtrue，仅部分诊断。未运行严格 causal/selector/monitor 成功验收，13域完整可变链及机制后三项仍 pending，global_bundle_complete=false。相同端点不证明日内无写入/分支未执行/唯一因果。

权威事实为 R0143-actual-endpoint-semantic-facts-a01.json；完整过程主回执 R0143-final-readonly-endpoint-receipt-a01.json。较早 semantic-facts.json 是本轮派生中间件，保留历史，不作为最终13域状态。全过程未改源码、原件、Git、屏幕、游戏或视频；没有加载 R0142 的存档或读数。
'''
 with(O/'README.md').open('x',encoding='utf-8',newline='\n')as f:f.write(content)
 assets=[ident(p)for p in sorted(O.rglob('*'))if p.is_file()]
 report={'kind':'R0143_ENDPOINT_READONLY_SOURCE_STOP_SEAL_A01','author':'/root/a04_reinforcement_evidence','status':'READY_ENDPOINT_ONLY_MECHANISM_PENDING','facts':ident(facts),'receipt':ident(receipt),'final_process_copies':copies,'all_current_exact_asset_count':len(assets),'all_current_exact_assets':assets,'original_four_saves_rechecked_unchanged':True,'source_stop':True,'no_source_Git_game_screen_video_operation':True,'global_bundle_complete':False,'case_13_domain_complete':False}
 out=O/'R0143-readonly-endpoint-ready-seal-a01.json'
 with out.open('x',encoding='utf-8',newline='\n')as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({'seal':ident(out),'facts':ident(facts),'receipt':ident(receipt),'asset_count':len(assets)},ensure_ascii=False))
if __name__=='__main__':main()
