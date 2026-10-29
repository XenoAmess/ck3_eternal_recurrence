package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.function.Supplier;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactCodec;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.wave2.military.actualcontact.ActualContactCodec;
import org.xar.ck3.control.wave2.military.actualcontact.ActualContactModel;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyJson.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ArmyTypes.*;
import static org.xar.ck3.control.nativebridge.capabilities.army.ContactScopeObservation.*;

/** Two existing application-main READ producers. A capability advertisement never replaces current source qualification. */
public final class ContactScopeReads {
    /** The immutable semantic frame is taken from the actual held Root capture, never supplied as a cached query. */
    public record Selection(Query query,Context context,Obj snapshot,BigInteger connectionGeneration) {
        public Selection {
            Objects.requireNonNull(query);Objects.requireNonNull(context);Objects.requireNonNull(snapshot);
            UInt64.positive(connectionGeneration);UInt64.positive(context.nativeRevision());context.dateRaw().intValueExact();
            var frame=context.before().frame();
            require(new OpportunityJson.Bool(true).equals(snapshot.get("paused")),"contact requires a paused current map");
            equalSnapshot(snapshot,"snapshot_id",frame.snapshotId());equalSnapshot(snapshot,"episode_run_id",frame.episodeRunId());
            equalSnapshot(snapshot,"revision",frame.revision());equalSnapshot(snapshot,"native_revision",context.nativeRevision());
            equalSnapshot(snapshot,"date_raw",context.dateRaw());
            Obj diagnostics=OpportunityJson.object(snapshot.get("diagnostics"),"contact diagnostics");
            require(OpportunityJson.integer(diagnostics.get("connection_generation"),"connection generation").equals(connectionGeneration),"contact connection differs");
            subject(query,snapshot);
        }
        public static Selection current(Query query,Complete actual,Instant deadline) {
            Objects.requireNonNull(actual);
            return new Selection(query,new Context(actual.identity(),actual.source(),actual.sessionId(),deadline),actual.semantic(),actual.connectionGeneration());
        }
    }
    public record ActualPorts(PlanningReadPort reads,ActionPorts.OutcomeArchive originals,
            NativeEffectEvidence.FrameLoader frames,Supplier<ContinuityStorePort.Session> currentSession) {
        public ActualPorts {Objects.requireNonNull(reads);Objects.requireNonNull(originals);Objects.requireNonNull(frames);Objects.requireNonNull(currentSession);}
    }
    @FunctionalInterface public interface ActualRuntime {ActualPorts current();}
    private final ActualRuntime runtime;
    private final RootReadContractCatalog.Family<Selection,ContactScopeObservation> projected,actual;
    public ContactScopeReads(ExactRef definition,ExactRef decoder,PlanningReadPort actualReads,
            ActionPorts.OutcomeArchive actualArchive,NativeEffectEvidence.FrameLoader originalFrames,Supplier<ContinuityStorePort.Session> sameSession) {
        this(definition,decoder,stable(actualReads,actualArchive,originalFrames,sameSession));
    }
    /** Deferred binding resolves actual ports only when invoked. Absence is an error, never a fabricated fallback. */
    public ContactScopeReads(ExactRef definition,ExactRef decoder,ActualRuntime actualRuntime) {
        runtime=Objects.requireNonNull(actualRuntime);
        projected=family("projected-contact-scope-v1",PROJECTED,definition,decoder);
        actual=family("actual-contact-scope-v1",ACTUAL,definition,decoder);
    }
    private static ActualRuntime stable(PlanningReadPort reads,ActionPorts.OutcomeArchive archive,NativeEffectEvidence.FrameLoader frames,Supplier<ContinuityStorePort.Session> session) {
        var actual=new ActualPorts(reads,archive,frames,session);return ()->actual;
    }
    public List<RootReadContractCatalog.Family<?,?>> families(){return List.of(projected,actual);}
    public ReadContract<ContactScopeObservation> contract(RootReadContractCatalog catalog,Selection selected) {
        Objects.requireNonNull(catalog);Objects.requireNonNull(selected);
        return catalog.issue(selected.query() instanceof Projected?projected:actual,selected);
    }
    public PlanningReadResult<ContactScopeObservation> collect(ContinuityStorePort.Session same,RootReadContractCatalog catalog,Selection selected) {
        Objects.requireNonNull(same);Objects.requireNonNull(selected);
        var contract=contract(catalog,selected);
        Context c=selected.context();
        ActualPorts actual=Objects.requireNonNull(runtime.current(),"actual Contact ports are not installed");
        return actual.reads().read(same,contract,new PlanningReadRequest(c.before(),c.source(),c.sessionId(),contract.operation(),arguments(),c.deadline()));
    }
    private RootReadContractCatalog.Family<Selection,ContactScopeObservation> family(String id,String capability,ExactRef definition,ExactRef decoder) {
        return new RootReadContractCatalog.Family<>(id,Selection.class,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of(capability),
                definition,decoder,ContactScopeReads::key,s->new OperationKey(s.query().step()),s->{
                    require(s.query().capability().equals(capability),"wrong typed contact family");subject(s.query(),s.snapshot());
                    return new ReadContract<>(id+"-"+DriverJson.sha256(key(s).bytes()),new OperationKey(s.query().step()),Optional.of(capability),capability,
                            ReadContract.PermissionMode.ADVERTISED_CAPABILITY,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,definition,
                            (request,requestId)->{verify(request,s);return new NativeRequest(s.query().step(),Optional.of(capability),new RawJson(new byte[]{'{','}'}));},
                            receipt->{verify(receipt.request(),s);return decode(s,receipt);},
                            receipt->{verify(receipt.request(),s);return decode(s,receipt);},
                            (original,value,current,semantic)->{
                                verify(original.request(),s);verify(current,s);
                                // This comparison is DATA only. The sole canonical publisher additionally proves exact raw Native bytes,
                                // installed decoder/contract, source, session, capabilities and current writer ancestry.
                                require(org.xar.ck3.control.application.planning.military.NativeMilitaryInputView.sameNativeOperands(s.snapshot(),semantic),"contact canonical reuse changed native operands");
                                require(value.equals(decode(s,original)),"contact canonical value differs from the archived full decoder");
                            });
                });
    }
    public ContactScopeObservation decode(Selection selected,PlanningReadReceipt receipt) {
        verify(receipt.request(),selected);Context c=selected.context();
        ObjectNode result=ArmyNativeReadEvidence.result(ArmyNativeReadEvidence.contextForRequest(c,receipt.request()),receipt);
        ActualPorts ports=Objects.requireNonNull(runtime.current(),"actual Contact ports are not installed");
        var archive=ports.originals().withSession(Objects.requireNonNull(ports.currentSession().get(),"actual current writer session required"));
        Complete before=RootGuardEvidence.loadFrame(receipt.before().binding(),archive,ports.frames());
        Complete after=RootGuardEvidence.loadFrame(receipt.after().binding(),archive,ports.frames());
        require(before.identity().equals(c.before())&&before.source().equals(c.source())&&before.sessionId().equals(c.sessionId())
                &&before.connectionGeneration().equals(selected.connectionGeneration())&&before.semantic().equals(selected.snapshot())
                &&after.identity().equals(before.identity())&&after.source().equals(before.source())&&after.sessionId().equals(before.sessionId())
                &&after.connectionGeneration().equals(before.connectionGeneration())&&after.fullBindingSha256().equals(before.fullBindingSha256())
                &&after.semantic().equals(before.semantic()),"contact query crossed its complete original native/Driver/source frame");
        return normalize(selected,result);
    }
    /** Pure strict body normalization, shared by live decoder and archived replay. It does not mint source authority. */
    public static ContactScopeObservation normalize(Selection selected,ObjectNode result) {
        String payload=selected.query() instanceof Projected?"projected_contact_scope":"actual_contact_scope";
        if(selected.query() instanceof Projected) {
            closed(result,"step","accepted","status","query_sequence","snapshot_revision",payload,"backend_id");
        } else {
            closed(result,"step","accepted","status","query_sequence","snapshot_revision",payload);
        }
        equal(result.get("step"),selected.query().step());yes(result.get("accepted"));equal(result.get("status"),"available");
        equal(result.get("snapshot_revision"),selected.context().nativeRevision());
        BigInteger sequence=positive(result.get("query_sequence")).value();
        Obj army=subject(selected.query(),selected.snapshot());int origin=positiveId(army,"current_province_id"),owner=positiveId(army,"owner_character_id");
        var c=selected.context();var frame=c.before().frame();
        var capture=new ProjectedContactPolicy.Capture(frame.snapshotId(),frame.revision(),c.nativeRevision(),selected.connectionGeneration(),frame.episodeRunId());
        ContactScopeObservation.Scope scope;
        Optional<String> backendId;
        if(selected.query() instanceof Projected p) {
            var decoded=ProjectedContactCodec.decodeScope(result.get(payload));
            require(decoded.matches(new ProjectedContactPolicy.Snapshot(capture,c.dateRaw().intValueExact()),new ProjectedContactPolicy.Request(p.key(),origin,owner)),"projected native scope differs from actual selected subject/frame");
            scope=new ProjectedScope(decoded);
            backendId=Optional.of(text(result.get("backend_id")));
        }else {
            var a=(Actual)selected.query();var decoded=ActualContactCodec.decodeScope(result.get(payload));
            require(decoded.matches(new ActualContactModel.Binding(a.key(),c.dateRaw().intValueExact(),c.nativeRevision()))
                    &&decoded.subjectOwnerCharacterId()==owner,"actual native scope differs from actual selected subject/frame");
            scope=new ActualScope(decoded);
            backendId=Optional.empty();
        }
        return new ContactScopeObservation(selected.query(),scope,sequence,backendId,capture);
    }
    private static Obj subject(Query query,Obj snapshot) {
        var expected=new OpportunityJson.IntegerValue(BigInteger.valueOf(query.subject()));
        var matches=OpportunityJson.array(snapshot.get("player_armies"),"player armies").stream().map(row->OpportunityJson.object(row,"army"))
                .filter(row->expected.equals(row.get("army_id"))).toList();
        require(matches.size()==1&&new OpportunityJson.Bool(true).equals(matches.getFirst().get("controllable")),"contact subject must be exactly one current controllable public CUnit");
        Obj army=matches.getFirst();int origin=positiveId(army,"current_province_id");positiveId(army,"owner_character_id");
        if(query instanceof Actual)require(origin==query.target(),"actual contact subject must currently occupy the requested Province");
        return army;
    }
    private static int positiveId(Obj row,String name){int id=OpportunityJson.integer(row.get(name),name).intValueExact();require(id>0,"positive full native identity required: "+name);return id;}
    private static void equalSnapshot(Obj row,String field,String expected){require(new OpportunityJson.Text(expected).equals(row.get(field)),"contact semantic "+field+" differs");}
    private static void equalSnapshot(Obj row,String field,BigInteger expected){require(new OpportunityJson.IntegerValue(expected).equals(row.get(field)),"contact semantic "+field+" differs");}
    private static Obj arguments(){return DriverJson.object(new byte[]{'{','}'},2);}
    private static RawJson key(Selection s) {
        Context c=s.context();var frame=c.before().frame();
        ObjectNode n=empty().put("step",s.query().step()).put("snapshot_sha256",DriverJson.sha256(DriverJson.encode(s.snapshot())))
                .put("source_sha256",c.source().sourceRef().sha256()).put("session_id",c.sessionId()).put("snapshot_id",frame.snapshotId())
                .put("revision",frame.revision()).put("native_revision",c.nativeRevision()).put("date_raw",c.dateRaw())
                .put("connection_generation",s.connectionGeneration()).put("episode_run_id",frame.episodeRunId()).put("observation_version",c.before().observationVersion());
        n.set("game",c.before().game().toJson());return new RawJson(bytes(n));
    }
    private static void verify(PlanningReadRequest request,Selection selected) {
        Context c=selected.context();
        require(request.before().equals(c.before())&&request.source().equals(c.source())&&request.sessionId().equals(c.sessionId())
                &&request.operation().value().equals(selected.query().step())&&request.arguments().equals(arguments()),"contact request changed source/origin/operation/arguments");
    }
}
