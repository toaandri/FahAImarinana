package screens;

import javax.microedition.lcdui.*;
import java.util.Hashtable;
import java.util.Vector;
import network.Api;
import network.Json;
import utils.ScreenManager;

public class CaseScreen extends ApiForm {
    private String id;
    private String path;
    private ChoiceGroup actions = new ChoiceGroup("Action",Choice.POPUP);
    private Vector operations = new Vector();
    private StringItem description = new StringItem("Dossier","");
    private Command go = new Command("Continuer",Command.OK,1);
    private Command reload = new Command("Actualiser",Command.SCREEN,2);
    public CaseScreen(String identifier) {
        super("Investigation #" + identifier); id=identifier; path="/cases/"+id;
        append(description); append(actions); addCommand(go); addCommand(reload);
        option("Affirmations","claims"); option("Preuves","evidence"); option("Sources de veille disponibles","sources");
        option("Brouillons / relecture","drafts"); option("Recherches enregistrees","research");
        if (Api.can("claims.add")) option("Ajouter une affirmation","claim_add");
        if (Api.can("evidence.add")) { option("Ajouter une preuve","evidence_add"); option("Relier preuve et affirmation","link"); }
        if (Api.can("signals.ingest")) option("Ajouter un signal documente","signal");
        if (Api.can("drafts.edit")) option("Preparer un brouillon humain","draft_add");
        if (Api.can("research.run")) option("Rechercher dans les pieces locales","search");
        load();
    }
    private void option(String label,String operation) { actions.append(label,null); operations.addElement(operation); }
    private void load() {
        call("GET",path,null,new Api.Listener() {
            public void success(Object data) {
                Hashtable item=(Hashtable)data;
                description.setText(Json.str(item,"title") + "\n" + Json.str(item,"description") + "\nEtat : " + Json.str(item,"status"));
            }
            public void failure(String problem) { }
        });
    }
    private Api.Listener back() {
        return new Api.Listener() {
            public void success(Object data) { ScreenManager.show(new CaseScreen(id)); }
            public void failure(String problem) { }
        };
    }
    protected void act(Command command) {
        if (command == reload) { load(); return; }
        if (command != go || actions.getSelectedIndex()<0) return;
        String action=(String)operations.elementAt(actions.getSelectedIndex());
        EntryForm form=null;
        if (action.equals("claim_add")) form=new EntryForm("Affirmation",path+"/claims",this,back()).field("statement","Texte original",5000,false);
        else if (action.equals("evidence_add")) form=new EntryForm("Preuve confidentielle",path+"/evidence",this,back()).fixed("kind","document")
            .field("title","Titre",250,false).field("content","Extrait / description",10000,false)
            .field("original_url","Reference URL originale",500,false).field("source_id","Numero source (voir Sources)",10,true);
        else if (action.equals("signal")) form=new EntryForm("Signal documente","/signals/ingest",this,new Api.Listener() {
            public void success(Object data) {
                Alert alert=new Alert("Signal enregistre","Numero du signal : " + Json.str((Hashtable)data,"id") + ". Utilisez-le pour preparer le brouillon.",null,AlertType.INFO);
                alert.setTimeout(Alert.FOREVER); ScreenManager.getDisplay().setCurrent(alert,CaseScreen.this);
            }
            public void failure(String problem) { }
        }).fixed("case_id",Long.valueOf(id)).field("source_id","Numero source",10,true).field("contenu","Texte original",10000,false)
            .field("url_origine","URL originale",500,false).field("horodatage_publication","Date ISO : 2026-11-02T12:00:00Z",40,false);
        else if (action.equals("draft_add")) form=new EntryForm("Brouillon humain",path+"/drafts",this,new Api.Listener() {
            public void success(Object data) { ScreenManager.show(new DraftScreen(Json.str((Hashtable)data,"id"),CaseScreen.this)); }
            public void failure(String problem) { }
        }).field("signal_id","Numero signal",10,true).field("claim_id","Numero affirmation",10,true)
            .field("titre_suggere","Titre du brouillon",250,false).field("synthese_ia","Texte du brouillon humain",15000,false);
        else if (action.equals("search")) form=new EntryForm("Recherche locale",path+"/research",this,new Api.Listener() {
            public void success(Object data) { ScreenManager.show(new ResourceScreen("Resultats locaux",path+"/research",CaseScreen.this,false)); }
            public void failure(String problem) { }
        }).field("question","Question",500,false);
        else if (action.equals("link")) { ScreenManager.show(new LinkEvidenceScreen(path,this)); return; }
        else { ScreenManager.show(new ResourceScreen(action,path+"/"+action,this,action.equals("drafts"))); return; }
        ScreenManager.show(form);
    }
}
