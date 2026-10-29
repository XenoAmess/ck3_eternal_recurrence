package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeWire;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeWire.Envelope;
import org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeWire.Stage;

/** Retains the real compiled-native software corpus; it never implements a Root startup provider. */
public final class M7FormalLawNativeFixture {
    public static final String DIRECTORY_PROPERTY="xar.m7.formalNativeWireDirectory";
    private M7FormalLawNativeFixture() { }
    public record Pin(String filename,int bytes,String sha256,Stage stage) {
        public Pin { StrictJson.text(filename);StrictJson.require(bytes>0,"positive original byte count required");
            StrictJson.require(sha256.matches("[0-9a-f]{64}"),"exact original SHA required");Objects.requireNonNull(stage); }
    }
    public static final List<Pin> ORIGINALS=List.of(
        new Pin("wire-law-crown-query.json",1761,"b949489716a1b93c430aab57775822de64ccb57a580f9a5dedaec390ef9d8af1",Stage.QUERY),
        new Pin("wire-law-crown-submit-pending.json",1093,"47bac4c39291a164d1a19d547b969ecef2bc0bde8ca046a5902d5a79b9a7086b",Stage.SUBMITTED_PENDING),
        new Pin("wire-law-crown-receipt-unchanged.json",953,"66eff6266a65e6e3cefc06d6ff6cc4dce200c6f00fc1a4f226cd34253ae92237",Stage.UNCHANGED),
        new Pin("wire-law-crown-receipt-enacted.json",1030,"56e18b0dda2818f55e3fad43814e42e47ab50c688f776b289d160df4d1c5e3bc",Stage.ENACTED));
    public record Original(Pin pin,byte[] bytes,Envelope envelope) {
        public Original { Objects.requireNonNull(pin);bytes=bytes.clone();Objects.requireNonNull(envelope); }
        @Override public byte[] bytes(){return bytes.clone();}
    }
    public record Inputs(Original query,Original pending,Original unchanged,Original enacted) {
        public Inputs { Objects.requireNonNull(query);Objects.requireNonNull(pending);
            Objects.requireNonNull(unchanged);Objects.requireNonNull(enacted); }
        public List<Original> originals(){return List.of(query,pending,unchanged,enacted);}
        public String nativeProducerMachineId(){return "unknown";}
        public boolean currentRootQualification(){return false;}
    }
    public static Inputs retainOriginals() throws IOException {
        String configured=System.getProperty(DIRECTORY_PROPERTY);
        if(configured==null||configured.isBlank())throw new IOException(
                "MISSING_M7_NATIVE_LAW_DATA: mandatory "+DIRECTORY_PROPERTY+" is absent; NOT_RUN is not PASS");
        Path directory=Path.of(configured);
        if(!directory.isAbsolute())throw new IOException("M7 native law corpus directory must be absolute");
        return retainOriginals(directory);
    }
    public static Inputs retainOriginals(Path directory) throws IOException {
        Objects.requireNonNull(directory);
        if(!directory.isAbsolute()||!Files.isDirectory(directory))throw new IOException("M7 original corpus directory unavailable");
        Path root=directory.toRealPath();
        Original query=read(root,ORIGINALS.get(0)),pending=read(root,ORIGINALS.get(1));
        Original unchanged=read(root,ORIGINALS.get(2)),enacted=read(root,ORIGINALS.get(3));
        Inputs inputs=new Inputs(query,pending,unchanged,enacted);requireDataOnly(inputs);return inputs;
    }
    private static Original read(Path root,Pin pin) throws IOException {
        Path file=root.resolve(pin.filename()).normalize();
        if(!file.getParent().equals(root)||!Files.isRegularFile(file,LinkOption.NOFOLLOW_LINKS)
                ||Files.size(file)!=pin.bytes())throw new IOException("M7 original native law size/path mismatch: "+pin.filename());
        byte[] bytes=Files.readAllBytes(file);
        if(bytes.length!=pin.bytes()||!sha256(bytes).equals(pin.sha256()))
            throw new IOException("M7 original native law SHA mismatch: "+pin.filename());
        Envelope decoded=CrownAuthorityNativeWire.decode(bytes);
        if(decoded.payload().stage()!=pin.stage())throw new IOException("M7 original native law stage mismatch");
        return new Original(pin,bytes,decoded);
    }
    /** The actual Root callback and the independent software regression invoke this identical producer/consumer. */
    public static void requireDataOnly(Inputs inputs) throws IOException {
        for(Original original:inputs.originals()){
            byte[] persisted=CrownAuthorityNativeWire.encode(original.envelope());
            Envelope restored=CrownAuthorityNativeWire.decode(persisted);
            if(!restored.equals(original.envelope())
                    ||!StrictJson.parse(original.bytes()).equals(StrictJson.parse(persisted))
                    ||restored.currentMembership()!=CrownAuthorityNativeWire.Relation.UNKNOWN
                    ||restored.currentRootQualification())throw new IOException("M7 native law original serde/UNKNOWN drift");
        }
        var query=inputs.query().envelope();var observation=((CrownAuthorityNativeWire.Query)query.payload()).observation();
        var missing=CrownAuthorityNativeWire.consume(query,query.source(),observation.frame().playerCharacterId(),
                Optional.empty(),Optional.empty(),Map.of());
        if(!(missing instanceof CrownAuthorityNativeWire.Unknown unknown)
                ||unknown.reason()!=CrownAuthorityNativeWire.Missing.MEMBERSHIP_UNOBSERVED)
            throw new IOException("native law DATA must not create current membership or a queried frame");
        if(CrownAuthorityNativeWire.querySubmitRelation(query,inputs.pending().envelope())!=CrownAuthorityNativeWire.Relation.UNKNOWN
                ||CrownAuthorityNativeWire.effect(inputs.pending().envelope())!=CrownAuthorityNativeWire.Effect.PENDING
                ||CrownAuthorityNativeWire.effect(inputs.unchanged().envelope())!=CrownAuthorityNativeWire.Effect.NOT_ENACTED
                ||CrownAuthorityNativeWire.effect(inputs.enacted().envelope())!=CrownAuthorityNativeWire.Effect.NATIVE_ENACTED_UNBOUND)
            throw new IOException("M7 native law pending/unchanged/enacted DATA distinction drift");
        var context=originalSoftwareQueryContext(inputs);
        var chosen=org.xar.ck3.control.governance.crownauthority.CrownAuthorityProjectionCatalog.projectNativeQuery(
                context,query,context.before(),Map.of());
        if(chosen.status()!=org.xar.ck3.control.governance.crownauthority.CrownAuthorityPolicy.Status.READY
                ||!chosen.lawKey().equals("crown_authority_1"))
            throw new IOException("original software request/frame did not reach existing Crown selector");
        if(inputs.currentRootQualification())throw new IOException("software native corpus cannot qualify a Root");
    }
    /** Exact outer software context of the original Python FormalWholeWireDriver, not a current Game frame. */
    public static org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.RequestContext
            originalSoftwareQueryContext(Inputs input) {
        var query=input.query().envelope();var frame=((CrownAuthorityNativeWire.Query)query.payload()).observation().frame();
        var actor=StrictJson.object();actor.put("character_id",frame.playerCharacterId());actor.put("alive",true);
        var snapshot=new org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.Snapshot(query.source(),
                Optional.of("compiled-fixture-native:40"),frame.snapshotRevision().add(java.math.BigInteger.ONE),
                frame.snapshotRevision(),frame.dateRaw(),
                org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.Actor.fromOriginal(actor),true,true);
        return new org.xar.ck3.control.governance.crownauthority.CrownAuthorityNativeQuery.RequestContext(
                query.requestId(),snapshot.publicRevision(),true,snapshot);
    }
    private static String sha256(byte[] bytes){
        try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}
        catch(NoSuchAlgorithmException impossible){throw new IllegalStateException(impossible);}
    }
}
