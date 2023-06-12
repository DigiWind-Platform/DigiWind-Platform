import os
import sys
import wx
import json
import ast
import shutil
import datetime
from glob import glob
from fmpy import read_model_description

from DigiWind_GUI import MyFrame

wildcard = "FMU Files (*.fmu*)|*.fmu*"
# Get FMU directory
curr_dir = os.path.dirname(os.path.abspath(__file__))
fmu_path = os.path.join(os.path.dirname(curr_dir), "ServiceFramework", "services", "modelmanagementservice", "fmus")
# Get User directory
usr_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
# Other global variables for easy change
metafile = "metadata.json"
ID_CREATE_FMU_BTN = 1001
ID_UPDATE_LOCAL_FMU_BTN = 2002
ID_UPDATE_SERVER_FMU_BTN = 3003
ID_DELETE_SERVER_FMU_BTN = 4004
CREATE_VERSION = "_V_1_0"

class DigiWindFrame(MyFrame):

    error_list = []


########## Start button event handler ##########

    def on_apply(self, event):  
        # validations for input data 
        valid_json = self.correctJSON(self.create_metadata_txt.GetValue())
        #JSON needs to be valid to execute other validations
        if valid_json:
            unique_fmu_name = self.uniqueFMUName(ast.literal_eval(self.create_metadata_txt.GetValue())["metaInformation"]["name"])
            valid_json_content = self.validations(self.create_metadata_txt.GetValue(), ast.literal_eval(self.create_metadata_txt.GetValue()))
            # check if everything is valid
            if valid_json_content and unique_fmu_name:
                self.create_folder(ast.literal_eval(self.create_metadata_txt.GetValue()), CREATE_VERSION, self.create_fmu_upload_txt_input.GetValue(), fmu_path)
                self.error_txt.SetValue("FMU uploaded!")
                self.error_txt.SetForegroundColour(wx.Colour(35, 142, 35))
                self.error_txt.Show()
                self.Layout()
                print("Created!")
            else:
                error_msg = self.buildErrMsg()
                self.error_txt.SetValue(error_msg)
                self.error_txt.Show()
                self.Layout()
        else:
            error_msg = self.buildErrMsg()
            self.error_txt.SetValue(error_msg)
            self.error_txt.Show()
            self.Layout()
        
    def on_update(self, event): 
        metadata_path = os.path.join(self.update_upload_fmu_server_txt.GetValue(), metafile)
        with open(metadata_path) as file:
            metadata_json = json.load(file)
            file.close()
        new_version = self.update_version(metadata_json)
        metadata_json["metaInformation"]["startOfValidity"] = self.update_sov_txt.GetValue()
        metadata_json["metaInformation"]["referenceID"] = self.update_ref_ID_txt.GetValue()
        valid_sov = self.checkDate("metaInformation", "startOfValidity", metadata_json)
        if valid_sov:
            self.create_folder(
                metadata_json, 
                new_version, 
                self.update_upload_fmu_local_txt.GetValue(), 
                os.path.dirname(self.update_upload_fmu_server_txt.GetValue())
                )
            self.update_error_txt.SetValue("FMU updated to version: " + new_version)
            self.update_error_txt.SetForegroundColour(wx.Colour(35, 142, 35))
            self.update_error_txt.Show()
            self.Layout()
            print("Updated!")
        else:
            error_msg = self.buildErrMsg()
            self.update_error_txt.SetValue(error_msg)
            self.update_error_txt.Show()
            self.Layout()
    
    def on_delete(self, event):
        dir_path = self.delete_fmu_txt.GetValue()
        try:
            shutil.rmtree(dir_path)
        except OSError as e:
            error_msg = "An operating system error occured: \r\n " + repr(e)
            self.delete_error_txt.SetValue(error_msg)
            self.delete_error_txt.Show()
            self.Layout()
        else:
            self.delete_error_txt.SetValue("FMU folder deleted: \r\n " + dir_path)
            self.delete_error_txt.SetForegroundColour(wx.Colour(35, 142, 35))
            self.delete_fmu_txt.SetValue("")
            self.delete_error_txt.Show()
            self.Layout()
            print("Deleted!")

########## End button event handler ##########

