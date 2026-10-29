package org.xar.ck3.control.wave2.events.occurrence;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

/** One-time original producer capture, exclusively launched by the shared qualified Job owner. */
public final class OccurrenceGoldenCapture {
    private OccurrenceGoldenCapture() { }
    public static void main(String[] arguments) throws IOException, InterruptedException {
        if (arguments.length != 3) throw new IllegalArgumentException("repository python-executable new-output-file");
        Path root = Path.of(arguments[0]).toAbsolutePath().normalize();
        Path python = Path.of(arguments[1]).toAbsolutePath().normalize();
        Path output = Path.of(arguments[2]).toAbsolutePath().normalize();
        if (!Files.isDirectory(root) || !Files.isRegularFile(python) || Files.exists(output)) throw new IllegalArgumentException("capture paths");
        Files.createDirectories(output.getParent());
        String machine = new String(run(List.of(python.toString(), root.resolve("tools/ck3_live_run_id.py").toString(), "machine"),
            root, output.resolveSibling(output.getFileName() + ".machine.stderr"), 4096), StandardCharsets.UTF_8).strip();
        if (!machine.matches("[A-Za-z0-9][A-Za-z0-9._-]{3,127}")) throw new IllegalStateException("machine identity unavailable");
        byte[] golden = run(List.of(python.toString(), "-c", CAPTURE, root.toString(), machine), root,
            output.resolveSibling(output.getFileName() + ".producer.stderr"), 81_920);
        Files.write(output, golden, StandardOpenOption.CREATE_NEW);
        System.out.println("captured " + golden.length + " bytes on " + machine);
    }
    private static byte[] run(List<String> command, Path root, Path errors, int maximum) throws IOException, InterruptedException {
        ProcessBuilder builder = new ProcessBuilder(command).directory(root.toFile()).redirectError(errors.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTHONPATH", root.resolve("ck3_autonomous_player/src").toString());
        Process process = builder.start();
        FutureTask<byte[]> reading = new FutureTask<>(() -> process.getInputStream().readNBytes(maximum + 1));
        Thread.startVirtualThread(reading);
        try {
            if (!process.waitFor(90, TimeUnit.SECONDS)) throw new IOException("original capture timed out");
            byte[] bytes = reading.get(5, TimeUnit.SECONDS);
            if (process.exitValue() != 0 || bytes.length > maximum) throw new IOException("original producer capture rejected: " + process.exitValue());
            return bytes;
        } catch (ExecutionException | TimeoutException error) { throw new IOException("capture output unavailable", error); }
        finally { if (process.isAlive()) process.destroyForcibly(); reading.cancel(true); }
    }
    private static final String CAPTURE = """
from pathlib import Path
from datetime import datetime, timezone
import copy, hashlib, json, sys
root, machine = Path(sys.argv[1]), sys.argv[2]
from xar_autoplayer.vanilla_events.occurrence import observed_event_occurrences_v1
from xar_autoplayer.vanilla_events.policy import _typed_character_id
from xar_autoplayer.bridge.event_window_context_contract import QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP
def query(instance=11, snapshot='native:a', public=3, native=7, actor=29829, key='health.1015'):
    context = {'status':'available','current_event_instance_id':instance,'snapshot_revision':native,
        'date_raw':1000,'event_definition_key':key,'root_scope':{'status':'available','type_key':'character',
        'typed_identity':{'status':'available','kind':'character','character_id':actor}}}
    return {'command':QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,'ok':True,'result':{
        'step':QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,'accepted':True,'current_event_window_context':context,
        'current_event_instance_id':instance,'queried_native_revision':native,'snapshot_revision':native,
        'date_raw':1000,'queried_revision':public,'queried_snapshot_id':snapshot}}
def select(instance=11, snapshot='native:a', public=3, new=12):
    return {'command':'select-event-option-2','ok':True,'result':{'accepted':True,'event_selection':{
        'status':'event_instance_advanced','postcondition_verified':True,'selected_option_number':2,
        'selected_native_option_index':1,'new_event_instance_id':new,'old_event_instance_id':instance,
        'starting_snapshot_id':snapshot,'starting_revision':public}}}
cases = []
def add(name, commands):
    request = {'schema':'xar.ck3.event-occurrence-input/v1','event_definition_key':'health.1015','played_character_id':29829,'commands':commands}
    expected = observed_event_occurrences_v1(commands,event_key='health.1015',played_character_id=29829,character_id_reader=_typed_character_id)
    cases.append({'name':name,'request':request,'expected':expected})
add('history-unavailable', None)
add('empty-history', [])
add('query-is-not-occurrence', [query()])
add('one-verified-selection-public3-native7', [query(),select()])
add('native-plus-expanded-duplicate-is-one', [query(),select(),copy.deepcopy(select())])
add('two-distinct-frames', [query(),select(),query(12,'native:b',4,8),select(12,'native:b',4,13)])
add('non-object-history-rows-are-ignored', [None,'irrelevant',42])
add('other-actor-is-not-this-player', [query(actor=999),select()])
add('other-event-is-not-this-event', [query(key='other.1'),select()])
add('unbound-selection', [select()])
row = select(); row['result']['event_selection']['status']='submitted'; row['result']['event_selection']['postcondition_verified']=False
add('ack-only-does-not-count', [query(),row])
row = select(); row['ok']=False; add('failed-command', [query(),row])
row = select(); row['result']['accepted']=False; add('rejected-submit', [query(),row])
row = select(); row['result']['event_selection']['postcondition_verified']=False; add('postcondition-unverified', [query(),row])
row = select(); row['result']['event_selection']['selected_option_number']=1; add('option-number-mismatch', [query(),row])
row = select(); row['result']['event_selection']['new_event_instance_id']=11; add('same-instance', [query(),row])
row = select(); row['result']['event_selection'].pop('old_event_instance_id'); add('old-instance-missing', [query(),row])
row = select(); row['result']['event_selection'].pop('starting_snapshot_id'); add('starting-frame-missing', [query(),row])
row = select(); row['result']['event_selection']['starting_revision']=4; add('public-frame-unbound', [query(),row])
add('conflicting-query-identity', [query(),query(actor=999),select()])
row = query(); row['result']['date_raw']=1001; add('query-date-drift', [row,select()])
row = query(); row['result']['current_event_window_context']['root_scope']['typed_identity']['kind']='province'; add('typed-character-kind-drift', [row,select()])
row = select(); row['command']='select-event-option-0002'; add('ascii-leading-zero-step-is-parsed', [query(),row])
row = select(); row['command']='select-event-option-２'; add('unicode-digit-step-is-not-parsed', [query(),row])
add('duplicate-query-same-identity', [query(),copy.deepcopy(query()),select()])
add('no-next-event-is-valid-advance', [query(),select(new=None)])
add('query-first-pass-binds-earlier-selection-row', [select(),query()])
row = query(); row['result']['queried_native_revision']=3; add('public-revision-cannot-replace-native', [row,select()])
paths = ['ck3_autonomous_player/src/xar_autoplayer/vanilla_events/occurrence.py',
    'ck3_autonomous_player/src/xar_autoplayer/vanilla_events/policy.py',
    'ck3_autonomous_player/src/xar_autoplayer/bridge/event_contract.py',
    'ck3_autonomous_player/src/xar_autoplayer/bridge/event_window_context_contract.py']
record = {'schema':'xar.ck3.event-occurrence-golden/v1','machine_id':machine,'captured_at':datetime.now(timezone.utc).isoformat(),
    'evidence_scope':'actual-original-occurrence-producer; synthetic-retained-query-selection-lineage; no-game-no-action',
    'producer_refs':[{'path':p,'bytes':(root/p).stat().st_size,'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest()} for p in paths],
    'cases':cases}
sys.stdout.buffer.write(json.dumps(record,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')+b'\\n')
""";
}
