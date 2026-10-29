package org.xar.ck3.control.g2.m0;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Actual original recommendation -> typed Java trace -> original formal planner and persisted trace. */
public final class RaiktorUtilityComparisonTraceOracle {
    private static final JsonNodeFactory JSON = JsonNodeFactory.instance;
    private static final List<String> PINNED = List.of(
            "ck3_autonomous_player/src/xar_autoplayer/raiktor_formal_exit.py",
            "ck3_autonomous_player/src/xar_autoplayer/simulation/raiktor_three_way_exit_recommendation.py",
            "ck3_autonomous_player/src/xar_autoplayer/simulation/raiktor_three_way_exit_action_gate.py",
            "ck3_autonomous_player/src/xar_autoplayer/simulation/raiktor_exit_utility_evaluator.py",
            "ck3_autonomous_player/src/xar_autoplayer/simulation/raiktor_white_peace_narrow_projection_provider.py",
            "ck3_autonomous_player/src/xar_autoplayer/simulation/raiktor_white_peace_comparison_contracts.py",
            "ck3_autonomous_player/src/xar_autoplayer/simulation/raiktor_owner_budget_profile_provider.py",
            "ck3_autonomous_player/src/xar_autoplayer/simulation/raiktor_exit_utility_model_provider.py",
            "ck3_autonomous_player/src/xar_autoplayer/bridge/raiktor_surrender_session_binding_contract.py",
            "ck3_autonomous_player/src/xar_autoplayer/bridge/raiktor_surrender_six_domain_contract.py",
            "ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py",
            "ck3_autonomous_player/strategies/raiktor_exit_budget_v1.json",
            "ck3_autonomous_player/strategies/raiktor_exit_utility_v1.json",
            "ck3_autonomous_player/tests/unit/test_raiktor_exit_utility_evaluator.py",
            "ck3_autonomous_player/tests/unit/test_raiktor_white_peace_narrow_projection_provider.py",
            "ck3_autonomous_player/tests/unit/test_raiktor_formal_exit_consumer.py",
            "ck3_autonomous_player/tests/unit/test_raiktor_three_way_exit_recommendation.py");
    private RaiktorUtilityComparisonTraceOracle() { }

    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("repo, original Python, machine ID required");
        System.out.println(new String(RaiktorExitObservationCodec.encodeWire(run(Path.of(args[0]), args[1], args[2])), StandardCharsets.UTF_8));
    }

    public static ObjectNode run(Path repository, String python, String machineId) throws Exception {
        Path repo = repository.toRealPath(); ObjectNode before = pins(repo);
        ProcessBuilder builder = new ProcessBuilder(python, "-B", "-c", SCRIPT, repo.toString());
        builder.directory(repo.toFile()); builder.redirectError(ProcessBuilder.Redirect.INHERIT);
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        for (String key : List.of("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"))
            builder.environment().put(key, "1");
        Process process = builder.start();
        ObjectNode childReport = null; int handled = 0;
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                require(++handled <= 512 && line.length() <= 1_048_576, "bounded original consumer protocol exceeded");
                JsonNode packet = RaiktorExitObservationCodec.parseWire(line.getBytes(StandardCharsets.UTF_8));
                if (packet.has("report")) { childReport = (ObjectNode) packet.get("report"); break; }
                ObjectNode reply;
                try {
                    byte[] result = RaiktorUtilityComparisonTrace.execute(
                            RaiktorExitObservationCodec.encodeWire(packet.get("certificate")));
                    JsonNode value = RaiktorExitObservationCodec.parseWire(result);
                    var trace = RaiktorUtilityComparisonTrace.fromTrace(value);
                    require(value.equals(RaiktorExitObservationCodec.parseWire(RaiktorExitObservationCodec.encodeWire(
                            RaiktorUtilityComparisonTrace.toJson(trace)))), "typed trace JSON persistence changed");
                    require(trace.equals(RaiktorUtilityComparisonTrace.fromTrace(value)), "typed trace record roundtrip changed");
                    ObjectNode mutation = (ObjectNode) value.deepCopy(); mutation.withObject("/options/continue").put("utility_raw", 1);
                    require(!mutation.equals(RaiktorUtilityComparisonTrace.toJson(trace)), "trace retained mutable JSON");
                    boolean immutable = false;
                    try { trace.options().continuation().facts().hardBudgetBreaches().add("mutation"); }
                    catch (UnsupportedOperationException expected) { immutable = true; }
                    require(immutable, "trace lists remained mutable");
                    reply = JSON.objectNode().put("accepted", true); reply.set("result", value);
                } catch (IllegalArgumentException rejected) {
                    reply = JSON.objectNode().put("accepted", false).put("message", rejected.getMessage());
                }
                process.getOutputStream().write(RaiktorExitObservationCodec.encodeWire(reply));
                process.getOutputStream().write('\n'); process.getOutputStream().flush();
            }
            require(process.waitFor(45, TimeUnit.SECONDS), "original consumer did not exit before deadline");
            require(process.exitValue() == 0 && childReport != null, "original consumer failed or omitted report");
        } finally {
            if (process.isAlive()) {
                process.descendants().forEach(child -> child.destroyForcibly()); process.destroyForcibly();
                process.waitFor(5, TimeUnit.SECONDS);
            }
        }
        require(before.equals(pins(repo)), "original producer/consumer source changed");
        ObjectNode request = JSON.objectNode().put("operation", RaiktorUtilityComparisonTrace.OPERATION);
        request.set("certificate", childReport.get("example_certificate"));
        byte[] expected = RaiktorUtilityComparisonTrace.execute(RaiktorExitObservationCodec.encodeWire(request.get("certificate")));
        require(java.util.Arrays.equals(expected, RaiktorUtilityComparisonTrace.executeOperation(RaiktorExitObservationCodec.encodeWire(request))),
                "M0 internal operation and typed consumer disagree");
        int rawRejected = 0;
        for (byte[] raw : List.of("{} {}".getBytes(StandardCharsets.UTF_8), new byte[] {(byte) 0xff},
                "{\"operation\":\"project-formal-exit-utility-trace\",\"operation\":\"bad\",\"certificate\":{}}".getBytes(StandardCharsets.UTF_8),
                new byte[RaiktorExitObservationCodec.MAX_WIRE_BYTES + 1])) {
            try { RaiktorUtilityComparisonTrace.executeOperation(raw); }
            catch (IllegalArgumentException expectedRejection) { rawRejected++; }
        }
        require(rawRejected == 4, "actual raw ingress did not reject malformed packets");
        childReport.remove("example_certificate");
        ObjectNode report = JSON.objectNode().put("schema", "xar.raiktor-formal-exit-typed-trace/v1")
                .put("machine_id", machineId).put("observed_at_utc", Instant.now().toString()).put("status", "PASS")
                .put("child_exit", process.exitValue()).put("protocol_requests", handled - 1).put("raw_boundary_rejections", rawRejected)
                .put("new_game_actions", 0).put("native_or_live_acceptance", "NOT_RUN");
        report.set("actual_original_chain", childReport); report.set("source_pre_post_MATCH", before);
        return report;
    }

    private static ObjectNode pins(Path root) throws Exception {
        ObjectNode result = JSON.objectNode();
        for (String relative : PINNED) {
            byte[] raw = Files.readAllBytes(root.resolve(relative));
            result.set(relative, JSON.objectNode().put("bytes", raw.length)
                    .put("sha256", HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw))));
        }
        return result;
    }
    private static void require(boolean condition, String reason) { if (!condition) throw new IllegalStateException(reason); }

    private static final String SCRIPT = """
import copy, importlib, io, json, sys, unittest
from pathlib import Path
repo=Path(sys.argv[1]).resolve()
sys.path[:0]=[str(repo),str(repo/'ck3_autonomous_player/src'),str(repo/'ck3_autonomous_player/tests/unit')]
import xar_autoplayer.raiktor_formal_exit as formal
import test_raiktor_three_way_exit_recommendation as producer
original=formal._utility_comparison_trace
for function,relative in [(original,'ck3_autonomous_player/src/xar_autoplayer/raiktor_formal_exit.py'),
        (producer.provide_raiktor_three_way_exit_recommendation,'ck3_autonomous_player/src/xar_autoplayer/simulation/raiktor_three_way_exit_recommendation.py'),
        (producer._provide,'ck3_autonomous_player/tests/unit/test_raiktor_three_way_exit_recommendation.py')]:
    if Path(sys.modules[function.__module__].__file__).resolve()!=(repo/relative).resolve():
        raise RuntimeError('original source import drifted')
def java_trace(certificate):
    print(json.dumps({'certificate':certificate},ensure_ascii=True,allow_nan=False,separators=(',',':')),flush=True)
    line=sys.stdin.readline()
    if not line or len(line)>1048576: raise RuntimeError('typed Java response unavailable')
    reply=json.loads(line)
    if not reply['accepted']: raise ValueError(reply['message'])
    result=reply['result']
    if json.loads(json.dumps(result,allow_nan=False))!=result: raise AssertionError('persisted trace drift')
    return result
cases=0; accepted=0; rejected=0; strict=0
def check(name,certificate,delta=False):
    global cases,accepted,rejected,strict
    try: expected=original(copy.deepcopy(certificate)); old=True
    except (KeyError,TypeError,ValueError): old=False; expected=None
    try: actual=java_trace(copy.deepcopy(certificate)); new=True
    except ValueError: new=False; actual=None
    if delta:
        if not old or new: raise AssertionError(name+': documented typed rejection missing')
        strict+=1
    else:
        if old!=new or old and expected!=actual: raise AssertionError(name+': original consumer drift')
        accepted+=int(new); rejected+=int(not new)
    cases+=1
actual_certificates=[]
for relation in ['opponent_stronger','equal','actor_stronger']:
    for score,days in [(41,365),(-3,729),(-3,804),(-100,804)]:
        result=producer._provide(production_live=True,relation=relation,score=score,war_duration_days=days)
        certificate=result['recommendation_certificate']
        if certificate is None: raise AssertionError('original producer did not produce a certificate')
        actual_certificates.append(certificate)
        check('actual-'+relation+'-'+str(score)+'-'+str(days),certificate)
base=actual_certificates[0]
for path in [('utility_unit',),('options',),('comparison',),
        *[('options',name,key) for name in ['continue','white_peace','surrender']
          for key in ['eligible','utility_raw','hard_budget_breaches']],
        *[('options','continue',key) for key in ['measured_power_relation','tail_risk_penalty_raw',
          'tail_risk_base_penalty_raw','tail_risk_power_scale_applied','observed_war_duration_days',
          'observed_player_relative_war_score','measured_power_ratio_raw','measured_power_ratio_scale']],
        ('options','white_peace','uncertainty_penalty_raw'),('options','surrender','uncertainty_penalty_raw'),
        *[('comparison',key) for key in ['status','eligible_options','winning_margin_raw','minimum_switch_margin_raw']]]:
    changed=copy.deepcopy(base); target=changed
    for key in path[:-1]: target=target[key]
    del target[path[-1]]
    check('missing-'+'.'.join(path),changed)
numeric=[('options',name,'utility_raw') for name in ['continue','white_peace','surrender']]+[
    ('options','continue',key) for key in ['tail_risk_penalty_raw','tail_risk_base_penalty_raw',
      'observed_war_duration_days','observed_player_relative_war_score','measured_power_ratio_raw','measured_power_ratio_scale']]+[
    ('options','white_peace','uncertainty_penalty_raw'),('options','surrender','uncertainty_penalty_raw'),
    ('comparison','winning_margin_raw'),('comparison','minimum_switch_margin_raw')]
for path in numeric:
    for token in [True,1.0]:
        changed=copy.deepcopy(base); target=changed
        for key in path[:-1]: target=target[key]
        target[path[-1]]=token
        check('wrong-numeric-kind-'+'.'.join(path),changed,True)
for path in [('options','continue','eligible'),('options','white_peace','eligible'),('options','surrender','eligible'),
        ('options','continue','tail_risk_power_scale_applied')]:
    changed=copy.deepcopy(base); target=changed
    for key in path[:-1]: target=target[key]
    target[path[-1]]=1
    check('integer-boolean-'+'.'.join(path),changed,True)
for path,token in [(('options','continue','measured_power_relation'),'unknown'),
        (('comparison','status'),'unknown'),(('comparison','eligible_options'),['continue',True]),
        (('options','surrender','execution_blockers'),[True])]:
    changed=copy.deepcopy(base); target=changed
    for key in path[:-1]: target=target[key]
    target[path[-1]]=token
    check('wrong-typed-field-'+'.'.join(path),changed,True)
for name in ['continue','white_peace','surrender']:
    changed=copy.deepcopy(base); changed['options'][name].pop('execution_blockers',None)
    check('omitted-optional-blockers-'+name,changed)
    changed=copy.deepcopy(base); changed['options'][name]['execution_blockers']=None
    check('null-is-not-missing-blockers-'+name,changed)
changed=copy.deepcopy(base)
changed['comparison']['winning_margin_raw']=None
check('explicit-null-winning-margin',changed)
changed['comparison']['eligible_options']=[]
check('empty-list-is-not-null',changed)
changed=copy.deepcopy(base)
changed['options']['continue']['hard_budget_breaches']=['b','b','a']
changed['comparison']['eligible_options']=['surrender','continue','white_peace','continue']
changed['options']['continue']['utility_raw']=-(2**80)
changed['comparison']['winning_margin_raw']=2**81
changed['ignored_extension']={'float':1.0,'zero':-0.0,'empty':[],'null':None}
check('preserved-order-duplicates-bigint-ignored-extension',changed)
formal._utility_comparison_trace=java_trace
consumer=importlib.import_module('test_raiktor_formal_exit_consumer')
suite=unittest.defaultTestLoader.loadTestsFromModule(consumer)
result=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(suite)
if not result.wasSuccessful() or result.skipped: raise AssertionError('complete original formal consumer suite failed or skipped')
print(json.dumps({'report':{'differential_cases':cases,'equivalent_accepted':accepted,
    'equivalent_rejected':rejected,'explicit_typed_contract_differences':strict,
    'actual_original_recommendation_certificates':len(actual_certificates),
    'original_formal_consumer_tests':result.testsRun,'skips':len(result.skipped),
    'example_certificate':base}},allow_nan=False,separators=(',',':')),flush=True)
""";
}
