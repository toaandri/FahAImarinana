package screens;

import javax.microedition.lcdui.*;
import java.util.Hashtable;
import java.util.Vector;
import network.Api;
import network.Json;
import utils.ScreenManager;

public class ResourceScreen extends ApiForm {
    private String path;
    private Displayable parent;
    private boolean drafts;
    private int offset;
    private int count;
    private Vector records=new Vector();
    private ChoiceGroup choices=new ChoiceGroup("Brouillon",Choice.POPUP);
    private Command next=new Command("Page suivante",Command.SCREEN,5);
    private Command previous=new Command("Page precedente",Command.SCREEN,6);
    private Command open=new Command("Ouvrir",Command.OK,1);
    public ResourceScreen(String title,String endpoint,Displayable back,boolean draftList) {
        super(title); path=endpoint; parent=back; drafts=draftList;
        addCommand(next); addCommand(previous); if(drafts) addCommand(open); load();
    }
    private String display(Hashtable item) {
        if(item.containsKey("statement")) return "Affirmation #"+Json.str(item,"id")+" : "+Json.str(item,"statement")+" ["+Json.str(item,"verdict")+"]";
        if(item.containsKey("synthese")) return "Recherche #"+Json.str(item,"id")+" ["+Json.str(item,"statut")+"]\\n"+Json.str(item,"synthese")+"\\n"+Json.encode(item.get("citations"));
        if(item.containsKey("nom")) return "Source #"+Json.str(item,"id")+" : "+Json.str(item,"nom")+"\\n"+Json.str(item,"url");
        if(item.containsKey("snapshot")) return "Version "+Json.str(item,"version")+" - "+Json.str(item,"event")+"\\n"+Json.encode(item.get("snapshot"));
        return "Preuve #"+Json.str(item,"id")+" : "+Json.str(item,"title")+"\\n"+Json.str(item,"content")+"\\n"+Json.str(item,"original_url");
    }
    private void load() {
        call("GET",path+"?limit=20&offset="+offset,null,new Api.Listener() {
            public void success(Object data) {
                records=(Vector)data; count=records.size(); deleteAll(); append(status); choices.deleteAll();
                if(drafts) append(choices);
                for(int i=0;i<records.size();i++) {
                    Hashtable item=(Hashtable)records.elementAt(i);
                    if(drafts) choices.append("#"+Json.str(item,"id")+" "+Json.str(item,"titre_suggere")+" ["+Json.str(item,"statut")+"]",null);
                    else append(display(item));
                }
                status.setText(count==0?"Aucun resultat sur cette page.":"Elements "+(offset+1)+" a "+(offset+count));
            }
            public void failure(String problem) { }
        });
    }
    public void commandAction(Command command,Displayable view) {
        if(busy) return;
        if(command==home) ScreenManager.show(parent); else act(command);
    }
    protected void act(Command command) {
        if(command==next && count==20) { offset+=20; load(); }
        else if(command==previous) { offset=Math.max(0,offset-20); load(); }
        else if(command==open && choices.getSelectedIndex()>=0)
            ScreenManager.show(new DraftScreen(Json.str((Hashtable)records.elementAt(choices.getSelectedIndex()),"id"),this));
    }
}