########## Start util functions ##############

    def open_file_dialog(self, event):
        """
        Create and show the Open FileDialog
        """
        BTN_ID = event.GetEventObject().GetId()
        FD = wx.FileDialog(
                self, message="Choose a file",
                defaultDir=usr_path,
                defaultFile="",
                wildcard=wildcard,
                style=wx.FD_OPEN | wx.FD_CHANGE_DIR
            )
        DD = wx.DirDialog(self, message="Choose a file",
                        defaultPath=fmu_path,
                        style=wx.DD_DEFAULT_STYLE )

        if(BTN_ID == ID_CREATE_FMU_BTN):
            dlg = FD
        elif(BTN_ID == ID_UPDATE_LOCAL_FMU_BTN):
            dlg = FD
        elif(BTN_ID == ID_UPDATE_SERVER_FMU_BTN or BTN_ID == ID_DELETE_SERVER_FMU_BTN):
            dlg = DD
            
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if(BTN_ID == ID_CREATE_FMU_BTN):
                self.create_fmu_upload_txt_input.SetValue(path)
                template = self.create_template_json(path)
                self.create_metadata_txt.SetValue(template)
            elif(BTN_ID == ID_UPDATE_LOCAL_FMU_BTN):
                self.update_upload_fmu_local_txt.SetValue(path)
            elif(BTN_ID == ID_UPDATE_SERVER_FMU_BTN):
                self.update_upload_fmu_server_txt.SetValue(path)
                ex_metadata_path = os.path.join(path, metafile)
                with open(ex_metadata_path) as file:
                    ex_metadata = json.load(file)
                    file.close()
                self.update_sov_txt.SetValue(ex_metadata["metaInformation"]["startOfValidity"])
                self.update_ref_ID_txt.SetValue(ex_metadata["metaInformation"]["referenceID"])
            elif(BTN_ID == ID_DELETE_SERVER_FMU_BTN):
                self.delete_fmu_txt.SetValue(path)
        dlg.Destroy()

    def create_template_json(self, fmu):
        valid_file_ext = self.correctFileExtension(self.create_fmu_upload_txt_input.GetValue())
        if valid_file_ext:
            self.apply_btn.Enable()
            self.error_txt.Hide()
            self.Layout()
            fmu_description = read_model_description(fmu)
            name = fmu_description.modelName
            fmu_vars = fmu_description.modelVariables
            signals = {}
            for el in fmu_vars:
                if el.causality == "input" or el.causality == "output":
                    signals[el.name] = "MANDATORY (ONTOLOGY CLASS NAME)"
            template = {
                        "metaInformation": {
                                "type": "MANDATORY",
                                "name": name,
                                "startOfValidity": "YYYY-MM-DDTHH:MM:SS",
                                "referenceID": "OPTIONAL"
                            },
                        "signalBonds": {
                                "examplePort": {
                                    "type": "Example",
                                    "asFlow": "signalNameIn",
                                    "asEffort": "signalNameOut"
                                }
                            },
                        "signals": signals
                    }
            return json.dumps(template, indent = 4)
        else:
            self.error_list.append("- Chosen file ist not an .fmu file \r\n ")
            self.apply_btn.Disable()
            error_msg = self.buildErrMsg()
            self.error_txt.SetValue(error_msg)
            self.error_txt.Show()
            self.Layout()
    
    def create_folder(self, data, version, src_path, dst):
        fmu_name = data["metaInformation"]["name"]
        identifier = fmu_name + version
        data["metaInformation"]["identifier"] = identifier
        fmu_dir = os.path.join(dst, data["metaInformation"]["identifier"])
        if not os.path.exists(fmu_dir):
            os.mkdir(fmu_dir)
            metadata_path = os.path.join(fmu_dir, metafile)
            with open(metadata_path, "w+") as f:
                json.dump(data, f)
                dst_path = os.path.join(fmu_dir, f"{identifier}.fmu")
                shutil.copy(src_path, dst_path)
                f.close()
    
    def update_version(self, metadata):
        fmu_name = metadata["metaInformation"]["name"]
        subdirs = glob(fmu_path + "/*/", recursive = True) #array
        new_version = ""
        versions = []
        mainversions = []
        subversions = []
        for dir in subdirs:
            dir_name = os.path.dirname(dir).split("\\")[-1]
            ex_fmu_name = dir_name.split("_V_")[0]
            if(fmu_name == ex_fmu_name):
                version = dir_name.split("_V_")[1].split("_")
                versions.append(version)
                mainversions.append(int(version[0]))
        mainversion = max(mainversions)
        for ver in versions:
            if int(ver[0]) == mainversion:
                subversions.append(int(ver[1]))
        subversion = max(subversions)
        if self.replace_checkbox.GetValue():
            mainversion = mainversion+1
            subversion = 0
        else:
            subversion = subversion+1
        new_version = "_V_" + str(mainversion) + "_" + str(subversion)
        return(new_version)

    def buildErrMsg(self):
        error_msg = "Following errors occured: \r\n "
        for el in self.error_list:
            error_msg = error_msg + el
        self.error_list = []
        return error_msg


