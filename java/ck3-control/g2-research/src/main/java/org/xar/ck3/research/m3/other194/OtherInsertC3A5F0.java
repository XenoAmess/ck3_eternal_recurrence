package org.xar.ck3.research.m3.other194;
import org.xar.ck3.research.m3.map191.MapInsert191Api;
import org.xar.ck3.research.m3.map191.MapInsertC3B960;

/** Complete23B C3A5F0 normal business projection; wrapperBodyRsp is post-push/sub30. */
public final class OtherInsertC3A5F0 {
    private OtherInsertC3A5F0() { }

    public static long execute(long moduleBase, long map, long output, int hash, long descriptor,
                               long wrapperBodyRsp, MapInsert191Api.Memory memory, MapInsert191Api.Ports ports) {


        long childBodyRsp = wrapperBodyRsp - 0xB0L;


        MapInsert191Api.Scratch scratch = new MapInsert191Api.Scratch(childBodyRsp);
        MapInsert191Api.Input input = new MapInsert191Api.Input(moduleBase, map, output, hash, descriptor, scratch);



        MapInsertC3B960.execute(input, memory, ports);

        return output;
    }
}