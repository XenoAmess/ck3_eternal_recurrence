package org.xar.ck3.control.g2.m0;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

/** Real original producers feed the compiled Java producer, including changed schema rejection cases. */
public final class WarExitCodecOracle {
    private static final List<String> PINNED = List.of(
        "ck3_autonomous_player/src/xar_autoplayer/simulation/raiktor_white_peace_comparison_contracts.py",
        "ck3_autonomous_player/src/xar_autoplayer/bridge/raiktor_surrender_session_binding_contract.py",
        "ck3_autonomous_player/src/xar_autoplayer/simulation/raiktor_exit_utility_evaluator.py",
        "ck3_autonomous_player/src/xar_autoplayer/simulation/raiktor_white_peace_narrow_projection_provider.py",
        "ck3_autonomous_player/src/xar_autoplayer/bridge/raiktor_surrender_six_domain_contract.py",
        "ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py",
        "ck3_autonomous_player/tests/unit/test_raiktor_exit_utility_evaluator.py",
        "ck3_autonomous_player/tests/unit/test_raiktor_white_peace_narrow_projection_provider.py",
        "ck3_autonomous_player/tests/unit/test_raiktor_surrender_session_binding_contract.py",
        "ck3_autonomous_player/tests/unit/test_raiktor_surrender_six_domain_contract.py");
    private WarExitCodecOracle() { }
    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("repo, qualified Python, machine ID required");
        ObjectNode report = run(Path.of(args[0]), args[1], args[2]);
        System.out.println(WarExitCodecProbe.MAPPER.writeValueAsString(report));
    }
    public static ObjectNode run(Path repo, String python, String machineId) throws Exception {
        ObjectNode before = pins(repo);
        ProcessBuilder builder = new ProcessBuilder(python, "-B", "-c", SCRIPT, repo.toAbsolutePath().toString());
        builder.directory(repo.toFile()); builder.redirectError(ProcessBuilder.Redirect.INHERIT);
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        Process process = builder.start();
        CompletableFuture<byte[]> output = CompletableFuture.supplyAsync(() -> {
            try { return process.getInputStream().readNBytes(2_097_153); }
            catch (IOException error) { throw new IllegalStateException(error); }
        });
        if (!process.waitFor(45, TimeUnit.SECONDS)) {
            process.descendants().forEach(child -> child.destroyForcibly()); process.destroyForcibly();
            throw new IllegalStateException("original producer exceeded finite deadline");
        }
        byte[] raw = output.get(5, TimeUnit.SECONDS);
        if (process.exitValue() != 0 || raw.length > 2_097_152)
            throw new IllegalStateException("original producer failed or exceeded bounded output");
        // The bounded corpus contains many individual role-sized requests; its envelope is not a role request.
        JsonNode corpus = WarExitCodecProbe.MAPPER.readTree(raw);
        int checks = 0, strictDifferences = 0, accepted = 0, rejected = 0;
        for (JsonNode sample : corpus.path("cases")) {
            JsonNode actual = null; boolean success = false;
            try {
                actual = WarExitCodecProbe.execute(sample.get("request")).get("result"); success = true;
            } catch (IllegalArgumentException expectedRejection) { /* Actual production rejection is compared below. */ }
            boolean oldAccepted = sample.path("accepted").booleanValue();
            boolean strictDifference = sample.path("strict_delta").booleanValue();
            if (strictDifference) {
                require(oldAccepted && !success, sample.path("id").asText() + ": strict numeric rejection missing");
                strictDifferences++;
            } else {
                require(oldAccepted == success, sample.path("id").asText() + ": producer acceptance changed");
                if (success) {
                    require(sample.get("result").equals(actual), sample.path("id").asText() + ": normalized JSON domain changed");
                    // Persist and parse the real Java output; integer/float/null/empty collection types remain distinct.
                    JsonNode reparsed = WarExitCodecProbe.parse(WarExitCodecProbe.MAPPER.writeValueAsBytes(actual));
                    require(actual.equals(reparsed), sample.path("id").asText() + ": Java JSON roundtrip drift");
                    if (sample.path("id").asText().equals("opaque-json-number-kind-and-negative-zero")) {
                        JsonNode opaque = reparsed.path("terms").path("opaque_extension");
                        require(opaque.path("float").isFloatingPointNumber() && opaque.path("integer").isIntegralNumber(),
                                "opaque integer/float type distinction lost through actual wire");
                        require(Double.doubleToRawLongBits(opaque.path("zero").doubleValue()) == Long.MIN_VALUE,
                                "opaque negative zero lost through actual wire and persistence");
                    }
                    accepted++;
                } else rejected++;
            }
            checks++;
        }
        // The projection/session chain uses the same real producer fixtures, not precomputed expected packets.
        var projection = RaiktorExitObservationCodec.normalizeProjection(corpus.get("projection"));
        var session = RaiktorExitObservationCodec.normalizeSession(corpus.get("session"), projection.observation());
        require(session.raw().equals(corpus.get("session")), "actual session chain changed source body");
        // Compare the agreed persisted JSON domain, not IntNode versus BigIntegerNode implementation classes.
        JsonNode persistedObservation = RaiktorExitObservationCodec.parseWire(
                RaiktorExitObservationCodec.encodeWire(projection.observation().toJson()));
        require(persistedObservation.equals(corpus.path("projection").get("white_peace_observation")),
                "actual projection chain changed normalized observation");
        ObjectNode detached = projection.observation().terms(); detached.put("consumer_mutation", true);
        require(!projection.observation().terms().has("consumer_mutation"), "terms escaped immutable boundary");
        ObjectNode after = pins(repo);
        require(before.equals(after), "original source changed during actual producer run");
        for (byte[] malformed : List.of(
                "{\"operation\":\"normalize-white-peace-observation\",\"operation\":\"normalize-surrender-session\",\"value\":{}}".getBytes(StandardCharsets.UTF_8),
                "{} {}".getBytes(StandardCharsets.UTF_8), new byte[] {(byte) 0xff},
                new byte[] {'{', 0, '}'}, new byte[RaiktorExitObservationCodec.MAX_WIRE_BYTES + 1])) {
            boolean refused = false;
            try { RaiktorExitObservationCodec.execute(malformed); }
            catch (IllegalArgumentException expected) { refused = true; }
            require(refused, "real raw boundary accepted malformed/duplicate/oversize JSON");
        }
        return WarExitCodecProbe.MAPPER.createObjectNode().put("schema", "xar.raiktor-exit-observation-java-differential/v1")
                .put("machine_id", machineId).put("observed_at_utc", Instant.now().toString())
                .put("status", "PASS").put("cases", checks).put("legacy_equivalent_accepted", accepted)
                .put("legacy_equivalent_rejected", rejected).put("explicit_strict_numeric_differences", strictDifferences)
                .put("projection_session_actual_chain_checks", 4).put("oracle_exit", process.exitValue())
                .put("actual_raw_boundary_rejections", 5).put("negative_zero_persistence_checks", 2)
                .put("full_original_consumer_suites", "NOT_RUN_BY_THIS_FOCUSED_ORACLE")
                .set("source_refs_before_after_MATCH", before);
    }
    private static ObjectNode pins(Path root) throws Exception {
        ObjectNode result = WarExitCodecProbe.MAPPER.createObjectNode();
        for (String relative : PINNED) {
            Path file = root.resolve(relative); byte[] raw = Files.readAllBytes(file);
            result.set(relative, WarExitCodecProbe.MAPPER.createObjectNode().put("bytes", raw.length)
                    .put("sha256", HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw))));
        }
        return result;
    }
    private static void require(boolean condition, String reason) { if (!condition) throw new IllegalStateException(reason); }

    private static final String SCRIPT = """
import copy, json, sys
from pathlib import Path
repo = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(repo), str(repo/'ck3_autonomous_player/src'), str(repo/'ck3_autonomous_player/tests/unit')]
from test_raiktor_white_peace_narrow_projection_provider import _snapshot, _options_query, _terms_query
from xar_autoplayer.simulation.raiktor_white_peace_narrow_projection_provider import provide_raiktor_white_peace_narrow_projection
from xar_autoplayer.simulation.raiktor_white_peace_comparison_contracts import normalize_white_peace_terms_observation
from xar_autoplayer.bridge.raiktor_surrender_session_binding_contract import normalize_raiktor_surrender_aggregate_session_binding
for function, relative in (
    (normalize_white_peace_terms_observation, 'ck3_autonomous_player/src/xar_autoplayer/simulation/raiktor_white_peace_comparison_contracts.py'),
    (normalize_raiktor_surrender_aggregate_session_binding, 'ck3_autonomous_player/src/xar_autoplayer/bridge/raiktor_surrender_session_binding_contract.py'),
    (provide_raiktor_white_peace_narrow_projection, 'ck3_autonomous_player/src/xar_autoplayer/simulation/raiktor_white_peace_narrow_projection_provider.py'),
    (_snapshot, 'ck3_autonomous_player/tests/unit/test_raiktor_white_peace_narrow_projection_provider.py'),
    (_terms_query, 'ck3_autonomous_player/tests/unit/test_raiktor_white_peace_narrow_projection_provider.py')):
    if Path(sys.modules[function.__module__].__file__).resolve() != (repo/relative).resolve():
        raise RuntimeError('actual original producer/fixture import origin drifted: '+relative)
terms_query = _terms_query()
projection = provide_raiktor_white_peace_narrow_projection(_snapshot(), _options_query(), terms_query)
session = terms_query['raiktor_surrender_aggregate_session']
base_observation = projection['white_peace_observation']
expected = session['binding']
cases = []
def add(name, request, delta=False):
    try:
        if request['operation'] == 'normalize-white-peace-observation':
            result = normalize_white_peace_terms_observation(request['value'])
        else:
            e=request['expected']
            result = normalize_raiktor_surrender_aggregate_session_binding(request['value'],
                expected_snapshot_id=e['snapshot_id'],expected_snapshot_revision=e['snapshot_revision'],
                expected_native_revision=e['native_revision'],expected_date_raw=e['date_raw'],
                expected_connection_generation=e['connection_generation'],expected_episode_run_id=e['episode_run_id'],
                expected_episode_character_id=e['episode_character_id'],expected_process_id=e['process_id'],expected_war_id=e['war_id'])
        item={'accepted':True,'result':result}
    except (KeyError,TypeError,ValueError) as error:
        item={'accepted':False,'error':type(error).__name__}
    cases.append({'id':name,'request':copy.deepcopy(request),'strict_delta':delta,**item})
def obs():
    return {'operation':'normalize-white-peace-observation','value':copy.deepcopy(base_observation)}
def ses():
    return {'operation':'normalize-surrender-session','value':copy.deepcopy(session),'expected':copy.deepcopy(expected)}
add('actual-observation',obs()); add('actual-session',ses())
for key in sorted(base_observation):
    q=obs(); del q['value'][key]; add('observation-missing-'+key,q)
q=obs();q['value']['extra']=None;add('observation-extra',q)
for token,label in [(True,'bool'),(1.0,'float')]:
    q=obs();q['value']['schema_version']=token;add('observation-schema-'+label,q,True)
    q=ses();q['value']['schema_version']=token;add('session-schema-'+label,q,True)
for key in ['frame','option','terms','producer','completeness']:
    q=obs();q['value'][key]=None;add('observation-null-'+key,q)
for key in ['evaluated_candidate_sha256','evaluated_surrender_terms_sha256']:
    q=obs();q['value'][key]='ab'*32;add('observation-lower-sha-'+key,q)
q=obs();q['value']['same_frame_stable']=1;add('observation-sameframe-integer',q)
q=obs();q['value']['same_frame_stable']=False;add('observation-false-sameframe-is-data',q)
q=obs();q['value']['status']='incomplete';add('observation-incomplete-is-data',q)
q=obs();q['value']['producer']['producer_id']='\\u00a0';add('python-whitespace-blank',q)
q=obs();q['value']['producer']['producer_version']='\\u00a0v3\\u00a0';add('preserve-source-whitespace',q)
for key in sorted(base_observation['completeness']):
    q=obs();q['value']['completeness'][key]=False;add('explicit-false-'+key,q)
    q=obs();q['value']['completeness'][key]=1;add('reject-integer-bool-'+key,q)
q=obs();q['value']['terms']['opaque_extension']={'float':1.0,'integer':1,'zero':-0.0,'null':None,'empty':[]}
add('opaque-json-number-kind-and-negative-zero',q)
for key in sorted(expected):
    q=ses();del q['value']['binding'][key];add('session-binding-missing-'+key,q)
    if type(expected[key]) is int:
        q=ses();q['value']['binding'][key]=float(expected[key]);add('session-binding-float-'+key,q,True)
        q=ses();q['expected'][key]=float(expected[key]);add('session-expected-float-'+key,q)
q=ses();q['value']['binding']['extra']=1;add('session-binding-extra',q)
for key in sorted(session['readiness']):
    q=ses();q['value']['readiness'][key]=False;add('session-readiness-false-'+key,q)
    q=ses();q['value']['readiness'][key]=1;add('session-readiness-integer-'+key,q,True)
q=ses();q['value']['aggregate']=None;add('session-aggregate-null',q)
q=ses();q['value']['failure']={};add('session-failure-object',q)
q=ses();q['value']['extra_metadata']={'empty':{},'opaque_float':1.0};add('session-preserve-outer-extension',q)
q=ses();del q['value']['failure'];add('session-original-optional-failure-omission',q)
print(json.dumps({'cases':cases,'projection':projection,'session':session},ensure_ascii=True,allow_nan=False,separators=(',',':')))
""";
}

