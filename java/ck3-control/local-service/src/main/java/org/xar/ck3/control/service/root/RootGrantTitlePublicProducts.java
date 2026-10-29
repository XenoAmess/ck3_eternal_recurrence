package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collection;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.effects.*;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.nativebridge.capabilities.interactions.InteractionModels.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.service.mcp.McpExecutableDirectory;
import org.xar.ck3.control.service.mcp.PublicMcpBindings;
import org.xar.ck3.control.service.mcp.PublicMcpNativeAdapter;
import org.xar.ck3.control.service.mcp.PublicMcpDirectory.CallResult;
import org.xar.ck3.control.platform.OriginalRuntimeHandoffProof;

/** Original Grant Service algorithms, installed once beside the identical Known interaction authority. */
public final class RootGrantTitlePublicProducts {
    private RootGrantTitlePublicProducts() { }
    public static final String TARGET="local-service/src/main/java/org/xar/ck3/control/service/root/RootGrantTitlePublicProducts.java";
    /** The old provider is retained for the explicit legacy DATA branch; current Java work binds the actual managed Root. */
    public record Sources(ExactRef publicSource,ExactRef effectsSource,ExactRef decoderSource,OriginalRuntimeHandoffProof.Provider originalGrantStore) {
        public Sources { Objects.requireNonNull(publicSource); Objects.requireNonNull(effectsSource); Objects.requireNonNull(decoderSource); Objects.requireNonNull(originalGrantStore); }
    }
    public static final class Prepared implements RootDriverRegistryPublicProducts.PreparedProduct {
        private final Sources sources;
        private RootApplicationAssembly.Core core;
        private final IdentityHashMap<RootRuntimeContext,Attempt> attempts=new IdentityHashMap<>();
        public Prepared(Sources sources){this.sources=Objects.requireNonNull(sources);}
        @Override public RootDriverRegistryPublicProducts.Kind kind(){return RootDriverRegistryPublicProducts.Kind.GRANT;}
        @Override public RootDriverRegistryPublicProducts.ProductSource source(){return new RootDriverRegistryPublicProducts.ProductSource(RootGrantTitlePublicProducts.class,TARGET,sources.publicSource());}
        @Override public List<DomainBodies.Registration> domainRegistrations(){return List.of();}
        // The identical Known installation already contributes the source-qualified grant-query permission.
        @Override public Collection<NativePrivateActionPermission> privatePermissions(){return List.of();}
        @Override public synchronized void bindCore(RootApplicationAssembly.Core actual)throws IOException {
            if(core!=null&&core!=actual)throw new IOException("Grant Prepared belongs to another Core");core=Objects.requireNonNull(actual);
        }
        @Override public synchronized Runtime install(RootRuntimeContext actual)throws IOException {
            if(core==null||actual.core()!=core)throw new IOException("Grant requires its actual bound Core");
            var old=attempts.get(actual);if(old!=null){if(old.value!=null)return old.value;throw new IOException("partial Grant installation cannot replay",old.failure);}
            if(attempts.size()>=64)throw new IOException("Grant per-Game installation bound exhausted");
            var attempt=new Attempt();attempts.put(actual,attempt);
            try{attempt.value=new Runtime(actual,actual.interactions(),sources);return attempt.value;}
            catch(IOException failure){attempt.failure=failure;throw failure;}
            catch(RuntimeException failure){attempt.failure=new IOException("Grant installation failed",failure);throw attempt.failure;}
        }
        @Override public RootPublicHandlerProductsFactory.Contribution products(RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException {
            // Source audit gates removed
            context.source(GrantTitlePublicCodec.class);context.source(RootGrantLegacyClaims.class);context.source(RootManagedSessionScope.class);
            return publicBindings(context,sources.publicSource());
        }
    }
    private static final class Attempt { Runtime value;IOException failure; }
    public static final class Runtime implements RootDriverRegistryPublicProducts.Product {
        private final RootRuntimeContext context;
        private final KnownInteractionsRuntimeInstaller known;
        private final ReadContract<GrantResult> query;
        private final RootDomainInstallation installation;
        private final RootGrantLegacyClaims once;
        Runtime(RootRuntimeContext context,KnownInteractionsRuntimeInstaller same,Sources sources)throws IOException {
            this.context=Objects.requireNonNull(context);known=Objects.requireNonNull(same);known.requireContext(context);
            once=RootGrantLegacyClaims.forJavaSession(context,sources.originalGrantStore(),known,
                    List.of(sources.publicSource(),sources.effectsSource(),sources.decoderSource()));
            query=known.definitions().grantQuery();
            var effects=new GrantPickerControlEffects(query,this::after,()->{
                try{return context.withSession(s->context.archive().withSession(s));}catch(IOException failure){throw new UncheckedIOException(failure);}
            },once::verifyOriginals);
            var actions=new ArrayList<RootExecutableBindings.ActionBinding>();var archived=new ArrayList<NativeRecordedEvidenceVerifier.Binding>();
            for(GrantOperation operation:List.of(GrantOperation.PREPARE,GrantOperation.SELECT,GrantOperation.SEND)) {
                ActionPorts.PreparationPort producer=command->{
                    try{return context.withSession(writer->{var base=effects.prepare(command);var census=once.requireClear(writer,GrantPickerControlEffects.context(command),GrantPickerControlEffects.request(command),command);
                        return new NativeRequest(base.step(),base.requiredCapability(),base.additionalFields(),List.of(census));});}catch(IOException failure){throw new UncheckedIOException(failure);}
                };
                var binding=new NativeEffectRegistry.Binding(new OperationKey(GrantTitleCodec.step(operation)),sources.effectsSource(),producer,
                        (command,attempt,dispatch)->{
                            try{return effects.observe(command,attempt,dispatch);}catch(UncheckedIOException|IllegalArgumentException|IllegalStateException unavailable){
                                return NativeEffectRegistry.Projected.pending("Grant original independent post-state unavailable: "+unavailable.getMessage(),List.of(attempt.guard().nativeEvidence()));}
                        });
                actions.add(new RootExecutableBindings.ActionBinding(binding,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.of(GrantTitleCodec.capability(operation)),sources.decoderSource()));
                archived.add(effects.archived(operation,sources.effectsSource()));
            }
            var operations=actions.stream().map(a->a.effect().operation()).collect(java.util.stream.Collectors.toUnmodifiableSet());
            var intent=new RootDomainIntentPreparation.Binding("java-managed-grant-same-writer-once/v2",sources.publicSource(),c->operations.contains(c.operation()),(writer,command)->{
                try{context.writer().requireSession(writer);var before=GrantPickerControlEffects.context(command);var requested=GrantPickerControlEffects.request(command);
                    need(retained(ContinuityActionJournal.receipts(writer.head().state(),context.archive().withSession(writer)),before,requested).isEmpty(),"original Grant scope was claimed before INTENT");
                    once.requireClear(writer,before,requested,command);
                }catch(IOException failure){throw new UncheckedIOException(failure);}
            });
            installation=new RootDomainInstallation("original-grant-title-picker",List.of(),List.of(),List.of(),actions,List.of(),archived,List.of(),List.of(),List.of(),List.of(intent),operations,List.of(),List.of(),List.of(),List.of(),List.of());
        }
        @Override public void requireContext(RootRuntimeContext actual)throws IOException {if(context!=actual)throw new IOException("Grant product crossed actual Game context");known.requireContext(actual);}
        @Override public RootDomainInstallation installation(){return installation;}
        private Context current(Session same,Complete frame,BigInteger expected,Instant deadline)throws IOException {
            context.writer().requireSession(same);context.collector().requireHeldFrame(same,frame);known.requireContext(context);
            need(frame.identity().frame().revision().equals(expected),"stale public Grant revision");
            need(context.readCatalog().containsIdentity(query),"Grant query is not the identical installed Known contract");
            return known.projection().project(frame,deadline);
        }
        private PlanningReadResult.Known<GrantResult> read(Session same,Context current,GrantRequest request)throws IOException {
            var reply=known.capabilities().grantTitlePickerV1(current,request,Optional.empty());
            need(reply instanceof GrantRead,"readonly grant path changed");var result=((GrantRead)reply).result();
            if(!(result instanceof PlanningReadResult.Known<GrantResult> value))throw new IOException("actual source-qualified Grant query unavailable: "+result);
            NativeRecordedEvidenceVerifier.requireRead(value.receipt(),context.archive().withSession(same));
            need(query.replay(value.receipt()).equals(value.value()),"Grant query differs from sole native decoder");return value;
        }
        public GrantTitlePublicCodec.Reply query(Session same,Complete frame,GrantTitlePublicCodec.Query request,Instant deadline)throws IOException {
            Context before=current(same,frame,request.expectedRevision(),deadline);var value=read(same,before,request.nativeRequest());
            return GrantTitlePublicCodec.observed(value.receipt().original().originalResultToken().orElseThrow(),before,request.nativeRequest());
        }
        public RootApplicationSession.PublicActionDecision<GrantTitlePublicCodec.Reply> prepare(Session same,Complete frame,GrantTitlePublicCodec.Request request,Instant deadline)throws IOException {
            need(!(request instanceof GrantTitlePublicCodec.Query),"query cannot enter Grant command path");
            once.requireSourceFrame(frame);
            Context before=current(same,frame,request.expectedRevision(),deadline);GrantRequest original=request.nativeRequest();GrantTitleCodec.request(before,original);
            var archive=context.archive().withSession(same);var retained=retained(ContinuityActionJournal.receipts(same.head().state(),archive),before,original);
            if(retained.isPresent())return new RootApplicationSession.RetainPublicResult<>(publication(same,retained.orElseThrow()));
            need(context.bindings().actualActionBinding(new OperationKey(GrantTitleCodec.step(original.operation()))).isPresent(),"actual Grant preparer not installed");
            String id=ActionIds.forDecision(before.sessionId(),before.before(),"public-grant:"+original.operation().wire()+":"+original.recipient().value()+":"+ActionCodec.sha256(GrantTitlePublicCodec.encodeRequest(request).bytes()));
            var expected=new ExpectedPostcondition(1,before.before(),before.source(),GrantPickerControlEffects.OBSERVER,GrantPickerControlEffects.expectedValues());
            var actors=new java.util.HashSet<BigInteger>();actors.add(before.actor());actors.add(BigInteger.valueOf(original.recipient().value()));
            var claims=new Claims(Set.of(),Set.of(),actors,Set.of("foreground-window"));
            var command=known.capabilities().prepareGrantTitlePickerV1(new ActionContext(before,id,expected,claims),original);
            once.captureCommand(same,frame,command);
            return new RootApplicationSession.SubmitPublicAction<>(command);
        }
        public GrantTitlePublicCodec.Reply publication(Session same,ActionReceipt actual)throws IOException {
            context.writer().requireSession(same);var archive=context.archive().withSession(same);
            need(actual.command().before().machineId().equals(context.game().machineId()),"Grant original publication crossed its canonical machine");
            ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),actual,archive);
            return GrantTitlePublicCodec.action(actual,archive,GrantPickerControlEffects.context(actual.command()),GrantPickerControlEffects.request(actual.command()));
        }
        private GrantPickerControlEffects.After after(Context before,GrantRequest original) {
            try{return context.withSession(same->{var identity=new SessionPorts.SessionIdentity(context.game().machineId(),context.game().generation(),context.game().sessionId());
                return context.collector().currentOwned(same,identity,before.deadline(),lease->{
                    Context current=current(same,lease.frame(),lease.frame().identity().frame().revision(),before.deadline());
                    return new GrantPickerControlEffects.After(current,read(same,current,GrantPickerControlEffects.queryRequest(original)));
                });
            });}catch(IOException failure){throw new UncheckedIOException(failure);}
        }
    }
    /** Original unresolved scope ignores title/selection/revision changes, so changing parameters cannot resend UNKNOWN. */
    public static Optional<ActionReceipt> retained(List<ActionReceipt> canonical,Context current,GrantRequest requested) {
        Optional<ActionReceipt> found=Optional.empty();
        for(var receipt:List.copyOf(canonical)) {
            var command=receipt.command();if(receipt.settled()||!command.operation().value().equals(GrantTitleCodec.step(requested.operation())))continue;
            // A Java restore/replacement does not erase unresolved Grant scope from this same canonical episode.
            if(!command.before().machineId().equals(current.before().machineId()))continue;
            Context original=GrantPickerControlEffects.context(command);GrantRequest request=GrantPickerControlEffects.request(command);
            if(original.controls().episodeRunId().equals(current.controls().episodeRunId())&&original.actor().equals(current.actor())&&request.recipient().equals(requested.recipient())) {
                need(found.isEmpty(),"multiple unresolved canonical Grant claims share one original scope");found=Optional.of(receipt);
            }
        }
        return found;
    }
    private static Runtime runtime(RootPublicHandlerProductsFactory.Context context,RootApplicationSession root)throws IOException {
        var catalog=context.installed(root);var actual=catalog.additionalDomains().driverRegistry().product(RootDriverRegistryPublicProducts.Kind.GRANT,Runtime.class);
        actual.requireContext(catalog.context());need(catalog.context().actions()==root,"Grant public adapter resolved another Root writer");return actual;
    }
    private static GrantTitlePublicCodec.Reply call(RootPublicHandlerProductsFactory.Context context,GrantTitlePublicCodec.Request request)throws InterruptedException {
        Instant deadline=context.clock().instant().plus(request instanceof GrantTitlePublicCodec.Query?context.observationTimeout():context.actionTimeout());
        try{return context.withCurrent(root->{var installed=runtime(context,root);
            if(request instanceof GrantTitlePublicCodec.Query query)return root.withPublicObservation(deadline,(frame,driver,same)->installed.query(same,frame,query,deadline));
            return installed.once.withScope(()->root.executePublicDecision(deadline,(frame,driver,same)->installed.prepare(same,frame,request,deadline),(receipt,archive,same)->installed.publication(same,receipt)));
        });}catch(IOException failure){throw new UncheckedIOException("actual original Grant public service unavailable",failure);}
    }
    private static RootPublicHandlerProductsFactory.Contribution publicBindings(RootPublicHandlerProductsFactory.Context context,ExactRef source) {
        var direct=List.<McpExecutableDirectory.DirectBinding<?,?>>of(
                binding("ck3_query_grant_title_picker_v1",GrantTitlePublicCodec.Query.class,GrantTitlePublicCodec::query,context,source),
                binding("ck3_prepare_grant_title_picker_v1",GrantTitlePublicCodec.Prepare.class,GrantTitlePublicCodec::prepare,context,source),
                binding("ck3_select_grant_title_picker_v1",GrantTitlePublicCodec.Select.class,GrantTitlePublicCodec::select,context,source),
                binding("ck3_send_grant_title_picker_v1",GrantTitlePublicCodec.Send.class,GrantTitlePublicCodec::send,context,source));
        return new RootPublicHandlerProductsFactory.Contribution(direct,List.of(),List.of());
    }
    @FunctionalInterface private interface Decoder<T>{T decode(PublicBindings.Arguments arguments);}
    private static <T extends GrantTitlePublicCodec.Request> McpExecutableDirectory.DirectBinding<T,GrantTitlePublicCodec.Reply> binding(String name,Class<T> type,Decoder<T> decoder,RootPublicHandlerProductsFactory.Context context,ExactRef source) {
        return new McpExecutableDirectory.DirectBinding<>(name,PublicMcpBindings.Kind.DRIVER_DIRECT,type,GrantTitlePublicCodec.Reply.class,request->call(context,request),
                call->decoder.decode(PublicMcpNativeAdapter.arguments(call.arguments())),reply->CallResult.fromBusinessJson(GrantTitlePublicCodec.encode(reply)),
                new PublicRoutes.Target(RootGrantTitlePublicProducts.class.getName(),name,source));
    }
    public static RootPublicHandlerProductsFactory.Contribution install(RootPublicHandlerProductsFactory.Context context,PublicBindings registry)throws IOException {
        return context.definitions().additionalDomains().driverRegistry().prepared(RootDriverRegistryPublicProducts.Kind.GRANT,Prepared.class).products(context,registry);
    }
    private static void need(boolean value,String reason){StrictJson.require(value,reason);}
}
