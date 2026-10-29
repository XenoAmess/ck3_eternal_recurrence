package org.xar.ck3.control.wave2.military.capture;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.ByteBuffer;
import java.nio.CharBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.Base64;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.TreeSet;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Test-only historical oracle; qualified compiled capture classpath and stdin runner required. */
public final class OriginalProducerOracle {
    public static final long MAX_ARCHIVE_BYTES = 327_680;
    public static final int MAX_EXPANDED_BYTES = 2_097_152;
    private OriginalProducerOracle() { }

    public static String program(String originalScript, ExactRef archiveFileRef, Set<String> allowedModules) {
        return programWithArchives(originalScript, List.of(Objects.requireNonNull(archiveFileRef)), allowedModules);
    }

    public static String programWithArchives(String originalScript, List<ExactRef> archiveFileRefs, Set<String> allowedModules) {
        Objects.requireNonNull(originalScript);
        List<ExactRef> archives = List.copyOf(Objects.requireNonNull(archiveFileRefs));
        StrictJson.require(!archives.isEmpty() && archives.size() <= 6, "one primary and at most five supplement refs required");
        Set<String> modules = Set.copyOf(Objects.requireNonNull(allowedModules));
        byte[] script = utf8(originalScript);
        StrictJson.require(script.length > 0 && script.length <= 262_144, "bounded original capture script required");
        Set<String> archivePaths = new TreeSet<>();
        for (ExactRef ref : archives) {
            StrictJson.require(Path.of(ref.path()).isAbsolute() && ref.bytes() > 0 && ref.bytes() <= MAX_ARCHIVE_BYTES,
                    "explicit bounded archive ref required");
            StrictJson.require(archivePaths.add(Path.of(ref.path()).normalize().toString()), "duplicate archive path");
        }
        StrictJson.require(!modules.isEmpty() && modules.size() <= 256, "explicit nonempty original module set required");
        for (String module : modules) {
            StrictJson.require(module.length() <= 256 && module.matches("xar_autoplayer(?:\\.[A-Za-z_][A-Za-z0-9_]*)+"),
                    "explicit original module name required");
        }
        ObjectNode settings = StrictJson.object(); settings.set("archive", archives.getFirst().toJson());
        if (archives.size() > 1) {
            var supplements = settings.putArray("supplements"); archives.subList(1, archives.size()).forEach(ref -> supplements.add(ref.toJson()));
        }
        var names = settings.putArray("allowed_modules"); new TreeSet<>(modules).forEach(names::add);
        String config = Base64.getEncoder().encodeToString(StrictJson.canonical(settings));
        return BOOTSTRAP + "\n_historical_original_run('" + config + "','"
                + Base64.getEncoder().encodeToString(script) + "')\n";
    }

