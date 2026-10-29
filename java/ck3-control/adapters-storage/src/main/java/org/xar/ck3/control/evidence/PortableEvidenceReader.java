package org.xar.ck3.control.evidence;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.ByteBuffer;
import java.nio.channels.SeekableByteChannel;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.BasicFileAttributes;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.zip.CRC32;
import java.util.zip.DataFormatException;
import java.util.zip.Inflater;
import org.xar.ck3.control.contracts.evidence.PortableEvidenceJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes;
import static org.xar.ck3.control.contracts.evidence.PortableEvidence.*;

/** Actual portable bundle reader, with bounded inflation and exact compressed/uncompressed hashes.
 * No CK3 installation, historical external locator, event registry or native query is consulted.
 */
public final class PortableEvidenceReader {
    public static final class BundleException extends IOException {
        private static final long serialVersionUID=1L;
        public BundleException(String message){super(message);} public BundleException(String message,Throwable cause){super(message,cause);}
    }
    public record Limits(int maxManifestBytes,int maxCompressedBytes,long maxPayloadBytes) {
        public Limits {if(maxManifestBytes<1||maxManifestBytes>PortableEvidenceJson.MANIFEST_LIMIT||maxCompressedBytes<18||maxPayloadBytes<0||maxPayloadBytes>Integer.MAX_VALUE)throw new IllegalArgumentException("finite portable evidence limits required");}
        public static Limits defaults(){return new Limits(PortableEvidenceJson.MANIFEST_LIMIT,8*1024*1024,64L*1024*1024);}
    }
    private final Path root;private final Limits limits;private final Optional<ExactRef> originalManifest;
    public PortableEvidenceReader(Path root){this(root,Limits.defaults());}
    /** Unpinned compatibility/fixture reader; concrete public Methods require the source-pinned constructor. */
    public PortableEvidenceReader(Path root,Limits limits){this.root=Objects.requireNonNull(root).toAbsolutePath().normalize();this.limits=Objects.requireNonNull(limits);this.originalManifest=Optional.empty();}
    public PortableEvidenceReader(ExactRef manifest){this(manifest,Limits.defaults());}
    public PortableEvidenceReader(ExactRef manifest,Limits limits){
        Path path=Path.of(Objects.requireNonNull(manifest).path()).toAbsolutePath().normalize();
        if(!path.getFileName().toString().equals("manifest_v1.json")||manifest.bytes()<1)throw new IllegalArgumentException("actual portable manifest FileRef required");
        this.root=path.getParent();this.limits=Objects.requireNonNull(limits);this.originalManifest=Optional.of(manifest);
    }
    public ExactRef requireManifestSource(){return originalManifest.orElseThrow(()->new IllegalStateException("public evidence methods require a pinned original manifest source"));}
    public Manifest manifest() throws BundleException {
        try {
            requireDirectory(root);Path manifest=root.resolve("manifest_v1.json");byte[] bytes=readExact(manifest,limits.maxManifestBytes());
            if(originalManifest.isPresent()&&(originalManifest.orElseThrow().bytes()!=bytes.length||!originalManifest.orElseThrow().sha256().equals(hash(bytes))))throw new BundleException("portable manifest source changed");
            Manifest result=PortableEvidenceJson.manifest(bytes,hash(bytes).toUpperCase(Locale.ROOT));
            var expected=new HashSet<String>();result.evidence().forEach(blob->expected.add(blob.metadata().evidenceId().value()+".gz"));
            Path blobs=root.resolve("blobs");requireDirectory(blobs);var actual=new HashSet<String>();
            try(var paths=Files.list(blobs)){var entries=paths.iterator();int count=0;while(entries.hasNext()){Path path=entries.next();if(++count>expected.size()+1024)throw new BundleException("bounded blob directory entry budget exceeded");if(Files.isSymbolicLink(path))throw new BundleException("linked blob refused");if(Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS)){actual.add(path.getFileName().toString());if(actual.size()>expected.size())throw new BundleException("extra portable blob");}}}
            if(!actual.equals(expected))throw new BundleException("portable blob set mismatch");return result;
        }catch(BundleException failure){throw failure;}catch(IOException|IllegalArgumentException failure){throw new BundleException("portable manifest integrity error",failure);}
    }
    public Set<String> portableEventKeys() throws BundleException {
        var keys=new HashSet<String>();for(Blob blob:manifest().evidence())for(Reference reference:blob.metadata().references())keys.add(reference.eventDefinitionKey());return Set.copyOf(keys);
    }
    public List<Metadata> entriesFor(Optional<String> event,Optional<Kind> kind) throws BundleException {
        return filtered(manifest(),Objects.requireNonNull(event),Objects.requireNonNull(kind)).rows();
    }
    private record Filtered(List<Metadata> rows,boolean eventSeen) { }
    private static Filtered filtered(Manifest manifest,Optional<String> event,Optional<Kind> kind){
        var rows=new ArrayList<Metadata>();boolean seen=false;
        for(Blob blob:manifest.evidence()){
            Metadata value=blob.metadata();List<Reference> references=event.isEmpty()?value.references():value.references().stream().filter(reference->reference.eventDefinitionKey().equals(event.orElseThrow())).toList();
            if(!references.isEmpty())seen=true;if(references.isEmpty()||kind.isPresent()&&kind.orElseThrow()!=value.kind())continue;
            rows.add(new Metadata(value.evidenceId(),value.kind(),value.mediaType(),value.bytes(),references));
        }return new Filtered(List.copyOf(rows),seen);
    }
    public ListResult list(ListCall call){Objects.requireNonNull(call);if(call instanceof ListRejected invalid)return unavailable(invalid.parameters(),invalid.failure(),Optional.of(invalid.invalidParameter()));
        var query=(ListQuery)call;var parameters=query.parameters();final Manifest manifest;
        try{manifest=manifest();}catch(BundleException failure){return unavailable(parameters,Failure.INTEGRITY,Optional.empty());}
        if(parameters.afterEvidenceId().isPresent()&&manifest.evidence().stream().noneMatch(blob->blob.metadata().evidenceId().value().equals(parameters.afterEvidenceId().orElseThrow())))return unavailable(parameters,Failure.INVALID_CURSOR,Optional.of(Parameter.CURSOR));
        Filtered filtered=filtered(manifest,parameters.eventDefinitionKey(),parameters.kind());
        if(parameters.eventDefinitionKey().isPresent()&&!filtered.eventSeen())return unavailable(parameters,Failure.EVENT_NOT_INDEXED,Optional.of(Parameter.EVENT));
        List<Metadata> candidates=filtered.rows().stream().filter(value->parameters.afterEvidenceId().isEmpty()||value.evidenceId().value().compareTo(parameters.afterEvidenceId().orElseThrow())>0).toList();
        int size=Math.min(parameters.limit().orElseThrow(),candidates.size());List<Metadata> page=List.copyOf(candidates.subList(0,size));
        return new ListResult(parameters,Optional.of(manifest.datasetSha256()),filtered.rows().size(),page,candidates.size()>size?Optional.of(page.getLast().evidenceId().value()):Optional.empty(),Optional.empty(),Optional.empty());
    }
    private static ListResult unavailable(ListParameters parameters,Failure failure,Optional<Parameter> invalid){return new ListResult(parameters,Optional.empty(),0,List.of(),Optional.empty(),Optional.of(failure),invalid);}
    public ReadResult read(ReadCall call){Objects.requireNonNull(call);if(call instanceof ReadRejected invalid)return new ReadResult(invalid.parameters(),Optional.empty(),Optional.empty(),Optional.of(invalid.failure()));
        ReadQuery query=(ReadQuery)call;
        try {
            Optional<Blob> selected=manifest().evidence().stream().filter(value->value.metadata().evidenceId().equals(query.evidenceId())).findFirst();
            if(selected.isEmpty())return new ReadResult(query.parameters(),Optional.empty(),Optional.empty(),Optional.of(Failure.ID_NOT_INDEXED));
            Blob blob=selected.orElseThrow();byte[] compressed=readExact(root.resolve(blob.blobPath()),limits.maxCompressedBytes());
            if(compressed.length!=blob.blobBytes()||!hash(compressed).equals(blob.blobSha256())||blob.metadata().bytes()>limits.maxPayloadBytes())throw new BundleException("bounded compressed payload identity mismatch");
            Content content=verified(compressed,blob,query);
            if(query.offset()>blob.metadata().bytes())return new ReadResult(query.parameters(),Optional.of(blob.metadata()),Optional.empty(),Optional.of(Failure.OFFSET_RANGE));
            return new ReadResult(query.parameters(),Optional.of(blob.metadata()),Optional.of(content),Optional.empty());
        }catch(BundleException failure){return new ReadResult(query.parameters(),Optional.empty(),Optional.empty(),Optional.of(Failure.INTEGRITY));}
    }
    private static Content verified(byte[] compressed,Blob blob,ReadQuery query) throws BundleException {
        if(compressed.length<18||compressed[0]!=(byte)0x1f||compressed[1]!=(byte)0x8b||compressed[2]!=8||compressed[3]!=0||compressed[4]!=0||compressed[5]!=0||compressed[6]!=0||compressed[7]!=0)throw new BundleException("nondeterministic gzip header");
        try(var payload=new Payload(compressed,blob,query.offset(),query.maxBytes())){
            switch(blob.metadata().mediaType()){
                case JSON->{try(var parser=JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build().createParser(payload)){if(parser.nextToken()==null)throw new BundleException("empty JSON evidence");parser.skipChildren();if(parser.nextToken()!=null)throw new BundleException("trailing JSON evidence");}}
                case TEXT,YAML->{try(var reader=new InputStreamReader(payload,StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT))){char[] buffer=new char[8192];while(reader.read(buffer)!=-1){/* bounded streaming UTF-8 validation */}}}
                case PNG->{byte[] signature=payload.readNBytes(8);if(!java.util.Arrays.equals(signature,new byte[]{(byte)137,80,78,71,13,10,26,10}))throw new BundleException("invalid PNG evidence");payload.transferTo(java.io.OutputStream.nullOutputStream());}
            }
            payload.complete();return new Content(Base64.getEncoder().encodeToString(payload.slice.toByteArray()),payload.slice.size(),query.offset()+payload.slice.size()>=blob.metadata().bytes());
        }catch(BundleException failure){throw failure;}catch(IOException failure){throw new BundleException("invalid gzip or evidence media",failure);}
    }
    /** One inflation pass retains only the requested <=64 KiB slice, while verifying every byte. */
    private static final class Payload extends InputStream {
        final Inflater inflater=new Inflater(true);final MessageDigest digest=sha();final CRC32 crc=new CRC32();final ByteArrayOutputStream slice=new ByteArrayOutputStream();
        final byte[] compressed;final Blob blob;final long offset;final int maximum;long total;boolean finished;
        Payload(byte[] compressed,Blob blob,long offset,int maximum){this.compressed=compressed;this.blob=blob;this.offset=offset;this.maximum=maximum;inflater.setInput(compressed,10,compressed.length-18);}
        @Override public int read() throws IOException {byte[] one=new byte[1];int read=read(one,0,1);return read<0?-1:Byte.toUnsignedInt(one[0]);}
        @Override public int read(byte[] bytes,int start,int length) throws IOException {
            Objects.checkFromIndexSize(start,length,bytes.length);if(length==0)return 0;if(finished)return -1;
            try {
                int count=inflater.inflate(bytes,start,length);
                if(count==0){if(inflater.finished()){complete();return -1;}throw new BundleException("truncated or dictionary gzip stream");}
                long next=Math.addExact(total,count);if(next>blob.metadata().bytes())throw new BundleException("inflated evidence exceeds declared payload budget");
                digest.update(bytes,start,count);crc.update(bytes,start,count);long begin=Math.max(total,offset),end=Math.min(next,offset+maximum);
                if(begin<end)slice.write(bytes,start+(int)(begin-total),(int)(end-begin));total=next;return count;
            }catch(DataFormatException|ArithmeticException failure){throw new BundleException("invalid gzip deflate stream",failure);}
        }
        void complete() throws BundleException {
            if(finished)return;
            if(!inflater.finished()||inflater.getRemaining()!=0||total!=blob.metadata().bytes()||!HexFormat.of().formatHex(digest.digest()).equals(blob.metadata().evidenceId().value())
                    ||little(compressed,compressed.length-8)!=crc.getValue()||little(compressed,compressed.length-4)!=(total&0xFFFF_FFFFL))throw new BundleException("gzip trailing bytes, trailer, payload hash or length mismatch");finished=true;
        }
        @Override public void close(){inflater.end();}
    }
    private static long little(byte[] bytes,int start){return (long)Byte.toUnsignedInt(bytes[start])|((long)Byte.toUnsignedInt(bytes[start+1])<<8)|((long)Byte.toUnsignedInt(bytes[start+2])<<16)|((long)Byte.toUnsignedInt(bytes[start+3])<<24);}
    private static void requireDirectory(Path path) throws BundleException {if(Files.isSymbolicLink(path)||!Files.isDirectory(path,LinkOption.NOFOLLOW_LINKS))throw new BundleException("real bundle directory required");}
    private static byte[] readExact(Path path,int maximum) throws BundleException {
        try {
            BasicFileAttributes before=IdentityBearingFileAttributes.read(path);
            if(!before.isRegularFile()||before.isSymbolicLink()||before.fileKey()==null||before.size()>maximum)throw new BundleException("bounded original file identity required");
            byte[] result=new byte[Math.toIntExact(before.size())];
            try(SeekableByteChannel input=Files.newByteChannel(path,Set.of(StandardOpenOption.READ,LinkOption.NOFOLLOW_LINKS))){ByteBuffer buffer=ByteBuffer.wrap(result);while(buffer.hasRemaining()){if(input.read(buffer)<=0)throw new BundleException("original file truncated or made no progress");}if(input.read(ByteBuffer.allocate(1))!=-1)throw new BundleException("original file grew");}
            BasicFileAttributes after=IdentityBearingFileAttributes.read(path);
            if(!Objects.equals(before.fileKey(),after.fileKey())||!before.lastModifiedTime().equals(after.lastModifiedTime())||before.size()!=after.size())throw new BundleException("original file changed during evidence read");return result;
        }catch(BundleException failure){throw failure;}catch(IOException|ArithmeticException failure){throw new BundleException("portable evidence original unavailable",failure);}
    }
    private static MessageDigest sha(){try{return MessageDigest.getInstance("SHA-256");}catch(NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}}
    private static String hash(byte[] bytes){return HexFormat.of().formatHex(sha().digest(bytes));}
}
