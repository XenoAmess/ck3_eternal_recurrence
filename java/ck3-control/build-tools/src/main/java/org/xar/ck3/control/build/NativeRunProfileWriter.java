package org.xar.ck3.control.build;

import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Objects;
import java.util.jar.JarFile;
import org.xar.ck3.control.build.ControlBuild.FileRef;

/** Standalone typed thin entry into the original LS PROFILE/FORMAL_RELEASE bootstrap, without starting Quarkus/Core/Game.
 * All physical output remains in RootProfileBootstrapCommand/Inputs and its original finite issuer/Guard.
 * This bridge neither signs capacity nor implements another file writer or release registry. */
public final class NativeRunProfileWriter {
    static final String ORIGINAL_MAIN="org.xar.ck3.control.service.root.RootProfileBootstrapCommand";
    private static final List<String> REQUIRED=List.of(ORIGINAL_MAIN,
            "org.xar.ck3.control.service.root.RootProfileBootstrapInputs",
            "org.xar.ck3.control.service.root.RootBootstrapOutputGuard",
            "org.xar.ck3.control.service.root.RootBootstrapOutputContract");
    private NativeRunProfileWriter(){ }
    public enum Mode { PROFILE,FORMAL_RELEASE }
    public record Invocation(Mode mode,FileRef request,FileRef bootstrapBuild) {
        public Invocation {
            Objects.requireNonNull(mode);NativeRunProfileManifest.file(request,65536);
            NativeRunProfileManifest.file(bootstrapBuild,ControlBuild.BUILD_RECEIPT_ENVELOPE_MAX_BYTES);
        }
        /** Sole finite standalone argv producer; actual execution still reopens request/build and checks deployment. */
        public List<String> exactArguments(){
            return List.of(mode.name(),request.path(),Long.toString(request.bytes()),request.sha256(),
                    bootstrapBuild.path(),Long.toString(bootstrapBuild.bytes()),bootstrapBuild.sha256());
        }
        public List<String> originalArguments() {
            return List.of(mode.name(),request.path(),Long.toString(request.bytes()),request.sha256());
        }
    }

