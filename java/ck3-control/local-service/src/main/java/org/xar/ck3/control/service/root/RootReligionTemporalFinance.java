package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionTemporalFinance.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Clock;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.NativePrivateActionPermission;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.*;
import org.xar.ck3.control.nativebridge.capabilities.publicmethods.religion.extensions.ReligionTemporalFinance;
import org.xar.ck3.control.nativebridge.capabilities.religion.EpidemicOriginalDecoder;
import org.xar.ck3.control.nativebridge.capabilities.religion.ReligionModels;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.service.mcp.*;

/** Eight original read routes: five temporal contexts, two Rite inventories and the existing CE1 decoder. */
public final class RootReligionTemporalFinance {
    public static final String EPIDEMIC="ck3_query_player_epidemic_recovery_private_v1";
    private RootReligionTemporalFinance(){ }
    public record Definition(Kind kind,ReligionTemporalFinance.Sources sources){public Definition{Objects.requireNonNull(kind);Objects.requireNonNull(sources);}}
    public record Sources(ExactRef implementation,ExactRef decoder,List<Definition> definitions,ExactRef epidemicDefinition,ExactRef epidemicBridge){
        public Sources{Objects.requireNonNull(implementation);Objects.requireNonNull(decoder);Objects.requireNonNull(epidemicDefinition);Objects.requireNonNull(epidemicBridge);definitions=List.copyOf(definitions);need(definitions.size()==Kind.values().length&&definitions.stream().map(Definition::kind).distinct().count()==definitions.size(),"complete exact temporal/Rite definitions required");}
        public Sources(RootRuntimeDefinitions.Inputs inputs,RootRuntimeNativeOriginals.Bound originals,Clock clock,
                ExactRef implementation,ExactRef decoder,List<Definition> definitions,ExactRef epidemicDefinition,ExactRef epidemicBridge){
            this(implementation,decoder,definitions,epidemicDefinition,epidemicBridge);
        }
        public ReligionTemporalFinance.Sources source(Kind kind){return definitions.stream().filter(d->d.kind()==kind).findFirst().orElseThrow().sources();}
    }
    public static Prepared ordinary(RootAdditionalDomains.ImplementationMetadata metadata){
        Objects.requireNonNull(metadata);var implementation=metadata.implementation(RootReligionTemporalFinance.class);
        var decoder=metadata.implementation(ReligionTemporalFinance.class);var epidemic=metadata.implementation(EpidemicOriginalDecoder.class);
        var closure=java.util.stream.Stream.of(implementation,decoder,epidemic).distinct().toList();
        var definitions=Arrays.stream(Kind.values()).map(kind->new Definition(kind,new ReligionTemporalFinance.Sources(decoder,decoder,closure))).toList();
        return new Prepared(new Sources(implementation,decoder,definitions,epidemic,epidemic));
    }
    public static Prepared prepare(RootRuntimeDefinitions.Inputs inputs,RootRuntimeSelectedSources selected,RootRuntimeNativeOriginals.Bound originals,Clock clock)throws IOException{
        var implementation=selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootReligionTemporalFinance.class);
        var decoder=selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,ReligionTemporalFinance.class);
        String prefix="ck3_autonomous_player/src/xar_autoplayer/bridge/";var definitions=new ArrayList<Definition>();
        var shared=List.of(RootReligionSourcesFactory.original(inputs,selected,prefix+"native_driver.py"),RootReligionSourcesFactory.original(inputs,selected,prefix+"g2_private_query_transport.py"),RootReligionSourcesFactory.original(inputs,selected,prefix+"nonwar_private_build.py"),RootReligionSourcesFactory.original(inputs,selected,prefix+"version_identity.py"));
        for(Kind kind:Kind.values()){String leaf=switch(kind){case CLERGY->"player_clergy_appointment_private_transport.py";case GOLD->"player_head_of_faith_gold_context_private_transport.py";case LOAN->"player_holy_order_loan_context_private_transport.py";case TITLES->"player_holy_order_selected_title_terms_private_transport.py";case REPENTANCE->"player_repentance_context_private_transport.py";case RITE_GOVERNANCE->"player_rite_governance_private_transport.py";case RITE_MEMBERS->"player_rite_members_private_transport.py";};var definition=RootReligionSourcesFactory.original(inputs,selected,prefix+leaf);var closure=new ArrayList<>(shared);closure.add(definition);if(kind==Kind.CLERGY)for(String sibling:List.of("player_county_conversion_private_observation.py","player_clergy_candidate_terms_private_observation.py","player_clergy_mode0_source_12004.py"))closure.add(RootReligionSourcesFactory.original(inputs,selected,prefix+sibling));definitions.add(new Definition(kind,new ReligionTemporalFinance.Sources(definition,decoder,closure)));}
        var sources=new Sources(inputs,originals,clock,implementation,decoder,definitions,RootReligionSourcesFactory.original(inputs,selected,prefix+"epidemic_recovery_private_transport.py"),selected.javaSource(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT,EpidemicOriginalDecoder.class));return new Prepared(sources);
    }
    public record CandidateSelection(BigInteger candidate,BigInteger publicRevision){public CandidateSelection{range(candidate,BigInteger.ONE,I32_MAX);range(publicRevision,BigInteger.ONE,U64);}}
    public record EpidemicSelection(int title,BigInteger event){public EpidemicSelection{need(title>=0&& (title==0?event!=null&&event.signum()>0&&event.compareTo(I32_MAX)<=0:event==null),"epidemic list requires an actual signed32 event, explicit title must omit it");}}
    private static final class Attempt{Runtime runtime;IOException failure;}
    public static final class Prepared implements RootReligionPublicProducts.ExtensionPrepared{
        private final Sources sources;private RootReligionPublicProducts.SharedKernel kernel;private RootApplicationAssembly.Core core;
        private final IdentityHashMap<RootRuntimeContext,Attempt> attempts=new IdentityHashMap<>();
        public Prepared(Sources sources){this.sources=Objects.requireNonNull(sources);}
        public String id(){return "religion-temporal-finance-and-rite/v1";}public List<String> originalMethods(){return methodsList();}
        public List<DomainBodies.Registration> domainRegistrations(){return List.of();}public List<NativePrivateActionPermission> privatePermissions(){return List.of();}
        public synchronized void bindShared(RootReligionPublicProducts.SharedKernel same){need(kernel==null||kernel==same,"temporal component changed shared kernel");kernel=Objects.requireNonNull(same);}
        public synchronized void bindCore(RootApplicationAssembly.Core same){need(core==null||core==same,"temporal component changed actual Core");core=Objects.requireNonNull(same);}
        public synchronized RootReligionPublicProducts.ExtensionInstalled install(RootRuntimeContext context)throws IOException{
            if(core==null||kernel==null||context.core()!=core||context.writer()!=core.writer()||context.archive().writer()!=core.writer())throw new IOException("temporal component requires same bound Core/shared kernel/writer");var prior=attempts.get(context);if(prior!=null){if(prior.failure!=null)throw new IOException("previous temporal partial install is retained, never retry",prior.failure);return new RootReligionPublicProducts.ExtensionInstalled(prior.runtime.installation,prior.runtime);}
            if(attempts.size()>=64)throw new IOException("temporal per-Game install bound exceeded");var attempt=new Attempt();attempts.put(context,attempt);try{attempt.runtime=new Runtime(context,sources,kernel);return new RootReligionPublicProducts.ExtensionInstalled(attempt.runtime.installation,attempt.runtime);}catch(RuntimeException failure){attempt.failure=new IOException("temporal actual install failed",failure);throw attempt.failure;}
        }
        private synchronized Runtime installed(RootRuntimeContext same)throws IOException{var attempt=attempts.get(same);if(attempt==null||attempt.runtime==null||attempt.failure!=null)throw new IOException("temporal component was not actually installed in this physical Root");return attempt.runtime;}
        public RootPublicHandlerProductsFactory.Contribution products(RootPublicHandlerProductsFactory.Context publicContext,PublicBindings registry)throws IOException{
            need(!registry.frozen(),"temporal public factory crossed frozen registry");
            return new RootPublicHandlerProductsFactory.Contribution(bindings(sources.implementation(),request->{var deadline=publicContext.clock().instant().plus(timeout(request,publicContext.observationTimeout()));try{return publicContext.withCurrent(root->{var context=publicContext.installed(root).context();var runtime=installed(context);return root.withPublicObservation(deadline,(frame,known,same)->runtime.invoke(same,new ReligionService.ActualFrame(frame,context.transport().originalHello(),deadline),request));});}catch(IOException failure){throw new UncheckedIOException(failure);}}),List.of(),List.of());
        }
    }
    public static List<String> methodsList(){var methods=new ArrayList<String>();for(Kind kind:Kind.values())methods.add(kind.method());methods.add(EPIDEMIC);return List.copyOf(methods);}
    static List<McpExecutableDirectory.DirectBinding<?,?>> bindings(ExactRef source,PublicRoutes.Handler<ReligionContract.Request,ReligionContract.Response> actual){return methodsList().stream().<McpExecutableDirectory.DirectBinding<?,?>>map(name->new McpExecutableDirectory.DirectBinding<>(name,PublicMcpBindings.Kind.DRIVER_DIRECT,ReligionContract.Request.class,ReligionContract.Response.class,actual,call->{need(call.name().equals(name),"temporal public identity drift");return ReligionCodec.decode(name,call.arguments().objectOrEmpty());},result->PublicMcpDirectory.CallResult.fromBusinessJson(ReligionCodec.encode(result)),new PublicRoutes.Target(Runtime.class.getName(),"invoke",source))).toList();}
    public static final class Runtime implements ReligionService.Component{
        private final RootRuntimeContext context;private final Sources sources;private final RootReligionPublicProducts.SharedKernel kernel;
        private final EnumMap<Kind,ReadContract<Observed>> fixed=new EnumMap<>(Kind.class);
        private final RootReadContractCatalog.Family<CandidateSelection,Observed> clergy;
        private final RootReadContractCatalog.Family<EpidemicSelection,ReligionModels.EpidemicResult> epidemic;
        private final RootDomainInstallation installation;
        private Runtime(RootRuntimeContext context,Sources sources,RootReligionPublicProducts.SharedKernel kernel){
            this.context=context;this.sources=sources;this.kernel=kernel;
            for(Kind kind:Kind.values())if(kind!=Kind.CLERGY)fixed.put(kind,ReligionTemporalFinance.contract(new Selection(kind,BigInteger.ZERO),sources.source(kind),kernel.readAdmission()::verify));
            var clergySource=sources.source(Kind.CLERGY);
            clergy=new RootReadContractCatalog.Family<>("religion-original-clergy-candidate/v1",CandidateSelection.class,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.empty(),clergySource.definition(),sources.decoder(),selection->raw(selectionArguments(new Selection(Kind.CLERGY,selection.candidate()))),selection->new OperationKey(Kind.CLERGY.step()),selection->ReligionTemporalFinance.contract(new Selection(Kind.CLERGY,selection.candidate()),clergySource,kernel.readAdmission()::verify));
            epidemic=new RootReadContractCatalog.Family<>("religion-original-epidemic-selected/v1",EpidemicSelection.class,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,Optional.empty(),sources.epidemicDefinition(),sources.epidemicBridge(),selection->{var n=org.xar.ck3.control.contracts.StrictJson.object();if(selection.title()==0)n.put("expected_event_instance_id",selection.event());return raw(n);},selection->new OperationKey(epidemicStep(selection)),selection->epidemicContract(selection,sources.epidemicDefinition(),sources.epidemicBridge(),kernel.readAdmission()::verify)
            );
            var reads=fixed.values().stream().map(contract->new RootReadContractCatalog.InstalledRead(contract,sources.decoder())).toList();installation=new RootDomainInstallation("religion-original-temporal-and-rite/v1",List.of(),reads,List.of(clergy,epidemic),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
        }
        public RootDomainInstallation installation(){return installation;}public List<String> methods(){return methodsList();}
        public ReligionContract.Response invoke(Session same,ReligionService.ActualFrame actual,ReligionContract.Request request){
            try{
                context.writer().requireSession(same);need(actual.frame().source().equals(context.source())&&actual.frame().sessionId().equals(context.game().sessionId())&&actual.frame().identity().game().equals(context.game().generation())&&actual.frame().identity().frame().revision().equals(request.expectedRevision()),"temporal invocation crossed actual source/session/revision");
                if(request.method().name().equals(EPIDEMIC)){
                    int title=ReligionCodec.optionalInteger(request,ReligionContract.Field.REQUESTED_TITLE_ID,BigInteger.ZERO).intValueExact();var event=request.value(ReligionContract.Field.EXPECTED_EVENT_INSTANCE_ID);var selected=new EpidemicSelection(title,event instanceof ReligionContract.IntegerValue value?value.value():null);var contract=context.readCatalog().issue(epidemic,selected);var fields=org.xar.ck3.control.contracts.StrictJson.object();if(title==0)fields.put("expected_event_instance_id",selected.event());var result=ReligionService.readKnown(context.reads(),context.archive(),same,contract,actual,fields);return new ReligionContract.Response(request.method(),raw(EpidemicOriginalDecoder.publicResult(result.receipt(),selected.title(),selected.event())));
                }
                Kind kind=Kind.method(request.method().name());var selected=new Selection(kind,kind==Kind.CLERGY?request.integer(ReligionContract.Field.CANDIDATE_CHARACTER_ID):BigInteger.ZERO);ReadContract<Observed> contract=kind==Kind.CLERGY?context.readCatalog().issue(clergy,new CandidateSelection(selected.candidate(),request.expectedRevision())):fixed.get(kind);
                var result=ReligionService.readKnown(context.reads(),context.archive(),same,contract,actual,selectionArguments(selected));return new ReligionContract.Response(request.method(),raw(result.value().publicResult()));
            }catch(IOException failure){throw new UncheckedIOException(failure);}
        }
    }
    /** The same recipe is installed by the actual family and consumed by original packet regressions. */
    public static ReadContract<ReligionModels.EpidemicResult> epidemicContract(EpidemicSelection selection,ExactRef definition,ExactRef decoder,ReligionTemporalFinance.Admission admission){
        Objects.requireNonNull(selection);Objects.requireNonNull(definition);Objects.requireNonNull(decoder);Objects.requireNonNull(admission);
        java.util.function.Function<PlanningReadReceipt,ReligionModels.EpidemicResult> decode=receipt->EpidemicOriginalDecoder.decode(receipt,selection.title(),selection.event());
        return new ReadContract<>("religion.extension.epidemic."+selection.title()+"."+(selection.event()==null?"none":selection.event()),new OperationKey(epidemicStep(selection)),Optional.empty(),"allow_private_epidemic_recovery_query",ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,definition,(request,id)->{
            admission.verify(request);var expected=org.xar.ck3.control.contracts.StrictJson.object();if(selection.title()==0)expected.put("expected_event_instance_id",selection.event());
            need(request.arguments().equals(OpportunityJson.object(OpportunityJson.parse(raw(expected).bytes()),"epidemic arguments")),"epidemic selector drift");return new NativeRequest(epidemicStep(selection),Optional.empty(),raw(org.xar.ck3.control.contracts.StrictJson.object()));
        },decode,decode);
    }
    private static String epidemicStep(EpidemicSelection selection){return "query-player-epidemic-recovery-v1"+(selection.title()==0?"":"-title-"+selection.title());}
}
