package org.xar.ck3.control.wave2.events.eventoutcome;

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

/** Explicit one-time capture tool; never invoked by default Maven/JUnit. Run inside the shared Win32 Job. */
public final class EventOutcomeGoldenCapture {
    private EventOutcomeGoldenCapture() { }
    public static void main(String[] arguments) throws IOException, InterruptedException {
        if (arguments.length != 3) throw new IllegalArgumentException("repository python-executable new-output-file");
        Path repository = Path.of(arguments[0]).toAbsolutePath().normalize();
        Path python = Path.of(arguments[1]).toAbsolutePath().normalize();
        Path output = Path.of(arguments[2]).toAbsolutePath().normalize();
        if (!Files.isDirectory(repository) || !Files.isRegularFile(python) || Files.exists(output)) throw new IllegalArgumentException("capture paths");
        Files.createDirectories(output.getParent());
        String machine = new String(run(List.of(python.toString(), repository.resolve("tools/ck3_live_run_id.py").toString(), "machine"),
            repository, output.resolveSibling(output.getFileName() + ".machine.stderr"), 4096), StandardCharsets.UTF_8).strip();
        if (!machine.matches("[A-Za-z0-9][A-Za-z0-9._-]{3,127}")) throw new IllegalStateException("machine identity unavailable");
        byte[] golden = run(List.of(python.toString(), "-c", PRODUCER_CAPTURE, repository.toString(), machine), repository,
            output.resolveSibling(output.getFileName() + ".producer.stderr"), 98_304);
        Files.write(output, golden, StandardOpenOption.CREATE_NEW);
        System.out.println("captured " + golden.length + " bytes on " + machine);
    }
    private static byte[] run(List<String> command, Path repository, Path errorFile, int maximumBytes) throws IOException, InterruptedException {
        ProcessBuilder builder = new ProcessBuilder(command).directory(repository.toFile()).redirectError(errorFile.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTHONPATH", repository.resolve("ck3_autonomous_player/src").toString());
        Process process = builder.start();
        FutureTask<byte[]> reading = new FutureTask<>(() -> process.getInputStream().readNBytes(maximumBytes + 1));
        Thread.startVirtualThread(reading);
        try {
            if (!process.waitFor(90, TimeUnit.SECONDS)) throw new IOException("capture timed out");
            byte[] data = reading.get(5, TimeUnit.SECONDS);
            if (process.exitValue() != 0 || data.length > maximumBytes) throw new IOException("original producer capture failed: " + process.exitValue());
            return data;
        } catch (ExecutionException | TimeoutException error) {
            throw new IOException("producer output unavailable", error);
        } finally {
            if (process.isAlive()) process.destroyForcibly();
            reading.cancel(true);
        }
    }
    private static final String PRODUCER_CAPTURE = """
from pathlib import Path
from datetime import datetime, timezone
import copy, gzip, hashlib, json, sys
root = Path(sys.argv[1])
machine = sys.argv[2]
from xar_autoplayer.vanilla_events import outcome
from xar_autoplayer.vanilla_events.registry import query_vanilla_event_knowledge_v1
from xar_autoplayer.native_auto_run import _registered_event_material_postcondition_issue
cases = []
knowledge_refs = []
def make(key, native, build, metric, relation, before, after, variant='delta'):
    knowledge = query_vanilla_event_knowledge_v1(key, build)
    analysis = knowledge.get('analysis') or {}
    raw_profile = analysis.get('selected_choice_effect_profile')
    wanted = {'metric':metric, 'expected_relation':relation, 'material_change_required_for_evidence':True}
    profile_origin = 'actual_registry_profile'
    if not isinstance(raw_profile, dict) or raw_profile.get('observable_postcondition') != wanted:
        raw_profile = {'schema':'xar.ck3.vanilla-event-choice-effect', 'schema_version':1,
            'selected_native_option_index':native, 'observable_postcondition':wanted}
        profile_origin = 'explicit_scalar_contract_fixture_not_native_observation'
    profile = {k:raw_profile.get(k) for k in ('schema','schema_version','selected_native_option_index','observable_postcondition')}
    decision = {'status':'recommended','event_definition_key':key,'ck3_build':build,
        'selected_option_number':native+1,'selected_native_option_index':native,'choice_effect_profile':profile}
    stress = metric == 'played_character.stress_points'
    noun = 'stress' if stress else 'gold' if metric == 'played_character_gold.raw' else 'prestige'
    field = 'stress_points' if stress else noun+'_raw'
    player = {'character_id':27181,'alive':True,'stress_points':before if stress else 42}
    inputs = {'schema':'xar.ck3.scalar-event-outcome-plan-input/v1','decision':decision,'played_character':player,
        'played_character_gold':{'raw':before,'scale':100000} if noun == 'gold' else None,
        'played_character_prestige':{'raw':before,'scale':100000} if noun == 'prestige' else None,
        'snapshot_id':'native:19','revision':33}
    selection = {'postcondition_verified':True,'starting_snapshot_id':'native:19','starting_revision':33,
        'ending_snapshot_id':'native:20','ending_revision':34,
        'starting_played_character_'+noun:{'status':'available','character_id':27181,field:before},
        'ending_played_character_'+noun:{'status':'available','character_id':27181,field:after}}
    if not stress:
        selection['starting_played_character_'+noun]['scale'] = 100000
        selection['ending_played_character_'+noun]['scale'] = 100000
    if variant == 'ack_only':
        selection = {'accepted':True,'status':'submitted','postcondition_verified':False}
    elif variant == 'character_drift': selection['ending_played_character_'+noun]['character_id'] = 27182
    elif variant == 'stale_frame': selection['ending_snapshot_id'] = 'native:19'
    elif variant == 'wrong_scale': selection['ending_played_character_'+noun]['scale'] = 1
    elif variant == 'missing_stress': inputs['played_character'].pop('stress_points', None)
    elif variant == 'profile_missing': inputs['decision']['choice_effect_profile'] = None
    elif variant == 'profile_drift': inputs['decision']['choice_effect_profile']['observable_postcondition']['expected_relation'] = 'strictly_decreasing'
    elif variant == 'unknown_event': inputs['decision']['event_definition_key'] = 'unknown.9999'
    elif variant == 'starting_binding_drift': selection['starting_revision'] = 32
    expected = outcome.plan_registered_event_material_postcondition_v1(inputs['decision'], inputs['played_character'],
        played_character_gold=inputs['played_character_gold'], played_character_prestige=inputs['played_character_prestige'],
        snapshot_id=inputs['snapshot_id'], revision=inputs['revision'])
    observed = outcome.evaluate_registered_event_material_postcondition_v1(expected, selection) if expected is not None else None
    issue = _registered_event_material_postcondition_issue({'event_material_postcondition':expected},
        {'event_material_postcondition':observed})
    cases.append({'name':key+':'+build+':'+variant+':'+str(after-before),'profile_origin':profile_origin,
        'plan_input':inputs,'event_selection':selection,'expected_plan':expected,'expected_evaluation':observed,'expected_runner_issue':issue})
    anchor = {'event_definition_key':key,'ck3_build':build,'knowledge_status':knowledge.get('status'),
        'ck3_exe_sha256':knowledge.get('ck3_exe_sha256'),'source_sha256':analysis.get('source_sha256')}
    if anchor not in knowledge_refs: knowledge_refs.append(anchor)
specs = [(key,native,'1.19.0.6',metric,relation) for (key,native),(metric,relation) in outcome._SUPPORTED_CHOICES.items()]
specs += [('trait_specific.9001',2,'1.20.0.4','played_character.stress_points','strictly_decreasing'),
          ('feast.7002',0,'1.20.0.3','played_character_prestige.raw','strictly_increasing'),
          ('feast_default.6231',0,'1.20.0.3','played_character_gold.raw','strictly_decreasing')]
for key,native,build,metric,relation in specs:
    for delta in (-1,0,1): make(key,native,build,metric,relation,42,42+delta)
for variant in ('ack_only','character_drift','missing_stress','profile_missing','profile_drift','unknown_event','starting_binding_drift'):
    make('tgp_travel_events.0030',1,'1.19.0.6','played_character.stress_points','non_increasing',42,27,variant)
make('epidemic_events.1020',0,'1.19.0.6','played_character_gold.raw','strictly_decreasing',1000000,900000,'stale_frame')
make('epidemic_events.1020',0,'1.19.0.6','played_character_gold.raw','strictly_decreasing',1000000,900000,'wrong_scale')
make('trait_specific.8001',1,'1.19.0.6','played_character_gold.raw','strictly_increasing',-(2**63),2**63-1)
paths = ['ck3_autonomous_player/src/xar_autoplayer/vanilla_events/outcome.py',
    'ck3_autonomous_player/src/xar_autoplayer/native_auto_run.py',
    'ck3_autonomous_player/src/xar_autoplayer/vanilla_events/registry.py',
    'ck3_autonomous_player/tests/unit/test_vanilla_event_outcome.py']
record = {'schema':'xar.ck3.scalar-event-outcome-golden/v1','machine_id':machine,
    'captured_at':datetime.now(timezone.utc).isoformat(),'evidence_scope':'actual-old-plan-evaluate-runner-consumer; synthetic-boundary-observations; no-game-no-action',
    'producer_refs':[{'path':p,'bytes':(root/p).stat().st_size,'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest()} for p in paths],
    'knowledge_refs':knowledge_refs,'cases':cases}
payload = json.dumps(record, ensure_ascii=False, allow_nan=False, separators=(',',':')).encode('utf-8')+b'\\n'
print('uncompressed_golden_bytes='+str(len(payload)), file=sys.stderr)
sys.stdout.buffer.write(gzip.compress(payload, compresslevel=9, mtime=0))
""";
}
