package screens;

import javax.microedition.lcdui.*;
import java.util.Hashtable;
import network.Api;
import network.Json;
import utils.ScreenManager;

/** Editorial actions always use the server version and explicit human confirmation. */
public class DraftScreen extends ApiForm {
    private String id;
    private Displayable parent;
    private Hashtable draft;
    private TextField title=new TextField("Titre final","",250,TextField.ANY);
    private TextField body=new TextField("Article final","",15000,TextField.ANY);
    private TextField category=new TextField("Categorie","",50,TextField.ANY);
    private TextField summary=new TextField("Resume public SMS","",480,TextField.ANY);
    private TextField notes=new TextField("Notes de relecture","",3000,TextField.ANY);
    private ChoiceGroup verdict=new ChoiceGroup("Decision editoriale humaine",Choice.POPUP,new String[]{"Vrai","Faux","Trompeur"},null);
    private Command validate=new Command("Valider cette version",Command.SCREEN,2);
    private Command publish=new Command("Publier",Command.SCREEN,3);
    private Command review=new Command("Relu",Command.SCREEN,1);
    private Command reject=new Command("Refuser",Command.SCREEN,4);
    private Command history=new Command("Historique",Command.SCREEN,5);
    private Command reload=new Command("Actualiser",Command.SCREEN,6);
    private Command save=new Command("Enregistrer nouvelle revision",Command.OK,1);
    public DraftScreen(String identifier,Displayable back) {
        super("Brouillon #"+identifier); id=identifier; parent=back;
        addCommand(history); addCommand(reload); load();
    }
    private void load() {
        call("GET","/drafts/"+id+"/version",null,new Api.Listener() {
            public void success(Object data) {
                draft=(Hashtable)data; deleteAll(); append(status);
                append(new StringItem(Json.str(draft,"titre_suggere"),Json.str(draft,"synthese_ia")));
                append("Version "+Json.str(draft,"version")+" - "+Json.str(draft,"statut"));
                Object approved=draft.get("approved_payload");
                Hashtable content=approved instanceof Hashtable ? (Hashtable)approved : Json.object();
                title.setString(content.containsKey("titre_final")?Json.str(content,"titre_final"):Json.str(draft,"titre_suggere"));
                String text=content.containsKey("corps_article")?Json.str(content,"corps_article"):Json.str(draft,"synthese_ia");
                if(text.length()>15000) { status.setText("Texte trop long pour ce mobile. Utilisez l'API pour la relecture complete."); return; }
                body.setString(text); category.setString(Json.str(content,"categorie")); summary.setString(Json.str(content,"contenu_optimise_sms"));
                for(int i=0;i<verdict.size();i++) if(verdict.getString(i).equals(Json.str(content,"statut_verification"))) verdict.setSelectedIndex(i,true);
                if(Api.can("versions.validate")) {
                    append(title); append(body); append(category); append(summary); append(verdict); append(notes);
                    addCommand(review); addCommand(validate); addCommand(reject); addCommand(publish);
                    status.setText("Examinez les preuves du dossier avant validation. La publication utilisera exactement ce contenu.");
                } else if(Api.can("drafts.edit")) {
                    append(title); append(body); addCommand(save);
                    status.setText("Brouillon prive. Une nouvelle revision annulera la validation precedente.");
                } else status.setText("Brouillon prive. Validation et publication reservees a un editeur.");
            }
            public void failure(String problem) { }
        });
    }
    private Hashtable publication() {
        Hashtable content=Json.object(); content.put("titre_final",title.getString()); content.put("corps_article",body.getString());
        content.put("categorie",category.getString()); content.put("contenu_optimise_sms",summary.getString());
        content.put("statut_verification",verdict.getString(verdict.getSelectedIndex())); return content;
    }
    public void commandAction(Command command,Displayable view) {
        if(busy) return;
        if(command==home) ScreenManager.show(parent); else act(command);
    }
    protected void act(final Command command) {
        if(command==history) { ScreenManager.show(new ResourceScreen("Historique prive","/drafts/"+id+"/history",this,false)); return; }
        if(command==reload) { load(); return; }
        if(draft==null) return;
        if(command==save) {
            Hashtable content=Json.object(); content.put("expected_version",draft.get("version"));
            content.put("titre_suggere",title.getString()); content.put("synthese_ia",body.getString());
            call("POST","/drafts/"+id+"/revisions",content,new Api.Listener() {
                public void success(Object data) { load(); }
                public void failure(String problem) { }
            });
            return;
        }
        if(command==publish || command==validate || command==reject) {
            final Alert confirmation=new Alert("Decision editoriale",command.getLabel()+" le brouillon #"+id+" version "+Json.str(draft,"version")+" ?",null,AlertType.CONFIRMATION);
            final Command confirm=new Command("Confirmer",Command.OK,1);
            final Command cancel=new Command("Annuler",Command.CANCEL,2);
            confirmation.addCommand(confirm); confirmation.addCommand(cancel); confirmation.setTimeout(Alert.FOREVER);
            confirmation.setCommandListener(new CommandListener() {
                public void commandAction(Command selected,Displayable view) {
                    ScreenManager.show(DraftScreen.this);
                    if(selected==confirm) execute(command);
                }
            });
            ScreenManager.show(confirmation);
        } else execute(command);
    }
    private void execute(final Command command) {
        Hashtable payload;
        String action;
        if(command==validate || command==publish) {
            payload=publication(); action=command==validate?"validate":"publish";
            if(command==validate) payload.put("expected_version",draft.get("version"));
        } else {
            payload=Json.object(); action="review"; payload.put("expected_version",draft.get("version"));
            payload.put("decision",command==reject?"rejected":"reviewed");
            payload.put("notes",notes.getString());
        }
        call("POST","/workflow/drafts/"+id+"/"+action,payload,new Api.Listener() {
            public void success(Object data) {
                if(command==publish) ScreenManager.show(new PublicationScreen()); else load();
            }
            public void failure(String problem) { }
        });
    }
}
