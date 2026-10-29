package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Test consumer of the one C16 Person10NativeCorpus v1 producer. A measured manifest grants no Native credit. */
final class Person10CorpusManifest {
    private static final int MANIFEST_MAX=1<<20,FILE_MAX=1<<20,TOTAL_MAX=16<<20,FILE_LIMIT=256,ENTRY_LIMIT=1024;
    private Person10CorpusManifest() { }
    record FileRef(String path,long bytes,String sha256) {
        FileRef { absolute(path);need(bytes>=1&&bytes<=FILE_MAX,"bounded original corpus file required");sha(sha256); }
        byte[] read() throws IOException { return verified(absolute(path),bytes,sha256); }
    }
    record Manifest(Path source,String sourceSha256,String machineId,String observedAtUtc,Path root,List<FileRef> files) {
        Manifest { files=List.copyOf(files); }
    }
    static Manifest configured() throws IOException {
        return require(absolute(required("xar.person10.nativeCorpus")),absolute(required("xar.person10.nativeCorpus.manifest")),required("xar.person10.nativeCorpus.manifest.sha256"));
    }
    static Manifest require(Path corpus,Path source,String expectedSha) throws IOException {
        Path root=absolute(corpus.toString()),manifestPath=absolute(source.toString());sha(expectedSha);plain(manifestPath,false);plain(root,true);
        long manifestBytes=Files.size(manifestPath);need(manifestBytes>=1&&manifestBytes<=MANIFEST_MAX,"bounded corpus manifest required");
        byte[] raw=verified(manifestPath,manifestBytes,expectedSha);JsonNode node=StrictJson.parse(raw,MANIFEST_MAX);
        ObjectNode object=StrictJson.object(node,Set.of("schema","machine_id","observed_at_utc","corpus_root","files"));
        need("xar.person10-native-corpus/v1".equals(text(object,"schema")),"exact Person10 corpus schema required");
        String machine=text(object,"machine_id"),observed=text(object,"observed_at_utc");need(!machine.isBlank()&&machine.length()<=256,"measurement machine required");Instant.parse(observed);
        need(root.toString().equals(text(object,"corpus_root")),"corpus root and pinned manifest differ");
        JsonNode values=object.get("files");need(values.isArray()&&!values.isEmpty()&&values.size()<=FILE_LIMIT,"bounded nonempty corpus file list required");
        List<FileRef> files=new ArrayList<>();Set<Path> paths=new HashSet<>();long total=0;
        for(JsonNode value:values){ObjectNode row=StrictJson.object(value,Set.of("path","bytes","sha256"));String path=text(row,"path");Path child=absolute(path);
            need(child.startsWith(root)&&!child.equals(root)&&child.getFileName().toString().endsWith(".json")&&paths.add(child),"distinct canonical JSON children required");
            FileRef ref=new FileRef(path,StrictJson.integer(row.get("bytes"),1,FILE_MAX),text(row,"sha256"));total=Math.addExact(total,ref.bytes());need(total<=TOTAL_MAX,"finite corpus byte total required");files.add(ref);
        }
        need(files.equals(files.stream().sorted(Comparator.comparing(FileRef::path)).toList()),"manifest files must retain producer path order");
        Manifest manifest=new Manifest(manifestPath,expectedSha,machine,observed,root,files);verify(manifest);return manifest;
    }
    static void verify(Manifest manifest) throws IOException {
        plain(manifest.source(),false);long size=Files.size(manifest.source());need(size>=1&&size<=MANIFEST_MAX,"manifest size drift");verified(manifest.source(),size,manifest.sourceSha256());
        for(FileRef file:manifest.files())file.read();
        need(manifest.files().equals(measure(manifest.root())),"actual complete corpus differs from pinned file list");
        verified(manifest.source(),size,manifest.sourceSha256());
    }
    private static List<FileRef> measure(Path root) throws IOException {
        plain(root,true);List<FileRef> files=new ArrayList<>();int entries=0;long total=0;
        try(var walk=Files.walk(root)){var paths=walk.iterator();while(paths.hasNext()){
            Path path=paths.next();need(++entries<=ENTRY_LIMIT,"bounded corpus entries required");plainAncestors(path);need(path.toRealPath().equals(path),"corpus canonical identity drift");
            if(Files.isDirectory(path,LinkOption.NOFOLLOW_LINKS))continue;plain(path,false);if(!path.getFileName().toString().endsWith(".json"))continue;
            long bytes=Files.size(path);need(bytes>=1&&bytes<=FILE_MAX&&files.size()<FILE_LIMIT,"bounded plain JSON corpus required");total=Math.addExact(total,bytes);need(total<=TOTAL_MAX,"finite corpus total required");
            byte[] raw=Files.readAllBytes(path);need(raw.length==bytes&&Files.size(path)==bytes,"corpus changed while reading");files.add(new FileRef(path.toString(),bytes,digest(raw)));
        }}
        need(!files.isEmpty(),"NOT_EXECUTED: original native corpus is empty");files.sort(Comparator.comparing(FileRef::path));return List.copyOf(files);
    }
    private static byte[] verified(Path path,long expectedBytes,String expectedSha) throws IOException {
        plain(path,false);need(Files.size(path)==expectedBytes,"original file size differs");byte[] raw=Files.readAllBytes(path);
        need(raw.length==expectedBytes&&Files.size(path)==expectedBytes&&digest(raw).equals(expectedSha),"original file SHA/identity differs");plain(path,false);return raw;
    }
    private static void plain(Path path,boolean directory) throws IOException {
        plainAncestors(path);need((directory?Files.isDirectory(path,LinkOption.NOFOLLOW_LINKS):Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS))&&path.toRealPath().equals(path),"plain canonical corpus path required");
    }
    private static void plainAncestors(Path path) throws IOException {
        for(Path current=path;current!=null;current=current.getParent())if(Files.exists(current,LinkOption.NOFOLLOW_LINKS))need(!Files.isSymbolicLink(current)&&current.toRealPath().equals(current),"corpus link or canonical ancestor drift");
    }
    private static Path absolute(String value){need(value!=null&&!value.isBlank()&&value.length()<=4096&&value.codePoints().noneMatch(c->c<32||c==127),"bounded canonical absolute corpus path required");Path p=Path.of(value);need(p.isAbsolute()&&p.equals(p.normalize()),"canonical absolute path required");return p;}
    private static String required(String property){String value=System.getProperty(property);need(value!=null&&!value.isBlank(),"NOT_EXECUTED: required original Person10 corpus property missing: "+property);return value;}
    private static String text(ObjectNode node,String name){return StrictJson.text(node.get(name));}
    private static void sha(String value){need(value!=null&&value.matches("[0-9a-f]{64}"),"exact lowercase SHA256 required");}
    private static String digest(byte[] raw){try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));}catch(NoSuchAlgorithmException failure){throw new IllegalStateException(failure);}}
    private static void need(boolean condition,String reason){StrictJson.require(condition,reason);}
}
