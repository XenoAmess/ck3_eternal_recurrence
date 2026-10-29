package org.xar.ck3.control.nativebridge.capabilities.publicmethods.coatofarms.extensions;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeEffectRegistry;
import org.xar.ck3.control.application.effects.coa.NativeSourceObservation;
import org.xar.ck3.control.application.readiness.NativeSourceProofCodec;
import org.xar.ck3.control.application.readiness.NativeSourceProofDocument;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.frontend_coa.*;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_coa.CoaData.*;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaContract.need;
import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.frontendcoa.FrontendCoaCodec.*;

/** Completes the native source/clipboard function using its actual independent clipboard read and source scope.
 * It never observes pixels, dynasty application, a game day, or a Game domain effect. */
public final class CoaSourceEffects implements NativeEffectRegistry.Observer {
    @FunctionalInterface public interface ScopePort {Scope current(ActionCommand original,ActionState.Attempt actual)throws IOException;}
    @FunctionalInterface public interface ClipboardPort {NativeCoaClipboard.Sample read()throws IOException;}
    @FunctionalInterface public interface OriginalReader {byte[] read(ExactRef original,int maximum)throws IOException;}
    public record Scope(Binding binding,Optional<BigInteger> frontendSequence,ExactRef nativePacket,ExactRef helloPacket,Optional<ExactRef> qualification,
            Instant qualifiedAt,Instant validUntil,List<ExactRef> supporting){
        public Scope(Binding binding,Optional<BigInteger> frontendSequence,ExactRef nativePacket,ExactRef helloPacket,ExactRef qualification,Instant qualifiedAt,Instant validUntil,List<ExactRef> supporting){this(binding,frontendSequence,nativePacket,helloPacket,Optional.of(qualification),qualifiedAt,validUntil,supporting);}
        public Scope{Objects.requireNonNull(qualification);Objects.requireNonNull(binding);frontendSequence=Objects.requireNonNull(frontendSequence);frontendSequence.ifPresent(FrontendFrame::positive);need(frontendSequence.isPresent()==(binding instanceof FrontendBinding||binding instanceof SnapshotBinding b&&b.mode()==SnapshotMode.FRONTEND_SNAPSHOT),"frontend observation sequence must come from its actual frontend scope");for(ExactRef ref:List.of(nativePacket,helloPacket))need(ref.bytes()>0,"actual native/HELLO/source qualification originals required");Objects.requireNonNull(qualifiedAt);Objects.requireNonNull(validUntil);need(validUntil.isAfter(qualifiedAt),"source observation scope was not current");supporting=List.copyOf(supporting);need(supporting.size()<=16,"bounded actual source scope evidence required");}
        ObjectNode encode(){ObjectNode n=empty().put("schema","xar.coa-independent-source-scope/v1").put("qualified_at",qualifiedAt.toString()).put("valid_until",validUntil.toString());frontendSequence.ifPresentOrElse(v->n.put("frontend_sequence",v),()->n.putNull("frontend_sequence"));n.set("binding",CoaSourceMaterials.bindingNode(binding));n.set("native_packet",nativePacket.toJson());n.set("hello_packet",helloPacket.toJson());qualification.ifPresentOrElse(value->n.set("qualification",value.toJson()),()->n.putNull("qualification"));var refs=n.putArray("supporting");supporting.forEach(ref->refs.add(ref.toJson()));return n;}
        static Scope decode(ObjectNode n){if(!n.has("qualification")){n=n.deepCopy();n.putNull("qualification");}exact(n,Set.of("schema","qualified_at","valid_until","frontend_sequence","binding","native_packet","hello_packet","qualification","supporting"));need(string(n,"schema").equals("xar.coa-independent-source-scope/v1"),"source scope schema differs");JsonNode refs=n.get("supporting");need(refs.isArray()&&refs.size()<=16,"source scope support outside bound");var support=new ArrayList<ExactRef>();for(JsonNode ref:refs)support.add(ExactRef.fromJson(ref));return new Scope(CoaCodec.binding(raw(n.get("binding"))),n.get("frontend_sequence").isNull()?Optional.empty():Optional.of(exactInteger(n,"frontend_sequence")),ExactRef.fromJson(n.get("native_packet")),ExactRef.fromJson(n.get("hello_packet")),n.get("qualification").isNull()?Optional.empty():Optional.of(ExactRef.fromJson(n.get("qualification"))),Instant.parse(string(n,"qualified_at")),Instant.parse(string(n,"valid_until")),support);}
        List<ExactRef> references(){var out=new LinkedHashSet<ExactRef>();out.add(nativePacket);out.add(helloPacket);qualification.ifPresent(out::add);out.addAll(supporting);return List.copyOf(out);}
    }
    private record Result(RawJson publicResult,NativeSourceObservation.Outcome outcome,String expectedClipboard,boolean clipboardMustMatch){ }
    private final CoaSourceMaterials materials;
    private final ActionPorts.OutcomeArchive archive;
    private final ScopePort scopes;
    private final ClipboardPort clipboard;
    private final OriginalReader reader;
    private final List<ExactRef> sources;
    public CoaSourceEffects(CoaSourceMaterials sameMaterials,ActionPorts.OutcomeArchive sameArchive,ScopePort actualScopes,ClipboardPort actualClipboard,OriginalReader actualOriginals,List<ExactRef> actualSourceOriginals){
        materials=Objects.requireNonNull(sameMaterials);archive=Objects.requireNonNull(sameArchive);scopes=Objects.requireNonNull(actualScopes);clipboard=Objects.requireNonNull(actualClipboard);reader=Objects.requireNonNull(actualOriginals);sources=List.copyOf(actualSourceOriginals);need(!sources.isEmpty()&&sources.size()<=8,"actual source producer roster required");
    }
    @Override public NativeEffectRegistry.Projected observe(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch){
        if(!(dispatch instanceof NativeActionPort.AckReceived ack)||!ack.nativeOk()||ack.originalResultToken().isEmpty())return pending(attempt,"CoA native source outcome remains unknown; no native call is replayed");
        try{
            Binding expected=binding(command,attempt);Result result=decode(command,attempt,ack,expected,archive);
            Scope before=scopes.current(command,attempt);NativeCoaClipboard.Sample actual=clipboard.read();Scope after=scopes.current(command,attempt);
            validateScope(before,expected,command,attempt,ack);validateScope(after,expected,command,attempt,ack);
            requirePair(before,actual,after);
            requireClipboard(result,actual);need(!actual.observedAt().isBefore(attempt.submittedAt()),"independent clipboard is older than original native submission");
            ObjectNode scope=empty().put("schema","xar.coa-independent-source-pair/v1");scope.set("before",before.encode());scope.set("after",after.encode());
            ExactRef dispatchRef=archive.referenceOf(dispatch),clipboardRef=archive.preserveMaterial(actual.encode()),scopeRef=archive.preserveMaterial(raw(scope)),resultRef=archive.preserveMaterial(result.publicResult());
            var refs=new LinkedHashSet<ExactRef>(sources);refs.add(command.source().sourceRef());refs.addAll(before.references());refs.addAll(after.references());need(refs.size()<=64,"complete source/native originals exceed finite observation roster");
            var observation=new NativeSourceObservation(command.operation(),ActionCodec.bodySha256(command),attempt.requestId(),result.outcome(),actual.observedAt(),dispatchRef,clipboardRef,scopeRef,resultRef,List.copyOf(refs));
            observation.validate(command,attempt,dispatch);verify(command,attempt,dispatch,observation,archive);
            return new NativeEffectRegistry.Projected(new ActionPorts.NativeSourceObserved(observation),java.util.Optional.of(result.publicResult()));
        }catch(IOException|RuntimeException unavailable){return pending(attempt,"independent CoA clipboard/source completion unavailable: "+(unavailable.getMessage()==null?unavailable.getClass().getSimpleName():unavailable.getMessage()));}
    }
    private static NativeEffectRegistry.Projected pending(ActionState.Attempt attempt,String reason){return NativeEffectRegistry.Projected.pending(reason,List.of(attempt.guard().nativeEvidence()));}
    private static Binding binding(ActionCommand command,ActionState.Attempt attempt){
        if(command.origin() instanceof CommandOrigin.Frontend)return CoaSourceMaterials.bindingOf(command.origin(),command.sessionId());
        var original=command.before().frame();return new SnapshotBinding(SnapshotMode.GAMEPLAY,original.snapshotId(),original.revision(),original.identity().nativeRevision(),original.identity().dateRaw().longValueExact(),java.util.Optional.of(original.episodeRunId()),attempt.guard().connectionGeneration(),command.origin().game().pid());
    }
    private Result decode(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived ack,Binding binding,ActionPorts.OutcomeArchive originalArchive){
        need(ack.requestId().equals(attempt.requestId())&&ack.outbound().isPresent(),"CoA actual original native outbound identity required");
        NativeRequest retained=attempt.preparedRequest();need(retained.step().equals(command.operation().value())&&retained.requiredCapability().equals(java.util.Optional.of(CoaUpload.capability(retained.step()))),"CoA original prepared native operation/capability changed");
        RawJson token=ack.originalResultToken().orElseThrow();
        try{
            NativeWire.Frame packet=NativeWire.decode(ack.originalPacket());need(packet instanceof NativeWire.CommandResult,"CoA original complete returned packet required");var actual=(NativeWire.CommandResult)packet;
            need(actual.nativeOk()&&actual.requestId().equals(attempt.requestId())&&actual.result().token().isPresent()&&java.util.Arrays.equals(actual.result().token().orElseThrow().value(),token.bytes()),"CoA native token differs from original returned packet");
            byte[] expected=NativeWire.execute(attempt.requestId(),retained.step(),binding.nativeRevision(),retained.additionalFields().bytes());
            need(java.util.Arrays.equals(expected,ack.outbound().orElseThrow().originalPacket()),"CoA actual outbound source/revision/operation differs from the canonical prepared native request");
        }catch(IOException malformed){throw new IllegalArgumentException("CoA original native packet is malformed",malformed);}
        if(command.operation().value().equals(PROBE_STEP)){
            var material=new CoaSourceMaterials(originalArchive).material(command,binding);var args=object(raw(org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(command.arguments())));boolean apply=bool(args,"apply",null);
            ProbeResult value=CoaCodec.nativeProbe(token,material.source(),binding,apply);
            var outcome=NativeSourceObservation.Outcome.valueOf("PROBE_"+value.status().name());
            return new Result(raw(probe(value)),outcome,material.source().source(),value.clipboardReadbackMatched());
        }
        need(command.operation().value().equals(EXPORT_STEP)&&command.arguments().members().isEmpty(),"CoA native Copy accepts only its original empty request");
        ExportResult value=CoaCodec.nativeExport(token,binding);boolean success=value.status()==ExportStatus.EXPORTED;
        return new Result(raw(exported(value)),success?NativeSourceObservation.Outcome.EXPORTED:NativeSourceObservation.Outcome.EXPORT_UNAVAILABLE,value.source().orElse(""),success);
    }
    private static void requireClipboard(Result result,NativeCoaClipboard.Sample actual){
        if(result.clipboardMustMatch())need(actual.source().isPresent()&&actual.source().orElseThrow().equals(result.expectedClipboard()),"actual independent clipboard source differs from original native source result");
        // A validated native negative result records the independent clipboard fact; it claims no write/paste effect.
    }
    private void validateScope(Scope actual,Binding expected,ActionCommand command,ActionState.Attempt attempt,NativeActionPort.AckReceived dispatch)throws IOException{
        need(actual.binding().equals(expected)&&!actual.qualifiedAt().isBefore(attempt.submittedAt()),"independent source scope crossed original binding or submission time");
        NativeWire.Frame hello=NativeWire.decode(reader.read(actual.helloPacket(),1024*1024));need(hello instanceof NativeWire.Hello,"actual source scope HELLO original required");NativeWire.Hello h=(NativeWire.Hello)hello;
        need(h.pid()==expected.bridgePid()&&h.connectionGeneration().equals(expected.connectionGeneration())&&h.gameSha256().equalsIgnoreCase(EXE_SHA256)&&h.adapterId().equals(ADAPTER_ID)&&h.adapterStatus().equals("ready")&&h.buildMatch()&&h.capabilities().contains(CoaUpload.capability(command.operation().value())),"independent native source scope changed HELLO/build/process/capability");
        NativeWire.Frame frame=NativeWire.decode(reader.read(actual.nativePacket(),NativeWire.MAXIMUM_FRAME_BYTES+4));
        if(expected instanceof FrontendBinding||expected instanceof SnapshotBinding b&&b.mode()==SnapshotMode.FRONTEND_SNAPSHOT){
            need(frame instanceof NativeWire.CommandResult,"independent frontend source scope requires original route response");var result=(NativeWire.CommandResult)frame;need(result.nativeOk()&&!result.requestId().equals(attempt.requestId())&&result.result().token().isPresent(),"original action ACK cannot substitute for independent source observation");
            ObjectNode route=object(new RawJson(result.result().token().orElseThrow().value()));need(string(route,"step").equals("query-frontend-gui-route-v1"),"independent scope packet is not the actual native route observer");
            var actualSource=new org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.Source(new org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.Binding(h.pid(),h.connectionGeneration()),org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.Build.require(GAME_VERSION,h.gameSha256()));
            var actualRoute=org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesCodec.route(new RawJson(result.result().token().orElseThrow().value()),actualSource,actual.frontendSequence().orElseThrow());
            need(actualRoute.route()!=org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.Route.UNAVAILABLE,"independent actual frontend route is unavailable");
            need(actual.frontendSequence().orElseThrow().compareTo(command.origin().requireFrontend().frame().querySequence())>0,"independent actual frontend sequence is not later than original source command");
            // Original C++ CommandResultFrame emits only step/accepted/status for this route.
            // Its ordering is the actual FOS lease sequence, never invented native query/revision fields.
            if(expected instanceof SnapshotBinding snapshot){
                // FOS frontend_host10 owns the fixed qualification/manifest/Driver/native roster.
                need(actual.supporting().size()>=4&&actual.supporting().getFirst().equals(actual.qualification()),"actual frontend snapshot lost its sole FOS provenance roster");
                ExactRef manifestRef=actual.supporting().get(1),driverRef=actual.supporting().get(2),snapshotRef=actual.supporting().get(3);
                RawJson manifest=new RawJson(reader.read(manifestRef,RawJson.MAXIMUM_BYTES)),driver=new RawJson(reader.read(driverRef,RawJson.MAXIMUM_BYTES));
                need(org.xar.ck3.control.application.driver.DriverObservationEvidenceReader.currentDriverReference(manifestRef,manifest).equals(driverRef),"actual frontend snapshot Driver reference differs");
                var original=org.xar.ck3.control.application.driver.DriverObservationEvidenceReader.nativeFrame(manifestRef,manifest,reader.read(snapshotRef,NativeWire.MAXIMUM_FRAME_BYTES+4));
                var facts=org.xar.ck3.control.application.driver.DriverObservationEvidenceReader.decode(manifestRef,manifest,driver,original);
                need(facts.source().equals(command.source())&&facts.transport().game().equals(command.origin().game())&&facts.transport().sessionId().equals(command.sessionId())&&facts.transport().connectionGeneration().equals(expected.connectionGeneration())&&facts.snapshotId().equals(snapshot.snapshotId())&&facts.nativeRevision().equals(snapshot.nativeRevision())&&facts.publicRevision().equals(snapshot.revision()),"independent frontend snapshot crossed actual Driver/public/native source identity");
                ObjectNode state=object(original.state());need(exactInteger(state,"date_raw").equals(BigInteger.valueOf(snapshot.dateRaw()))&&(!state.has("played_character")||state.get("played_character").isNull())&&(!state.has("episode_run_id")||state.get("episode_run_id").isNull()),"independent frontend snapshot invented gameplay identity or date");
            }
        }else{
            need(frame instanceof NativeWire.Snapshot,"independent gameplay source scope requires original complete Native snapshot");var value=(NativeWire.Snapshot)frame;
            need(value.snapshotId().equals(((SnapshotBinding)expected).snapshotId())&&value.revision().equals(expected.nativeRevision()),"independent complete Native snapshot crossed original source frame");
            JsonNode state=org.xar.ck3.control.contracts.FullJsonTree.parse(value.state().value(),NativeWire.MAXIMUM_FRAME_BYTES);need(state instanceof ObjectNode&&exactInteger((ObjectNode)state,"date_raw").equals(BigInteger.valueOf(expected.dateRaw())),"independent complete native date differs");
        }
        // The real source-authority proof and every supporting original remain in the same immutable archive.
        if(actual.qualification().isPresent()){
            NativeSourceProofDocument qualification=NativeSourceProofCodec.decode(reader.read(actual.qualification().orElseThrow(),NativeSourceProofDocument.MAXIMUM_BYTES));
            need(qualification.machineId().equals(command.source().machineId())&&qualification.sessionId().equals(command.sessionId())&&qualification.source().equals(command.source().sourceRef()),"independent source qualification crossed its original Root source/session/machine");
            Instant qualified=Instant.parse(qualification.observedAtUtc());need(!qualified.isBefore(attempt.submittedAt())&&!qualified.isAfter(actual.qualifiedAt()),"independent source qualification is not the actual post-submission scope");
        }
        for(ExactRef ref:actual.supporting())reader.read(ref,NativeWire.MAXIMUM_FRAME_BYTES+4);
    }
    public void verify(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch,NativeSourceObservation observed,ActionPorts.OutcomeArchive sameArchive)throws IOException{
        observed.validate(command,attempt,dispatch);need(sameArchive.referenceOf(dispatch).equals(observed.originalDispatch())&&sameArchive.load(observed.originalDispatch()).equals(dispatch),"source completion changed its canonical original dispatch");
        need(dispatch instanceof NativeActionPort.AckReceived,"source completion requires original complete native result");Binding binding=binding(command,attempt);Result actual=decode(command,attempt,(NativeActionPort.AckReceived)dispatch,binding,sameArchive);
        NativeCoaClipboard.Sample clip=NativeCoaClipboard.Sample.decode(sameArchive.loadMaterial(observed.independentClipboard()));requireClipboard(actual,clip);need(clip.observedAt().equals(observed.observedAt())&&actual.outcome()==observed.outcome(),"independent source result changed during replay");
        ObjectNode pair=object(sameArchive.loadMaterial(observed.afterScope()));exact(pair,Set.of("schema","before","after"));need(string(pair,"schema").equals("xar.coa-independent-source-pair/v1")&&pair.get("before") instanceof ObjectNode&&pair.get("after") instanceof ObjectNode,"independent source pair schema differs");
        Scope before=Scope.decode((ObjectNode)pair.get("before")),after=Scope.decode((ObjectNode)pair.get("after"));validateScope(before,binding,command,attempt,(NativeActionPort.AckReceived)dispatch);validateScope(after,binding,command,attempt,(NativeActionPort.AckReceived)dispatch);
        requirePair(before,clip,after);
        var complete=new LinkedHashSet<ExactRef>(sources);complete.add(command.source().sourceRef());complete.addAll(before.references());complete.addAll(after.references());need(List.copyOf(complete).equals(observed.sourceOriginals()),"source completion dropped or changed actual original provenance");
        need(sameArchive.loadMaterial(observed.compatibleResult()).equals(actual.publicResult()),"retained native source public result changed");
    }
    public void replay(ActionReceipt receipt,ActionPorts.OutcomeArchive sameArchive){
        need(receipt.state() instanceof ActionState.Settled&&((ActionState.Settled)receipt.state()).settlement() instanceof ActionState.NativeSourceCompleted,"source verifier requires its exact scoped native-source settlement");
        var settled=(ActionState.Settled)receipt.state();var observed=((ActionState.NativeSourceCompleted)settled.settlement()).observation();
        try{verify(receipt.command(),settled.attempt(),settled.dispatch(),observed,sameArchive);}catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    private static void requirePair(Scope before,NativeCoaClipboard.Sample clip,Scope after){
        need(!clip.observedAt().isBefore(before.qualifiedAt())&&clip.observedAt().isBefore(before.validUntil())&&!after.qualifiedAt().isBefore(clip.observedAt()),"independent clipboard read escaped its actual current source scopes");
        if(before.frontendSequence().isPresent())need(after.frontendSequence().orElseThrow().compareTo(before.frontendSequence().orElseThrow())>0,"independent frontend source pair did not advance its actual observation sequence");
    }
    private static void exact(ObjectNode row,Set<String> fields){need(row.properties().stream().map(java.util.Map.Entry::getKey).collect(java.util.stream.Collectors.toSet()).equals(fields),"independent source original fields differ");}
    private static BigInteger exactInteger(ObjectNode row,String field){JsonNode n=row.get(field);need(n!=null&&n.isIntegralNumber(),"exact native source integer required: "+field);return n.bigIntegerValue();}
}