########## End util function ##################

########## Start validation function ##########

    def validations(self, metadata, metadata_json):
        #initial variables
        mand = True
        #check if mandatory fields are defined 
        if "MANDATORY" in metadata:
            mand = False
            self.error_list.append("- At least one mandatory field is not defined \r\n  ")
        #check fields inside metadata.json
        meta_inf = self.checkJSON(True, "metaInformation", "", metadata_json)
        signal_bonds = self.checkJSON(True, "signalBonds", "", metadata_json)
        signals = self.checkJSON(True, "signals", "", metadata_json)
        fmu_typ = self.checkJSON(False, "metaInformation", "type", metadata_json)
        fmu_id = self.checkJSON(False, "metaInformation", "name", metadata_json)
        sov = self.checkDate("metaInformation", "startOfValidity", metadata_json)
        #final check if any errors occured
        if not mand or not meta_inf or not signal_bonds or not signals or not fmu_typ or not fmu_id or not sov:
            return False
        else:
            return True
        
    def correctFileExtension(self, path):
        if path.endswith(".fmu"):
            return True
        else:
            self.error_list.append("- Chosen file ist not an .fmu file \r\n ")
            return False

    def uniqueFMUName(self, name):
        subdirs = glob(fmu_path + "/*/", recursive = True) #array
        unique = True

        for dir in subdirs:
            dir_name = os.path.dirname(dir).split("\\")[-1]
            ex_fmu_name = dir_name.split("V")[0]
            if(name == ex_fmu_name):
                unique = False
        
        if unique:
            return True
        else:
            self.error_list.append("- FMU already exists, please use the update option \r\n")
            return False
    
    def correctDateFormat(self, date):
        date_format = "%Y-%m-%dT%H:%M:%S"
        try:
            datetime.datetime.strptime(date, date_format)
        except ValueError:
            self.error_list.append("- The start of validity has an incorrect date format. It should be YYYY-MM-DDTHH:MM:SS")
            return False
        else:
            return True
    
    def checkDate(self, toplevelfield, lowerlevelfield, metadata_json):
        if lowerlevelfield not in metadata_json[toplevelfield].keys() or metadata_json[toplevelfield][lowerlevelfield] == "YYYY-MM-DDTHH:MM:SS":
            self.error_list.append(f"- {toplevelfield} does not include the mandatory field '{lowerlevelfield}' or it is set to the default value \r\n")
            return False
        else:
            sov_format = self.correctDateFormat(metadata_json[toplevelfield][lowerlevelfield])
            if sov_format:
                return True
            else:
                return False

    def correctJSON(self, json_data):
        try:
            json.loads(json_data)
        except ValueError:
            self.error_list.append("- JSON Format is not correct, please check if you deleted any quotation marks or commatas. \r\n ")
        else:
            return True

    def checkJSON(self, onlykey, toplevelfield, lowerlevelfield, metadata_json):
        if onlykey:
            if toplevelfield not in metadata_json.keys():
                self.error_list.append(f"- Key '{toplevelfield}' was manipulated and cannot be found \r\n")
                return False
            else:
                return True
        else:
            if lowerlevelfield not in metadata_json[toplevelfield].keys() or metadata_json[toplevelfield][lowerlevelfield] == "":
                self.error_list.append(f"- {toplevelfield} does not include the mandatory field '{lowerlevelfield}' or it is empty \r\n")
                return False
            else:
                return True

########## End validation function ##########

class DigiWindApp(wx.App):
    def OnInit(self):
        self.frame = DigiWindFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True


if __name__ == "__main__":
    app = DigiWindApp(0)
    try:
        usr_path = sys.argv[1]
    except IndexError:
        usr_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    app.MainLoop()
