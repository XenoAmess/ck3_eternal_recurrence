package org.xar.ck3.control.service.root;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.family.FamilyObligationsQueries;
import org.xar.ck3.control.nativebridge.capabilities.family.EpidemicTreatmentPresenceQueries;
import org.xar.ck3.control.nativebridge.capabilities.interactions.*;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.service.mcp.*;
import org.xar.ck3.control.service.mcp.FamilySupplementPublicCodec.*;
import org.xar.ck3.control.service.root.RootPublicHandlerProductsFactory.Context;
import org.xar.ck3.control.service.root.RootPublicHandlerProductsFactory.Contribution;
import org.xar.ck3.control.service.root.RootRuntimeSelectedSources.Module;

/** Four original native-driver reads, using the current Family's identical installed producers. */
public final class RootFamilySupplementReadPublicProducts {
    public static final String OBLIGATIONS="ck3_query_family_obligations_private_v1";
    public static final String SUBJECT="ck3_query_player_child_marriage_subject_private_v1";
    public static final String VALUE="ck3_query_player_child_marriage_value_private_v1";
    public static final String TREATMENT="ck3_query_player_epidemic_treatment_presence_private_v1";
    public static final List<String> NAMES=List.of(OBLIGATIONS,SUBJECT,VALUE,TREATMENT);
    @FunctionalInterface interface Current {RawJson read(Request actual)throws InterruptedException;}
    private RootFamilySupplementReadPublicProducts() {}
    public static Contribution install(Context context,PublicBindings registry)throws IOException {
        Objects.requireNonNull(context);Objects.requireNonNull(registry);
        try {
            ExactRef source=context.source(RootFamilySupplementReadPublicProducts.class);
            for(Class<?> type:List.of(FamilySupplementPublicCodec.class,RootFamilyRuntimeFactory.class,RootEpidemicTreatmentRead.class,
                    RootFamilyNativeReadProducts.class,RootFamilyChildRead.class))context.source(type);
            for(Class<?> type:List.of(FamilyObligationsQueries.class,FamilyChildMarriageQueries.class,
                    FamilyChildMarriageSubject.class,FamilyMarriageValue.class,EpidemicTreatmentPresenceQueries.class))context.source(Module.NATIVE_TRANSPORT,type);
            return new Contribution(bindings(source,new ActualCurrent(context)),List.of(),List.of());
        }catch(IOException missing) {
            return new Contribution(List.of(),List.of(),NAMES.stream().map(name->new RootRuntimePublicCatalog.DefinitionGap(name,
                    "actual supported native Family read sources/definitions unavailable: "+missing.getMessage())).toList());
        }
    }
    static List<McpExecutableDirectory.DirectBinding<?,?>> bindings(ExactRef source,Current current) {
        Objects.requireNonNull(source);Objects.requireNonNull(current);
        return List.of(
            new McpExecutableDirectory.DirectBinding<>(OBLIGATIONS,PublicMcpBindings.Kind.DRIVER_DIRECT,Obligations.class,RawJson.class,
                request->current.read(request),call->FamilySupplementPublicCodec.decodeObligations(required(call.arguments())),
                PublicMcpDirectory.CallResult::fromBusinessJson,target(source)),
            new McpExecutableDirectory.DirectBinding<>(SUBJECT,PublicMcpBindings.Kind.DRIVER_DIRECT,ChildSubject.class,RawJson.class,
                request->current.read(request),call->FamilySupplementPublicCodec.decodeSubject(required(call.arguments())),
                PublicMcpDirectory.CallResult::fromBusinessJson,target(source)),
            new McpExecutableDirectory.DirectBinding<>(VALUE,PublicMcpBindings.Kind.DRIVER_DIRECT,ChildValue.class,RawJson.class,
                request->current.read(request),call->FamilySupplementPublicCodec.decodeValue(required(call.arguments())),
                PublicMcpDirectory.CallResult::fromBusinessJson,target(source)),
            new McpExecutableDirectory.DirectBinding<>(TREATMENT,PublicMcpBindings.Kind.DRIVER_DIRECT,Treatment.class,RawJson.class,
                request->current.read(request),call->FamilySupplementPublicCodec.decodeTreatment(required(call.arguments())),
                PublicMcpDirectory.CallResult::fromBusinessJson,target(source)));
    }
    private static PublicRoutes.Target target(ExactRef source){return new PublicRoutes.Target(ActualCurrent.class.getName(),"read",source);}
    private static RawJson required(PublicMcpDirectory.Arguments arguments) {
        StrictJson.require(arguments.presence()==PublicMcpDirectory.Presence.VALUE,"Family Driver read needs present non-null named arguments");
        return arguments.original().orElseThrow();
    }
    /** Retained read DATA only. Finding a JSON match still requires the same actual archive and strict child contract. */
    static final class Subjects {
        private final List<PlanningReadResult.Known<Obj>> rows=new ArrayList<>();
        synchronized void remember(PlanningReadResult.Known<Obj> known,ActionPorts.OutcomeArchive archive) {
            requireOriginal(known,archive);FamilyChildMarriageQueries.decodeSubject(known.receipt());
            rows.removeIf(row->!row.receipt().request().before().equals(known.receipt().request().before())
                    ||!row.receipt().request().source().equals(known.receipt().request().source())
                    ||!row.receipt().request().sessionId().equals(known.receipt().request().sessionId())
                    ||row.originalReceipt().equals(known.originalReceipt()));
            if(rows.size()==64)rows.removeFirst();rows.add(known);
        }
        synchronized PlanningReadResult.Known<Obj> find(ChildValue request,InteractionModels.Context current,ActionPorts.OutcomeArchive archive) {
            var matches=rows.stream().filter(row->row.value().equals(request.legality())
                    &&row.receipt().request().before().equals(current.before())&&row.receipt().request().source().equals(current.source())
                    &&row.receipt().request().sessionId().equals(current.sessionId())).toList();
            StrictJson.require(matches.size()==1,"child value lacks its unique retained actual same-frame subject read; query subject again");
            var actual=matches.getFirst();requireOriginal(actual,archive);return actual;
        }
        private static void requireOriginal(PlanningReadResult.Known<Obj> known,ActionPorts.OutcomeArchive archive) {
            StrictJson.require(archive.readReferenceOf(known.receipt()).equals(known.originalReceipt())
                    &&archive.loadRead(known.originalReceipt()).equals(known.receipt())
                    &&FamilyChildMarriageSubject.project(FamilyChildMarriageQueries.decodeSubject(known.receipt())).equals(known.value()),
                    "retained subject projection or actual archive custody changed");
        }
    }
    private static final class ActualCurrent implements Current {
        private final Context context;private final Subjects subjects=new Subjects();
        private ActualCurrent(Context context){this.context=Objects.requireNonNull(context);}
        @Override public RawJson read(Request request)throws InterruptedException {
            Objects.requireNonNull(request);var deadline=context.clock().instant().plus(context.observationTimeout());
            try{return context.withCurrent(root->root.executePublicDecision(deadline,(frame,driver,same)->{
                var installed=context.installed(root);var runtime=installed.context();runtime.writer().requireSession(same);
                var view=installed.additionalDomains().driverRegistry().product(RootDriverRegistryPublicProducts.Kind.FAMILY,RootDriverFamilyPublicProduct.Installed.class);
                view.requireContext(runtime);var family=view.family();
                StrictJson.require(family==installed.remainingDomains().family(),"Driver Family view replaced the sole installed Family");family.nativeReads().requireOwner(root);
                var actual=family.nativeReads().contextProjection().project(frame,deadline);
                PlanningReadResult.Known<Obj> known;
                if(request instanceof Treatment input) {
                    family.treatment().requireContext(runtime);known=family.treatment().read(same,frame,input.expectedRevision(),deadline);
                } else {
                    ReadContract<Obj> contract;Obj arguments;
                    if(request instanceof Obligations input) {
                        StrictJson.require(input.expectedRevision().equals(frame.identity().frame().revision()),"family obligations public expected revision is stale");
                        contract=family.obligationsContract();arguments=FamilyObligationsQueries.arguments(input.nativeRequest());
                    } else if(request instanceof ChildSubject input) {
                        contract=family.nativeReads().childMarriage().subject();
                        ObjectNode flat=StrictJson.object().put("expected_native_revision",input.expectedNativeRevision())
                                .put("subject_character_id",input.subjectCharacterId()).put("diagnose_family_arrays",input.diagnoseFamilyArrays());
                        arguments=FamilyChildMarriageQueries.canonicalSubject(actual,object(flat));
                    } else if(request instanceof ChildValue input) {
                        contract=family.nativeReads().childMarriage().value();var prior=subjects.find(input,actual,runtime.archive().withSession(same));
                        ObjectNode flat=StrictJson.object().put("candidate_character_id",input.candidateCharacterId()).put("request_matrilineal_option",input.requestMatrilineal());
                        flat.set("legality",OpportunityJson.toNode(input.legality()));flat.set("subject_read",prior.originalReceipt().toJson());
                        arguments=family.nativeReads().childMarriage().canonicalValue(actual,object(flat));
                    } else throw new IllegalArgumentException("unknown Family Driver read");
                    StrictJson.require(runtime.readCatalog().containsIdentity(contract),"public Family read lost the identical installed contract");
                    var nativeRequest=new PlanningReadRequest(frame.identity(),frame.source(),frame.sessionId(),contract.operation(),arguments,deadline);
                    var result=runtime.reads().read(same,contract,nativeRequest);
                    if(!(result instanceof PlanningReadResult.Known<Obj> available))throw new IOException("actual Family native read unavailable");
                    known=available;
                    if(request instanceof ChildSubject)subjects.remember(known,runtime.archive().withSession(same));
                }
                runtime.writer().requireSession(same);
                return new RootApplicationSession.RetainPublicResult<RawJson>(FamilySupplementPublicCodec.publicResult(known.value()));
            },(receipt,archive,same)->{throw new IOException("Family read cannot select an action result");}));
            }catch(IOException unavailable){throw new UncheckedIOException("actual Family Driver read unavailable",unavailable);}
        }
    }
    private static Obj object(ObjectNode node){return org.xar.ck3.control.application.driver.DriverJson.object(StrictJson.canonical(node,1048576),1048576);}
}

