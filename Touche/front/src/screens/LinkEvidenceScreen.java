package screens;
import javax.microedition.lcdui.*;
import java.util.Hashtable;
import network.Api;
import network.Json;
import utils.ScreenManager;

public class LinkEvidenceScreen extends ApiForm {
    private TextField claim=new TextField("Numero affirmation","",10,TextField.NUMERIC);
    private TextField evidence=new TextField("Numero preuve","",10,TextField.NUMERIC);
    private TextField rationale=new TextField("Justification","",3000,TextField.ANY);
    private Command save=new Command("Relier",Command.OK,1);
    private String path;
    private Displayable parent;
    public LinkEvidenceScreen(String base,Displayable back) {
        super("Relier les pieces"); path=base; parent=back;
        append(claim); append(evidence); append(rationale); addCommand(save);
        status.setText("Relation de contexte proposee ; aucune confirmation automatique.");
    }
    protected void act(Command command) {
        if(command!=save) return;
        try {
            String identifier=Long.valueOf(claim.getString()).toString();
            Hashtable body=Json.object(); body.put("evidence_id",Long.valueOf(evidence.getString()));
            body.put("stance","context"); body.put("rationale",rationale.getString());
            call("POST",path+"/claims/"+identifier+"/evidence",body,new Api.Listener() {
                public void success(Object data) { ScreenManager.show(parent); }
                public void failure(String problem) { }
            });
        } catch(Exception ex) { status.setText("References numeriques requises."); }
    }
}
