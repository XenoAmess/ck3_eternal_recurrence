package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.*;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.frontend_rules.GameplayStartEffects;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real first-episode transition. Preview and commit reread the same surviving settled Start and originals. */
public final class GameplayEntryAuthority implements WriterContracts.TransitionAuthority {
    private final ContinuityWriter writer;
    private final NativeOutcomeArchive archive;
    private final InitialDriverBootstrap bootstrap;
    private final GameplayStartEffects effects;
    private final ExactRef implementation;
    public GameplayEntryAuthority(ContinuityWriter writer,NativeOutcomeArchive archive,InitialDriverBootstrap bootstrap,
            GameplayStartEffects effects,ExactRef actualImplementation) {
        this.writer=Objects.requireNonNull(writer);this.archive=Objects.requireNonNull(archive);this.bootstrap=Objects.requireNonNull(bootstrap);
        this.effects=Objects.requireNonNull(effects);implementation=Objects.requireNonNull(actualImplementation);
        StrictJson.require(archive.writer()==writer && implementation.bytes()>0,"same writer/archive and actual first-episode implementation required");
    }
    private RootExecutableBindings fixtureBindings;
    public synchronized void bindFixtureBindings(RootExecutableBindings identical) {
        Objects.requireNonNull(identical);
        StrictJson.require(fixtureBindings==null||fixtureBindings==identical,"entry cannot replace its identical installed fixture catalog");
        fixtureBindings=identical;
    }
    public WriterContracts.Request request(ContinuityStorePort.Session borrowed,ActionReceipt actual)throws IOException {
        writer.requireSession(borrowed);var staged=bootstrap.current(actual.command().actionId());staged.assertCurrent(borrowed);
        StrictJson.require(bootstrap.fixture().isEmpty()&&actual.state() instanceof ActionState.Settled
                &&((ActionState.Settled)actual.state()).settlement() instanceof ActionState.GameplayEntered,
                "ordinary first episode requires its settled actual Start observation");
        var observation=((ActionState.GameplayEntered)((ActionState.Settled)actual.state()).settlement()).observation();
        return requestBody(borrowed,actual,staged,observation.after(),observation.supportingEvidence().getFirst(),
                observation.references(),observation.campaignRootRead(),java.util.Optional.empty());
    }
    public WriterContracts.Request requestFixture(ContinuityStorePort.Session same,ActionReceipt actual,ActionCommand parent,
            String handlerId,FixtureBusinessEvidence business)throws IOException {
        writer.requireSession(same);var cursor=fixtureCurrent(same,actual,parent,handlerId,business);
        var staged=bootstrap.current(actual.command().actionId());staged.assertCurrent(same);
        StrictJson.require(staged.semantic().equals(business.finalSemantic())&&staged.rootRead().equals(business.campaignRootRead()),
                "fixture entry changed its actual final semantic or independent campaign-root READ");
        var bound=archive.withSession(same);
        var fixture=new WriterContracts.GameplayEntryFixture(handlerId,bound.receiptReferenceOf(cursor.parent()),
                ContinuityJson.canonical(FixtureProofCodec.businessEvidence(business,bound))).toJson();
        var refs=new LinkedHashSet<>(business.references());refs.add(bound.receiptReferenceOf(cursor.parent()));
        for(var child:cursor.recordedChildren())refs.add(bound.receiptReferenceOf(child));
        var request=requestBody(same,actual,staged,business.finalSemantic().frame(),business.qualification(),List.copyOf(refs),
                business.campaignRootRead(),java.util.Optional.of(fixture));
        staged.retainFixtureEntrySeed(same,request);return request;
    }
    private ActionChildPlanningScope.FixtureCursor fixtureCurrent(ContinuityStorePort.Session same,ActionReceipt actual,
            ActionCommand parent,String handlerId,FixtureBusinessEvidence business)throws IOException {
        StrictJson.require(bootstrap.fixture().isPresent()&&fixtureBindings!=null,"actual explicit fixture entry products are absent");
        var cursor=ActionChildPlanningScope.fixtureCurrent(same,same.head(),parent,handlerId);
        var installed=fixtureBindings.composites().find(parent.operation()).orElseThrow();
        StrictJson.require(installed instanceof FixtureCompositeActionPort&&installed.handlerId().equals(handlerId),
                "fixture entry has no identical installed source-owned business verifier");
        business.validateParent(parent);business.validateChildren(cursor.execution(),cursor.recordedChildren());
        StrictJson.require(business.originalStart().equals(actual)&&cursor.recordedChildren().contains(actual),
                "fixture entry substituted its canonical physically settled Start");
        ((FixtureCompositeActionPort)installed).requireFixtureBusiness(parent,cursor.execution(),business);
        for(var retained:ContinuityActionJournal.receipts(same.head().state(),archive.withSession(same))){
            if(retained.command().actionId().equals(parent.actionId())){
                StrictJson.require(retained.bodySha256().equals(ActionCodec.bodySha256(parent)),"fixture parent body changed");continue;
            }
            StrictJson.require(retained.settled()&&(retained.command().origin() instanceof CommandOrigin.Frontend
                    ||cursor.recordedChildren().contains(retained)&&retained.command().source().equals(parent.source())
                        &&retained.command().sessionId().equals(parent.sessionId())),
                    "fixture cannot absorb another unresolved or unrelated gameplay history");
        }
        return cursor;
    }
    private WriterContracts.Request requestBody(ContinuityStorePort.Session borrowed,ActionReceipt actual,InitialDriverBootstrap.Staged staged,
            org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity after,ExactRef entryBasis,List<ExactRef> materials,
            PlanningReadReceipt campaignRootRead,java.util.Optional<ObjectNode> fixtureDetails)throws IOException {
        var seed=staged.seed();var frame=after.frame();var state=StrictJson.object();
        state.put("evidence_id","gameplay-entry:"+actual.command().actionId());
        var source=state.putObject("source");source.set("implementation",implementation.toJson());source.set("policy",staged.policy().source().toJson());
        source.set("environment",staged.policy().environment().toJson());source.put("machine_id",actual.command().source().machineId());
        state.put("action_id",actual.command().actionId());state.put("action_body_sha256",actual.bodySha256());
        ExactRef receipt=archive.withSession(borrowed).receiptReferenceOf(actual);state.set("start_receipt",receipt.toJson());
        state.set("entry_basis",entryBasis.toJson());state.set("full_driver",seed.fullDriver().toJson());
        var facts=OpportunityJson.object(staged.frame().semantic().get("java_driver_facts_evidence"),"java_driver_facts_evidence");
        ExactRef driverFacts=new ExactRef(OpportunityJson.text(facts.get("path"),"path"),OpportunityJson.integer(facts.get("bytes"),"bytes").longValueExact(),
                OpportunityJson.text(facts.get("sha256"),"sha256"));
        state.set("driver_facts",driverFacts.toJson());state.put("driver_version",seed.driverVersion());state.put("episode_epoch",seed.episodeEpoch());
        state.put("episode_id",frame.episodeRunId());state.put("auxiliary_sha256",staged.auxiliarySha256());
        var f=state.putObject("frame");f.put("snapshot_id",frame.snapshotId());f.put("revision",frame.revision());f.put("native_revision",frame.identity().nativeRevision());
        f.put("date_raw",frame.identity().dateRaw());f.put("player_character_id",frame.identity().player());f.put("connection_generation",staged.frame().connectionGeneration().toString());
        var game=state.putObject("game");game.put("pid",after.game().pid());game.put("creation_filetime",after.game().creationFiletime().value().toString());
        state.put("session_id",actual.command().sessionId());
        var refs=new LinkedHashSet<ExactRef>();refs.add(implementation);refs.add(receipt);refs.addAll(materials);
        refs.add(seed.fullDriver());refs.add(driverFacts);refs.addAll(staged.policy().evidenceClosure());
        refs.add(archive.withSession(borrowed).readReferenceOf(campaignRootRead));
        if(fixtureDetails.isPresent())state.set("fixture",fixtureDetails.orElseThrow());
        return new WriterContracts.Request(WriterContracts.GAMEPLAY_ENTRY_KIND,ContinuityJson.canonical(state),List.copyOf(refs));
    }
    @Override public String revalidate(ContinuityState predecessor,WriterContracts.Request request)throws IOException {
        throw new IOException("first episode requires the original actual writer Head and borrowed Session");
    }
    @Override public String revalidate(WriterContracts.Head predecessor,WriterContracts.Request request)throws IOException {
        var borrowed=writer.borrowedSession();writer.requireSession(borrowed);
        StrictJson.require(predecessor.digest().equals(borrowed.head().digest()),"first episode is not borrowing the original current writer Head");
        ObjectNode details=checkedDetails(predecessor.state(),request);
        var archive=this.archive.withSession(borrowed);
        ExactRef reference=ExactRef.fromJson(details.get("start_receipt"));ActionReceipt actual=archive.loadReceipt(reference);
        ActionReceipt canonical=ContinuityActionJournal.lookup(predecessor.state(),StrictJson.text(details.get("action_id")),archive)
                .orElseThrow(()->new IOException("actual first Start is absent from the surviving canonical action chain"));
        StrictJson.require(archive.receiptReferenceOf(actual).equals(reference)
                && Arrays.equals(ActionReceiptCodec.encodeReceipt(actual,archive),ActionReceiptCodec.encodeReceipt(canonical,archive))
                && actual.bodySha256().equals(StrictJson.text(details.get("action_body_sha256"))),"first episode receipt is not the exact current canonical Start");
        if(!details.has("fixture")){
            for(ActionReceipt retained:ContinuityActionJournal.receipts(predecessor.state(),archive))
                StrictJson.require(retained.settled() && retained.command().origin() instanceof CommandOrigin.Frontend,
                        "first empty gameplay branch cannot absorb an unresolved or prior gameplay action");
        }
        var prior=predecessor.state().toJson();
        StrictJson.require(!prior.has("pending_cycle") || prior.get("pending_cycle").isNull(),"first entry cannot replace an unresolved original cycle");
        WriterContracts.Request reproduced;
        if(details.has("fixture")){
            var row=WriterContracts.GameplayEntryFixture.fromJson(details.get("fixture"));
            var parent=archive.loadReceipt(row.parentReceipt());
            var business=FixtureProofCodec.businessEvidence(DriverJson.toNode(DriverJson.object(row.businessEvidence(),DriverJson.MAX_NATIVE_BYTES)),archive);
            reproduced=requestFixture(borrowed,actual,parent.command(),row.handlerId(),business);
        }else{effects.verifyArchived(actual,archive);reproduced=request(borrowed,actual);}
        var staged=bootstrap.current(actual.command().actionId());staged.assertCurrent(borrowed);
        StrictJson.require(Arrays.equals(reproduced.details(),request.details()) && reproduced.evidence().equals(request.evidence()),
                "first entry fields or complete evidence differ from the actual sole producer");
        var seed=staged.seed();
        StrictJson.require(seed.fullDriver().equals(ExactRef.fromJson(details.get("full_driver")))
                && seed.driverVersion()==StrictJson.integer(details.get("driver_version"),0,StrictJson.MAX_SAFE_INTEGER)
                && seed.episodeEpoch()==StrictJson.integer(details.get("episode_epoch"),0,StrictJson.MAX_SAFE_INTEGER)
                && staged.auxiliarySha256().equals(StrictJson.text(details.get("auxiliary_sha256")))
                && seed.expectedSession().sessionId().equals(StrictJson.text(details.get("session_id")))
                && staged.frame().identity().frame().episodeRunId().equals(StrictJson.text(details.get("episode_id"))),"actual first full Driver/session/auxiliary changed before entry commit");
        ObjectNode source=StrictJson.object(details.get("source"),Set.of("implementation","policy","environment","machine_id"));
        StrictJson.require(implementation.equals(ExactRef.fromJson(source.get("implementation"))) && staged.policy().source().equals(ExactRef.fromJson(source.get("policy")))
                && staged.policy().environment().equals(ExactRef.fromJson(source.get("environment")))
                && predecessor.state().machineId().equals(StrictJson.text(source.get("machine_id"))),"first entry source qualification differs");
        for(ExactRef ref:request.evidence()){var pin=borrowed.capturePin(ref,WriterContracts.MAX_PIN_BYTES);borrowed.verifyPin(pin);}
        byte[] full=this.archive.readArtifact(borrowed,seed.fullDriver(),org.xar.ck3.control.application.readiness.ReadinessArchive.Role.DRIVER.maximumBytes());
        var decoded=org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.decodeComplete(full);
        StrictJson.require((details.has("fixture")?Arrays.equals(decoded.encode(),staged.fixtureDriver(borrowed).driver().encode()):decoded.commandHistory().isEmpty())
                &&decoded.session().episodeRunId().equals(StrictJson.text(details.get("episode_id")))
                &&decoded.session().bridgePid()==seed.expectedSession().game().pid(),
                "actual initial full Driver/history differs from its source-produced original branch");
        var result=StrictJson.object();result.put("head_sha256",predecessor.digest());result.set("entry",details);
        return ContinuityJson.digest(result);
    }
    /** Canonical archived Entry verification only. It never reopens a retired fixture scope or grants current Game permission. */
    public void verifyFixtureEntry(ContinuityStorePort.Session same,FixtureBusinessObservation actual)throws IOException {
        writer.requireSession(same);Objects.requireNonNull(actual);
        var prepared=WriterTransactionCodec.decodePrepared(archive.readArtifact(same,actual.entryPrepared(),WriterTransactionCodec.MAXIMUM_BYTES),
                same.head().state().machineId());
        var receipt=WriterTransactionCodec.decodeReceipt(archive.readArtifact(same,actual.entryReceipt(),WriterTransactionCodec.MAXIMUM_BYTES),
                same.head().state().machineId());
        same.requireCommitted(prepared,receipt);
        StrictJson.require(receipt.disposition()!=WriterContracts.Disposition.NO_CHANGE&&receipt.eventIdentity().equals(prepared.request().identity()),
                "fixture parent has no actual canonical Entry commit");
        var details=checkedDetails(prepared.predecessor().state(),prepared.request());
        StrictJson.require(details.has("fixture"),"ordinary Entry cannot stand in for fixture business completion");
        var fixture=WriterContracts.GameplayEntryFixture.fromJson(details.get("fixture"));
        var bound=archive.withSession(same);
        StrictJson.require(Arrays.equals(ContinuityJson.canonical(FixtureProofCodec.businessEvidence(actual.evidence(),bound)),fixture.businessEvidence()),
                "fixture completion changed the Entry's exact original qualification/root/history inputs");
        var originalParent=bound.loadReceipt(fixture.parentReceipt());
        var parent=ContinuityActionJournal.lookup(same.head().state(),actual.evidence().parentActionId(),bound).orElseThrow();
        ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),originalParent,bound);
        StrictJson.require(parent.bodySha256().equals(originalParent.bodySha256()),"fixture Entry changed its actual canonical parent");
        actual.validateParent(parent.command());
        CompositeExecution execution;
        if(parent.state() instanceof ActionState.CompositeRunning value)execution=value.execution();
        else if(parent.state() instanceof ActionState.CompositeUnknown value)execution=value.execution();
        else if(parent.state() instanceof ActionState.CompositeSettled value)execution=value.execution();
        else throw new IOException("fixture Entry has no actual composite parent");
        var children=new ArrayList<ActionReceipt>();
        for(var child:execution.children()){
            var canonical=ContinuityActionJournal.lookup(same.head().state(),child.actionId(),bound).orElseThrow();
            StrictJson.require(canonical.bodySha256().equals(child.bodySha256()),"fixture canonical child body changed");
            children.add(canonical);
        }
        actual.validateChildren(execution,children);
        StrictJson.require(execution.handlerId().equals(fixture.handlerId())
                &&actual.evidence().originalStart().command().actionId().equals(StrictJson.text(details.get("action_id")))
                &&actual.evidence().originalStart().bodySha256().equals(StrictJson.text(details.get("action_body_sha256"))),
                "fixture Entry changed its source-owned handler or real original Start");
        var expected=details.deepCopy();expected.put("schema","xar.java.first-gameplay-entry-state/v1");
        var current=same.head().state().toJson();
        StrictJson.require(ContinuityJson.same(expected,current.get(WriterContracts.GAMEPLAY_ENTRY_FIELD))
                &&ExactRef.fromJson(details.get("full_driver")).equals(ExactRef.fromJson(current.get(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD))),
                "fixture Entry/history was replaced after its original canonical commit");
        var full=org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.decodeComplete(
                archive.readArtifact(same,ExactRef.fromJson(details.get("full_driver")),
                        org.xar.ck3.control.application.readiness.ReadinessArchive.Role.DRIVER.maximumBytes()));
        StrictJson.require(full.session().episodeRunId().equals(StrictJson.text(details.get("episode_id")))
                &&full.session().bridgePid()==actual.evidence().finalSemantic().frame().game().pid(),
                "fixture retained full Driver belongs to another original episode/Game");
    }
    @Override public ContinuityState reduce(ContinuityState predecessor,WriterContracts.Request request)throws IOException {
        return reduceInitial(predecessor,request);
    }
    static ContinuityState reduceInitial(ContinuityState predecessor,WriterContracts.Request request) {
        ObjectNode details=checkedDetails(predecessor,request);
        ObjectNode next=org.xar.ck3.control.continuity.FreshContinuityGenesis.entryPredecessor(predecessor,request);
        next.set(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD,details.get("full_driver").deepCopy());
        ObjectNode entry=details.deepCopy();entry.put("schema","xar.java.first-gameplay-entry-state/v1");
        next.set(WriterContracts.GAMEPLAY_ENTRY_FIELD,entry);
        var reduced=ContinuityState.fromJson(next,predecessor.machineId());
        WriterContracts.requireGameplayEntryReduction(predecessor,reduced,request,false);return reduced;
    }
    static ObjectNode checkedDetails(ContinuityState predecessor,WriterContracts.Request request) {
        StrictJson.require(WriterContracts.GAMEPLAY_ENTRY_KIND.equals(request.kind()),"exact shared first-episode event kind required");
        var state=predecessor.toJson();
        StrictJson.require(!state.has(WriterContracts.DRIVER_HISTORY_BASELINE_FIELD) && !state.has(WriterContracts.GAMEPLAY_ENTRY_FIELD),
                "missing, null and existing canonical history are distinct; only absent first entry may initialize");
        ObjectNode row=WriterContracts.gameplayEntryDetails(request);
        StrictJson.text(row.get("action_id"));WriterContracts.requireDigest(StrictJson.text(row.get("action_body_sha256")));
        WriterContracts.requireDigest(StrictJson.text(row.get("auxiliary_sha256")));StrictJson.text(row.get("episode_id"));StrictJson.text(row.get("session_id"));
        StrictJson.require(StrictJson.text(row.get("evidence_id")).equals("gameplay-entry:"+StrictJson.text(row.get("action_id")))
                && StrictJson.text(row.get("episode_id")).equals("java-start-"+StrictJson.text(row.get("action_body_sha256")).substring(0,32)),
                "initial episode identity differs from its original immutable Start body");
        ObjectNode source=StrictJson.object(row.get("source"),Set.of("implementation","policy","environment","machine_id"));
        StrictJson.require(predecessor.machineId().equals(StrictJson.text(source.get("machine_id"))),"first entry source belongs to another machine");
        for(String field:List.of("implementation","policy","environment"))StrictJson.require(request.evidence().contains(ExactRef.fromJson(source.get(field))),"missing actual initial source: "+field);
        ObjectNode frame=StrictJson.object(row.get("frame"),Set.of("snapshot_id","revision","native_revision","date_raw","player_character_id","connection_generation"));
        StrictJson.text(frame.get("snapshot_id"));StrictJson.integer(frame.get("revision"),1,StrictJson.MAX_SAFE_INTEGER);
        StrictJson.integer(frame.get("native_revision"),java.math.BigInteger.ONE,StrictJson.UINT64_MAX);
        StrictJson.integer(frame.get("date_raw"),Integer.MIN_VALUE,Integer.MAX_VALUE);StrictJson.integer(frame.get("player_character_id"),1,StrictJson.MAX_SAFE_INTEGER);
        var connection=new org.xar.ck3.control.contracts.CrossJsDecimalUInt64(StrictJson.text(frame.get("connection_generation")));
        StrictJson.require(new java.math.BigInteger(connection.decimal()).signum()>0,"positive exact connection required");
        ObjectNode game=StrictJson.object(row.get("game"),Set.of("pid","creation_filetime"));StrictJson.integer(game.get("pid"),1,0xffff_ffffL);
        var birth=new org.xar.ck3.control.contracts.CrossJsDecimalUInt64(StrictJson.text(game.get("creation_filetime")));
        StrictJson.require(new java.math.BigInteger(birth.decimal()).signum()>0,"positive exact Game birth required");
        for(String field:List.of("start_receipt","entry_basis","full_driver","driver_facts")) {
            ExactRef ref=ExactRef.fromJson(row.get(field));StrictJson.require(ref.bytes()>0 && request.evidence().contains(ref),"complete actual entry reference missing from writer evidence: "+field);
        }
        StrictJson.integer(row.get("driver_version"),0,StrictJson.MAX_SAFE_INTEGER);StrictJson.integer(row.get("episode_epoch"),0,StrictJson.MAX_SAFE_INTEGER);
        return row;
    }
}