    private static byte[] utf8(String value) {
        try {
            ByteBuffer bytes = StandardCharsets.UTF_8.newEncoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT).encode(CharBuffer.wrap(value));
            byte[] result = new byte[bytes.remaining()]; bytes.get(result); return result;
        } catch (CharacterCodingException error) { throw new IllegalArgumentException("exact UTF8 script required", error); }
    }

    private static final String BOOTSTRAP = """
def _historical_original_run(config_b64, script_b64):
    import base64,gzip,hashlib,importlib.abc,importlib.util,io,json,os,sys
    from pathlib import Path
    def need(ok,message):
        if not ok: raise RuntimeError('historical-original oracle: '+message)
    def object_pairs(pairs):
        result={}
        for key,value in pairs:
            need(key not in result,'duplicate JSON key'); result[key]=value
        return result
    config=json.loads(base64.b64decode(config_b64,validate=True),object_pairs_hook=object_pairs)
    need(type(config) is dict and set(config) in ({'archive','allowed_modules'},{'archive','allowed_modules','supplements'}),'config fields')
    reference=config['archive']; allowed=config['allowed_modules']
    supplements=config.get('supplements',[])
    need(type(supplements) is list and len(supplements)<=5,'supplement ref count')
    references=[reference]+supplements
    need(type(allowed) is list and 0<len(allowed)<=256 and len(set(allowed))==len(allowed),'module list')
    def module_name(name):
        return (type(name) is str and len(name)<=256 and name.startswith('xar_autoplayer.')
            and all(p.isascii() and p.isidentifier() for p in name.split('.')))
    need(all(module_name(name) for name in allowed),'explicit module names')
    def identity(info):
        return (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns)
    def read_archive(reference):
        need(type(reference) is dict and set(reference)=={'path','bytes','sha256'},'archive ref fields')
        need(type(reference['path']) is str and Path(reference['path']).is_absolute(),'absolute archive path')
        need(type(reference['bytes']) is int and 0<reference['bytes']<=327680,'archive byte cap')
        need(type(reference['sha256']) is str and len(reference['sha256'])==64
            and all(c in '0123456789abcdef' for c in reference['sha256']),'archive SHA')
        path=Path(reference['path']).resolve(strict=True)
        before=identity(path.stat())
        with path.open('rb') as stream:
            opened=identity(os.fstat(stream.fileno())); raw=stream.read(reference['bytes']+1)
            need(identity(os.fstat(stream.fileno()))==opened,'opened archive identity changed')
        need(before==opened==identity(path.stat()),'archive path/file identity changed')
        need(len(raw)==reference['bytes'] and hashlib.sha256(raw).hexdigest()==reference['sha256'],'archive bytes/SHA')
        return before,raw
    original_identity,compressed=read_archive(reference)
    with gzip.GzipFile(fileobj=io.BytesIO(compressed),mode='rb') as stream:
        expanded=stream.read(2097153)
    need(0<len(expanded)<=2097152,'expanded archive cap')
    archive=json.loads(expanded.decode('utf-8',errors='strict'),object_pairs_hook=object_pairs)
    def validate_archive(archive):
        need(type(archive) is dict and set(archive)=={'schema','machine_id','observed_at_utc','source_machine_id','scope','sources'},'archive fields')
        need(archive['schema']=='xar.ck3.military-original-producer-source/v1','archive schema')
        need(all(type(archive[key]) is str and 0<len(archive[key])<=4096
            for key in ('machine_id','observed_at_utc','source_machine_id','scope')),'archive metadata')
        need(type(archive['sources']) is list and 0<len(archive['sources'])<=256,'source list')
    validate_archive(archive)
    remaining=2097152-len(expanded); identities=[original_identity]
    source_rows=[(reference,row) for row in archive['sources']]
    for supplement in supplements:
        observed,compressed=read_archive(supplement)
        need(observed not in identities,'duplicate archive file identity')
        with gzip.GzipFile(fileobj=io.BytesIO(compressed),mode='rb') as stream:
            expanded=stream.read(remaining+1)
        need(0<len(expanded)<=remaining,'combined expanded archive cap'); remaining-=len(expanded)
        extra=json.loads(expanded.decode('utf-8',errors='strict'),object_pairs_hook=object_pairs)
        validate_archive(extra); source_rows.extend((supplement,row) for row in extra['sources']); identities.append(observed)
    need(len(source_rows)<=256,'combined source count')
    sources={}; origins={}; module_keys=set()
    for source_reference,row in source_rows:
        need(type(row) is dict and set(row)=={'path','bytes','sha256','utf8'},'source fields')
        source_path=row['path']; need(type(source_path) is str,'source path')
        if source_path=='java/ck3-control/wave2-military/src/main/java/org/xar/ck3/control/wave2/military/sharedwire/ArmyManagerSharedWire.java':
            need(source_path not in module_keys,'duplicate Java metadata')
            need(type(row['bytes']) is int and row['bytes']==9946 and type(row['utf8']) is str,'exact Java metadata bytes/text')
            source=row['utf8'].encode('utf-8',errors='strict')
            need(len(source)==9946 and row['sha256']=='c098ad486883e5e23e3dbf61349fae50ff888b6748c463ce2902f0a1b1e0376f'
                and hashlib.sha256(source).hexdigest()==row['sha256'],'exact Java metadata SHA')
            module_keys.add(source_path)
            continue
        prefix='ck3_autonomous_player/src/'
        need(source_path.startswith(prefix) and source_path.endswith('.py'),'source root/suffix')
        name=source_path[len(prefix):-3].replace('/','.')
        need(module_name(name) and source_path==prefix+name.replace('.','/')+'.py','canonical source path')
        need(name.casefold() not in module_keys and type(row['utf8']) is str,'duplicate/source text')
        source=row['utf8'].encode('utf-8',errors='strict')
        need(type(row['bytes']) is int and row['bytes']==len(source),'source bytes')
        need(type(row['sha256']) is str and row['sha256']==hashlib.sha256(source).hexdigest(),'source SHA')
        sources[name]=row; origins[name]=source_reference['path']; module_keys.add(name.casefold())
    need(set(allowed)<=set(sources),'requested module absent')
    need(not any(name in sys.modules for name in allowed),'requested original module already loaded')
    class Finder(importlib.abc.MetaPathFinder,importlib.abc.Loader):
        def find_spec(self,fullname,path=None,target=None):
            if fullname in allowed:
                return importlib.util.spec_from_loader(fullname,self,origin=str(origins[fullname])+'!'+sources[fullname]['path'])
            return None
        def create_module(self,spec): return None
        def exec_module(self,module):
            row=sources[module.__name__]; module.__file__=str(origins[module.__name__])+'!'+row['path']
            exec(compile(row['utf8'],module.__file__,'exec'),module.__dict__)
    finder=Finder(); sys.meta_path.insert(0,finder)
    namespace=vars(sys.modules['__main__'])
    namespace.update(HISTORICAL_ORIGINAL_ORACLE_REF=dict(reference),HISTORICAL_ORIGINAL_ORACLE_REFS=tuple(dict(ref) for ref in references),HISTORICAL_ORIGINAL_ORACLE_MODULES=tuple(allowed))
    try:
        script=base64.b64decode(script_b64,validate=True).decode('utf-8',errors='strict')
        exec(compile(script,'<historical-original-capture-script>','exec'),namespace,namespace)
    finally:
        sys.meta_path.remove(finder)
        for ref,expected_identity in zip(references,identities,strict=True):
            current_identity,unused=read_archive(ref)
            need(current_identity==expected_identity,'archive original identity changed')
""";
}
