import java.util.Hashtable;
import java.util.Vector;
import network.Json;

public class CodecTest {
    public static void main(String[] args) {
        Hashtable object=(Hashtable)Json.parse("{\"texte\":\"Français, Malagasy, \\u00e9\\n\",\"n\":12,\"none\":null,\"items\":[true,false,-1,1.25,1e2]}");
        Hashtable copy=(Hashtable)Json.parse(Json.encode(object));
        if(!Json.str(object,"texte").equals(Json.str(copy,"texte"))) throw new RuntimeException("UTF-8 round trip");
        if(((Vector)copy.get("items")).size()!=5) throw new RuntimeException("Array round trip");
        String[] invalid={"", "{\"x\":1,\"x\":2}","[1,]","01","-","1.","1e","true false","\"unterminated","{x:1}"};
        for(int i=0;i<invalid.length;i++) {
            boolean rejected=false;
            try { Json.parse(invalid[i]); } catch(IllegalArgumentException expected) { rejected=true; }
            if(!rejected) throw new RuntimeException("Malformed JSON accepted: "+invalid[i]);
        }
        System.out.println("CODEC_TEST_OK");
    }
}
