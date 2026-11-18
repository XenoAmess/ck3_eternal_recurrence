package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Objects;
import org.xar.ck3.control.application.driver.InitialEpisodePolicy;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.platform.NativeLaunchPlan;
import org.xar.ck3.control.platform.NativeLaunchPlanCodec;

/** Exact configuration DATA for the existing source/preentry readers. This class grants no admission or live phase. */
public final class RootSavedRuntimeConfigurationInputs {
    private static final int MAXIMUM_BYTES=1<<20;
    private RootSavedRuntimeConfigurationInputs(){ }

    /** A Saved source configuration binds its own exact retained plan, before the canonical source is qualified. */
    public static RootOrdinaryRuntimeConfiguration readSource(ExactRef actualConfiguration)throws IOException {
        return read(actualConfiguration,null);
    }
    /** The loaded entry supplies the actual exact owner descriptor's plan; the later private admission remains mandatory. */
    public static RootOrdinaryRuntimeConfiguration readLoaded(ExactRef actualConfiguration,NativeLaunchPlan ownerPlan)throws IOException {
        Objects.requireNonNull(ownerPlan);
        if(!(ownerPlan.load() instanceof NativeLaunchPlan.SavedGame))throw new IOException("loaded configuration requires its exact Saved owner plan");
        return read(actualConfiguration,ownerPlan);
    }
    private static RootOrdinaryRuntimeConfiguration read(ExactRef actualConfiguration,NativeLaunchPlan ownerPlan)throws IOException {
        Objects.requireNonNull(actualConfiguration);Path file=Path.of(actualConfiguration.path());
        if(!file.isAbsolute()||!file.normalize().equals(file)||actualConfiguration.bytes()<1||actualConfiguration.bytes()>MAXIMUM_BYTES)
            throw new IOException("bounded exact absolute runtime configuration required");
        try(var custody=new InputCustody()) {
        var configuration=custody.observe(file);
        if(!same(configuration.source(),actualConfiguration))throw new IOException("runtime configuration differs from its exact request source");
        var root=StrictJson.parse(readBounded(file),MAXIMUM_BYTES);
        StrictJson.require(root.isObject()&&"xar.java-ordinary-runtime-configuration/v1".equals(StrictJson.text(root.get("schema"))),"exact runtime configuration schema required");
        Path policyPath=resolve(root.get("initial_policy_file"),file.getParent());
        custody.observe(policyPath);var policy=StrictJson.parse(readBounded(policyPath),MAXIMUM_BYTES);
        var schema=policy.get("schema");
        boolean saved=schema!=null&&schema.isTextual()&&(InitialEpisodePolicy.SAVED_SCHEMA.equals(schema.textValue())
                ||InitialEpisodePolicy.MATERIALIZED_SAVED_SCHEMA.equals(schema.textValue()));
        RootOrdinaryRuntimeConfiguration result;
        if(saved) {
            Path planPath=resolve(root.get("launch_plan_file"),file.getParent());custody.observe(planPath);
            NativeLaunchPlan decoded=NativeLaunchPlanCodec.read(planPath);
            if(ownerPlan!=null&&!NativeLaunchPlanCodec.describe(ownerPlan).equals(NativeLaunchPlanCodec.describe(decoded)))
                throw new IOException("loaded runtime configuration differs from the actual exact owner plan");
            NativeLaunchPlan samePlan=ownerPlan==null?decoded:ownerPlan;
            result=RootOrdinaryRuntimeConfiguration.readSaved(file,samePlan);
            result.initialPolicy().requireSavedHistory(samePlan);
        } else result=RootOrdinaryRuntimeConfiguration.read(file);
        custody.requireCurrent();return result;
        }
    }
    /** Retain the small configuration/plan/policy inputs through actual decoding; never carry these handles into Game. */
    private static final class InputCustody implements AutoCloseable {
        private final ArrayList<org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.ReadOnlyLease> leases=new ArrayList<>();
        private final ArrayList<SharedSourceFiles.Witness> inputs=new ArrayList<>();
        private SharedSourceFiles.Witness observe(Path file)throws IOException {
            var lease=org.xar.ck3.control.contracts.source.IdentityBearingFileAttributes.leaseBoundedWindows(file,MAXIMUM_BYTES);
            leases.add(lease);lease.releaseOriginalBytes();
            var result=SharedSourceFiles.observe(file);inputs.add(result);lease.verifyCurrent();return result;
        }
        private void requireCurrent()throws IOException {
            for(var lease:leases)lease.verifyCurrent();
            for(var input:inputs)SharedSourceFiles.assertUnchanged(input);
            for(var lease:leases)lease.verifyCurrent();
        }
        @Override public void close()throws IOException {
            IOException failure=null;
            for(int index=leases.size()-1;index>=0;index--)try{leases.get(index).close();}
            catch(IOException closing){if(failure==null)failure=closing;else if(failure!=closing)failure.addSuppressed(closing);}
            leases.clear();inputs.clear();if(failure!=null)throw failure;
        }
    }
    private static Path resolve(com.fasterxml.jackson.databind.JsonNode value,Path base) {
        Path path=Path.of(StrictJson.text(value));return(path.isAbsolute()?path:base.resolve(path)).normalize();
    }
    private static byte[] readBounded(Path file)throws IOException {
        byte[] bytes;try(var input=Files.newInputStream(file)){bytes=input.readNBytes(MAXIMUM_BYTES+1);}
        if(bytes.length<1||bytes.length>MAXIMUM_BYTES)throw new IOException("bounded nonempty runtime input required");return bytes;
    }
    private static boolean same(FileRef left,ExactRef right) {
        return left.path().equals(right.path())&&left.bytes()==right.bytes()&&left.sha256().equals(right.sha256());
    }
}
