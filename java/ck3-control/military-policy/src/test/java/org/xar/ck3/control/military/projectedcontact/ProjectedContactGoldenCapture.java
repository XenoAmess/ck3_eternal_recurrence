package org.xar.ck3.control.military.projectedcontact;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.stream.Stream;

/** Explicit one-time oracle capture. Default tests consume the checked-in result only. */
public final class ProjectedContactGoldenCapture {
    private ProjectedContactGoldenCapture() { }

    private static final String SCRIPT = """
            import copy, datetime, hashlib, importlib, json, pathlib, sys
            root = pathlib.Path(sys.argv[1])
            sys.path.insert(0, str(root / 'ck3_autonomous_player/tests/unit'))
            sys.path.insert(0, str(root / 'ck3_autonomous_player/src'))
            fixture = importlib.import_module('test_normal_army_projected_contact_consumer_12004')
            from xar_autoplayer.normal_army_projected_contact_v1 import select_normal_army_projected_contact_v1
            rows = []
            def base(transition='create_new', side='attacker'):
                row = fixture._contact_row(transition, side)
                return {'step': row['command'], 'ok': row['ok'], 'result': row['result']}
            request = {'subject_army_id':11, 'target_province_id':31, 'incoming_entry_province_id':30,
                       'subject_current_province_id':30, 'subject_owner_character_id':29829}
            def add(name, queries, snapshot=None, req=None):
                snap = fixture._snapshot() if snapshot is None else snapshot
                current = copy.deepcopy(request if req is None else req)
                expected = select_normal_army_projected_contact_v1(snap, queries, **current)
                rows.append({'name':name, 'input':{'snapshot':snap, 'query_rows':queries, 'request':current},
                             'expected':expected})
            add('native_order_attacker', [base()])
            add('native_order_defender', [base(side='defender')])
            add('complete_none', [base('none')])
            add('join_existing', [base('join_existing')])
            add('empty_history', [])
            for field, value in [('queried_snapshot_id','stale'), ('queried_revision',8),
                                 ('queried_native_revision',8), ('queried_connection_generation',4),
                                 ('queried_episode_run_id','another-episode')]:
                row=base(); row['result'][field]=value; add('stale_' + field, [row])
            for field, value in [('subject_army_id',True), ('subject_army_id',11.0),
                                 ('subject_owner_character_id',29830), ('subject_current_province_id',29),
                                 ('snapshot_revision',8), ('date_raw',1001),
                                 ('projected_attacker_army_ids',[11,11]),
                                 ('projected_defender_army_ids',[11,21]),
                                 ('projected_initiator_is_defender',None),
                                 ('incoming_adjacency_kind_raw',4)]:
                row=base(); row['result']['projected_contact_scope'][field]=value
                add('invalid_scope_' + field + '_' + str(value), [row])
            row=base(); row['result']['projected_contact_scope']['unknown_field']=1
            add('unknown_scope_field', [row])
            row=base(); del row['result']['projected_contact_scope']['selected_current_combat_id']
            add('missing_nullable_scope_field', [row])
            row=base(); row['result']['projected_contact_scope']['observed_target_public_cunit_ids']=None
            add('null_distinct_from_empty_array', [row])
            row=base('join_existing'); row['result']['projected_contact_scope']['selected_current_combat_array_index']=1
            add('selected_combat_index_outside_array', [row])
            row=base(); row['ok']=False; add('failed_row', [row])
            row=base(); row['step']='query-projected-contact-scope-v1-011-to-31-from-30'
            add('noncanonical_step', [row])
            stale=base(); stale['result']['queried_native_revision']=8
            add('newer_stale_retains_older_valid', [base(side='defender'), stale])
            snap=fixture._snapshot(); snap['native_revision']=2**64-1
            row=base(); row['result']['queried_native_revision']=2**64-1
            row['result']['projected_contact_scope']['snapshot_revision']=2**64-1
            add('uint64_max_exact', [row], snapshot=snap)
            row=base(); row['step']='query-projected-contact-scope-v1-0-to-31-from-30'
            scope=row['result']['projected_contact_scope']; scope['subject_army_id']=0
            scope['projected_attacker_army_ids']=[0]
            req=copy.deepcopy(request); req['subject_army_id']=0
            add('public_cunit_slot_zero', [row], req=req)
            req=copy.deepcopy(request); req['subject_owner_character_id']=None
            add('explicit_optional_owner_unbound', [base()], req=req)
            files=['ck3_autonomous_player/src/xar_autoplayer/normal_army_projected_contact_v1.py',
                   'ck3_autonomous_player/src/xar_autoplayer/bridge/projected_contact_contract.py',
                   'ck3_autonomous_player/src/xar_autoplayer/bridge/public_unit_contract.py',
                   'ck3_autonomous_player/tests/unit/test_normal_army_projected_contact_consumer_12004.py']
            result={'schema_version':1, 'machine_id':sys.argv[2],
                    'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'qualification':'actual_python_producer_source_fixture_not_native_or_live',
                    'producer':'xar_autoplayer.normal_army_projected_contact_v1.select_normal_army_projected_contact_v1',
                    'source_sha256':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in files},
                    'cases':rows}
            print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(',',':')))
            """;

