package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Clock;
import java.time.Instant;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.*;
import org.xar.ck3.control.nativebridge.capabilities.religion.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.*;

/** Finite shared implementation of the two LOCAL extension installers; no Native IO or second journal. */
public final class RootReligionConversionRuntime {
    private RootReligionConversionRuntime(){ }
    public static ReligionContract.Response invoke(Prepared prepared,RootPublicHandlerProductsFactory.Context context,ReligionContract.Request request)throws InterruptedException{return Objects.requireNonNull(prepared).invokePublic(context,request);}
    public static String canonicalActionId(ReligionConversionActions.Kind kind,String episode,BigInteger actor,String callerActionId){
        Objects.requireNonNull(kind);StrictJson.text(episode);Objects.requireNonNull(actor);new ReligionModels.OwnerId(callerActionId);
        ObjectNode identity=StrictJson.object().put("episode",episode).put("actor",actor).put("operation",kind.operation().value()).put("caller_action_id",callerActionId);
        return "religion-original-"+ActionCodec.sha256(ReligionCodec.raw(identity).bytes());
    }
    /** Pure canonical history selection; it cannot mint a permit, writer Session or reconciliation scope. */
    public static Optional<ActionReceipt> retainedOriginal(ReligionConversionActions.Kind kind,List<ActionReceipt> canonical,String episode,BigInteger actor,String actionId){
        ActionReceipt found=null;for(var receipt:List.copyOf(canonical)){var c=receipt.command();if(!c.operation().equals(kind.operation())||!c.before().frame().episodeRunId().equals(episode)||!c.before().frame().identity().player().equals(actor))continue;
            String original=arguments(c).get("action_id").textValue();if(original.equals(actionId)||!receipt.settled()){need(found==null,"multiple canonical Religion claims share one retained scope");found=receipt;}}
        return Optional.ofNullable(found);
    }
    public record Sources(ExactRef publicSource,ExactRef readDecoder,ExactRef actionDecoder,List<ReligionConversionRead.ReadSource> originalReads) {
        public Sources {Objects.requireNonNull(publicSource);Objects.requireNonNull(readDecoder);Objects.requireNonNull(actionDecoder);originalReads=List.copyOf(originalReads);}
    }
    public static Sources ordinarySources(ReligionConversionActions.Kind kind,Class<?> publicType,RootAdditionalDomains.ImplementationMetadata metadata){
        Objects.requireNonNull(kind);Objects.requireNonNull(publicType);Objects.requireNonNull(metadata);
        var readDecoder=metadata.implementation(ReligionConversionRead.class);var reads=new ArrayList<ReligionConversionRead.ReadSource>();
        if(kind==ReligionConversionActions.Kind.CONVERSION)for(var leaf:ReligionConversionRead.Kind.values())reads.add(new ReligionConversionRead.ReadSource(leaf,readDecoder));
        return new Sources(metadata.implementation(publicType),readDecoder,metadata.implementation(ReligionConversionActions.class),reads);
    }
    public static Sources sources(ReligionConversionActions.Kind kind,Class<?> publicType,RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected,RootRuntimeNativeOriginals.Bound originals,Clock clock)throws IOException {
        originals.requireCurrent(clock);selected.requireCurrent();
        var reads=new ArrayList<ReligionConversionRead.ReadSource>();
        if(kind==ReligionConversionActions.Kind.CONVERSION)for(var leaf:ReligionConversionRead.Kind.values())reads.add(new ReligionConversionRead.ReadSource(leaf,
                RootReligionSourcesFactory.original(inputs,selected,"ck3_autonomous_player/src/xar_autoplayer/bridge/player_religion_conversion_"+leaf.name().toLowerCase(java.util.Locale.ROOT)+"_private_transport.py")));
        return new Sources(selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,publicType),
                selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ReligionConversionRead.class),
                selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ReligionConversionActions.class),reads);
    }
    public static class Prepared implements RootReligionPublicProducts.ExtensionPrepared {
        private final ReligionConversionActions.Kind kind;private final Sources sources;
        private RootReligionPublicProducts.SharedKernel kernel;private RootApplicationAssembly.Core core;
        private List<ReadContract<ReligionConversionRead.View>> reads=List.of();
        private final IdentityHashMap<RootRuntimeContext,Attempt> attempts=new IdentityHashMap<>();
        public Prepared(ReligionConversionActions.Kind kind,Sources sources){this.kind=Objects.requireNonNull(kind);this.sources=Objects.requireNonNull(sources);}
        public String id(){return "original-religion-"+kind.name().toLowerCase(java.util.Locale.ROOT)+"-v1";}
        public List<String> originalMethods(){var result=new ArrayList<String>();if(kind==ReligionConversionActions.Kind.CONVERSION)for(var k:ReligionConversionRead.Kind.values())result.add(k.method());result.add(kind.method());return List.copyOf(result);}
        public List<DomainBodies.Registration> domainRegistrations(){return List.of();}
        public synchronized void bindShared(RootReligionPublicProducts.SharedKernel same){Objects.requireNonNull(same);need(kernel==null||kernel==same,"Religion leaf crossed its actual shared kernel");if(kernel!=null)return;kernel=same;
            if(kind==ReligionConversionActions.Kind.CONVERSION)reads=ReligionConversionRead.contracts(sources.originalReads(),same.readAdmission());}
        public synchronized void bindCore(RootApplicationAssembly.Core same){Objects.requireNonNull(same);need(core==null||core==same,"Religion leaf crossed its actual Core");core=same;}
        public synchronized List<NativePrivateActionPermission> privatePermissions(){need(kernel!=null,"shared actual qualification has not been bound");var q=kernel.actionQualification();return kernel.legacyRegistration().privateActions(q,q).stream().filter(p->p.operation().equals(kind.operation())).toList();}
        public synchronized RootReligionPublicProducts.ExtensionInstalled install(RootRuntimeContext same)throws IOException {
            if(core==null||kernel==null||same.core()!=core||same.writer()!=core.writer()||same.archive().writer()!=core.writer())throw new IOException("Religion leaf requires its actual bound Core/writer/kernel");
            Attempt previous=attempts.get(same);if(previous!=null){if(previous.failure!=null)throw new IOException("partial Religion installation retained; no retry",previous.failure);return previous.installed;}
            if(attempts.size()>=64)throw new IOException("finite Religion per-context installation bound exhausted");var attempt=new Attempt();attempts.put(same,attempt);
            try{attempt.runtime=new Runtime(kind,sources,kernel,reads,same);attempt.installed=kind==ReligionConversionActions.Kind.CONVERSION?new RootReligionPublicProducts.ExtensionInstalled(attempt.runtime.installation,attempt.runtime):new RootReligionPublicProducts.ExtensionInstalled(attempt.runtime.installation);return attempt.installed;}
            catch(RuntimeException failure){attempt.failure=new IOException("actual Religion leaf installation failed",failure);throw attempt.failure;}
        }
        private synchronized Runtime runtime(RootRuntimeContext actual)throws IOException {install(actual);return attempts.get(actual).runtime;}
        public RootPublicHandlerProductsFactory.Contribution products(RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException {
            Objects.requireNonNull(registry);need(!registry.frozen(),"Religion public registry already frozen");ExactRef rootSource=context.source(RootReligionConversionRuntime.class);
            var bindings=originalMethods().stream().<McpExecutableDirectory.DirectBinding<?,?>>map(name->new McpExecutableDirectory.DirectBinding<>(name,PublicMcpBindings.Kind.DRIVER_DIRECT,ReligionContract.Request.class,ReligionContract.Response.class,
                    request->RootReligionConversionRuntime.invoke(this,context,request),call->{need(call.name().equals(name),"Religion public method changed");return ReligionCodec.decode(name,call.arguments().objectOrEmpty());},
                    response->PublicMcpDirectory.CallResult.fromBusinessJson(ReligionCodec.encode(response)),new PublicRoutes.Target(RootReligionConversionRuntime.class.getName(),"invoke",rootSource))).toList();
            return new RootPublicHandlerProductsFactory.Contribution(bindings,List.of(),List.of());
        }
        public final ReligionContract.Response invokePublic(RootPublicHandlerProductsFactory.Context context,ReligionContract.Request request)throws InterruptedException {
            need(originalMethods().contains(request.method().name()),"foreign Religion public declaration");boolean action=request.method().name().equals(kind.method());Instant deadline=context.clock().instant().plus(action?context.actionTimeout():context.observationTimeout());
            try{return context.withCurrent(root->{var installed=context.installed(root);Runtime actual=runtime(installed.context());need(installed.context().actions()==root,"Religion public resolved another actual Root action owner");
                if(!action)return root.withPublicObservation(deadline,(frame,driver,same)->actual.invoke(same,actual.frame(frame,deadline),request));
                return root.executePublicDecision(deadline,(frame,driver,same)->actual.prepare(same,frame,request,deadline),(receipt,archive,same)->actual.publication(same,receipt,request));
            });}catch(IOException failure){throw new UncheckedIOException("actual Religion original route unavailable",failure);}
        }
    }
    private static final class Attempt {Runtime runtime;RootReligionPublicProducts.ExtensionInstalled installed;IOException failure;}
    private static final class Runtime implements ReligionService.Component {
        private final ReligionConversionActions.Kind kind;private final Sources sources;private final RootReligionPublicProducts.SharedKernel kernel;
        private final List<ReadContract<ReligionConversionRead.View>> reads;private final RootRuntimeContext context;private final ReligionConversionActions effects;
        private final RootDomainInstallation installation;
        Runtime(ReligionConversionActions.Kind kind,Sources sources,RootReligionPublicProducts.SharedKernel kernel,List<ReadContract<ReligionConversionRead.View>> reads,RootRuntimeContext context){
            this.kind=kind;this.sources=sources;this.kernel=kernel;this.reads=List.copyOf(reads);this.context=context;
            var snapshots=new NativeEffectSnapshots(()->context.adopted().observations(),context.archive(),context.frameLoader());
            effects=new ReligionConversionActions(kind,kernel.legacyRegistration(),resultContract(false),resultContract(true),snapshots,()->{
                try{return context.withSession(same->context.archive().withSession(same));}catch(IOException failure){throw new UncheckedIOException(failure);}
            },context.frameLoader(),this::readResult);
            var binding=new NativeEffectRegistry.Binding(kind.operation(),sources.actionDecoder(),effects::prepare,effects::observe);
            var action=new RootExecutableBindings.ActionBinding(binding,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.empty(),sources.actionDecoder());
            var pending=new RootDomainIntentPreparation.Binding("religion-original-once-"+kind.name().toLowerCase(java.util.Locale.ROOT),sources.publicSource(),c->c.operation().equals(kind.operation()),(same,command)->{
                try{context.writer().requireSession(same);need(retained(same,command.before().frame().episodeRunId(),command.before().frame().identity().player(),arguments(command).get("action_id").textValue()).isEmpty(),"Religion original once scope already exists before INTENT");}
                catch(IOException failure){throw new UncheckedIOException(failure);}
            });
            installation=new RootDomainInstallation("religion-original-"+kind.name().toLowerCase(java.util.Locale.ROOT),List.of(),reads.stream().map(c->new RootReadContractCatalog.InstalledRead(c,sources.readDecoder())).toList(),List.of(),List.of(action),List.of(),List.of(effects.archived(sources.actionDecoder())),List.of(),List.of(),List.of(),List.of(pending),Set.of(kind.operation()),List.of(),List.of(),List.of(),List.of(),List.of());
        }
        private ReadContract<?> resultContract(boolean reconciliation){var original=kernel.legacyRegistration();if(reconciliation)return kind==ReligionConversionActions.Kind.CONVERSION?original.conversionReconciliationContract():original.countyReconciliationContract();
            var wanted=kind==ReligionConversionActions.Kind.CONVERSION?ReligionCapabilities.ReadKind.RELIGION_RESULT:ReligionCapabilities.ReadKind.COUNTY_RESULT;
            return kernel.legacyReads().stream().filter(r->r.kind()==wanted).findFirst().orElseThrow().contract();}
        private ReligionService.ActualFrame frame(Complete actual,Instant deadline)throws IOException {context.requireCurrent(deadline);return new ReligionService.ActualFrame(actual,context.transport().diagnostics().originalHello().orElseThrow(()->new IOException("actual Religion original HELLO unavailable")).original(),deadline);}
        public List<String> methods(){return reads.stream().map(c->ReligionConversionRead.Kind.values()[reads.indexOf(c)].method()).toList();}
        public ReligionContract.Response invoke(Session same,ReligionService.ActualFrame actual,ReligionContract.Request request){
            need(actual.frame().identity().frame().revision().equals(request.expectedRevision()),"Religion public expected revision is stale");var leaf=java.util.Arrays.stream(ReligionConversionRead.Kind.values()).filter(k->k.method().equals(request.method().name())).findFirst().orElseThrow();
            var contract=reads.stream().filter(c->c.operation().value().equals(leaf.step())).findFirst().orElseThrow();ObjectNode args=StrictJson.object();if(leaf!=ReligionConversionRead.Kind.CHOICES)args.put("target_rite_id",request.integer(ReligionContract.Field.TARGET_RITE_ID));
            var read=ReligionService.readKnown(context.reads(),context.archive(),same,contract,actual,args);ObjectNode e=ReligionService.originalResult(read.receipt());var f=actual.frame().identity().frame();
            return new ReligionContract.Response(request.method(),ReligionCodec.raw(ReligionConversionRead.present(read.value(),ReligionService.boundBuild(read.receipt()),f.snapshotId(),f.revision(),f.identity().nativeRevision(),e)));
        }
        private PlanningReadReceipt readResult(ActionCommand command,ActionState.Attempt attempt,Complete after){
            try{return context.withSession(same->{context.writer().requireSession(same);boolean recon=ActionReconciliationScope.activeFor(command);ReadContract<?> contract=resultContract(recon);
                ObjectNode args=bound(after);args.put("submitted_request_id",attempt.requestId()).put("action_id",arguments(command).get("action_id").textValue());
                var nativeArgs=OpportunityJson.object(OpportunityJson.parse(ReligionCodec.raw(args).bytes()),"original Religion result request");
                PlanningReadRequest request=recon?PlanningReadRequest.newReconciliation(ActionReconciliationScope.requireIdentity(command,attempt),kind.resultOperation(),nativeArgs,ActionObservationWindow.deadline(command))
                        :new PlanningReadRequest(after.identity(),after.source(),after.sessionId(),kind.resultOperation(),nativeArgs,ActionObservationWindow.deadline(command));
                return ReligionService.readKnownRequest(context.reads(),context.archive(),same,contract,request).receipt();
            });}catch(IOException failure){throw new UncheckedIOException(failure);}
        }
        private Optional<ActionReceipt> retained(Session same,String episode,BigInteger actor,String actionId)throws IOException {
            return retainedOriginal(kind,ContinuityActionJournal.receipts(same.head().state(),context.archive().withSession(same)),episode,actor,actionId);
        }
        private RootApplicationSession.PublicActionDecision<ReligionContract.Response> prepare(Session same,Complete actual,ReligionContract.Request request,Instant deadline)throws IOException {
            context.writer().requireSession(same);context.collector().requireHeldFrame(same,actual);need(actual.identity().frame().revision().equals(request.expectedRevision()),"stale public Religion revision");
            var f=actual.identity().frame();String caller=request.text(ReligionContract.Field.ACTION_ID);ObjectNode fields=ReligionCodec.nativeArguments(request);fields.remove("expected_revision");ObjectNode rawIntent=fields.deepCopy();fields.setAll(bound(actual));
            Optional<ActionReceipt> previous=retained(same,f.episodeRunId(),f.identity().player(),caller);
            if(previous.isPresent()) {var receipt=previous.orElseThrow();ObjectNode old=arguments(receipt.command());old.remove(List.of("expected_snapshot_revision","expected_public_revision","expected_date_raw","expected_player_character_id"));need(old.equals(rawIntent),"caller Religion once identity cannot be reused with changed parameters or a different unresolved scope");
                if(!receipt.settled()&&ActionTransitions.attempt(receipt.state()).isPresent())return new RootApplicationSession.ReconcilePublicAction<>(receipt.command().actionId(),context.archive().withSession(same).receiptReferenceOf(receipt));
                return new RootApplicationSession.RetainPublicResult<>(publication(same,receipt,request));}
            var actualFrame=frame(actual,deadline);String version=java.util.Arrays.stream(PlayerReligionContext.Build.values()).filter(b->b.sha256().equalsIgnoreCase(actualFrame.hello().gameSha256())).findFirst().orElseThrow(()->new IllegalArgumentException("unknown actual Religion HELLO executable")).version();
            need(kind==ReligionConversionActions.Kind.CONVERSION?version.equals("1.20.0.3"):Set.of("1.20.0.3","1.20.0.4").contains(version),"original mutation build is not qualified");
            String id=canonicalActionId(kind,f.episodeRunId(),f.identity().player(),caller);var expected=new ExpectedPostcondition(1,actual.identity(),actual.source(),kind.observer(),ReligionConversionActions.expected(kind,fields));
            var actors=new java.util.HashSet<BigInteger>();actors.add(f.identity().player());if(kind==ReligionConversionActions.Kind.COUNTY)actors.add(request.integer(ReligionContract.Field.EXPECTED_INCUMBENT_CHARACTER_ID));
            var command=new ActionCommand(id,actual.identity(),actual.source(),actual.sessionId(),kind.operation(),OpportunityJson.object(OpportunityJson.parse(ReligionCodec.raw(fields).bytes()),"Religion original mutation arguments"),expected,new Claims(Set.of(),Set.of(),actors,Set.of()),deadline);
            effects.prepare(command);return new RootApplicationSession.SubmitPublicAction<>(command);
        }
        private ReligionContract.Response publication(Session same,ActionReceipt receipt,ReligionContract.Request request)throws IOException {
            context.writer().requireSession(same);var archive=context.archive().withSession(same);ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),receipt,archive);
            var attempt=ActionTransitions.attempt(receipt.state()).orElseThrow(()->new IOException("canonical Religion intent retained before submission"));var ack=receipt.ack().orElseThrow(()->new IOException("original Religion outcome UNKNOWN; do not submit again"));
            return new ReligionContract.Response(request.method(),ReligionCodec.raw(ReligionConversionActions.presentSubmission(ReligionConversionActions.decodeSubmission(kind,receipt.command(),attempt,ack))));
        }
    }
    private static ObjectNode arguments(ActionCommand command){return ReligionCodec.object(new RawJson(OpportunityJson.encode(command.arguments())));}
    private static ObjectNode bound(Complete frame){var f=frame.identity().frame();return StrictJson.object().put("expected_snapshot_revision",f.identity().nativeRevision()).put("expected_public_revision",f.revision()).put("expected_date_raw",f.identity().dateRaw()).put("expected_player_character_id",f.identity().player());}
    private static void need(boolean condition,String reason){StrictJson.require(condition,reason);}
}
