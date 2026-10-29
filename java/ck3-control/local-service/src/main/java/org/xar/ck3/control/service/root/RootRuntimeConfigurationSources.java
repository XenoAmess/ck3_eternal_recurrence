package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.*;

import java.io.IOException;
import java.time.Clock;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.g2.context.RootNativeRuntimeBinding;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionConfigurationAssembler.PhysicalOriginals;

/** Produces the default runtime source closures from the actual, bounded single-winner index.
 * Configuration data is not a Prepared product, a loaded runtime admission or a Game authority. */
public final class RootRuntimeConfigurationSources {
    private RootRuntimeConfigurationSources() { }

    /** Called by the production assembler before the sole Configuration constructor and codec. */
    public static PhysicalOriginals complete(PhysicalOriginals physical,String machineId,Clock clock)throws IOException {
        Objects.requireNonNull(physical);Objects.requireNonNull(machineId);Objects.requireNonNull(clock);
        List<SelectedSource> winners=RootRuntimeDefinitions.readSourceIndex(physical.sourceIndex(),machineId,clock);
        var configured=new LinkedHashMap<String,SelectedSource>();
        for(SourcePin source:physical.sources())retain(configured,source.selected());
        for(ProducerClosure closure:physical.closures())for(SelectedSource source:closure.sources())retain(configured,source);

        var startup=new ArrayList<SelectedSource>();
        for(String name:RootNativeRuntimeBinding.requiredRuntimeClassNames())startup.add(requireClass(winners,name));
        // Retain the actual source of both producing steps, rather than admitting an unrecorded assembler.
        startup.add(requireClass(winners,RootRuntimeConfigurationSources.class.getName()));
        startup.add(requireClass(winners,RootRuntimeDefinitionConfigurationAssembler.class.getName()));
        // The ordinary and fixture paths retain one code cut; source membership grants no fixture permission.
        for(var required:RootFrontendRuntime.requiredFixtureSources())startup.add(requireTarget(winners,required.targetRelative()));
        // Loaded nested classes retain their actual nest host's source; loaded-class checks still use the original Class.
        for(Class<?> type:RootColdReboundRuntime.requiredSourceTypes())startup.add(requireClass(winners,type.getNestHost().getName()));
        for(Class<?> type:requiredProfileSourceTypes())startup.add(requireClass(winners,type.getNestHost().getName()));
        for(Class<?> type:org.xar.ck3.control.build.runtime.JavaRuntimeLaunch.requiredInvocationSources()) {
            String target="build-tools/src/main/java/"+type.getNestHost().getName().replace('.','/')+".java";
            startup.add(requireTarget(winners,target));
        }
        for(var required:RootSavedNativeCoordinator.requiredSources()) {
            Class<?> host=required.type().getNestHost();
            startup.add(requireTarget(winners,required.module().directory()+"/src/main/java/"+host.getName().replace('.','/')+".java"));
        }
        // The restoration consumer and default producer share the one typed role roster.
        for(var required:RootRestoreRuntimeSources.requiredSources()) {
            Class<?> host=required.type().getNestHost();
            startup.add(requireTarget(winners,required.module().directory()+"/src/main/java/"+host.getName().replace('.','/')+".java"));
        }
        for(SelectedSource source:startup)retain(configured,source);

        var readHistory=new ArrayList<SelectedSource>();
        for(var required:RootRuntimeSourceProducts.requiredReadHistorySources()) {
            SelectedSource source=requireTarget(winners,required.targetRelative());
            retain(configured,source);readHistory.add(source);
        }
        var completed=new ArrayList<ProducerClosure>();
        for(ProducerClosure closure:physical.closures())completed.add(switch(closure.role()) {
            case STARTUP->merge(closure,startup);
            case READ_HISTORY->merge(closure,readHistory);
            default->closure;
        });
        if(completed.stream().filter(row->row.role()==ClosureRole.STARTUP).count()!=1
                ||completed.stream().filter(row->row.role()==ClosureRole.READ_HISTORY).count()!=1)
            throw new IOException("One original STARTUP and READ_HISTORY closure required by the production assembler");
        physical.sourceIndex().compressedRef().verify();
        RootRuntimeDefinitions.sourceIndexOriginalInput(physical.sourceIndex()).verify();
        return new PhysicalOriginals(physical.applicationRef(),physical.storageLeaseRef(),physical.nativeLaunchPlanRef(),
                physical.runtimePackageRequestRef(),physical.sourceIndex(),physical.sources(),completed,physical.originalData());
    }

    /** Actual typed profile providers retained by the default producer; this grants no profile qualification. */
    public static List<Class<?>> requiredProfileSourceTypes() {
        var types=new ArrayList<Class<?>>(org.xar.ck3.control.platform.NativeLaunchPlan.requiredPreparedProfileTypes());
        types.add(org.xar.ck3.control.build.NativeRunProfileManifest.class);
        types.add(org.xar.ck3.control.build.NativeRunProfileProducer.class);
        return List.copyOf(types);
    }

    private static SelectedSource requireClass(List<SelectedSource> winners,String className)throws IOException {
        String suffix="/src/main/java/"+className.replace('.','/')+".java";
        List<SelectedSource> selected=winners.stream().filter(row->row.targetRelative().endsWith(suffix)).toList();
        if(selected.size()!=1)throw new IOException("One exact single-winner Java target required for the actual runtime class: "+className);
        return read(selected.getFirst());
    }
    private static SelectedSource requireTarget(List<SelectedSource> winners,String target)throws IOException {
        List<SelectedSource> selected=winners.stream().filter(row->row.targetRelative().equals(target)).toList();
        if(selected.size()!=1)throw new IOException("Exact required producer is absent from the actual single-winner index: "+target);
        return read(selected.getFirst());
    }
    private static SelectedSource read(SelectedSource source)throws IOException {
        RootRuntimeDefinitions.read(RootApplicationConfiguration.file(source.sourceRef()),64<<20);
        return source;
    }
    private static ProducerClosure merge(ProducerClosure original,List<SelectedSource> required)throws IOException {
        var result=new LinkedHashMap<String,SelectedSource>();
        for(SelectedSource source:original.sources())retain(result,source);
        for(SelectedSource source:required)retain(result,source);
        try{return new ProducerClosure(original.role(),List.copyOf(result.values()));}
        catch(IllegalArgumentException invalid){throw new IOException("Complete production closure exceeds its existing contract",invalid);}
    }
    private static void retain(Map<String,SelectedSource> result,SelectedSource source)throws IOException {
        SelectedSource prior=result.putIfAbsent(source.targetRelative().toLowerCase(Locale.ROOT),source);
        if(prior!=null&&!prior.equals(source))
            throw new IOException("Production source closure conflicts with an original selected target: "+source.targetRelative());
    }
}