    public static void main(String[] args) throws Exception {
        if (args.length == 4 && args[0].equals("--freeze")) {
            freeze(Path.of(args[1]), Path.of(args[2]), args[3]); return;
        }
        if (args.length != 4) { throw new IllegalArgumentException("repository python machine_id output required"); }
        Path output = Path.of(args[3]).toAbsolutePath();
        if (Files.exists(output)) { throw new IllegalArgumentException("capture output must be new"); }
        Process process = new ProcessBuilder(args[1], "-c", SCRIPT, args[0], args[2])
                .redirectError(ProcessBuilder.Redirect.INHERIT).start();
        byte[] captured = process.getInputStream().readNBytes(192 * 1024 + 1);
        if (!process.waitFor(Duration.ofSeconds(30).toMillis(), TimeUnit.MILLISECONDS)) {
            process.destroyForcibly(); throw new IllegalStateException("producer capture timeout");
        }
        if (process.exitValue() != 0 || captured.length > 192 * 1024) {
            throw new IllegalStateException("producer capture failed or exceeded budget: " + process.exitValue());
        }
        String text = new String(captured, StandardCharsets.UTF_8);
        if (!text.startsWith("{")) { throw new IllegalStateException("producer did not emit JSON object"); }
        Files.createDirectories(output.getParent()); Files.write(output, captured);
        System.out.println("captured producer golden bytes=" + captured.length + " path=" + output);
    }

    private static void freeze(Path module, Path output, String machineId) throws Exception {
        if (Files.exists(output)) { throw new IllegalArgumentException("freeze output must be new"); }
        List<Path> sources = new ArrayList<>();
        sources.add(module.resolve("MIGRATION-projectedcontact.md"));
        for (String directory : List.of("src/main/java/org/xar/ck3/control/military/projectedcontact",
                "src/test/java/org/xar/ck3/control/military/projectedcontact", "src/test/resources/projectedcontact")) {
            try (Stream<Path> files = Files.walk(module.resolve(directory))) {
                sources.addAll(files.filter(Files::isRegularFile).toList());
            }
        }
        sources.sort(Comparator.comparing(Path::toString));
        StringBuilder json = new StringBuilder("{\"machine_id\":\"").append(machineId)
                .append("\",\"observed_at_utc\":\"").append(Instant.now())
                .append("\",\"qualification\":\"source_freeze_not_compile_or_consumer_adoption\",\"files\":[");
        long total = 0;
        for (Path source : sources) {
            byte[] bytes = Files.readAllBytes(source); total += bytes.length;
            if (json.charAt(json.length() - 1) != '[') { json.append(','); }
            json.append("{\"path\":\"").append(module.relativize(source).toString().replace('\\', '/'))
                    .append("\",\"bytes\":").append(bytes.length).append(",\"sha256\":\"")
                    .append(HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes))).append("\"}");
        }
        if (total > 192 * 1024) { throw new IllegalStateException("source plus golden exceeds 192 KiB"); }
        json.append("],\"total_bytes\":").append(total).append('}');
        Files.createDirectories(output.toAbsolutePath().getParent());
        Files.writeString(output, json, StandardCharsets.UTF_8);
        System.out.println("source freeze files=" + sources.size() + " bytes=" + total + " path=" + output);
    }
}
