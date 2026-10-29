package org.xar.ck3.control.wave2.military.holyreinf;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Once-only capture of the actual original producer and both consumers. Ordinary JUnit never runs Python. */
public final class HolyReinforcementGoldenCapture {
    private HolyReinforcementGoldenCapture() { }
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 4) { throw new IllegalArgumentException("repository python-exe fresh-output machine-id required"); }
        Path repository = Path.of(args[0]).toAbsolutePath().normalize(), output = Path.of(args[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) { throw new IllegalArgumentException("fresh output required"); }
        ProcessBuilder builder = new ProcessBuilder(List.of(args[1], "-B", "-X", "utf8", "-c", PROGRAM, repository.toString(), args[3]));
        builder.directory(repository.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1");
        builder.environment().put("PYTHONPATH", repository.resolve("ck3_autonomous_player/src") + File.pathSeparator
                + repository.resolve("ck3_autonomous_player/tests/unit"));
        builder.redirectError(ProcessBuilder.Redirect.INHERIT); Process process = builder.start(); byte[] bytes;
        try (var executor = Executors.newSingleThreadExecutor()) {
            var response = executor.submit(() -> { try (var stream = process.getInputStream()) { return stream.readNBytes(65_537); } });
            if (!process.waitFor(90, TimeUnit.SECONDS)) {
                process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); throw new IOException("producer capture timeout");
            }
            try { bytes = response.get(); } catch (ExecutionException error) { throw new IOException("producer read failed", error.getCause()); }
        }
        if (process.exitValue() != 0 || bytes.length == 0 || bytes.length > 65_536) { throw new IOException("capture failed/over budget: " + process.exitValue()); }
        Files.createDirectories(output.getParent()); Files.write(output, bytes, StandardOpenOption.CREATE_NEW);
        System.out.println("captured " + bytes.length + " bytes to " + output);
    }
    private static final String PROGRAM = """
            import sys,json,copy,hashlib,datetime,contextlib,gzip
            from pathlib import Path
            import pytest
            from xar_autoplayer import holy_order_siege_reinforcement_v1 as p
            from xar_autoplayer.bridge.driver import BridgeUnavailableError
            from test_holy_order_siege_reinforcement_service_v1 import _SyntheticCurrentWorld
            root=Path(sys.argv[1]); machine=sys.argv[2]
            original_tests=['ck3_autonomous_player/tests/unit/test_holy_order_siege_reinforcement_service_v1.py','ck3_autonomous_player/tests/unit/test_service_window_priority_copy.py']
            reports=[]
            class Reports:
                def pytest_runtest_logreport(self,report): reports.append(report)
            with contextlib.redirect_stdout(sys.stderr): code=pytest.main(['-q','-p','no:cacheprovider',*original_tests],plugins=[Reports()])
            calls=[r for r in reports if r.when=='call']
            if code!=0 or not calls or not all(r.passed for r in calls) or any(r.skipped for r in reports): raise RuntimeError('original consumer tests failed/skipped')
            def base(): return dict(policy='one-life-turn-v1',phase='native_war_siege_exit_blocked',selected_step=None,siege_state=dict(status='insufficient_strength',province_id=2592,player_army_besieging=True,garrison_size=1000,besieging_strength=600),pursuit=dict(war_id=44))
            def fresh():
                w=_SyntheticCurrentWorld(); s=w.take_snapshot(); c=w.query_player_holy_order_context_private_v1(expected_revision=s['revision']); return s,base(),c
            cases=[]
            def choice(name,s,plan,c):
                x=dict(schema='xar.ck3.holy-reinforcement-choose-input.v1',snapshot=s,plan=plan,holy_context=c)
                expected=p.choose_holy_order_siege_reinforcement_v1(snapshot=s,plan=plan,holy_context=c)
                cases.append(dict(name=name,operation='choose',input=copy.deepcopy(x),expected=expected))
            s,plan,c=fresh(); choice('current-native-zero-reference',s,plan,c)
            for name,field,value in [('native-hire-denied','can_hire',False),('native-afford-denied','can_afford',False)]:
                s,plan,c=fresh(); c['rows'][0]['military_terms'][field]=value; choice(name,s,plan,c)
            for name,edit in [('already-employed',lambda s,p,c:(c['rows'][0].update(employer_id=29829),c['rows'][0]['military_terms']['troop_association'].update(applies_to_player=True))),('current-deficit-too-large',lambda s,p,c:p['siege_state'].update(garrison_size=1100)),('troops-missing',lambda s,p,c:c['rows'][0]['military_terms'].pop('troop_strength')),('troops-unavailable',lambda s,p,c:c['rows'][0]['military_terms'].update(troop_strength=dict(available=False,unavailable_reason='not observed',current_soldiers=None))),('unavailable-input',lambda s,p,c:c.update(available=False,unavailable_reason='current query unavailable')),('other-selected-action',lambda s,p,c:p.update(selected_step='retreat-army-9')),('unpaused',lambda s,p,c:s.update(paused=False)),('war-no-longer-active',lambda s,p,c:s.update(active_wars=[])),('unknown-gold-stock',lambda s,p,c:s.pop('played_character_gold')),('native-quote-exceeds-piety',lambda s,p,c:s['played_character_piety'].update(raw=1)),('unsupported-resource-remains-separate',lambda s,p,c:c['rows'][0]['military_terms']['resource_costs_raw'].__setitem__(9,100))]:
                s,plan,c=fresh(); edit(s,plan,c); choice(name,s,plan,c)
            s,plan,c=fresh(); row=c['rows'][0]; row['holy_order_id']=4294967295; cheaper=copy.deepcopy(row); cheaper['holy_order_id']=0; cheaper['military_terms']['resource_costs_raw'][0]=99; c['rows']=[row,cheaper,copy.deepcopy(row)]; choice('native-currencies-lexicographic-full-reference-source-order',s,plan,c)
            s,plan,c=fresh(); terms=c['rows'][0]['military_terms']; terms.update(available=False,unavailable_reason='terms unreadable',can_hire=None,can_afford=None,resource_costs_raw=None); choice('partial-native-terms-remain-ineligible',s,plan,c)
            s,plan,c=fresh(); terms=c['rows'][0]['military_terms']
            terms['hire_cost_context']=dict(available=True,unavailable_reason=None,resource_scale=100000,order_title_resolved=True,order_title_id=0,order_title_holder_id=29829,title_holder_is_player=True,patron_is_player=None,employed_by_other=None,selected_patron_multiplier_raw=None,cost_branch='title_holder_zero')
            terms['current_war_eligibility']=dict(available=True,unavailable_reason=None,qualifies=False,reasons_available=True,reason_literal='independent subgate')
            terms['service_lifecycle']=dict(available=True,unavailable_reason=None,applies_to_player=False,release_eligible=None,associated_regiment_in_combat=None,release_check_queued=None)
            terms['current_reinforcement_v1']=dict(available=False,unavailable_reason='roster not observed',fraction_scale=100000,source_count=None,rows=[],army_roles=dict(available=False,unavailable_reason='role not observed',applies_to_player=False,rows=[]))
            choice('additive-observers-do-not-replace-final-predicates',s,plan,c)
            class Reader:
                def __init__(self,c): self.c=c
                def query_player_holy_order_context_private_v1(self,**kwargs): return copy.deepcopy(self.c)
            for name,available,caps,unavailable in [('planner-selected',True,[p.HIRE_HOLY_ORDER_V1_CAPABILITY],False),('planner-observation',True,[p.HIRE_HOLY_ORDER_V1_CAPABILITY],True),('planner-no-query',False,[p.HIRE_HOLY_ORDER_V1_CAPABILITY],False),('planner-no-capability',True,[],False)]:
                s,plan,c=fresh()
                if unavailable:c.update(available=False,unavailable_reason='query unavailable')
                planned=dict(revision=s['revision'],plan=plan,unrelated={'preserved':[]}); driver=Reader(c) if available else object()
                x=dict(schema='xar.ck3.holy-reinforcement-plan-input.v1',snapshot=s,planned=planned,bridge_capabilities=caps,query_available=available,holy_context=c,query_error=None)
                cases.append(dict(name=name,operation='plan',input=copy.deepcopy(x),expected=p.plan_holy_order_siege_reinforcement_v1(driver,planned=planned,snapshot=s,bridge_capabilities=caps)))
            def post(name,edit):
                w=_SyntheticCurrentWorld(); before=w.take_snapshot(); before_context=w.query_player_holy_order_context_private_v1(expected_revision=10); plan=base()
                proposal=p.choose_holy_order_siege_reinforcement_v1(snapshot=before,plan=plan,holy_context=before_context)
                ack=w.hire_holy_order_v1(holy_order_id=0,expected_revision=10); after=w.take_snapshot(); after_context=w.query_player_holy_order_context_private_v1(expected_revision=11)
                strengths=w.query_army_strengths(army_ids=[218104222],expected_revision=11); expenses=w.query_war_cash_current_resources_private_v1(expected_revision=11)
                data=dict(ack=ack,after=after,context=after_context,strengths=strengths,expenses=expenses); edit(data)
                class Frozen:
                    def hire_holy_order_v1(self,**kw): return copy.deepcopy(data['ack'])
                    def take_snapshot(self):
                        if data.get('post_error'): raise BridgeUnavailableError(data['post_error'])
                        return copy.deepcopy(data['after'])
                    def query_player_holy_order_context_private_v1(self,**kw): return copy.deepcopy(data['context'])
                    def query_army_strengths(self,**kw): return copy.deepcopy(data['strengths'])
                    def query_war_cash_current_resources_private_v1(self,**kw): return copy.deepcopy(data['expenses'])
                expected=p.submit_holy_order_siege_reinforcement_v1(Frozen(),plan={'holy_order_hire_proposal':proposal},expected_revision=10)
                x=dict(schema='xar.ck3.holy-reinforcement-post-input.v1',before_snapshot=before,plan=plan,before_context=before_context,ack=data['ack'],after_snapshot=None if data.get('post_error') else data['after'],after_context=None if data.get('post_error') else data['context'],army_strengths=data['strengths'],actor_expenses=data['expenses'] if data['ack'].get('accepted') is True and not data.get('post_error') else None,expense_query_error=None,post_query_error=data.get('post_error'))
                cases.append(dict(name=name,operation='post',input=x,expected=expected))
            post('ack-and-independent-material-army',lambda d:None)
            post('ack-denied-never-grants-state',lambda d:d['ack'].update(accepted=False))
            post('employer-only-not-usable',lambda d:d['strengths'].update(army_strengths=[]))
            post('unknown-army-not-usable',lambda d:d['strengths']['army_strengths'][0].update(status='unavailable'))
            post('uncontrollable-army-not-usable',lambda d:d['after']['player_armies'][0].update(controllable=False))
            post('different-date-cannot-attribute-quote',lambda d:(d['after'].update(date_raw=53288592),d['context'].update(date_raw=53288592)))
            post('wallet-delta-mismatch-observed',lambda d:d['after']['played_character_piety'].update(raw=900000))
            post('employer-unknown-never-grants-army',lambda d:(d['context']['rows'][0].update(employer_id=None),d['context']['rows'][0]['military_terms']['troop_association'].update(applies_to_player=False,rows=[])))
            post('unknown-post-query-never-replays-or-grants-army',lambda d:d.update(post_error='post query unavailable'))
            post('material-army-tie-prefers-lower-full-id',lambda d:(d['after']['player_armies'].append(dict(army_id=10,owner_character_id=4444,controllable=True,current_province_id=460)),d['strengths']['army_strengths'].append(dict(status='available',army_id=10,native_carmy_id=0,current_soldiers=500))))
            paths=['ck3_autonomous_player/src/xar_autoplayer/holy_order_siege_reinforcement_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/player_holy_order_context_private_transport.py','ck3_autonomous_player/src/xar_autoplayer/bridge/holy_order_current_reinforcement_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/player_holy_order_hire_cost_context.py','ck3_autonomous_player/src/xar_autoplayer/bridge/nonwar_private_build.py','ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py',*original_tests]
            pins=[dict(path=path,sha256=hashlib.sha256((root/path).read_bytes()).hexdigest()) for path in paths]
            result=dict(schema='xar.ck3.holy-reinforcement-golden.v1',machine_id=machine,captured_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_machine_id='unknown',synthetic_world_and_callback_outcomes=True,actual_production_functions=True,original_tests=len(calls),original_skipped=0,source_pins=pins,cases=cases)
            raw=json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
            if len(raw)>262144: raise RuntimeError('uncompressed capture byte budget exceeded')
            packed=gzip.compress(raw,mtime=0)
            if len(packed)>65536: raise RuntimeError('compressed capture byte budget exceeded')
            sys.stdout.buffer.write(packed)
            """;
}