    /** Only real completed SERVICE_FAST_JAR deployment can supply the original guarded static bootstrap. */
    public static void write(Invocation invocation)throws IOException {
        Objects.requireNonNull(invocation);
        var request=SharedSourceFiles.observe(Path.of(invocation.request().path()));
        if(!request.source().equals(invocation.request()))throw new IOException("actual bootstrap request differs from its exact source");
        var actual=ControlBuild.verifiedCompletedReceipt(invocation.bootstrapBuild());
        if(actual.targetKind()!=ControlBuild.TargetKind.SERVICE_FAST_JAR
                ||!actual.machineId().equals(WindowsJobProcess.currentMachineId()))
            throw new IOException("actual completed same-machine Host fast-JAR bootstrap deployment required");
        ClassLoader loader=NativeRunProfileWriter.class.getClassLoader();Class<?> command=null;
        requireDeployed(NativeRunProfileWriter.class,actual);
        for(String name:requiredClasses(invocation.mode())) {
            final Class<?> type;
            try {type=Class.forName(name,false,loader);}
            catch(ClassNotFoundException|LinkageError missing) {throw new IOException("original guarded bootstrap dependency unavailable: "+name,missing);}
            requireDeployed(type,actual);
            if(name.equals(ORIGINAL_MAIN))command=type;
        }
        SharedSourceFiles.assertUnchanged(request);
        for(FileRef file:actual.completeDeployment())file.verify();
        final Method original;
        try {
            original=Objects.requireNonNull(command).getMethod("main",String[].class);
            if(original.getReturnType()!=void.class||!java.lang.reflect.Modifier.isStatic(original.getModifiers()))
                throw new IOException("original bootstrap must retain public static void main(String[])");
        }
        catch(ReflectiveOperationException missing) {throw new IOException("original guarded bootstrap main is unavailable",missing);}
        try {
            // Both explicit modes enter the identical original CLI, preserving stdin/independent issuer.
            // Its existing finite Guard alone writes/readbacks formal payloads or ordinary profile assets.
            original.invoke(null,(Object)invocation.originalArguments().toArray(String[]::new));
        }catch(IllegalAccessException invalid) {throw new IOException("original guarded bootstrap main is inaccessible",invalid);}
        catch(InvocationTargetException failed) {
            Throwable cause=failed.getCause();
            if(cause instanceof IOException io)throw io;
            throw new IOException("original guarded bootstrap failed",cause);
        }
        SharedSourceFiles.assertUnchanged(request);
    }
    private static void requireDeployed(Class<?> type,ControlBuild.BuildReceipt build)throws IOException {
        String source=type.getSimpleName()+".java";
        if(build.compiledSourcePins().stream().filter(ref->Path.of(ref.path()).getFileName().toString().equals(source)).count()!=1)
            throw new IOException("original bootstrap class lacks its sole actual compiled source: "+type.getName());
        if(type.getProtectionDomain()==null||type.getProtectionDomain().getCodeSource()==null)
            throw new IOException("actual bootstrap CodeSource required: "+type.getName());
        final Path archive;
        try {archive=Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()).toRealPath();}
        catch(java.net.URISyntaxException invalid) {throw new IOException("invalid original bootstrap CodeSource",invalid);}
        if(!Files.isRegularFile(archive)||!build.completeDeployment().contains(FileRef.measure(archive)))
            throw new IOException("bootstrap must load from an exact JAR in the actual completed Host deployment");
        try(var jar=new JarFile(archive.toFile(),false)) {
            if(jar.getJarEntry(type.getName().replace((char)46,(char)47)+".class")==null)
                throw new IOException("actual bootstrap JAR omitted its loaded class");
        }
    }
    static List<String> requiredClasses(Mode mode){
        Objects.requireNonNull(mode);if(mode==Mode.PROFILE)return REQUIRED;
        var names=new java.util.ArrayList<String>(REQUIRED);
        names.add(FormalReleaseProducer.class.getName());names.add(FormalReleaseGit.class.getName());
        names.add(FormalReleaseDescriptor.class.getName());names.add(NativeRunProfileManifest.class.getName());
        return List.copyOf(names);
    }
    /** Explicit original LS mode then exact request3 and actual completed Host-build3; no inferred mode or alias. */
    static Invocation argument(String[] args)throws IOException {
        if(args.length!=7)throw new IOException("expected PROFILE|FORMAL_RELEASE, exact bootstrap-request3 and completed Host-build3");
        final Mode mode;try{mode=Mode.valueOf(args[0]);}
        catch(IllegalArgumentException invalid){throw new IOException("explicit PROFILE or FORMAL_RELEASE mode required",invalid);}
        return new Invocation(mode,exact(args,1,65536),exact(args,4,ControlBuild.BUILD_RECEIPT_ENVELOPE_MAX_BYTES));
    }
    private static FileRef exact(String[] args,int offset,long maximum)throws IOException {
        final long bytes;try {bytes=Long.parseLong(args[offset+1]);}
        catch(NumberFormatException invalid) {throw new IOException("canonical positive source byte count required",invalid);}
        if(bytes<1||bytes>maximum||!Long.toString(bytes).equals(args[offset+1]))
            throw new IOException("bounded canonical positive exact-source byte count required");
        try {NativeRunProfileManifest.absolute(args[offset]);return new FileRef(args[offset],bytes,args[offset+2]);}
        catch(IllegalArgumentException invalid) {throw new IOException("normalized absolute exact source required",invalid);}
    }
    public static void main(String[] args) {
        try {write(argument(args));}
        catch(Exception unavailable) {
            System.err.println("NATIVE_PROFILE_BOOTSTRAP_UNAVAILABLE: "+unavailable.getClass().getSimpleName()+": "+unavailable.getMessage());
            System.exit(2);
        }
    }
}

