package org.xar.ck3.control.application.planning.finance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import static org.xar.ck3.control.application.planning.finance.OrdinaryFinanceCollector.obj;
import java.io.IOException;
import java.util.Arrays;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FullJsonTree;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQueryCodec;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec.ObservedRequest;

/** Full construction request custody. A reference or a DATA factory is never a source or action permission. */
public final class ConstructionOriginalSource {
    public static final String SCHEMA="xar.java.construction-original-request/v2";
    @FunctionalInterface public interface Borrowed { Session current()throws IOException; }
    /** One internally consistent DATA result. Authority still requires a fresh same-session physical read. */
    public static final class Loaded {
        private final Obj original;
        private final ObservedRequest observed;
        private Loaded(Obj original,ObservedRequest observed) {
            this.original=Objects.requireNonNull(original);this.observed=Objects.requireNonNull(observed);
        }
        public Obj original(){return original;}
        public ObservedRequest observed(){return observed;}
    }
    private final ActionPorts.OutcomeArchive archive;
    private final Borrowed borrowed;
    public ConstructionOriginalSource(ActionPorts.OutcomeArchive archive,Borrowed borrowed) {
        this.archive=Objects.requireNonNull(archive);this.borrowed=Objects.requireNonNull(borrowed);
    }
    /** The old small representation remains inline. Only explicitly oversized new requests acquire a full sidecar. */
    public Obj preserve(ObservedRequest original) {
        Objects.requireNonNull(original);byte[] full=original.original();
        require(full.length>0&&full.length<=RawJson.MAXIMUM_BYTES,"construction full original exceeds material budget");
        try {
            var scoped=archive.withSession(Objects.requireNonNull(borrowed.current(),"held construction writer required"));
            if(full.length<=OrdinaryWartimeConstructionCodec.MAX_BYTES) {
                new ObservedRequest(full); // Preserve the old decoder and its narrower domain; never catch-fallback.
                return DriverJson.object(full,OrdinaryWartimeConstructionCodec.MAX_BYTES);
            }
            Obj value=DriverJson.object(full,FullJsonTree.MAXIMUM_BYTES);
            ExactRef reference=scoped.preserveMaterial(RawJson.fullMaterial(full));
            RawJson reopened=scoped.loadFullMaterial(reference);exact(reference,reopened.bytes());
            require(Arrays.equals(full,reopened.bytes()),"construction full original changed during archive readback");
            Obj manifest=obj("schema",new Text(SCHEMA),"input_ref",reference(reference),"financing_request",value.get("financing_request"));
            require(DriverJson.encode(manifest).length<=ActionCodec.MAX_COMMAND_BYTES,"construction manifest exceeds command bound");
            return manifest;
        } catch(IOException unavailable) { throw new IllegalArgumentException("held construction original archive unavailable",unavailable); }
    }
    /** Both versions have exact independent parsers. No parse or custody failure changes lanes. */
    public static Loaded resolve(Session same,ActionPorts.OutcomeArchive archive,Obj supplied) {
        Objects.requireNonNull(supplied);var scoped=Objects.requireNonNull(archive).withSession(Objects.requireNonNull(same));
        if(new Text(OrdinaryWartimeConstructionCodec.SCHEMA).equals(supplied.get("schema"))) {
            ObservedRequest original=new ObservedRequest(encode(supplied));
            return new Loaded(DriverJson.object(original.original(),OrdinaryWartimeConstructionCodec.MAX_BYTES),original);
        }
        require(new Text(SCHEMA).equals(supplied.get("schema"))
                &&supplied.members().keySet().equals(Set.of("schema","input_ref","financing_request")),"exact construction full manifest required");
        ExactRef reference=ExactRef.fromJson(StrictJson.parse(DriverJson.encode(object(supplied.get("input_ref"),"construction full input reference"))));
        require(reference.bytes()>0&&reference.bytes()<=RawJson.MAXIMUM_BYTES,"construction full input reference exceeds material budget");
        RawJson raw=scoped.loadFullMaterial(reference);byte[] full=raw.bytes();exact(reference,full);
        Obj original=DriverJson.object(full,FullJsonTree.MAXIMUM_BYTES);
        // ActionCodec owns canonical typed argument ordering. Compare its complete projection on both sides, never structural equality.
        require(Arrays.equals(PublicDataJson.encodeTyped(supplied.get("financing_request")).bytes(),
                        PublicDataJson.encodeTyped(original.get("financing_request")).bytes()),
                "construction manifest financing differs from full original");
        return new Loaded(original,ObservedRequest.fromFullMaterial(full));
    }
    public static Loaded resolveCommand(Session same,ActionPorts.OutcomeArchive archive,ActionCommand command) {
        require(command.operation().equals(OrdinaryConstructionPolicy.OPERATION),"construction command required");
        Obj supplied=object(command.arguments().get("ordinary_cash_request"),"construction original request");
        Loaded loaded=resolve(same,archive,supplied);
        if(new Text(OrdinaryWartimeConstructionCodec.SCHEMA).equals(supplied.get("schema")))return loaded;
        require(loaded.observed().input().stage()==OrdinaryWartimeConstruction.Stage.QUOTED_OUTLAY,"construction command requires its quoted original");
        Obj outlay=object(loaded.original().get("quoted_outlay"),"original quoted outlay");
        Obj query=object(outlay.get("query_observation"),"original native query");
        Obj snapshot=object(query.get("starting_snapshot"),"original complete snapshot");var frame=command.before().frame();var id=frame.identity();
        require(new Text(frame.snapshotId()).equals(snapshot.get("snapshot_id"))&&new IntegerValue(frame.revision()).equals(snapshot.get("revision"))
                &&new IntegerValue(id.nativeRevision()).equals(snapshot.get("native_revision"))&&new IntegerValue(id.dateRaw()).equals(snapshot.get("date_raw"))
                &&new Text(frame.episodeRunId()).equals(snapshot.get("episode_run_id"))
                &&new IntegerValue(id.player()).equals(object(snapshot.get("played_character"),"original actor").get("character_id"))
                &&new IntegerValue(frame.revision()).equals(query.get("expected_revision")),"construction full original crossed command frame");
        return loaded;
    }
    public Loaded load(Session same,ActionCommand command) { return resolveCommand(same,archive,command); }
    /** Only SDK computation receives a role; every original snapshot/native envelope remains in caller custody. */
    public static byte[] finalizeQuery(byte[] original) {
        return ConstructionQueryCodec.finalizeObservation(ConstructionQueryCodec.projectFullMaterialInput(original));
    }
    /** The archived binding consumes the original sidecar before delegating the unchanged native verifier. */
    public static NativeRecordedEvidenceVerifier.Binding archivedBinding(NativeRecordedEvidenceVerifier.Binding original,Borrowed borrowed) {
        Objects.requireNonNull(original);Objects.requireNonNull(borrowed);
        return new NativeRecordedEvidenceVerifier.Binding(original.operation(),original.definitionSource(),(head,receipt,archive)->{
            Obj supplied=object(receipt.command().arguments().get("ordinary_cash_request"),"archived construction original");
            if(new Text(SCHEMA).equals(supplied.get("schema"))) {
                try { resolveCommand(borrowed.current(),archive,receipt.command()); }
                catch(IOException unavailable) { throw new IllegalArgumentException("archived construction original writer unavailable",unavailable); }
            } else require(new Text(OrdinaryWartimeConstructionCodec.SCHEMA).equals(supplied.get("schema")),"unsupported archived construction request schema");
            original.verifier().verify(head,receipt,archive);
        });
    }
    private static Obj reference(ExactRef reference) {return DriverJson.object(StrictJson.canonical(reference.toJson(),4096),4096);}
    private static void exact(ExactRef reference,byte[] full) {
        require(reference.bytes()==full.length&&reference.sha256().equals(ActionCodec.sha256(full)),"construction full original length or SHA changed");
    }
}
