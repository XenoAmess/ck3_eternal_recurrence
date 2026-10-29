package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import org.xar.ck3.control.build.ControlBuild.FileRef;
import org.xar.ck3.control.build.FormalReleaseGit;
import org.xar.ck3.control.build.FormalReleaseProducer;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.build.ProjectStoragePolicy;
import org.xar.ck3.control.build.WindowsJobProcess;

/** Genuine private Prepared fixture through the actual managed Git producer, for the existing LS writer tests.
 * Missing explicit data-volume/Git configuration fails; no skip, fake Prepared, cached clean or Python path.
 */
public final class FormalReleaseTestFixture implements AutoCloseable {
    private static final byte[] REGISTRY=Base64.getDecoder().decode("IiIiRGVyaXZlIENLMyBXb3Jrc2hvcCBjb21wYXRpYmlsaXR5IHRhZ3MgZnJvbSBhIHJlbGVhc2Ugc3RhZ2luZyBkZXNjcmlwdG9yLgoKVGhlc2UgYXJlIG9yZGluYXJ5IFN0ZWFtIFdvcmtzaG9wIHRhZ3MuIEEgZGVzY3JpcHRvciB2ZXJzaW9uIGlzIGEgbWV0YWRhdGEKY2xhaW07IHRoaXMgaGVscGVyIGRvZXMgbm90IGVzdGFibGlzaCBnYW1lcGxheSBhY2NlcHRhbmNlIG9yIGF1dGhvcml6ZSB1cGxvYWQuCkF1dG9tYXRpYyB0YWdnaW5nIHN0YXJ0cyBhdCBDSzMgMS4yMC4gT2xkZXIgdmVyc2lvbnMgcHJlc2VydmUgdGhlaXIgdGFncy4gQWRkCmZ1dHVyZSBsYWJlbHMgb25seSBhZnRlciBjb25maXJtaW5nIHRoZSBnYW1lJ3MgYWN0dWFsIFdvcmtzaG9wIGZpbHRlci4KIiIiCgpmcm9tIF9fZnV0dXJlX18gaW1wb3J0IGFubm90YXRpb25zCgpmcm9tIHBhdGhsaWIgaW1wb3J0IFBhdGgKaW1wb3J0IHJlCmZyb20gdHlwaW5nIGltcG9ydCBTZXF1ZW5jZQoKCiMgU2luZ2xlIHJlZ2lzdHJ5IGZvciBib3RoIG5hdGl2ZSBwdWJsaWNhdGlvbiBhbmQgc3RhZ2luZyBkZXNjcmlwdG9yIHJlbmRlcmluZy4KIyBGdXR1cmUgY29uZmlybWVkIG1pbm9ycyBuZWVkIG9ubHkgYSBuZXcgZW50cnkgaGVyZTsgY29uc3VtZXJzIHJlbWFpbiB1bmNoYW5nZWQuCkNLM19XT1JLU0hPUF9WRVJTSU9OX1RBR1MgPSB7IjEuMjAiOiAiMS4yMCAnQ3JvemllcicifQpfU1VQUE9SVEVEX1ZFUlNJT04gPSByZS5jb21waWxlKAogICAgcideXHMqc3VwcG9ydGVkX3ZlcnNpb25ccyo9XHMqIihbXiJcclxuXSspIlxzKig/OiMuKik/JCcsCiAgICByZS5NVUxUSUxJTkUsCikKX1ZFUlNJT05fQVNTSUdOTUVOVCA9IHJlLmNvbXBpbGUociJeXHMqc3VwcG9ydGVkX3ZlcnNpb25ccyo9IiwgcmUuTVVMVElMSU5FKQpfVkVSU0lPTiA9IHJlLmNvbXBpbGUociIoWzAtOV0rKVwuKFswLTldKykoPzpcLig/OlswLTldK3xcKikpezAsMn0iKQpfQ09NUEFUSUJJTElUWV9UQUcgPSByZS5jb21waWxlKHIiWzAtOV0rXC5bMC05XSsoPzogJ1teJ1xyXG5dKycpPyIpCgoKZGVmIGNvbXBhdGliaWxpdHlfdGFnX2Zyb21fZGVzY3JpcHRvcihkZXNjcmlwdG9yOiBzdHIpIC0+IHN0ciB8IE5vbmU6CiAgICAiIiJSZXR1cm4gdGhlIGNvbmZpcm1lZCBXb3Jrc2hvcCB0YWcsIG9yIE5vbmUgZm9yIHZlcnNpb25zIGJlZm9yZSAxLjIwLgoKICAgIFRoZSB2ZXJzaW9uIG1heSBzcGVjaWZ5IGEgbWlub3IsIG51bWVyaWMgcGF0Y2gvYnVpbGQgb3IgQ0szIHdpbGRjYXJkLiBNaXNzaW5nLAogICAgZHVwbGljYXRlLCBtYWxmb3JtZWQgYW5kIHVubWFwcGVkIDEuMjArIHZhbHVlcyBmYWlsIGJlZm9yZSBhbnkgcmVtb3RlIG9wZXJhdGlvbi4KICAgICIiIgogICAgaWYgbm90IGlzaW5zdGFuY2UoZGVzY3JpcHRvciwgc3RyKToKICAgICAgICByYWlzZSBWYWx1ZUVycm9yKCJkZXNjcmlwdG9yIG11c3QgYmUgdGV4dCIpCiAgICBkZXNjcmlwdG9yID0gZGVzY3JpcHRvci5sc3RyaXAoIlx1ZmVmZiIpCiAgICB2ZXJzaW9ucyA9IF9TVVBQT1JURURfVkVSU0lPTi5maW5kYWxsKGRlc2NyaXB0b3IpCiAgICBpZiBsZW4odmVyc2lvbnMpICE9IDEgb3IgbGVuKF9WRVJTSU9OX0FTU0lHTk1FTlQuZmluZGFsbChkZXNjcmlwdG9yKSkgIT0gMToKICAgICAgICByYWlzZSBWYWx1ZUVycm9yKCJkZXNjcmlwdG9yIG11c3QgY29udGFpbiBleGFjdGx5IG9uZSBzdXBwb3J0ZWRfdmVyc2lvbiIpCiAgICB2ZXJzaW9uID0gX1ZFUlNJT04uZnVsbG1hdGNoKHZlcnNpb25zWzBdKQogICAgaWYgdmVyc2lvbiBpcyBOb25lOgogICAgICAgIHJhaXNlIFZhbHVlRXJyb3IoZiJpbnZhbGlkIHN1cHBvcnRlZF92ZXJzaW9uOiB7dmVyc2lvbnNbMF0hcn0iKQogICAgbWlub3JfdmVyc2lvbiA9IChpbnQodmVyc2lvbi5ncm91cCgxKSksIGludCh2ZXJzaW9uLmdyb3VwKDIpKSkKICAgIGlmIG1pbm9yX3ZlcnNpb24gPCAoMSwgMjApOgogICAgICAgIHJldHVybiBOb25lCiAgICBtaW5vciA9IGYie21pbm9yX3ZlcnNpb25bMF19LnttaW5vcl92ZXJzaW9uWzFdfSIKICAgIHRyeToKICAgICAgICByZXR1cm4gQ0szX1dPUktTSE9QX1ZFUlNJT05fVEFHU1ttaW5vcl0KICAgIGV4Y2VwdCBLZXlFcnJvcjoKICAgICAgICByYWlzZSBWYWx1ZUVycm9yKAogICAgICAgICAgICBmIm5vIGNvbmZpcm1lZCBDSzMgV29ya3Nob3AgY29tcGF0aWJpbGl0eSB0YWcgZm9yIHttaW5vcn07ICIKICAgICAgICAgICAgImNvbmZpcm0gdGhlIG9mZmljaWFsIHZlcnNpb24gbGFiZWwgYmVmb3JlIHB1Ymxpc2hpbmciCiAgICAgICAgKSBmcm9tIE5vbmUKCgpkZWYgY29tcGF0aWJpbGl0eV90YWdzX2Zvcl9zdGFnaW5nKAogICAgc3RhZ2luZ19kaXI6IFBhdGggfCBzdHIsIHRhZ3M6IFNlcXVlbmNlW3N0cl0KKSAtPiB0dXBsZVtzdHIsIC4uLl06CiAgICAiIiJSZXBsYWNlIHZlcnNpb24gdGFncyB3aGlsZSBwcmVzZXJ2aW5nIGV2ZXJ5IG90aGVyIHRhZyBhbmQgaXRzIG9yZGVyLgoKICAgIFJlYWQgb25seSB0aGUgYWN0dWFsIHN0YWdpbmcgZGVzY3JpcHRvci4gRG8gbm90IHVzZSB0aGUgZGV2ZWxvcG1lbnQgdHJlZSBvcgogICAgY2hhbmdlIGEgZGVzY3JpcHRvciwgY29udGVudCBmaWxlLCBkZXNjcmlwdGlvbiBvciBDaGFuZ2UgTm90ZXMuCiAgICAiIiIKICAgIGlmIGlzaW5zdGFuY2UodGFncywgKHN0ciwgYnl0ZXMpKSBvciBub3QgaXNpbnN0YW5jZSh0YWdzLCBTZXF1ZW5jZSk6CiAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigidGFncyBtdXN0IGJlIGEgc2VxdWVuY2Ugb2Ygbm9uLWVtcHR5IHN0cmluZ3MiKQogICAgaWYgYW55KG5vdCBpc2luc3RhbmNlKHRhZywgc3RyKSBvciBub3QgdGFnIGZvciB0YWcgaW4gdGFncyk6CiAgICAgICAgcmFpc2UgVmFsdWVFcnJvcigidGFncyBtdXN0IGJlIGEgc2VxdWVuY2Ugb2Ygbm9uLWVtcHR5IHN0cmluZ3MiKQogICAgZGVzY3JpcHRvciA9IFBhdGgoc3RhZ2luZ19kaXIpIC8gImRlc2NyaXB0b3IubW9kIgogICAgbGFiZWwgPSBjb21wYXRpYmlsaXR5X3RhZ19mcm9tX2Rlc2NyaXB0b3IoZGVzY3JpcHRvci5yZWFkX3RleHQoZW5jb2Rpbmc9InV0Zi04LXNpZyIpKQogICAgaWYgbGFiZWwgaXMgTm9uZToKICAgICAgICByZXR1cm4gdHVwbGUodGFncykKICAgIHJldGFpbmVkID0gdHVwbGUodGFnIGZvciB0YWcgaW4gdGFncyBpZiBfQ09NUEFUSUJJTElUWV9UQUcuZnVsbG1hdGNoKHRhZykgaXMgTm9uZSkKICAgIHJldHVybiByZXRhaW5lZCArIChsYWJlbCwpCg==");
    private final Path root;private final FormalReleaseGit.Session git;private final FormalReleaseProducer.Prepared actual;
    private FormalReleaseTestFixture(Path root,FormalReleaseGit.Session git,FormalReleaseProducer.Prepared actual){this.root=root;this.git=git;this.actual=actual;}
    public Path root(){return root;}
    public FormalReleaseProducer.Prepared actual(){return actual;}
    public static FormalReleaseTestFixture create(FormalReleaseProducer.Mode mode)throws Exception{
        return create(mode,0,0);
    }
    public static FormalReleaseTestFixture create(FormalReleaseProducer.Mode mode,int extraFiles,int largeLeafBytes)throws Exception{
        return create(mode,extraFiles,largeLeafBytes,FormalReleaseProducer.Layout.DIRECT_STAGING);
    }
    public static FormalReleaseTestFixture create(FormalReleaseProducer.Mode mode,int extraFiles,int largeLeafBytes,FormalReleaseProducer.Layout layout)throws Exception{
        if(extraFiles<0||extraFiles>200||largeLeafBytes<0||largeLeafBytes>2<<20)throw new IllegalArgumentException("finite integration fixture shape required");
        String configuredRoot=System.getProperty("xar.formalReleaseTestRoot"),configuredGit=System.getProperty("xar.formalReleaseGitExecutable");
        if(configuredRoot==null||configuredGit==null)throw new IOException("explicit xar.formalReleaseTestRoot and xar.formalReleaseGitExecutable required");
        String storageFlag=System.getProperty(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK);
        if(storageFlag==null)storageFlag=System.getenv(ProjectStoragePolicy.FORBID_SYSTEM_VOLUME_BULK);
        if(!"true".equals(storageFlag)&&!"false".equals(storageFlag))
            throw new IOException("explicit valid XAR_PROJECT_FORBID_SYSTEM_VOLUME_BULK required before fixture files or Git children");
        Path parent=Path.of(configuredRoot),gitExecutable=Path.of(configuredGit);
        if(!parent.isAbsolute()||!parent.normalize().equals(parent)||!Files.isDirectory(parent,LinkOption.NOFOLLOW_LINKS))
            throw new IOException("existing normalized explicit test root required");
        SharedSourceFiles.plainAncestors(parent);
        Path system=Path.of(System.getenv("SystemRoot"));
        if(Files.getFileStore(parent).equals(Files.getFileStore(system)))throw new IOException("formal release integration fixture must remain off system volume");
        Path root=Files.createTempDirectory(parent,"formal-release-chain-"),repository=root.resolve("repository");
        Files.createDirectory(repository);Path source=repository.resolve("XenoAmess_s_Eternal_Recurrence");
        for(String relative:List.of("common/scripted_effects","events","gfx","gui","localization"))Files.createDirectories(source.resolve(relative));
        Files.writeString(source.resolve("descriptor.mod"),"version=\"1.0.2\"\nsupported_version=\"1.20.0.3\"\ntags={ \"Gameplay\" \"1.19 'Basileus'\" }\nname=\"fixture\"\n",StandardCharsets.UTF_8);
        Files.write(source.resolve("thumbnail.png"),new byte[]{1,2,3});
        Files.createDirectories(source.resolve("gfx/interface/icons/traits"));
        Files.write(source.resolve("gfx/interface/icons/traits/_stars_10.dds"),new byte[]{1,2,3});
        Files.writeString(source.resolve("common/scripted_effects/actual.txt"),"real=yes\n# XAR_ACCEPTANCE_ONLY_BEGIN\nxar_selftest=yes\n# XAR_ACCEPTANCE_ONLY_END\n",StandardCharsets.UTF_8);
        Files.writeString(source.resolve("events/xar_acceptance_events.txt"),"xar_acceptance_removed=yes\n",StandardCharsets.UTF_8);
        for(int index=0;index<extraFiles;index++){Path extra=source.resolve("common/fixture/branch"+index+"/actual"+index+".txt");
            Files.createDirectories(extra.getParent());Files.writeString(extra,"actual="+index+"\n",StandardCharsets.UTF_8);}
        if(largeLeafBytes>0)Files.write(source.resolve("gfx/large.dds"),new byte[largeLeafBytes]);
        Path registry=repository.resolve("ck3_workshop_mcp/src/ck3_workshop_mcp/compatibility_tags.py");
        Files.createDirectories(registry.getParent());Files.write(registry,REGISTRY);
        FileRef gitOriginal=FileRef.measure(gitExecutable);Path setup=Files.createDirectory(root.resolve("git-setup"));
        var setupCommands=List.of(List.of("init","--quiet","--object-format=sha1"),List.of("add","--","."),
                List.of("-c","user.name=Formal Release Fixture","-c","user.email=formal-fixture@example.invalid","commit","--quiet","-m","fixture"),
                List.of("tag","v1.0.2"));
        for(int index=0;index<setupCommands.size();index++)setup(gitOriginal,repository,setup,index,setupCommands.get(index));
        Path commandRoot=Files.createDirectory(root.resolve("git-observations"));
        Path outputRoot=layout==FormalReleaseProducer.Layout.DIRECT_STAGING?root.resolve("direct-staging"):root.resolve("isolated-state");
        Files.createDirectory(outputRoot);
        Path production=layout==FormalReleaseProducer.Layout.DIRECT_STAGING?outputRoot.resolve("xar-production"):outputRoot.resolve("profile/mod-content/xar-production");
        var request=new FormalReleaseProducer.Request(FormalReleaseProducer.REQUEST_SCHEMA,WindowsJobProcess.currentMachineId(),
                Instant.now().plusSeconds(600).toString(),repository,source,outputRoot,production,
                outputRoot.resolve("xar-production.manifest.json"),mode,layout);
        var execution=new FormalReleaseGit.Execution(request.machineId(),request.reviewAtUtc(),repository,gitOriginal,commandRoot,64L<<20);
        var session=FormalReleaseGit.open(execution);
        try{return new FormalReleaseTestFixture(root,session,FormalReleaseProducer.prepare(request,session,Clock.systemUTC()));}
        catch(Exception failure){session.close();throw failure;}
    }
    private static void setup(FileRef git,Path repository,Path logs,int index,List<String> command)throws Exception{
        git.verify();Path stdout=logs.resolve(index+".stdout"),stderr=logs.resolve(index+".stderr");
        var arguments=new ArrayList<String>(List.of("--no-pager","-c","core.autocrlf=false","-c","core.fsmonitor=false","-C",repository.toString()));
        arguments.addAll(command);var environment=new java.util.TreeMap<String,String>(System.getenv());
        environment.keySet().removeIf(key->key.toUpperCase(java.util.Locale.ROOT).startsWith("GIT_"));
        environment.put("GIT_TERMINAL_PROMPT","0");environment.put("LC_ALL","C");
        var spec=new WindowsJobProcess.CommandSpec(Path.of(git.path()),arguments,repository,environment,stdout,stderr,64L<<20);
        WindowsJobProcess.CommandResult terminal;
        try(var child=WindowsJobProcess.start(spec)){terminal=child.await(Duration.ofSeconds(30),Instant.now().plusSeconds(60),()->{
            try{git.verify();for(Path path:List.of(stdout,stderr))if(Files.exists(path)&&Files.size(path)>65536)throw new IOException("fixture Git setup output bound");}
            catch(IOException failure){throw new IllegalStateException(failure);}
        });}
        if(!terminal.passed())throw new IOException("genuine isolated Git fixture setup failed: "+terminal);
        git.verify();for(Path path:List.of(stdout,stderr))if(Files.size(path)>65536)throw new IOException("fixture setup capture exceeds bound");
    }
    /** Explicit isolated test mutation; never present in a production source artifact. */
    public void removeReleaseTagForTest()throws Exception{
        setup(git.execution().gitExecutable(),actual.request().repository(),root.resolve("git-setup"),4,List.of("tag","--delete","v1.0.2"));
    }
    @Override public void close(){git.close();}
}

