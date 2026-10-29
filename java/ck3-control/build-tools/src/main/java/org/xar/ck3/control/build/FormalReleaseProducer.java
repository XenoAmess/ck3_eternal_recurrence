package org.xar.ck3.control.build;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Set;
import java.util.TreeMap;
import java.util.TreeSet;
import java.util.regex.Pattern;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.NativeRunProfileManifest.ReleaseEntry;
import org.xar.ck3.control.build.NativeRunProfileManifest.ReleaseManifest;

/** The one pure Java allowlist -> stripped payload -> native registry descriptor -> format2 producer.
 * All bytes remain private to Prepared until the existing LS bootstrap writer admits its complete quote.
 * This class never writes, removes a path, invokes Python, publishes, launches Game or grants qualification.
 */
public final class FormalReleaseProducer {
    public static final String REQUEST_SCHEMA="xar.java-formal-release-request/v2";
    public static final String WORKSHOP_ITEM_ID="3784706360";
    public static final int MAXIMUM_FILES=4096,MAXIMUM_ENTRIES=16384;
    public static final long MAXIMUM_LOGICAL_BYTES=512L<<20,MAXIMUM_FILE_BYTES=64L<<20;
    public static final String BEGIN="# XAR_ACCEPTANCE_ONLY_BEGIN",END="# XAR_ACCEPTANCE_ONLY_END",RELEASE_ONLY="# XAR_RELEASE_ONLY ";
    private static final Set<String> ROOT_FILES=Set.of("descriptor.mod","thumbnail.png"),DEVELOPMENT=Set.of("tools",".idea");
    private static final java.util.Map<String,Set<String>> SUFFIXES=java.util.Map.of(
            "common",Set.of(".txt"),"events",Set.of(".txt"),"gfx",Set.of(".dds"),
            "gui",Set.of(".gui",".txt"),"localization",Set.of(".yml"));
    private static final Set<String> ACCEPTANCE_FILES=Set.of(
            "common/on_action/xar_acceptance_on_actions.txt",
            "common/scripted_effects/xar_acceptance_balance_effects.txt",
            "common/scripted_effects/xar_acceptance_balance_wire_effects.txt",
            "common/scripted_effects/xar_acceptance_bargain_effects.txt",
            "common/scripted_effects/xar_acceptance_courtier_effects.txt",
            "common/scripted_effects/xar_acceptance_death_effects.txt",
            "common/scripted_effects/xar_acceptance_progression_effects.txt",
            "common/scripted_effects/xar_acceptance_scoring_effects.txt",
            "common/scripted_effects/xar_selftest_effects.txt",
            "common/script_values/xar_acceptance_balance_wire_values.txt",
            "events/xar_acceptance_bargain_events.txt","events/xar_acceptance_events.txt",
            "events/xar_acceptance_scoring_events.txt","gui/xar_trait_test.gui");
    private static final List<String> LINE_TOKENS=List.of("setting_xar_selftest","xar_trait_hover_sentinel",
            "xar_trait_hover_off","gui/xar_trait_test.gui");
    private static final List<String> FORBIDDEN=List.of("xar_selftest","setting_xar_selftest","xar_test_sweep_effect",
            "xar_acceptance_","xa_bargain_reopen","xa_progression_ui","xa_scoring_matrix","xar_test_dispatcher_sweep_effect",
            "xar_trait_test","xar_trait_hover","xa_full_ui_test","xa_ui_test","xa_test_","xa_selftest_","XAR: TEST",
            "xar_balance_","xa_balance_","XAR: BALANCE",BEGIN,END,RELEASE_ONLY);
    private FormalReleaseProducer(){ }
    /** PROFILE_STAGING is the legacy ordinary build path; PUBLISH_RELEASE additionally requires clean tagged HEAD. */
    public enum Mode { PROFILE_STAGING,PUBLISH_RELEASE }
    public enum Layout { DIRECT_STAGING,ISOLATED_PROFILE_IMPORT }
    public enum PayloadRole { PRODUCTION_FILE,MANIFEST }
    public record Request(String schema,String machineId,String reviewAtUtc,Path repository,Path sourceRoot,
            Path outputRoot,Path productionRoot,Path manifestTarget,Mode mode,Layout layout){
        public Request{
            if(!REQUEST_SCHEMA.equals(schema)||machineId==null||!machineId.matches("[a-z0-9][a-z0-9-]{0,63}")||machineId.equals("unknown"))
                throw new IllegalArgumentException("exact current machine formal release request required");
            Instant.parse(reviewAtUtc);Objects.requireNonNull(mode);Objects.requireNonNull(layout);
            for(Path path:List.of(repository,sourceRoot,outputRoot,productionRoot,manifestTarget))
                if(!path.isAbsolute()||!path.normalize().equals(path)||path.getParent()==null)
                    throw new IllegalArgumentException("normalized absolute release paths required");
            if(!sourceRoot.equals(repository.resolve("XenoAmess_s_Eternal_Recurrence"))
                    ||repository.startsWith(outputRoot)||outputRoot.startsWith(repository)
                    ||productionRoot.equals(manifestTarget))
                throw new IllegalArgumentException("original mod and disjoint exact output root required");
            boolean direct=layout==Layout.DIRECT_STAGING&&productionRoot.getParent().equals(outputRoot)
                    &&manifestTarget.getParent().equals(outputRoot)
                    &&manifestTarget.getFileName().toString().equals(productionRoot.getFileName()+".manifest.json");
            boolean imported=layout==Layout.ISOLATED_PROFILE_IMPORT
                    &&productionRoot.equals(outputRoot.resolve("profile/mod-content/xar-production"))
                    &&manifestTarget.equals(outputRoot.resolve("xar-production.manifest.json"));
            if(!direct&&!imported)throw new IllegalArgumentException("exact explicitly selected formal staging/import layout required");
        }
    }
    public record PlannedFile(PayloadRole role,Path target,byte[] bytes){
        public PlannedFile{Objects.requireNonNull(role);Objects.requireNonNull(target);bytes=bytes.clone();
            if(!target.isAbsolute()||!target.normalize().equals(target)||bytes.length>MAXIMUM_FILE_BYTES)
                throw new IllegalArgumentException("bounded exact staged file required");}
        @Override public byte[] bytes(){return bytes.clone();}
        public FileRef expected(){return new FileRef(target.toString(),bytes.length,NativeRunProfileRules.sha(bytes));}
    }
    private record CensusEntry(String relative,boolean directory){ }
    private record SourceFile(String relative,SharedSourceFiles.Witness witness,byte[] bytes){
        private SourceFile{bytes=bytes.clone();}
    }
    private record SourceTree(List<CensusEntry> entries,List<NativeRunProfileManifest.TreeDirectory> directories,List<SourceFile> files){
        private SourceTree{entries=List.copyOf(entries);directories=List.copyOf(directories);files=List.copyOf(files);}
    }
    public static final class Prepared {
        private final Request request;private final SourceTree original;private final FormalReleaseGit.Session git;
        private final FormalReleaseGit.Snapshot identity;private final List<PlannedFile> payload;
        private final List<String> directories;private final ReleaseManifest manifest;private final byte[] manifestBytes;
        private Prepared(Request request,SourceTree original,FormalReleaseGit.Session git,FormalReleaseGit.Snapshot identity,
                List<PlannedFile> payload,List<String> directories,ReleaseManifest manifest,byte[] manifestBytes){
            this.request=request;this.original=original;this.git=git;this.identity=identity;this.payload=List.copyOf(payload);
            this.directories=List.copyOf(directories);this.manifest=manifest;this.manifestBytes=manifestBytes.clone();
        }
        public Request request(){return request;}
        public Path outputRoot(){return request.outputRoot();}
        public List<PlannedFile> payload(){return payload;}
        public List<String> outputDirectories(){return directories;}
        public ReleaseManifest manifest(){return manifest;}
        public byte[] manifestBytes(){return manifestBytes.clone();}
        /** Cheap source custody guard for the existing LS writer's per-file checks; no CLI process or write. */
        public void verifyOriginals()throws IOException{
            current(request,Clock.systemUTC());verifyCensus(request.sourceRoot(),original);
            for(var source:original.files())SharedSourceFiles.assertUnchanged(source.witness());
            git.requireOutputRoot(request.outputRoot());
        }
        /** Mandatory phase boundaries: before quote, immediately before sole writer, after readback. */
        public void verifyGitCurrent(FormalReleaseGit.Phase phase)throws IOException,InterruptedException{
            verifyOriginals();git.requireSame(identity,request.mode(),manifest.modVersion(),phase);verifyOriginals();
        }
        /** The shared real profile consumer validates complete actual staging files and rejects extras/missing/hash drift. */
        public NativeRunProfileManifest.ProductionTree verifyCreatedPayload()throws IOException{
            verifyOriginals();
            var manifestWitness=SharedSourceFiles.observe(request.manifestTarget());
            FileRef expected=new FileRef(request.manifestTarget().toString(),manifestBytes.length,NativeRunProfileRules.sha(manifestBytes));
            if(!manifestWitness.source().equals(expected)||!Arrays.equals(manifestBytes,Files.readAllBytes(request.manifestTarget())))
                throw new IOException("actual release manifest differs from its sole pure producer");
            ReleaseManifest decoded=ControlBuild.strictMapper().readValue(manifestBytes,ReleaseManifest.class);
            if(!decoded.equals(manifest))throw new IOException("release manifest serialization round trip changed");
            var result=NativeRunProfileProducer.verifyProduction(request.productionRoot(),decoded);
            SharedSourceFiles.assertUnchanged(manifestWitness);verifyOriginals();return result;
        }
    }
    public static Request readRequest(FileRef original)throws IOException{
        if(original.bytes()<1||original.bytes()>65536)throw new IOException("finite actual formal release request required");
        var held=SharedSourceFiles.observe(Path.of(original.path()));
        if(!held.source().equals(original))throw new IOException("formal release request changed before read");
        Request request=ControlBuild.strictMapper().readValue(Files.readAllBytes(Path.of(original.path())),Request.class);
        SharedSourceFiles.assertUnchanged(held);return request;
    }
    public static Prepared prepare(Request request,FormalReleaseGit.Session git,Clock clock)throws IOException,InterruptedException{
        current(request,clock);Objects.requireNonNull(git);
        if(!request.repository().equals(git.repository())||!request.machineId().equals(git.machineId()))
            throw new IOException("actual Git owner/repository/machine differs from formal producer");
        git.requireOutputRoot(request.outputRoot());
        SourceTree source=readSource(request.sourceRoot());String version=descriptorVersion(source.files().stream()
                .filter(row->row.relative().equals("descriptor.mod")).findFirst().orElseThrow().bytes());
        var identity=git.capture(request.mode(),version,FormalReleaseGit.Phase.PREPARE);
        byte[] registry=identity.registryBytes();FormalReleaseDescriptor.requireRegistry(registry);
        List<Rendered> rendered=project(source.files().stream().map(row->new SourceBytes(row.relative(),row.bytes())).toList(),registry);
        String tag=request.mode()==Mode.PUBLISH_RELEASE?"v"+version:null;
        ReleaseManifest manifest=manifest(rendered,identity.head(),version,tag);
        byte[] manifestBytes=NativeRunProfileManifest.canonical(ControlBuild.strictMapper().valueToTree(manifest));
        if(manifestBytes.length>1<<20)throw new IOException("complete formal release manifest exceeds finite control bound");
        var payload=new ArrayList<PlannedFile>();var directories=new TreeSet<String>();
        String prefix=slash(request.outputRoot().relativize(request.productionRoot()));
        directories.add(prefix);for(String root:SUFFIXES.keySet())directories.add(prefix+"/"+root);
        for(var row:rendered){
            Path target=request.productionRoot().resolve(row.relative());Path parent=request.outputRoot().relativize(target).getParent();
            while(parent!=null){directories.add(slash(parent));parent=parent.getParent();}
            payload.add(new PlannedFile(PayloadRole.PRODUCTION_FILE,target,row.bytes()));
        }
        payload.add(new PlannedFile(PayloadRole.MANIFEST,request.manifestTarget(),manifestBytes));
        var prepared=new Prepared(request,source,git,identity,payload,List.copyOf(directories),manifest,manifestBytes);
        prepared.verifyOriginals();return prepared;
    }
    /** Test seam exercises the actual pure production path; it issues no Prepared, Git or storage authority. */
    record SourceBytes(String relative,byte[] bytes){
        SourceBytes{FormalReleaseProducer.relative(relative);bytes=bytes.clone();}
        @Override public byte[] bytes(){return bytes.clone();}
    }
    record Rendered(String relative,byte[] bytes){
        Rendered{FormalReleaseProducer.relative(relative);bytes=bytes.clone();}
        @Override public byte[] bytes(){return bytes.clone();}
    }
    static List<Rendered> project(List<SourceBytes> sources,byte[] registry)throws IOException{
        FormalReleaseDescriptor.requireRegistry(registry);var result=new ArrayList<Rendered>();var seen=new HashSet<String>();
        for(var row:sources.stream().sorted(Comparator.comparing(SourceBytes::relative)).toList()){
            if(!seen.add(row.relative())||!allowedFile(row.relative()))throw new IOException("invalid or duplicate release path: "+row.relative());
            if(ACCEPTANCE_FILES.contains(row.relative()))continue;
            if(row.relative().equals("descriptor.mod")){String descriptor=FormalReleaseDescriptor.decode(row.bytes());
                if(descriptor.contains("remote_file_id")||Pattern.compile("(?m)^\\s*path\\s*=").matcher(descriptor).find())
                    throw new IOException("canonical inner release descriptor must not contain remote ID or installed path");}
            byte[] bytes=row.relative().equals("descriptor.mod")?FormalReleaseDescriptor.project(row.bytes(),registry):strip(row.relative(),row.bytes());
            if(Set.of(".txt",".gui",".yml",".mod").contains(suffix(row.relative()))){
                String text=FormalReleaseDescriptor.decode(bytes);
                for(String forbidden:FORBIDDEN)if(text.contains(forbidden))throw new IOException("acceptance identifier leaked: "+row.relative()+" / "+forbidden);
            }
            result.add(new Rendered(row.relative(),bytes));
        }
        if(result.size()>MAXIMUM_FILES||result.stream().mapToLong(row->row.bytes().length).sum()>MAXIMUM_LOGICAL_BYTES)
            throw new IOException("projected production payload exceeds finite bound");
        return List.copyOf(result);
    }
    static ReleaseManifest manifest(List<Rendered> rendered,String revision,String version,String tag){
        return new ReleaseManifest(2,version,tag,revision,WORKSHOP_ITEM_ID,
                rendered.stream().map(row->new ReleaseEntry(row.relative(),row.bytes().length,NativeRunProfileRules.sha(row.bytes()))).toList());
    }
    static String descriptorVersion(byte[] bytes)throws IOException{
        var matcher=Pattern.compile("^version=\"([0-9]+\\.[0-9]+\\.[0-9]+)\"$",Pattern.MULTILINE).matcher(FormalReleaseDescriptor.decode(bytes));
        if(!matcher.find())throw new IOException("descriptor must contain exactly one semantic version");String value=matcher.group(1);
        if(matcher.find())throw new IOException("descriptor must contain exactly one semantic version");return value;
    }
    static byte[] strip(String relative,byte[] original)throws IOException{
        if(!Set.of(".txt",".gui",".yml").contains(suffix(relative)))return original.clone();
        String text=FormalReleaseDescriptor.decode(original);var output=new StringBuilder();boolean inside=false;int begins=0,ends=0;
        for(String line:pythonLines(text)){
            String marker=FormalReleaseDescriptor.pythonStrip(line);
            if(marker.equals(BEGIN)){if(inside)throw new IOException("nested acceptance marker: "+relative);inside=true;begins++;continue;}
            if(marker.equals(END)){if(!inside)throw new IOException("unmatched acceptance end marker: "+relative);inside=false;ends++;continue;}
            if(marker.startsWith(RELEASE_ONLY)){
                if(inside)throw new IOException("release-only line inside acceptance block: "+relative);
                int indent=0;while(indent<line.length()&&FormalReleaseDescriptor.pythonWhitespace(line.charAt(indent)))indent++;
                String ending=line.endsWith("\r\n")?"\r\n":line.endsWith("\n")?"\n":"";
                output.append(line,0,indent).append(marker.substring(RELEASE_ONLY.length())).append(ending);continue;
            }
            if(LINE_TOKENS.stream().anyMatch(line::contains))continue;
            if(!inside)output.append(line);
        }
        if(inside||begins!=ends)throw new IOException("unclosed acceptance marker: "+relative);
        return FormalReleaseDescriptor.encode(output.toString(),FormalReleaseDescriptor.hasBom(original));
    }
    private static SourceTree readSource(Path root)throws IOException{
        List<CensusEntry> census=census(root);var directories=new ArrayList<NativeRunProfileManifest.TreeDirectory>();var files=new ArrayList<SourceFile>();long total=0;
        for(var entry:census){Path path=entry.relative().isEmpty()?root:root.resolve(entry.relative());
            if(entry.directory()){directories.add(new NativeRunProfileManifest.TreeDirectory(path.toString(),SharedSourceFiles.nativeDirectory(path)));continue;}
            if(!allowedFile(entry.relative()))continue;
            var witness=SharedSourceFiles.observe(path);long size=witness.source().bytes();total=Math.addExact(total,size);
            if(size>MAXIMUM_FILE_BYTES||total>MAXIMUM_LOGICAL_BYTES)throw new IOException("actual release source exceeds finite bytes");
            byte[] bytes=Files.readAllBytes(path);SharedSourceFiles.assertUnchanged(witness);
            if(bytes.length!=size||!NativeRunProfileRules.sha(bytes).equals(witness.source().sha256()))throw new IOException("actual release source changed during read");
            files.add(new SourceFile(entry.relative(),witness,bytes));
        }
        if(files.size()>MAXIMUM_FILES+ACCEPTANCE_FILES.size())throw new IOException("finite source file count exceeded");
        var tree=new SourceTree(census,directories,files);verifyCensus(root,tree);return tree;
    }
    private static List<CensusEntry> census(Path root)throws IOException{
        SharedSourceFiles.plainAncestors(root);
        if(!Files.isDirectory(root,LinkOption.NOFOLLOW_LINKS))throw new IOException("original mod source missing");
        for(String name:ROOT_FILES)if(!Files.isRegularFile(root.resolve(name),LinkOption.NOFOLLOW_LINKS))throw new IOException("required root file missing: "+name);
        for(String name:SUFFIXES.keySet())if(!Files.isDirectory(root.resolve(name),LinkOption.NOFOLLOW_LINKS))throw new IOException("required release directory missing: "+name);
        var result=new ArrayList<CensusEntry>();
        try(var walk=Files.walk(root)){
            var iterator=walk.iterator();while(iterator.hasNext()){
                Path path=iterator.next();if(result.size()>=MAXIMUM_ENTRIES)throw new IOException("complete mod source exceeds finite entry bound");
                SharedSourceFiles.plainAncestors(path);String relative=slash(root.relativize(path));
                boolean directory=Files.isDirectory(path,LinkOption.NOFOLLOW_LINKS);
                if(!directory&&!Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS))throw new IOException("nonordinary source entry: "+relative);
                if(!relative.isEmpty()){
                    String first=relative.split("/",2)[0];String suffix=suffix(relative);
                    if(!ROOT_FILES.contains(first)&&!SUFFIXES.containsKey(first)&&!DEVELOPMENT.contains(first))throw new IOException("path outside release allowlist: "+relative);
                    if(!directory&&(List.of(relative.split("/")).contains("__pycache__")||suffix.equals(".pyc")||suffix.equals(".pyo")))
                        throw new IOException("Python cache is forbidden in source: "+relative);
                    if(!directory&&!DEVELOPMENT.contains(first)&&!allowedFile(relative))throw new IOException("file outside release allowlist: "+relative);
                }
                result.add(new CensusEntry(relative,directory));
            }
        }
        result.sort(Comparator.comparing(CensusEntry::relative));return List.copyOf(result);
    }
    private static void verifyCensus(Path root,SourceTree original)throws IOException{
        if(!census(root).equals(original.entries()))throw new IOException("complete release source census changed");
        for(var directory:original.directories())if(!SharedSourceFiles.nativeDirectory(Path.of(directory.path())).equals(directory.identity()))
            throw new IOException("release source directory identity changed");
    }
    private static boolean allowedFile(String relative){
        String[] parts=relative.split("/",2);if(parts.length==1)return ROOT_FILES.contains(relative);
        Set<String> allowed=SUFFIXES.get(parts[0]);return allowed!=null&&allowed.contains(suffix(relative));
    }
    private static String suffix(String relative){int index=relative.lastIndexOf('.'),slash=relative.lastIndexOf('/');return index>slash?relative.substring(index).toLowerCase(Locale.ROOT):"";}
    private static String slash(Path path){return path.toString().replace('\\','/');}
    private static void relative(String value){
        if(value==null||value.isEmpty()||value.startsWith("/")||value.contains("\\")||value.indexOf('\0')>=0||value.contains(":")
                ||Arrays.stream(value.split("/",-1)).anyMatch(part->part.isEmpty()||part.equals(".")||part.equals("..")))
            throw new IllegalArgumentException("canonical relative production path required");
    }
    private static List<String> pythonLines(String text){
        var lines=new ArrayList<String>();int start=0;
        for(int i=0;i<text.length();i++){
            char ch=text.charAt(i);
            if(ch=='\r'){if(i+1<text.length()&&text.charAt(i+1)=='\n')i++;lines.add(text.substring(start,i+1));start=i+1;}
            else if(ch=='\n'||ch=='\u000b'||ch=='\f'||ch=='\u001c'||ch=='\u001d'||ch=='\u001e'||ch=='\u0085'||ch=='\u2028'||ch=='\u2029'){
                lines.add(text.substring(start,i+1));start=i+1;
            }
        }
        if(start<text.length())lines.add(text.substring(start));return List.copyOf(lines);
    }
    private static void current(Request request,Clock clock)throws IOException{
        if(!request.machineId().equals(WindowsJobProcess.currentMachineId())||!Instant.parse(request.reviewAtUtc()).isAfter(clock.instant()))
            throw new IOException("current machine and unexpired formal release request required");
    }
}

