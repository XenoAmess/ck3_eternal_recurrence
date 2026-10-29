package org.xar.ck3.control.wave2.events.sourcecatalog;

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

/** Explicit original producer capture only; run by the shared qualified Windows Job owner. */
public final class SourceCatalogueGoldenCapture {
    private SourceCatalogueGoldenCapture() { }
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
        byte[] bytes = run(List.of(python.toString(), "-", root.toString(), machine), root,
            output.resolveSibling(output.getFileName() + ".producer.stderr"), 65_536,
            CAPTURE.getBytes(StandardCharsets.UTF_8));
        Files.write(output, bytes, StandardOpenOption.CREATE_NEW);
        System.out.println("captured " + bytes.length + " bytes on " + machine);
    }
    private static byte[] run(List<String> command, Path root, Path errors, int maximum) throws IOException, InterruptedException {
        return run(command, root, errors, maximum, null);
    }
    private static byte[] run(List<String> command, Path root, Path errors, int maximum, byte[] standardInput) throws IOException, InterruptedException {
        ProcessBuilder builder = new ProcessBuilder(command).directory(root.toFile()).redirectError(errors.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTHONPATH", root.resolve("ck3_autonomous_player/src").toString());
        Process process = builder.start();
        FutureTask<byte[]> reading = new FutureTask<>(() -> process.getInputStream().readNBytes(maximum + 1));
        Thread.startVirtualThread(reading);
        try {
            try (var input = process.getOutputStream()) { if (standardInput != null) input.write(standardInput); }
            if (!process.waitFor(90, TimeUnit.SECONDS)) throw new IOException("capture timed out");
            byte[] bytes = reading.get(5, TimeUnit.SECONDS);
            if (process.exitValue() != 0 || bytes.length > maximum) throw new IOException("original producer capture rejected: " + process.exitValue());
            return bytes;
        } catch (ExecutionException | TimeoutException error) { throw new IOException("original output unavailable", error); }
        finally { if (process.isAlive()) process.destroyForcibly(); reading.cancel(true); }
    }
    private static final String CAPTURE = """
from pathlib import Path
from datetime import datetime, timezone
import gzip, hashlib, json, sys, tempfile
from xar_autoplayer.vanilla_events import event_offline_analysis as original
from xar_autoplayer.interaction_offline_analysis import block
root, machine = Path(sys.argv[1]), sys.argv[2]
cases = []
def request(op, text, wanted=None, count=None):
    return {'schema':'xar.ck3.event-source-catalogue-input/v1','operation':op,'source':text,'wanted':wanted,'native_option_count':count}
def add(name, op, text, wanted):
    try:
        value = original._blocks(text,wanted) if op == 'blocks' else original._scalars(text,wanted)
        expected = {'status':'value','value':value}
    except ValueError as error: expected = {'status':'rejected','message':str(error)}
    cases.append({'name':name,'request':request(op,text,wanted),'expected':expected})
LF, CR, QUOTE, SLASH = chr(10), chr(13), chr(34), chr(92)
add('two-inline-direct-options','blocks','fixture.1 = { option = { name=a } option={name=b} }','option')
add('nested-option-is-not-direct','blocks','fixture.1={ immediate={option={name=ignored}} option={name=kept} }','option')
add('quoted-braces-and-hash','blocks','fixture.1={ option={name="a # { }"} # ignored }'+LF+' }','option')
add('escaped-quote','blocks','fixture.1={option={name='+QUOTE+'a'+SLASH+QUOTE+'b'+QUOTE+'}}','option')
add('cr-comment-termination','blocks','fixture.1={ #ignored'+CR+'option={name=a}}','option')
add('unicode-whitespace-nbsp-and-control','blocks','fixture.1={'+chr(160)+'option'+chr(28)+'='+chr(0x2003)+'{name=a}}','option')
add('negative-depth','blocks','} fixture.1={}','option')
add('unclosed-root','blocks','fixture.1={x=yes','option')
add('unterminated-child','blocks','fixture.1={option={name=a','option')
add('empty-source','blocks','','option')
add('unterminated-quote-regex-fallback','blocks','fixture.1={option={name="oops } }','option')
add('escaped-lf-regex-fallback','blocks','fixture.1={option={name='+QUOTE+'a'+SLASH+LF+'} }','option')
add('quoted-name-values-retain-order','scalars','option={name="b" name=a name="b"}','name')
add('skip-conditional-name-block','scalars','option={name={text=a} name=b}','name')
add('nested-scalar-is-not-direct','scalars','option={trigger={name=ignored} name=kept}','name')
add('quoted-hash-is-not-comment','scalars','option={name="# braces { }"}','name')
add('scalars-do-not-validate-global-depth','scalars','option={name=a','name')
add('scalars-negative-depth-keeps-original-result','scalars','} option={name=a}','name')
add('source-type-scalar','scalars','fixture.1={type=character_event option={name=a}}','type')
add('empty-quoted-scalar','scalars','option={name=""}','name')
add('escaped-text-is-not-unescaped','scalars','option={name='+QUOTE+'a'+SLASH+QUOTE+'b'+QUOTE+'}','name')
add('unicode-name-token','scalars','option={name=中文😀}','name')
add('unicode-scalar-whitespace','scalars','option={name'+chr(0x85)+'='+chr(0x202f)+'a}','name')
add('same-level-other-key','scalars','option={other=a name=b}','name')
blob_relative = 'ck3_autonomous_player/src/xar_autoplayer/vanilla_events/portable_evidence/blobs/42b8b1e56c029054fbc4e0b3964511a980d9b5053c47bff980cd3f5f3924db37.gz'
blob = (root/blob_relative).read_bytes()
if hashlib.sha256(blob).hexdigest() != 'f1c1bfa3d6db9160edd5dad837499394526050462d85e7667e1ce4c2d145a0db': raise ValueError('archived source gzip identity differs')
raw = gzip.decompress(blob)
if hashlib.sha256(raw).hexdigest() != '42b8b1e56c029054fbc4e0b3964511a980d9b5053c47bff980cd3f5f3924db37': raise ValueError('archived source bytes differ')
index = original._index('1.19.0.6')
relative = 'events/travel_events/tgp_travel_events.txt'
source_cases = 0
with tempfile.TemporaryDirectory(prefix='java-event-source-') as temporary:
    game_root = Path(temporary)
    source_file = game_root/relative
    source_file.parent.mkdir(parents=True)
    source_file.write_bytes(raw)
    candidates = sorted(key for key,row in index['events'].items() if isinstance(row.get('definition'),dict) and row['definition'].get('relative_path') == relative)
    for key in candidates:
        definition = block(raw.decode('utf-8-sig'),key)
        count = len(original._blocks(definition,'option'))
        if not count: continue
        binding = {'event_definition_key':key,'ck3_build':'1.19.0.6','native_option_count':count}
        _,_,actual_definition,options = original._source(game_root,binding)
        value = {'event_types':original._scalars(actual_definition,'type'),'options':options,
            'immediate':block(actual_definition,'immediate'),'after':block(actual_definition,'after')}
        cases.append({'name':'actual-archived-source:'+key,'request':request('catalogue',actual_definition,count=count),
            'expected':{'status':'value','value':value}})
        add('actual-archived-direct-options:'+key,'blocks',actual_definition,'option')
        add('actual-archived-event-type:'+key,'scalars',actual_definition,'type')
        if source_cases == 0:
            try: original._source(game_root,{**binding,'native_option_count':count+1})
            except ValueError as error:
                cases.append({'name':'actual-source-native-count-drift','request':request('catalogue',actual_definition,count=count+1),
                    'expected':{'status':'rejected','message':str(error)}})
        source_cases += 1
        if source_cases == 3: break
if source_cases == 0: raise ValueError('no actual archived source catalogue exercised')
paths = ['ck3_autonomous_player/src/xar_autoplayer/vanilla_events/event_offline_analysis.py',
    'ck3_autonomous_player/src/xar_autoplayer/interaction_offline_analysis.py',
    'ck3_autonomous_player/src/xar_autoplayer/vanilla_events/source_index.py']
record = {'schema':'xar.ck3.event-source-catalogue-golden/v1','machine_id':machine,'captured_at':datetime.now(timezone.utc).isoformat(),
    'evidence_scope':'actual-original-helpers-and-_source-with-pinned-archived-1.19.0.6-source; no-current-install-or-game-proof',
    'producer_refs':[{'path':p,'bytes':(root/p).stat().st_size,'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest()} for p in paths],
    'archived_source':{'path':blob_relative,'blob_sha256':hashlib.sha256(blob).hexdigest(),'raw_sha256':hashlib.sha256(raw).hexdigest(),
        'raw_bytes':len(raw),'ck3_build':'1.19.0.6','actual_catalogues':source_cases},'cases':cases}
payload = json.dumps(record,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')+b'\\n'
print('uncompressed_golden_bytes='+str(len(payload)),file=sys.stderr)
sys.stdout.buffer.write(gzip.compress(payload,compresslevel=9,mtime=0))
""";
}
