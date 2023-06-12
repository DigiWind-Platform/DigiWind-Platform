#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
#
# generated by wxGlade 1.1.0pre on Fri Jul 15 17:07:59 2022
#

import wx

# begin wxGlade: dependencies
# end wxGlade

# begin wxGlade: extracode
from textWidget import TextWidget
# end wxGlade


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MyFrame.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((800, 600))
        self.SetTitle("DigiWind - FMU Interface")

        self.panel_1 = wx.Panel(self, wx.ID_ANY)

        sizer_1 = wx.BoxSizer(wx.VERTICAL)

        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_1.Add(sizer_2, 1, wx.EXPAND, 0)

        GUI_title = wx.StaticText(self.panel_1, wx.ID_ANY, "DigiWind FMU Manager")
        GUI_title.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, ""))
        sizer_2.Add(GUI_title, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 5)

        self.notebook_1 = wx.Notebook(self.panel_1, wx.ID_ANY)
        sizer_2.Add(self.notebook_1, 1, wx.EXPAND, 0)

        self.create_pane_1 = wx.Panel(self.notebook_1, wx.ID_ANY)
        self.notebook_1.AddPage(self.create_pane_1, "CREATE")

        sizer_3 = wx.BoxSizer(wx.VERTICAL)

        sizer_5 = wx.BoxSizer(wx.VERTICAL)
        sizer_3.Add(sizer_5, 1, wx.EXPAND, 0)

        sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_5.Add(sizer_6, 1, wx.EXPAND, 0)

        sizer_8 = wx.BoxSizer(wx.VERTICAL)
        sizer_6.Add(sizer_8, 1, wx.EXPAND, 0)

        sizer_9 = wx.StaticBoxSizer(wx.StaticBox(self.create_pane_1, wx.ID_ANY, "File Upload"), wx.HORIZONTAL)
        sizer_8.Add(sizer_9, 0, wx.EXPAND, 0)

        self.create_fmu_upload_txt_input = wx.TextCtrl(self.create_pane_1, wx.ID_ANY, "")
        sizer_9.Add(self.create_fmu_upload_txt_input, 1, wx.ALL | wx.EXPAND, 5)

        self.create_fmu_upload_btn = wx.Button(self.create_pane_1, 1001, "Upload FMU")
        sizer_9.Add(self.create_fmu_upload_btn, 0, wx.ALL, 5)

        sizer_10 = wx.BoxSizer(wx.VERTICAL)
        sizer_8.Add(sizer_10, 1, wx.EXPAND, 0)

        self.error_txt = wx.TextCtrl(self.create_pane_1, wx.ID_ANY, "", style=wx.BORDER_NONE | wx.TE_MULTILINE | wx.TE_NO_VSCROLL | wx.TE_READONLY)
        self.error_txt.SetMinSize((360, 100))
        self.error_txt.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.error_txt.SetForegroundColour(wx.Colour(255, 0, 0))
        self.error_txt.SetFont(wx.Font(9, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        self.error_txt.Hide()
        sizer_10.Add(self.error_txt, 1, wx.RESERVE_SPACE_EVEN_IF_HIDDEN, 0)

        self.apply_btn = wx.Button(self.create_pane_1, wx.ID_ANY, "Apply")
        sizer_10.Add(self.apply_btn, 0, wx.ALL | wx.EXPAND, 5)

        sizer_11 = wx.StaticBoxSizer(wx.StaticBox(self.create_pane_1, wx.ID_ANY, "Metadata"), wx.VERTICAL)
        sizer_6.Add(sizer_11, 1, wx.EXPAND, 0)

        self.create_metadata_txt = TextWidget(self.create_pane_1, wx.ID_ANY)
        sizer_11.Add(self.create_metadata_txt, 1, wx.EXPAND, 0)

        self.notebook_1_pane_2 = wx.Panel(self.notebook_1, wx.ID_ANY)
        self.notebook_1.AddPage(self.notebook_1_pane_2, "UPDATE")

        sizer_4 = wx.BoxSizer(wx.VERTICAL)

        sizer_12 = wx.BoxSizer(wx.VERTICAL)
        sizer_4.Add(sizer_12, 1, wx.EXPAND, 0)

        sizer_13 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_12.Add(sizer_13, 1, wx.EXPAND, 0)

        sizer_14 = wx.StaticBoxSizer(wx.StaticBox(self.notebook_1_pane_2, wx.ID_ANY, "Upload FMUs"), wx.VERTICAL)
        sizer_13.Add(sizer_14, 1, wx.EXPAND, 0)

        sizer_20 = wx.StaticBoxSizer(wx.StaticBox(self.notebook_1_pane_2, wx.ID_ANY, "Existing FMU"), wx.HORIZONTAL)
        sizer_14.Add(sizer_20, 0, wx.EXPAND, 0)

        self.update_upload_fmu_server_txt = wx.TextCtrl(self.notebook_1_pane_2, wx.ID_ANY, "")
        sizer_20.Add(self.update_upload_fmu_server_txt, 1, wx.ALL | wx.EXPAND, 5)

        self.update_upload_fmu_server_btn = wx.Button(self.notebook_1_pane_2, 3003, "Upload FMU")
        sizer_20.Add(self.update_upload_fmu_server_btn, 0, wx.ALL, 5)

        sizer_15 = wx.StaticBoxSizer(wx.StaticBox(self.notebook_1_pane_2, wx.ID_ANY, "New FMU"), wx.HORIZONTAL)
        sizer_14.Add(sizer_15, 0, wx.EXPAND, 0)

        self.update_upload_fmu_local_txt = wx.TextCtrl(self.notebook_1_pane_2, wx.ID_ANY, "")
        sizer_15.Add(self.update_upload_fmu_local_txt, 1, wx.ALL | wx.EXPAND, 5)

        self.update_upload_fmu_local_btn = wx.Button(self.notebook_1_pane_2, 2002, "Upload FMU")
        sizer_15.Add(self.update_upload_fmu_local_btn, 0, wx.ALL, 5)

        sizer_18 = wx.StaticBoxSizer(wx.StaticBox(self.notebook_1_pane_2, wx.ID_ANY, "Update Metadata (optional)"), wx.VERTICAL)
        sizer_14.Add(sizer_18, 1, wx.EXPAND, 0)

        sizer_16 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_18.Add(sizer_16, 0, wx.EXPAND, 0)

        self.update_sov_txt = wx.TextCtrl(self.notebook_1_pane_2, wx.ID_ANY, "")
        sizer_16.Add(self.update_sov_txt, 0, wx.ALL, 5)

        update_sov_label = wx.StaticText(self.notebook_1_pane_2, wx.ID_ANY, "start of Validity")
        sizer_16.Add(update_sov_label, 0, wx.ALL, 5)

        self.panel_2 = wx.Panel(self.notebook_1_pane_2, wx.ID_ANY)
        self.panel_2.SetMinSize((150, 33))
        sizer_16.Add(self.panel_2, 0, wx.EXPAND, 0)

        self.update_ref_ID_txt = wx.TextCtrl(self.notebook_1_pane_2, wx.ID_ANY, "")
        sizer_16.Add(self.update_ref_ID_txt, 0, wx.ALL, 5)

        update_ref_ID_label = wx.StaticText(self.notebook_1_pane_2, wx.ID_ANY, "reference ID (internal)")
        sizer_16.Add(update_ref_ID_label, 0, wx.ALL, 5)

        static_line_1 = wx.StaticLine(self.notebook_1_pane_2, wx.ID_ANY)
        sizer_18.Add(static_line_1, 0, wx.EXPAND, 0)

        self.update_error_txt = wx.TextCtrl(self.notebook_1_pane_2, wx.ID_ANY, "", style=wx.BORDER_NONE | wx.TE_MULTILINE | wx.TE_NO_VSCROLL | wx.TE_READONLY)
        self.update_error_txt.SetMinSize((700, 150))
        self.update_error_txt.SetForegroundColour(wx.Colour(255, 0, 0))
        self.update_error_txt.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        self.update_error_txt.Hide()
        sizer_18.Add(self.update_error_txt, 0, wx.EXPAND | wx.RESERVE_SPACE_EVEN_IF_HIDDEN, 0)

        grid_sizer_1 = wx.FlexGridSizer(1, 2, 0, 0)
        sizer_12.Add(grid_sizer_1, 0, wx.EXPAND, 0)

        self.replace_checkbox = wx.CheckBox(self.notebook_1_pane_2, wx.ID_ANY, "Replace FMU?")
        grid_sizer_1.Add(self.replace_checkbox, 0, wx.ALL, 10)

        self.update_btn = wx.Button(self.notebook_1_pane_2, wx.ID_ANY, "Update FMU")
        grid_sizer_1.Add(self.update_btn, 0, wx.ALL | wx.EXPAND, 5)

        self.notebook_1_pane_3 = wx.Panel(self.notebook_1, wx.ID_ANY)
        self.notebook_1.AddPage(self.notebook_1_pane_3, "DELETE")

        sizer_7 = wx.BoxSizer(wx.VERTICAL)

        sizer_21 = wx.StaticBoxSizer(wx.StaticBox(self.notebook_1_pane_3, wx.ID_ANY, "Select FMU to delete"), wx.HORIZONTAL)
        sizer_7.Add(sizer_21, 0, wx.EXPAND, 0)

        self.delete_fmu_txt = wx.TextCtrl(self.notebook_1_pane_3, wx.ID_ANY, "")
        sizer_21.Add(self.delete_fmu_txt, 1, wx.ALL | wx.EXPAND, 5)

        self.delete_fmu_btn = wx.Button(self.notebook_1_pane_3, 4004, "Choose FMU to delete")
        sizer_21.Add(self.delete_fmu_btn, 0, wx.ALL, 5)

        self.delete_error_txt = wx.TextCtrl(self.notebook_1_pane_3, wx.ID_ANY, "", style=wx.BORDER_NONE | wx.TE_MULTILINE | wx.TE_NO_VSCROLL | wx.TE_READONLY)
        self.delete_error_txt.SetMinSize((700, 150))
        self.delete_error_txt.SetForegroundColour(wx.Colour(255, 0, 0))
        self.delete_error_txt.SetFont(wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, 0, ""))
        self.delete_error_txt.Hide()
        sizer_7.Add(self.delete_error_txt, 1, wx.EXPAND | wx.RESERVE_SPACE_EVEN_IF_HIDDEN, 0)

        self.delete_btn = wx.Button(self.notebook_1_pane_3, 4004, "Delete FMU")
        sizer_7.Add(self.delete_btn, 0, wx.ALL | wx.EXPAND, 5)

        self.notebook_1_pane_3.SetSizer(sizer_7)

        grid_sizer_1.AddGrowableCol(1)

        self.notebook_1_pane_2.SetSizer(sizer_4)

        self.create_pane_1.SetSizer(sizer_3)

        self.panel_1.SetSizer(sizer_1)

        self.Layout()

        self.create_fmu_upload_btn.Bind(wx.EVT_BUTTON, self.open_file_dialog)
        self.apply_btn.Bind(wx.EVT_BUTTON, self.on_apply)
        self.update_upload_fmu_server_btn.Bind(wx.EVT_BUTTON, self.open_file_dialog)
        self.update_upload_fmu_local_btn.Bind(wx.EVT_BUTTON, self.open_file_dialog)
        self.update_btn.Bind(wx.EVT_BUTTON, self.on_update)
        self.delete_fmu_btn.Bind(wx.EVT_BUTTON, self.open_file_dialog)
        self.delete_btn.Bind(wx.EVT_BUTTON, self.on_delete)
        # end wxGlade

    def open_file_dialog(self, event):  # wxGlade: MyFrame.<event_handler>
        print("Event handler 'open_file_dialog' not implemented!")
        event.Skip()

    def on_apply(self, event):  # wxGlade: MyFrame.<event_handler>
        print("Event handler 'on_apply' not implemented!")
        event.Skip()

    def on_update(self, event):  # wxGlade: MyFrame.<event_handler>
        print("Event handler 'on_update' not implemented!")
        event.Skip()

    def on_delete(self, event):  # wxGlade: MyFrame.<event_handler>
        print("Event handler 'on_delete' not implemented!")
        event.Skip()

# end of class MyFrame

class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True

# end of class MyApp

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()