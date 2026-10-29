package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.jar.JarFile;
import org.xar.ck3.control.build.ControlBuild;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.service.root.RootBootstrapProtocol.ClassOrigin;
import org.xar.ck3.control.service.root.RootBootstrapProtocol.Mode;

/** Complete genuine deployments and actual same-child class origins. Classpath order alone is never qualification. */
public final class RootBootstrapRuntime {
    private RootBootstrapRuntime(){ }
    public enum Role { TOOLS,SERVICE }
    public record ClassBinding(String className,Role role,FileRef compiledSource) {
        public ClassBinding {java.util.Objects.requireNonNull(className);java.util.Objects.requireNonNull(role);java.util.Objects.requireNonNull(compiledSource);}
    }
    public record Request(FileRef toolsBuild,FileRef serviceBuild,FileRef javaExecutable,List<FileRef> classpath,List<ClassBinding> classes) {
        public Request {java.util.Objects.requireNonNull(toolsBuild);java.util.Objects.requireNonNull(serviceBuild);java.util.Objects.requireNonNull(javaExecutable);
            classpath=List.copyOf(classpath);classes=List.copyOf(classes);
            RootBootstrapProtocol.require(!classpath.isEmpty()&&classpath.size()<=2048&&classpath.stream().distinct().count()==classpath.size(),"bounded distinct exact archives required");}
    }
    private static final List<String> TOOLS=List.of("ControlBuild","NativeRunProfileProducer","NativeRunProfileManifest","SharedSourceFiles","WindowsJobProcess","ProjectStoragePolicy","NativeRunProfileRules","NativeStorageGeometry","SharedOwnedCommand","SharedOwnedCommandBinding","CiBootstrap","JavaUtf8NativeCustody","Win32StdioPipes");
    private static final List<String> FORMAL=List.of("FormalReleaseProducer","FormalReleaseGit","FormalReleaseDescriptor");
    private static final List<String> LOCAL=List.of("RootProfileBootstrapSession","RootBootstrapProtocol","RootBootstrapRuntime","RootProfileBootstrapCommand",
            "RootBootstrapDuplex","RootBootstrapFileReply","RootProfileBootstrapInputs","RootBootstrapOutputGuard","RootBootstrapOutputContract","RootBootstrapAssetTree","RootRuntimeDefinitions");
    private static final List<String> DEPENDENCIES=List.of("com.fasterxml.jackson.databind.ObjectMapper","com.fasterxml.jackson.core.JsonFactory",
            "com.fasterxml.jackson.annotation.JsonInclude","com.sun.jna.Native","com.sun.jna.platform.win32.Kernel32");
    public static List<String> requiredClasses(Mode mode){
        var names=new ArrayList<String>();for(String name:TOOLS)names.add("org.xar.ck3.control.build."+name);
        if(mode==Mode.FORMAL_RELEASE)for(String name:FORMAL)names.add("org.xar.ck3.control.build."+name);
        if(mode==Mode.ORIGINAL_DRIVER_RUN_PROFILE){names.add("org.xar.ck3.control.service.root.RootOriginalDriverRunProfileProducer");names.add("org.xar.ck3.control.service.root.RootFrozenRunProfile");}
        if(mode==Mode.NORMAL_EXIT){names.add("org.xar.ck3.control.platform.NormalExitSourceInventory");names.add("org.xar.ck3.control.platform.NativeLaunchPlan");names.add("org.xar.ck3.control.platform.NativeBridgeLaunchEvidence");}
        for(String name:LOCAL)names.add("org.xar.ck3.control.service.root."+name);
        names.add("org.xar.ck3.control.build.RootBootstrapSessionScope");
        names.add("org.xar.ck3.control.application.checkpoint.NativeCheckpointFiles");
        names.add("org.xar.ck3.control.contracts.StrictJson");return List.copyOf(names);
    }
    public static List<FileRef> verify(Request request,Mode mode)throws IOException {
        var tools=ControlBuild.verifiedCompletedReceipt(request.toolsBuild());
        var service=ControlBuild.verifiedCompletedReceipt(request.serviceBuild());
        if(tools.targetKind()!=ControlBuild.TargetKind.BUILD_TOOLS_RUNTIME||service.targetKind()!=ControlBuild.TargetKind.SERVICE_FAST_JAR)
            throw new IOException("genuine completed Tools and SERVICE deployments required");
        if(!service.javaExecutableRef().equals(request.javaExecutable()))throw new IOException("child Java must be the actual qualified SERVICE Java executable");
        request.javaExecutable().verify();
        var accepted=new LinkedHashSet<FileRef>();if(mode==Mode.PROFILE)accepted.addAll(archives(tools));accepted.addAll(archives(service));
        if(!accepted.equals(new LinkedHashSet<>(request.classpath())))throw new IOException("child classpath must contain all exact qualified archives for its mode");
        var names=request.classes().stream().map(ClassBinding::className).toList();
        if(names.size()!=requiredClasses(mode).size()||!Set.copyOf(names).equals(Set.copyOf(requiredClasses(mode))))
            throw new IOException("closed complete class/source binding set required");
        for(var binding:request.classes()){
            boolean toolClass=TOOLS.stream().anyMatch(n->binding.className().equals("org.xar.ck3.control.build."+n));
            Role expected=mode==Mode.PROFILE&&toolClass?Role.TOOLS:Role.SERVICE;
            var receipt=expected==Role.TOOLS?tools:service;
            String sourceName=binding.className().replace('.','/')+".java";
            if(binding.role()!=expected||!binding.compiledSource().path().replace('\\','/').endsWith("/"+sourceName)
                    ||!receipt.compiledSourcePins().contains(binding.compiledSource()))throw new IOException("actual compiled source is not a member of its genuine owner receipt: "+binding.className());
            binding.compiledSource().verify();
        }
        List<FileRef> effective=effectiveClasspath(request.classpath(),accepted);var providers=providers(effective);
        // Census every top-level/nest Tools provider, including classes not yet resolved by the VM.
        // Duplicate archives are intentional between the two deployments; the selected provider must match its mode.
        List<FileRef> expectedTools=mode==Mode.PROFILE?archives(tools):archives(service);
        for(FileRef archive:expectedTools)try(var jar=new JarFile(Path.of(archive.path()).toFile(),true,JarFile.OPEN_READ,Runtime.version())){
            var entries=jar.entries();while(entries.hasMoreElements()){
                String name=entries.nextElement().getName();
                if(name.startsWith("org/xar/ck3/control/build/")&&name.endsWith(".class")){
                    String className=name.substring(0,name.length()-6).replace('/','.');
                    if(!expectedTools.contains(providers.get(className)))throw new IOException("qualified Tools provider shadowed for mode: "+className);
                }
            }
        }
        if(mode==Mode.PROFILE){
            var toolArchives=archives(tools);for(String name:TOOLS){
                FileRef provider=providers.get("org.xar.ck3.control.build."+name);
                if(!toolArchives.contains(provider))throw new IOException("PROFILE Tools class shadowed outside qualified flat Tools: "+name);
            }
        }
        return effective;
    }
    public static void verifyParent(Request request)throws Exception {
        var service=ControlBuild.verifiedCompletedReceipt(request.serviceBuild());
        for(Class<?> type:List.of(RootProfileBootstrapSession.class,RootBootstrapRuntime.class,ControlBuild.class,
                org.xar.ck3.control.build.RootBootstrapSessionScope.class,org.xar.ck3.control.build.SharedOwnedCommand.class)){
            FileRef actual=FileRef.measure(Path.of(type.getProtectionDomain().getCodeSource().getLocation().toURI()));
            if(!service.completeDeployment().contains(actual))throw new IOException("parent Session requires one qualified SERVICE class-loader context");
        }
        samePackageLoader();
    }
    public static List<ClassOrigin> observeInChild(Request request,Mode mode)throws Exception {
        var effective=verify(request,mode);var tools=ControlBuild.verifiedCompletedReceipt(request.toolsBuild());
        var service=ControlBuild.verifiedCompletedReceipt(request.serviceBuild());var result=new ArrayList<ClassOrigin>();
        ClassLoader loader=RootBootstrapRuntime.class.getClassLoader();var providers=providers(effective);
        for(var binding:request.classes()){
            Class<?> actual=Class.forName(binding.className(),false,loader);
            var source=actual.getProtectionDomain().getCodeSource();
            if(source==null)throw new IOException("child class has no actual archive origin");
            FileRef archive=FileRef.measure(Path.of(source.getLocation().toURI()));
            var receipt=binding.role()==Role.TOOLS?tools:service;
            if(!receipt.completeDeployment().contains(archive)||!ObjectsEqual(providers.get(binding.className()),archive))
                throw new IOException("actual child CodeSource differs from qualified provider census: "+binding.className());
            result.add(new ClassOrigin(binding.className(),archive));
        }
        for(String name:DEPENDENCIES){
            Class<?> actual=Class.forName(name,false,loader);FileRef archive=FileRef.measure(Path.of(actual.getProtectionDomain().getCodeSource().getLocation().toURI()));
            if(!ObjectsEqual(providers.get(name),archive))throw new IOException("actual child dependency origin differs from qualified provider census: "+name);
            result.add(new ClassOrigin(name,archive));
        }
        samePackageLoader();
        if(mode==Mode.PROFILE&&!Set.copyOf(ControlBuild.producerClosure()).equals(Set.copyOf(tools.completeDeployment())))
            throw new IOException("actual child ControlBuild producer closure is not the qualified flat Tools runtime");
        return List.copyOf(result);
    }
    public static void verifyObservation(Request request,Mode mode,List<ClassOrigin> origins)throws IOException {
        var providers=providers(verify(request,mode));var names=new ArrayList<>(request.classes().stream().map(ClassBinding::className).toList());names.addAll(DEPENDENCIES);
        if(origins.size()!=names.size())throw new IOException("child origin observation incomplete");
        for(int i=0;i<origins.size();i++)if(!origins.get(i).className().equals(names.get(i))
                ||!origins.get(i).archive().equals(providers.get(origins.get(i).className())))throw new IOException("child origin observation differs from exact qualified census");
    }
    public static ClassOrigin observeCarrier(Request request)throws Exception {
        Class<?> actual=Class.forName("org.xar.ck3.control.build.CiBootstrap",false,ClassLoader.getSystemClassLoader());
        var origin=new ClassOrigin(actual.getName(),FileRef.measure(Path.of(actual.getProtectionDomain().getCodeSource().getLocation().toURI())));
        verifyCarrier(request,origin);return origin;
    }
    public static void verifyCarrier(Request request,ClassOrigin origin)throws IOException {
        String name="org.xar.ck3.control.build.CiBootstrap";
        var tools=ControlBuild.verifiedCompletedReceipt(request.toolsBuild());
        if(!name.equals(origin.className())||!provider(archives(tools),name).equals(origin.archive()))throw new IOException("actual system-loader sole Java carrier differs from qualified Tools");
    }
    public static List<FileRef> retained(Request request)throws IOException {
        var result=new LinkedHashSet<FileRef>();result.add(request.toolsBuild());result.add(request.serviceBuild());result.add(request.javaExecutable());
        result.addAll(ControlBuild.verifiedCompletedReceipt(request.toolsBuild()).completeDeployment());
        result.addAll(ControlBuild.verifiedCompletedReceipt(request.serviceBuild()).completeDeployment());
        for(var binding:request.classes())result.add(binding.compiledSource());return List.copyOf(result);
    }
    private static List<FileRef> archives(ControlBuild.BuildReceipt receipt){return receipt.completeDeployment().stream().filter(r->r.path().endsWith(".jar")).toList();}
    static List<FileRef> effectiveClasspath(List<FileRef> classpath,Set<FileRef> accepted)throws IOException {
        var result=new ArrayList<FileRef>();var seen=new LinkedHashSet<FileRef>();
        for(FileRef ref:classpath)visit(ref,accepted,seen,result);return List.copyOf(result);
    }
    private static void visit(FileRef ref,Set<FileRef> accepted,Set<FileRef> seen,List<FileRef> result)throws IOException {
        if(!accepted.contains(ref)||!ref.path().endsWith(".jar"))throw new IOException("recursive JAR Class-Path escaped qualified archive closure");
        if(!seen.add(ref))return;if(seen.size()>2048)throw new IOException("bounded archive closure exceeded");ref.verify();result.add(ref);
        try(var jar=new JarFile(Path.of(ref.path()).toFile(),true,JarFile.OPEN_READ,Runtime.version())){
            var manifest=jar.getManifest();String cp=manifest==null?null:manifest.getMainAttributes().getValue("Class-Path");
            if(cp!=null)for(String name:cp.trim().split("\\s+"))if(!name.isEmpty()){
                java.net.URI uri=Path.of(ref.path()).toUri().resolve(name);
                if(!"file".equalsIgnoreCase(uri.getScheme())||uri.getFragment()!=null||uri.getQuery()!=null)throw new IOException("plain exact JAR manifest dependency required");
                Path path=Path.of(uri).toAbsolutePath().normalize();FileRef dependency=accepted.stream().filter(r->Path.of(r.path()).toAbsolutePath().normalize().equals(path)).findFirst().orElseThrow(()->new IOException("unqualified manifest dependency: "+path));
                visit(dependency,accepted,seen,result);
            }
        }
    }
    static FileRef provider(List<FileRef> effective,String className)throws IOException {
        String entry=className.replace('.','/')+".class";
        for(FileRef ref:effective)try(var jar=new JarFile(Path.of(ref.path()).toFile(),true,JarFile.OPEN_READ,Runtime.version())){
            if(jar.getJarEntry(entry)!=null)return ref;
        }
        throw new IOException("required class absent from qualified complete archives: "+className);
    }
    private static java.util.Map<String,FileRef> providers(List<FileRef> effective)throws IOException {
        var result=new java.util.LinkedHashMap<String,FileRef>();
        for(FileRef ref:effective)try(var jar=new JarFile(Path.of(ref.path()).toFile(),true,JarFile.OPEN_READ,Runtime.version());var entries=jar.versionedStream()){
            entries.filter(entry->entry.getName().endsWith(".class")).forEach(entry->{String name=entry.getName();
                if(!name.startsWith("META-INF/"))result.putIfAbsent(name.substring(0,name.length()-6).replace('/','.'),ref);});
        }return java.util.Map.copyOf(result);
    }
    private static boolean ObjectsEqual(Object left,Object right){return java.util.Objects.equals(left,right);}
    private static void samePackageLoader()throws IOException {
        Class<?> scope=org.xar.ck3.control.build.RootBootstrapSessionScope.class;
        for(Class<?> type:List.of(org.xar.ck3.control.build.SharedOwnedCommand.class,org.xar.ck3.control.build.SharedOwnedCommandBinding.class,org.xar.ck3.control.build.CiBootstrap.class))
            if(scope.getClassLoader()!=type.getClassLoader()||scope.getPackage().isSealed()||type.getPackage().isSealed())throw new IOException("Session read-only package seam requires one unsealed defining loader");
    }
}
