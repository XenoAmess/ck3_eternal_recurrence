package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.service.root.RootRuntimeDefinitionModel.SelectedSource;

/** Historical source references are passive DATA; selecting them grants no runtime admission. */
public final class RootRuntimeSelectedSources {
    public enum OriginalKind { NATIVE_CPP,NATIVE_HEADER,ORIGINAL_PYTHON,STOCK_SCRIPT }
    public enum Module {
        APPLICATION("application"),LOCAL_SERVICE("local-service"),NATIVE_TRANSPORT("native-transport"),
        G2_RESEARCH("g2-research"),WAVE2_MILITARY("wave2-military"),PLANNING_ADMISSION("planning-admission"),
        CONTRACTS("contracts"),ADAPTERS_STORAGE("adapters-storage"),VANILLA_DATA("vanilla-data"),
        GOVERNANCE("governance"),PLANNING("planning"),RECONCILIATION("reconciliation");
        private final String directory;
        Module(String directory){this.directory=directory;}
        public String directory(){return directory;}
    }
    private static final int MAXIMUM_SOURCES=8192;
    private static final int MAXIMUM_SOURCE_BYTES=64<<20;
    private final Map<String,SelectedSource> index;
    private final Optional<RootRuntimeDefinitions.Inputs> capturedInputs;
    private final Map<Path,ExactRef> retained=new LinkedHashMap<>();

    public RootRuntimeSelectedSources(RootRuntimeDefinitions.Inputs actual)throws IOException {
        this(Objects.requireNonNull(actual).sourceIndex(),Optional.of(actual));
    }
    /** Source-only regression entry; it cannot create Runtime Inputs, Native permissions or readiness authority. */
    RootRuntimeSelectedSources(List<SelectedSource> actualIndex)throws IOException {
        this(actualIndex,Optional.empty());
    }
    private RootRuntimeSelectedSources(List<SelectedSource> actualIndex,
            Optional<RootRuntimeDefinitions.Inputs> capturedInputs)throws IOException {
        Objects.requireNonNull(actualIndex);this.capturedInputs=Objects.requireNonNull(capturedInputs);
        if(actualIndex.isEmpty()||actualIndex.size()>MAXIMUM_SOURCES)throw new IOException("complete bounded winner index required");
        var unique=new LinkedHashMap<String,SelectedSource>();
        for(var source:actualIndex)if(unique.putIfAbsent(source.targetRelative(),source)!=null)
            throw new IOException("winner index contains a duplicate target: "+source.targetRelative());
        index=Map.copyOf(unique);
    }
    public synchronized ExactRef javaSource(Module module,Class<?> actualClass)throws IOException {
        Objects.requireNonNull(module);Class<?> sourceClass=outer(actualClass);
        String target=module.directory()+"/src/main/java/"+sourceClass.getName().replace('.','/')+".java";
        return javaSourceAt(target,sourceClass);
    }
    /** Some inherited source targets deliberately differ from their declared Java package directory.
     * Their sole owner's exact roster supplies this target; no fallback path is guessed from the FQN. */
    public synchronized ExactRef javaSourceAt(String target,Class<?> actualClass)throws IOException {
        Class<?> sourceClass=outer(actualClass);
        if(!Objects.requireNonNull(target).endsWith("/"+sourceClass.getSimpleName()+".java"))
            throw new IOException("actual source target filename differs from its retained project class");
        ExactRef selected=javaTarget(target);
        return selected;
    }
    private static Class<?> outer(Class<?> actual)throws IOException {
        Objects.requireNonNull(actual);Class<?> sourceClass=actual;
        while(sourceClass.getEnclosingClass()!=null)sourceClass=sourceClass.getEnclosingClass();
        if(!sourceClass.getName().startsWith("org.xar.ck3.control."))throw new IOException("actual project Java source class required");
        return sourceClass;
    }
    synchronized ExactRef javaTarget(String target)throws IOException {
        SelectedSource actual=index.get(Objects.requireNonNull(target));
        if(actual==null||!target.endsWith(".java"))throw new IOException("actual unique Java source target missing: "+target);
        return retain(actual.sourceRef(),".java");
    }
    /** Existing Python/C++/stock files are provenance only, never a new executable Python path or a Java stand-in. */
    public synchronized ExactRef original(FileRef original,OriginalKind expectedKind)throws IOException {
        Objects.requireNonNull(original);Objects.requireNonNull(expectedKind);
        String suffix=switch(expectedKind){case NATIVE_CPP->".cpp";case NATIVE_HEADER->".hpp";
            case ORIGINAL_PYTHON->".py";case STOCK_SCRIPT->".txt";};
        return retain(new ExactRef(original.path(),original.bytes(),original.sha256()),suffix);
    }
    private ExactRef retain(ExactRef expected,String suffix)throws IOException {
        Path path=Path.of(expected.path());
        if(!path.isAbsolute()||!path.normalize().equals(path)||!path.getFileName().toString().endsWith(suffix)
                ||expected.bytes()<=0||expected.bytes()>MAXIMUM_SOURCE_BYTES)
            throw new IOException("actual bounded source kind/path differs: "+path);
        var previous=retained.get(path);
        if(previous!=null){
            if(!same(expected,previous))throw new IOException("one actual producer source has conflicting exact refs: "+path);
            return expected;
        }
        if(retained.size()>=MAXIMUM_SOURCES)throw new IOException("bounded concrete runtime source inventory exceeded");
        retained.put(path,expected);return expected;
    }
    /** Reuses the identical immutable Inputs which supplied the historical source metadata.
     * Source-only selectors cannot be rebound into a runtime input selection. */
    public synchronized void requireInputs(RootRuntimeDefinitions.Inputs identical)throws IOException {
        Objects.requireNonNull(identical);
        if(capturedInputs.isEmpty()||capturedInputs.orElseThrow()!=identical)
            throw new IOException("runtime sources belong to different actual captured Inputs/source index");
    }
    public synchronized void requireCurrent()throws IOException { }
    /** Historical loaded-class and Native source rosters do not create runtime qualification. */
    public synchronized void requireLoadedClasses(NativeLaunchPlan sameActualPlan)throws IOException {
        Objects.requireNonNull(sameActualPlan);
    }
    public synchronized List<ExactRef> retainedSources(){return List.copyOf(retained.values());}
    private static boolean same(ExactRef expected,ExactRef actual){return Path.of(expected.path()).equals(Path.of(actual.path()))
            &&expected.bytes()==actual.bytes()&&expected.sha256().equalsIgnoreCase(actual.sha256());}
}