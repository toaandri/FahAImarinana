package screens;

import javax.microedition.lcdui.*;
import java.util.Hashtable;
import java.util.Vector;
import network.Api;
import network.Json;
import network.PublicCache;

public class PublicationScreen extends ApiForm {
    private Command sync = new Command("Synchroniser",Command.OK,1);
    public PublicationScreen() {
        super("Publications publiques"); addCommand(sync);
        Hashtable cached = PublicCache.load();
        if (cached == null) status.setText("Aucun contenu synchronise. Connexion requise.");
        else render(cached,"Cache hors ligne - actualite non garantie");
    }
    private void render(Hashtable snapshot,String label) {
        deleteAll(); append(status);
        status.setText(label + "\nDerniere synchronisation : " + Json.str(snapshot,"synchronized_at"));
        Vector items = (Vector)snapshot.get("items");
        if (items.size() == 0) append("Aucune verification publiee.");
        for (int i = 0; i < items.size(); i++) {
            Hashtable item = (Hashtable)items.elementAt(i);
            append(new StringItem(Json.str(item,"titre_final") + " [" + Json.str(item,"statut_verification") + "]",Json.str(item,"corps_article")));
        }
    }
    protected void act(Command command) {
        if (command != sync) return;
        call("GET","/public/sync",null,new Api.Listener() {
            public void success(Object data) {
                Hashtable snapshot = (Hashtable)data;
                snapshot.put("server",Api.baseUrl);
                try { PublicCache.save(snapshot); render(snapshot,"Synchronisation reussie"); }
                catch (Exception ex) { status.setText("Cache conserve : " + ex.getMessage()); }
            }
            public void failure(String problem) { }
        });
    }
}
