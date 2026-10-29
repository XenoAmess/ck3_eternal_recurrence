package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.checkpoint.SavedCheckpointMaterialStore;
import org.xar.ck3.control.application.checkpoint.SavedFirstCheckpointMaterialStore;
import org.xar.ck3.control.application.driver.DriverBootstrap;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.platform.GameRestoreAdapter;
import org.xar.ck3.control.platform.GameRestoreNativeAdapter;
import org.xar.ck3.control.platform.NativeLaunchPlan;

/** The selected Java originals and the identical launch plan's runtime originals must agree before
 * startup constructs restoration products. This is source custody only: it creates no Game, material,
 * restored binding, reducer proof, checkpoint, writer, or readiness token. */
public final class RootRestoreRuntimeSources {
    private RootRestoreRuntimeSources() { }

    /** A closed production roster. No caller supplies a target, class name, source path, or verifier. */
    public enum Role {
        IMPLEMENTATION(RootRuntimeSelectedSources.Module.LOCAL_SERVICE, RootRestoreRuntimeSources.class),
        STARTUP_NEXT(RootRuntimeSelectedSources.Module.LOCAL_SERVICE, RootStartupNextResources.class),
        PUBLIC_RESTORE(RootRuntimeSelectedSources.Module.LOCAL_SERVICE, RootPublicRestoreRuntime.class),
        RESTORED_ASSEMBLY(RootRuntimeSelectedSources.Module.LOCAL_SERVICE, RootRestoreAssemblyInputs.class),
        FIRST_REOPEN(RootRuntimeSelectedSources.Module.LOCAL_SERVICE, RootSavedFirstReopen.class),
        ORIGINAL_PROOF(RootRuntimeSelectedSources.Module.LOCAL_SERVICE, RootRestorationOriginalProof.class),
        MATERIAL_FACTORY(RootRuntimeSelectedSources.Module.LOCAL_SERVICE, RootRestoreMaterialFactory.class),
        MATERIALS(RootRuntimeSelectedSources.Module.LOCAL_SERVICE, RootRestoreMaterials.class),
        RESTORE_ADAPTERS(RootRuntimeSelectedSources.Module.LOCAL_SERVICE, RootRestoreAdapters.class),
        POST_ADOPTION(RootRuntimeSelectedSources.Module.LOCAL_SERVICE, RootPostAdoptionCollector.class),
        RESTORE_SERVICE(RootRuntimeSelectedSources.Module.APPLICATION, RestoreCheckpointService.class),
        CHECKPOINT_MATERIALS(RootRuntimeSelectedSources.Module.APPLICATION, SavedCheckpointMaterialStore.class),
        FIRST_MATERIALS(RootRuntimeSelectedSources.Module.APPLICATION, SavedFirstCheckpointMaterialStore.class),
        DRIVER_BOOTSTRAP(RootRuntimeSelectedSources.Module.LOCAL_SERVICE, DriverBootstrap.class),
        GAME_REPLACEMENT(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT, GameRestoreAdapter.class),
        GAME_NATIVE(RootRuntimeSelectedSources.Module.NATIVE_TRANSPORT, GameRestoreNativeAdapter.class);

        private final RootRuntimeSelectedSources.Module module;
        private final Class<?> javaClass;
        Role(RootRuntimeSelectedSources.Module module, Class<?> javaClass) {
            this.module=module; this.javaClass=javaClass;
        }
    }

    /** One closed source-role roster shared by the actual default producer and runtime capture.
     * These types identify required source/loaded-class originals; they grant no restoration authority. */
    public record RequiredSource(Role role,RootRuntimeSelectedSources.Module module,Class<?> type) {
        public RequiredSource {
            Objects.requireNonNull(role);Objects.requireNonNull(module);Objects.requireNonNull(type);
            if(module!=role.module||type!=role.javaClass)
                throw new IllegalArgumentException("restoration source role must retain its exact declared module/type");
        }
    }
    public static List<RequiredSource> requiredSources() {
        var sources=new ArrayList<RequiredSource>();
        for(Role role:Role.values())sources.add(new RequiredSource(role,role.module,role.javaClass));
        return List.copyOf(sources);
    }

