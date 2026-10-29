package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.application.planning.sway.*;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.service.sway.SwayRuntimeInstaller;
import org.xar.ck3.control.vanilla.schemesway.OrdinarySwayService;
import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.DataRole.SWAY_CONFIGURATION;

/** Sole strict Sway configuration producer/reader and pre-Core source products. No parser result grants gameplay readiness. */
public final class RootSwaySourcesFactory {
    public static final String SCHEMA="xar.java.sway-source-configuration/v3";
    public static final int MAXIMUM_BYTES=1<<20;
    private RootSwaySourcesFactory() { }
    public record SourceConfiguration(String machineId,Instant observedAt,Instant reviewAt,Path originalWriterLock,Path legacyLedger,
            OrdinarySwayService.Capabilities capabilities,RootRuntimeDomainAssembly.SwayInitialization initialization,boolean invalidationReasonQuery) {
        public SourceConfiguration {
            require(machineId!=null&&machineId.matches("[a-z0-9][a-z0-9-]{0,63}")&&!machineId.equals("unknown"),"explicit Sway source machine required");
            Objects.requireNonNull(observedAt);Objects.requireNonNull(reviewAt);require(observedAt.isBefore(reviewAt),"bounded Sway source review interval required");
            absolute(originalWriterLock);absolute(legacyLedger);Objects.requireNonNull(capabilities);Objects.requireNonNull(initialization);
            if(initialization instanceof RootRuntimeDomainAssembly.SwayOriginals originals) {
                original(originals.formal(),SwayFormalCodec.MAX);originals.scheduler().ifPresent(value->original(value,SwayFormalCodec.MAX));original(originals.guardedOriginRead(),StrictJson.MAX_SAFE_INTEGER);
                require(legacyLedger.equals(Path.of(originals.formal().path())),"legacy source path must be the selected actual original formal ledger");
            }
        }
    }
    public record Products(SwayRuntimeInstaller.Prepared prepared,RootRuntimeDomainAssembly.SwayInitialization initialization) {
        public Products {Objects.requireNonNull(prepared);Objects.requireNonNull(initialization);}
    }
    public static byte[] encode(SourceConfiguration value) {
        var row=StrictJson.object();row.put("schema",SCHEMA);row.put("machine_id",value.machineId());row.put("observed_at_utc",value.observedAt().toString());row.put("review_at_utc",value.reviewAt().toString());row.put("invalidation_reason_query",value.invalidationReasonQuery());
        row.put("original_writer_lock",value.originalWriterLock().toString());row.put("legacy_ledger",value.legacyLedger().toString());var capabilities=row.putObject("capabilities");capabilities.put("formal_query",value.capabilities().formalQuery());capabilities.put("formal_action",value.capabilities().formalAction());capabilities.put("lifecycle_reader",value.capabilities().lifecycleReader());
        var initialization=row.putObject("initialization");switch(value.initialization()) {
            case RootRuntimeDomainAssembly.SwayFresh fresh -> initialization.put("kind","fresh_after_actual_initial_entry");
            case RootRuntimeDomainAssembly.SwayOriginals originals -> {
                initialization.put("kind","import_original");initialization.set("formal",originals.formal().toJson());
                if(originals.scheduler().isPresent())initialization.set("scheduler",originals.scheduler().orElseThrow().toJson());else initialization.putNull("scheduler");
                initialization.set("guarded_origin_read",originals.guardedOriginRead().toJson());
            }
        }return StrictJson.canonical(row,MAXIMUM_BYTES);
    }
    public static SourceConfiguration decode(byte[] raw) {
        var row=StrictJson.object(StrictJson.parse(raw,MAXIMUM_BYTES),Set.of("schema","machine_id","observed_at_utc","review_at_utc","original_writer_lock","legacy_ledger","capabilities","initialization","invalidation_reason_query"));require(SCHEMA.equals(StrictJson.text(row.get("schema"))),"strict versioned Sway source configuration required");
        var capabilities=StrictJson.object(row.get("capabilities"),Set.of("formal_query","formal_action","lifecycle_reader"));
        var initialization=row.get("initialization");require(initialization!=null&&initialization.isObject(),"explicit Sway initialization branch required");
        RootRuntimeDomainAssembly.SwayInitialization selected=switch(StrictJson.text(initialization.get("kind"))) {
            case "fresh_after_actual_initial_entry" -> {StrictJson.object(initialization,Set.of("kind"));yield new RootRuntimeDomainAssembly.SwayFresh();}
            case "import_original" -> {
                StrictJson.object(initialization,Set.of("kind","formal","scheduler","guarded_origin_read"));
                require(initialization.has("scheduler"),"scheduler must be an explicit original or explicit null, never missing");
                yield new RootRuntimeDomainAssembly.SwayOriginals(ExactRef.fromJson(initialization.get("formal")),initialization.get("scheduler").isNull()?Optional.empty():Optional.of(ExactRef.fromJson(initialization.get("scheduler"))),ExactRef.fromJson(initialization.get("guarded_origin_read")));
            }
            default -> throw new IllegalArgumentException("unsupported Sway initialization kind");
        };
        return new SourceConfiguration(StrictJson.text(row.get("machine_id")),instant(row.get("observed_at_utc")),instant(row.get("review_at_utc")),Path.of(StrictJson.text(row.get("original_writer_lock"))),Path.of(StrictJson.text(row.get("legacy_ledger"))),
                new OrdinarySwayService.Capabilities(bool(capabilities.get("formal_query")),bool(capabilities.get("formal_action")),bool(capabilities.get("lifecycle_reader"))),
                selected,bool(row.get("invalidation_reason_query")));
    }
    public static SourceConfiguration readExact(FileRef original)throws IOException {
        Objects.requireNonNull(original);absolute(Path.of(original.path()));if(original.bytes()<1||original.bytes()>MAXIMUM_BYTES)throw new IOException("bounded exact SWAY_CONFIGURATION required");original.verify();var held=SharedSourceFiles.observe(Path.of(original.path()));
        byte[] raw;try(var input=Files.newInputStream(Path.of(original.path()))){raw=input.readNBytes(MAXIMUM_BYTES+1);}if(raw.length!=original.bytes()||!org.xar.ck3.control.application.action.ActionCodec.sha256(raw).equalsIgnoreCase(original.sha256()))throw new IOException("Sway source configuration bytes/hash changed during bounded read");
        try{var result=decode(raw);SharedSourceFiles.assertUnchanged(held);original.verify();return result;}catch(IllegalArgumentException|java.time.DateTimeException invalid){throw new IOException("invalid exact SWAY_CONFIGURATION",invalid);}
    }
    /** Sole create-only role10 DATA publisher; the strict consumer rereads the actual file before returning its reference. */
    public static FileRef publish(SourceConfiguration data,Path exactOutput,RootBootstrapOutputGuard authority)throws IOException {
        Objects.requireNonNull(data);absolute(exactOutput);Objects.requireNonNull(authority);byte[] raw=encode(data);
        var output=new RootBootstrapOutputContract.Output(RootBootstrapOutputContract.Kind.SWAY_CONFIGURATION,exactOutput.getFileName().toString(),raw.length,org.xar.ck3.control.application.action.ActionCodec.sha256(raw));
        authority.requirePlan(exactOutput.getParent(),List.of(output),List.of(),List.of());
        var files=authority.files();var created=files.createNew(exactOutput,raw);files.verify(created);
        var exact=created.reference();var original=new FileRef(exact.path(),exact.bytes(),exact.sha256());
        require(data.equals(readExact(original)),"published Sway source configuration differs from actual strict readback");
        authority.requireTargets(List.of(exactOutput));files.verify(created);return original;
    }
    static SwayRuntimeInstaller.Configuration runtimeConfiguration(SourceConfiguration data,Path sameWriterLock,FinanceReadContracts.Registration sameRootRegistration) {
        require(data.originalWriterLock().equals(Objects.requireNonNull(sameWriterLock)),"Sway configuration names another original canonical writer lock");
        return new SwayRuntimeInstaller.Configuration(data.originalWriterLock(),data.legacyLedger(),data.capabilities(),new SwayRuntimeInstaller.SharedRootSelection(FinanceReadContracts.ROOT_CONTRACT_ID,Objects.requireNonNull(sameRootRegistration)),data.invalidationReasonQuery());
    }
    public static Products prepare(RootRuntimeDefinitions.Inputs sameInputs,RootRuntimeSelectedSources selected,RootRuntimeDomainSettings.Bound settings,FinanceReadContracts.Registration sameRootRegistration)throws IOException {
        Objects.requireNonNull(sameInputs);Objects.requireNonNull(selected);Objects.requireNonNull(settings);Objects.requireNonNull(sameRootRegistration);
        var original=sameInputs.data(SWAY_CONFIGURATION);var data=readExact(original);
        require(data.machineId().equals(sameInputs.application().machineId())&&settings.configuration().machineId().equals(data.machineId()),"actual Sway inputs/settings machine differs");
        require(!data.observedAt().isAfter(Instant.parse(sameInputs.configuration().observedAtUtc()))&&!Instant.parse(sameInputs.configuration().reviewAtUtc()).isAfter(data.reviewAt()),"runtime definitions cannot predate the original Sway source or outlive its review");
        var config=runtimeConfiguration(data,sameInputs.application().ledger().lock(),sameRootRegistration);
        var module=RootRuntimeSelectedSources.Module.APPLICATION;
        for(Class<?> type:List.of(SwayNativeBindings.class,SwayNativeWire.class,SwayObservationReads.class,SwayRootReads.class,SwayRootActions.class,SwayActionLifecycle.class,SwayCanonicalDomain.class,SwayFormalState.class,SwayFormalCodec.class,SwayLegacyImport.class,SwayTransitionCodec.class,SwaySchedulerReplay.class,SwayNextEpisodeImport.class,SwayOrdinaryExecutor.class,SwayFollowingConsumption.class,SwayOrdinaryComposite.class,SwaySessionInputs.class,OrdinarySwayPolicy.class,OrdinarySwayReadSource.class,OrdinarySwayPolicyFactory.class,SwaySelectedFinish.class,SwaySelectedJournal.class,SwaySelectedObservation.class,SwayPublicCodec.class,SwaySelectedStart.class,SwayDriverCodec.class))selected.javaSource(module,type);
        var runtimeSource=selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,SwayRuntimeInstaller.class);selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootSwaySourcesFactory.class);
        var initialProofSource=selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootInitialEpisodeProof.class);
        var domainAssemblySource=selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootRuntimeDomainAssembly.class);
        var configurationProducerSource=selected.javaSource(RootRuntimeSelectedSources.Module.LOCAL_SERVICE,RootSwayConfigurationProducer.class);
        selected.javaSource(RootRuntimeSelectedSources.Module.G2_RESEARCH,OrdinarySwayService.class);
        var closure=new ArrayList<ExactRef>();for(var source:sameInputs.sourceIndex().stream().sorted(java.util.Comparator.comparing(RootRuntimeDefinitionModel.SelectedSource::targetRelative)).toList()){
            String target=source.targetRelative();String m6="g2-research/src/main/java/org/xar/ck3/control/g2/m6/";
            if(target.startsWith("application/src/main/java/org/xar/ck3/control/application/planning/sway/")||target.startsWith("local-service/src/main/java/org/xar/ck3/control/service/sway/")||target.startsWith("g2-research/src/main/java/org/xar/ck3/control/vanilla/schemesway/")||(target.startsWith(m6)&&target.substring(m6.length()).indexOf('/')<0)||target.equals("local-service/src/main/java/org/xar/ck3/control/service/root/RootSwaySourcesFactory.java"))closure.add(selected.javaTarget(target));
        }
        closure.add(initialProofSource);closure.add(domainAssemblySource);closure.add(configurationProducerSource);closure.add(new ExactRef(original.path(),original.bytes(),original.sha256()));require(closure.contains(runtimeSource),"actual installed Sway implementation absent from complete closure");
        var definitions=selected.javaSource(module,SwayNativeBindings.class);var nativeDecoder=selected.javaSource(module,SwayNativeWire.class);var observations=selected.javaSource(module,SwayObservationReads.class);var pending=selected.javaSource(module,SwayActionLifecycle.class);
        var sources=new SwayRuntimeInstaller.Sources(new SwayRootReads.Sources(definitions,nativeDecoder,observations),new SwayRootActions.Sources(definitions,nativeDecoder,pending),selected.javaSource(module,OrdinarySwayPolicy.class),selected.javaSource(module,SwayOrdinaryExecutor.class),selected.javaSource(module,SwayOrdinaryComposite.class),pending,closure.stream().distinct().toList());
        selected.requireCurrent();original.verify();return new Products(new SwayRuntimeInstaller.Prepared(config,sources),data.initialization());
    }
    private static void absolute(Path path){Objects.requireNonNull(path);require(path.isAbsolute()&&path.normalize().equals(path),"normalized absolute Sway source path required");}
    private static void original(ExactRef value,long maximum){Objects.requireNonNull(value);absolute(Path.of(value.path()));require(value.bytes()>0&&value.bytes()<=maximum&&value.sha256().matches("[0-9a-f]{64}"),"exact bounded canonical original Sway source required");}
    private static Instant instant(com.fasterxml.jackson.databind.JsonNode value){String text=StrictJson.text(value);Instant parsed=Instant.parse(text);require(text.equals(parsed.toString()),"canonical UTC Sway source time required");return parsed;}
    private static boolean bool(com.fasterxml.jackson.databind.JsonNode value){require(value!=null&&value.isBoolean(),"actual Sway capability must be boolean");return value.booleanValue();}
}
