package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.service.root.RootBootstrapOutputContract.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import org.xar.ck3.control.build.NativeRunProfileProducer;
import org.xar.ck3.control.build.SharedSourceFiles;

/** Complete closed mutable-output census plus the independently verified immutable production subtree. No writes. */
final class RootBootstrapAssetTree {
    record Snapshot(SharedSourceFiles.DirectoryIdentity root,List<Entry> files,List<DirectoryEntry> directories,
            long generatedCharged,long retainedAllocatedUpper) { }
    private RootBootstrapAssetTree(){ }
    static Snapshot scan(Declaration declaration)throws IOException {
        Snapshot first=once(declaration),second=once(declaration);
        if(!first.equals(second))throw new IOException("complete bootstrap profile/input census changed between observations");
        return second;
    }
    static long directoryQuote(Path root)throws IOException {
        return Math.max(4096,org.xar.ck3.control.build.NativeStorageGeometry.read(root).clusterBytes());
    }
    private static Snapshot once(Declaration declaration)throws IOException {
        Path root=Path.of(declaration.assetRoot());var identity=SharedSourceFiles.nativeDirectory(root);
        var files=new ArrayList<Entry>();var directories=new ArrayList<DirectoryEntry>();long retained=walk(root,root,declaration,files,directories);
        if(!declaration.retainedInputs().isEmpty()&&retained==0)throw new IOException("declared retained production input is missing");
        files.sort(Comparator.comparing(Entry::fileName));directories.sort(Comparator.comparing(DirectoryEntry::relative));
        if(!identity.equals(SharedSourceFiles.nativeDirectory(root)))throw new IOException("bootstrap asset root identity drifted");
        long charged=directoryQuote(root);for(var file:files)charged=add(charged,file.nativeFile().allocatedBytes());
        charged=add(charged,Math.multiplyExact(directoryQuote(root),directories.size()));
        return new Snapshot(identity,List.copyOf(files),List.copyOf(directories),charged,retained);
    }
    private static long walk(Path root,Path directory,Declaration declaration,List<Entry> files,List<DirectoryEntry> directories)throws IOException {
        var before=SharedSourceFiles.nativeDirectory(directory);long retained=0;
        try(var children=Files.newDirectoryStream(directory)){
            for(Path child:children){
                String relative=root.relativize(child).toString().replace('\\','/');
                var input=declaration.retainedInputs().stream().filter(value->value.directoryName().equals(relative)).findFirst();
                if(input.isPresent()){
                    if(!SharedSourceFiles.nativeDirectory(child).equals(input.orElseThrow().parentDirectory()))
                        throw new IOException("retained production parent directory identity drifted");
                    Path inventory=Path.of(input.orElseThrow().productionInventory().path());
                    if(!SharedSourceFiles.nativeFile(inventory).equals(input.orElseThrow().inventoryNativeFile()))throw new IOException("retained production inventory native identity drifted");
                    var tree=NativeRunProfileProducer.readProductionTree(input.orElseThrow().productionInventory());
                    if(!SharedSourceFiles.nativeFile(inventory).equals(input.orElseThrow().inventoryNativeFile()))throw new IOException("retained production inventory changed during read");
                    if(!Path.of(tree.root()).equals(child.resolve("xar-production")))throw new IOException("retained profile production tree changed its actual root");
                    int count=0;try(var installed=Files.newDirectoryStream(child)){
                        for(Path actual:installed)if(++count!=1||!actual.equals(Path.of(tree.root())))
                            throw new IOException("retained production parent contains an unaccounted input");
                    }
                    if(count!=1)throw new IOException("complete retained production input is absent");
                    NativeRunProfileProducer.verifyProductionTree(tree);
                    retained=add(retained,add(tree.retainedAllocatedUpperBytes(),directoryQuote(root)));continue;
                }
                if(Files.isDirectory(child,LinkOption.NOFOLLOW_LINKS)){
                    if(!declaration.outputDirectories().contains(relative))throw new IOException("undeclared bootstrap asset directory: "+relative);
                    if(files.size()+directories.size()>=declaration.maximumEntries())throw new IOException("generated bootstrap census exceeded its signed bound");
                    var nativeDirectory=SharedSourceFiles.nativeDirectory(child);directories.add(new DirectoryEntry(relative,nativeDirectory));
                    retained=add(retained,walk(root,child,declaration,files,directories));
                    if(!nativeDirectory.equals(SharedSourceFiles.nativeDirectory(child)))throw new IOException("generated profile directory changed during census");
                }else{
                    if(declaration.outputs().stream().noneMatch(value->value.fileName().equals(relative)))
                        throw new IOException("unaccounted file in complete bootstrap asset root: "+relative);
                    if(files.size()+directories.size()>=declaration.maximumEntries())throw new IOException("generated bootstrap census exceeded its signed bound");
                    var first=SharedSourceFiles.nativeFile(child);var last=SharedSourceFiles.nativeFile(child);
                    if(!first.equals(last))throw new IOException("bootstrap asset native file changed during census");files.add(new Entry(relative,first));
                }
            }
        }
        if(!before.equals(SharedSourceFiles.nativeDirectory(directory)))throw new IOException("bootstrap input directory changed during census");
        return retained;
    }
}
