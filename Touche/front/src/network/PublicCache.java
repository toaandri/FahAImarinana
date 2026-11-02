package network;

import java.util.Hashtable;
import javax.microedition.rms.RecordStore;
import javax.microedition.rms.RecordEnumeration;

/** One record update is atomic. Only the anonymous complete public feed is accepted. */
public final class PublicCache {
    private static final String STORE = "fa-public-v1";
    public static synchronized void save(Hashtable snapshot) throws Exception {
        if (!Boolean.TRUE.equals(snapshot.get("complete")) || !"replace".equals(snapshot.get("strategy")))
            throw new Exception("Synchronisation incomplete. Cache conserve.");
        byte[] bytes = Json.encode(snapshot).getBytes("UTF-8");
        if (bytes.length > 262144) throw new Exception("Cache trop volumineux");
        RecordStore store = RecordStore.openRecordStore(STORE,true);
        try {
            RecordEnumeration records = store.enumerateRecords(null,null,false);
            try {
                if (records.hasNextElement()) store.setRecord(records.nextRecordId(),bytes,0,bytes.length);
                else store.addRecord(bytes,0,bytes.length);
            } finally { records.destroy(); }
        } finally { store.closeRecordStore(); }
    }
    public static synchronized Hashtable load() {
        RecordStore store = null;
        try {
            store = RecordStore.openRecordStore(STORE,false);
            RecordEnumeration records = store.enumerateRecords(null,null,false);
            try {
                if (records.hasNextElement()) {
                    Hashtable cached=(Hashtable)Json.parse(new String(store.getRecord(records.nextRecordId()),"UTF-8"));
                    // A cache from another backend must not be mistaken for this server's feed.
                    if (Api.baseUrl.equals(Json.str(cached,"server"))) return cached;
                }
            } finally { records.destroy(); }
        } catch (Exception ignored) { }
        finally { if (store != null) try { store.closeRecordStore(); } catch (Exception ignored) { } }
        return null;
    }
}