    /** Immutable source data, never an admission. Integer sizes and identities keep the existing
     * ExactRef contract; there is no second configuration or JSON field representation. */
    public record Original(Role role, ExactRef source) {
        public Original {
            Objects.requireNonNull(role); Objects.requireNonNull(source);
            if(source.bytes()<=0)throw new IllegalArgumentException("nonempty actual restoration Java source required");
        }
    }

    /** Only capture can retain this source snapshot. Revalidation requires the identical source
     * resolver and launch plan objects, not equivalent caller-made configuration records. */
    public static final class Captured {
        private final RootRuntimeSelectedSources selected;
        private final NativeLaunchPlan plan;
        private final List<Original> originals;
        private Captured(RootRuntimeSelectedSources selected,NativeLaunchPlan plan,List<Original> originals) {
            this.selected=selected; this.plan=plan; this.originals=List.copyOf(originals);
        }
        public List<Original> originals() { return originals; }
        public ExactRef source(Role required) {
            Objects.requireNonNull(required);
            return originals.stream().filter(row->row.role()==required).findFirst().orElseThrow().source();
        }
        /** Invoke during startup's current-source checks and again before constructing its original
         * Shared products. This method does not enter a writer lock or inspect a saved head. */
        public void requireCurrent(RootRuntimeSelectedSources sameSelected,NativeLaunchPlan samePlan)throws IOException {
            if(sameSelected!=selected||samePlan!=plan)
                throw new IOException("restoration sources crossed the original startup resolver or launch plan");
            selected.requireCurrent();
            var closure=plan.sources().review().completeRuntimeSources();
            for(RequiredSource required:requiredSources()) {
                var role=required.role();
                Original original=originals.stream().filter(row->row.role()==role).findFirst()
                        .orElseThrow(()->new IOException("actual restoration source role disappeared: "+role));
                ExactRef actual=selected.javaSource(required.module(),required.type());
                if(!actual.equals(original.source()))
                    throw new IOException("restoration selected source changed for "+role);
                requirePlanOriginal(original.source(),closure,role);
                // The actual class, loader and CodeSource must belong to this identical accepted plan.
                plan.sources().requireLoadedClass(required.type());
            }
            // The existing authority verifies actual package/class custody and complete configured
            // native inputs. Listing matching Java data alone is insufficient.
            selected.requireLoadedClasses(plan);
            selected.requireCurrent();
        }
    }

    public static Captured capture(RootRuntimeSelectedSources actualSelected,NativeLaunchPlan sameActualPlan)throws IOException {
        Objects.requireNonNull(actualSelected); Objects.requireNonNull(sameActualPlan);
        var originals=new ArrayList<Original>();
        for(RequiredSource required:requiredSources())
            originals.add(new Original(required.role(),actualSelected.javaSource(required.module(),required.type())));
        requireComplete(originals);
        var captured=new Captured(actualSelected,sameActualPlan,originals);
        captured.requireCurrent(actualSelected,sameActualPlan);
        return captured;
    }

    private static void requireComplete(List<Original> originals)throws IOException {
        var found=EnumSet.noneOf(Role.class);
        for(Original original:originals)
            if(!found.add(original.role()))throw new IOException("duplicate restoration source role");
        if(!found.equals(EnumSet.allOf(Role.class)))throw new IOException("incomplete restoration source closure");
    }

    /** Join both independently validated source tables. A match is the exact original path, size
     * and SHA; a file copied elsewhere or a same-name class from another source cannot replace it. */
    static void requirePlanOriginal(ExactRef selected,List<FileRef> runtime,Role role)throws IOException {
        Path original=Path.of(selected.path()).toRealPath();
        int matches=0;
        for(FileRef retained:runtime) {
            if(retained.bytes()==selected.bytes()&&retained.sha256().equalsIgnoreCase(selected.sha256())
                    &&Path.of(retained.path()).toRealPath().equals(original)) {
                retained.verify(); matches++;
            }
        }
        if(matches!=1)
            throw new IOException("restoration source is absent or ambiguous in the identical plan's complete runtime closure: "+role);
    }
}
