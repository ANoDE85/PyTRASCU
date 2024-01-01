
import os
import subprocess
import traceback
import wx
import wx.adv

from collections import OrderedDict

have_winreg = False
try:
    import winreg
    have_winreg = True
except:
    pass

have_win32api = False
try:
    from win32api import GetFileVersionInfo, LOWORD, HIWORD
    have_win32api = True
except Exception as e:
    pass

import __version__
from gui.tra_scu_base import TraScuMainFrame

def MakeCheckpointList(prefix, ids, caption_prefix="Checkpoint", start_idx=1):
    return [(
        "%s%d" % (prefix, i,),
        "%s %d" % (caption_prefix, idx + start_idx, ))
        for idx, i in enumerate(ids)]

LevelChoices = OrderedDict([
    ("Main Menu",
        None),
    ("Mansion",
        MakeCheckpointList("ma", range(1, 18))),
    ("Peru - Mountain Caves",
        MakeCheckpointList("pu", range(1, 8))),
    ("Peru - City of Vilcabamba",
        MakeCheckpointList("pu", (8, 9, 90, 10))),
    ("Peru - Lost Valley",
        MakeCheckpointList("pu", (11, 12, 13, 14, 15, 94, 95))),
    ("Peru - Tomb of Qualopec",
        MakeCheckpointList("pu", (16, 161, 17, 18, 19, 20, 21, 22, 23))),
    ("Peru - Frontend",
        MakeCheckpointList("pu", (104, ), "Menu")),

    ("Greece - St. Francis Folly",
        MakeCheckpointList("gr", range(1, 12))),
    ("Greece - Coliseum",
        MakeCheckpointList("gr", (12, 13, 14, 15, 31))),
    ("Greece - Midas' Palace",
        MakeCheckpointList("gr", range(18, 25))),
    ("Greece - Tomb of Tihocan",
        MakeCheckpointList("gr", range(27, 31))),
    ("Greece - Frontend",
        MakeCheckpointList("gr", (104, ), "Menu")),
    ("Greece - Other",
        MakeCheckpointList("gr", (16, 17, 25, 26, 32))),

    ("Egypt - Temple of Khamoon",
        MakeCheckpointList("eg", range(1, 11))),
    ("Egypt - Obelisk of Khamoon",
        MakeCheckpointList("eg", range(11, 18))),
    ("Egypt - Sanctuary of the Scion",
        MakeCheckpointList("eg", range(20, 32))),
    ("Egypt - Frontend",
        MakeCheckpointList("eg", (104, ), "Menu")),
    ("Egypt - Other",
        MakeCheckpointList("eg", (18, 19, 32, 33))),

    ("Lost City - Natla's Mines",
        MakeCheckpointList("lc", (1, 2, 3, 5, 11, 14))),
    ("Lost City - Great Pyramid",
        MakeCheckpointList("lc", (10, 12, 13, 15, 16))),
    ("Lost City - Final Conflict",
        MakeCheckpointList("lc", (6, 7, 16, 17, 18, 19, 20))),
    ("Lost City - Frontend",
        MakeCheckpointList("lc", (104, ), "Menu")),

    ("Style Units Peru",
        MakeCheckpointList("pusource", (1, 2, 3), "Style unit")),
    ("Style Units Greece",
        MakeCheckpointList("grsource", (1, 2), "Style unit")),
    ("Style Units Egypt",
        MakeCheckpointList("egyptstyle", (1, 3), "Style unit")),
    ("Style Units Lost City",
        MakeCheckpointList("lcpuhall", (1, ), "Style unit") +
        MakeCheckpointList("lostcitystyle", (1, ), "Style unit", 2)),

    ("Cinematics", [
        ("cn4", "St. Francis Folly"),
        ("cn8", "Final cutscene (Natla's mines)"),
        ("cn9", "Temple of Khamoon"),] +
        MakeCheckpointList("cn", (1, 2, 3, 5, 6, 7, 10), "Cutscene", 4)),

    ("Other", []),
])

OutfitChoices = OrderedDict([
    (None, "Default"),
    ("lara_classic", "Classic Lara"),
    ("lara_natla", "Scorched Natla"),
    ("lara_sport", "Lara Sport"),
    ("lara_aod", "AOD Lara"),
    ("lara_legend", "Legend Lara"),
    ("lara_wetsuit", "Wetsuit"),
    ("lara_catsuit", "Catsuit"),
    ("lara_gold", "Golden Lara"),
    ("lara_dgang", "Bacon Lara"),
    ("lara", "Lara"),
])

AdvancedOptions = OrderedDict([
    ("-DRAWMONSTERATTACK", ("Draw monster attack" , False)),
    ("-DRAWMONSTERCOMBAT", ("Draw monster combat", False)),
    ("-EASYCHEAT", ("Easy Cheat mode", False)),
    ("-FONTNAME", ("Font name", True)),
    ("-CHAPTERVARS", ("Chapter variables", True)),
    ("-MAINMENU", ("Show Main Menu", False)),
    ("-NOHINTS", ("Dont' show hints", False)),
    ("-NOMONSTERATTACK", ("No monster attack", False)),
    ("-NOTRACE", ("No trace", False)),
    ("-NOVIBRATION", ("No vibration", False)),
    ("-NOHEALTH", ("God Mode", False)),
    ("-NOMONSTERHEALTH", ("No monster health", False)),
])

class MainFrame(TraScuMainFrame):
    def __init__(self):
        TraScuMainFrame.__init__(self, None)
        self.SetTitle(self.GetTitle() + " - " + __version__.Version)
        self.__m_current_outfit = None
        self.__m_outfit_to_id_map = {}
        self.__m_current_level = None
        self.__m_current_adv_opts = {}
        self.__m_outfit_boxes = []
        self.__m_devopts_controls = {}
        self._InitMainOptions()
        self._InitAdvancedOptions()
        self._FindAnniversary()
        self._LoadConfig()
        self.Fit()

    def _InitMainOptions(self):
        for group_name in LevelChoices.keys():
            self.m_level_choice.Append(group_name)
        self._SelectLevel(0)

        is_first = True
        for id, name in OutfitChoices.items():
            if is_first:
                flags = wx.RB_GROUP
            else:
                flags = 0
            is_first = False
            outfit_button = wx.RadioButton( self.m_outer_radio_sizer.GetStaticBox(), wx.ID_ANY, name, wx.DefaultPosition, wx.DefaultSize, flags )
            outfit_button.Bind( wx.EVT_RADIOBUTTON, self.OnOutfitChoice)
            self.__m_outfit_boxes.append(outfit_button)
            self.__m_outfit_to_id_map[outfit_button.GetId()] = id
            self.m_outfit_sizer.Add( outfit_button, 0, wx.ALL, 5 )
        self.m_outer_radio_sizer.Layout()

    def _InitSublevelChoices(self, level_name):
        self.m_sublevel_choice.Clear()
        group_choices = LevelChoices[level_name]
        if group_choices is None:
            self.m_sublevel_choice.Append("-", None)
        else:
            for id, caption in group_choices:
                name = "%s (%s)" % (caption, id)
                self.m_sublevel_choice.Append(name, id)
        self._SelectSublevel(0)

    def _InitAdvancedOptions(self):
        for key, (caption, has_parameter) in AdvancedOptions.items():
            text_box = None
            check_box = wx.CheckBox(self.m_outer_dev_opts_sizer.GetStaticBox(), wx.ID_ANY, caption, wx.DefaultPosition, wx.DefaultSize, 0, name=key)
            check_box.SetToolTip(key)
            check_box.Bind(wx.EVT_CHECKBOX, self.OnToggleAdvanced)
            self.m_inner_dev_opts_content_sizer.Add( check_box, 0, wx.ALL, 5 )
            if has_parameter:
                text_box = wx.TextCtrl( self.m_outer_dev_opts_sizer.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
                text_box.Enabled = False
                self.m_inner_dev_opts_content_sizer.Add( text_box, 0, wx.ALL|wx.EXPAND, 5 )
            else:
                self.m_inner_dev_opts_content_sizer.Add( (0, 0), 0, wx.ALL, 5 )
            self.__m_devopts_controls[key] =  (check_box, text_box)
        self.m_outer_dev_opts_sizer.Layout()

    def _FindAnniversary(self):
        if not have_winreg:
            return
        try:
            with winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE) as aReg:
                with winreg.OpenKey(aReg, r"SOFTWARE\Crystal Dynamics\Tomb Raider: Anniversary") as aKey:
                    val = winreg.QueryValueEx(aKey, "InstallPath")[0]
                    try:
                        is_steam = winreg.QueryValueEx(aKey, "SKUType")[0] == "STEAM"
                    except:
                        is_steam = "steam" in val
            self.SetAnniversaryExecutable(os.path.join(val, "tra.exe"), is_steam)
        except Exception as e:
            wx.MessageBox(
                "Could not auto-detect TR Anniversary:\n\n%s" % (str(e), ),
                "Auto detection failed",
                wx.ICON_WARNING)

    def SetAnniversaryExecutable(self, exe_path, is_steam):
        exe_path = os.path.abspath(exe_path)
        self.m_exe_picker.SetPath(exe_path)
        exe_version = self.GetExecutableVersion(exe_path)
        exe_version_string = ".".join((str(x) for x in exe_version))
        self.m_version_display_text.SetValue(exe_version_string)
        self.m_chk_steam.SetValue(is_steam)

    def GetExecutableVersion(self, filename):
        if not have_win32api:
            wx.MessageBox("No api")
            return 0, 0, 0, 0
        try:
            info = GetFileVersionInfo(filename, "\\")
            ms = info['FileVersionMS']
            ls = info['FileVersionLS']
            return HIWORD (ms), LOWORD (ms), HIWORD (ls), LOWORD (ls)
        except:
            return 0,0,0,0

    def OnExeSelected(self, event):
        self.SetAnniversaryExecutable(event.GetPath(), "steam" in event.GetPath())

    def OnOutfitChoice(self, evt):
        self.__m_current_outfit = self.__m_outfit_to_id_map[evt.GetEventObject().GetId()]

    def _SelectLevel(self, idx):
        self.m_level_choice.Select(idx)
        self._InitSublevelChoices(self.m_level_choice.GetString(idx))

    def _SelectLevelByName(self, name, chapter_idx):
        if not self.m_level_choice.SetStringSelection(name):
            return False
        self._InitSublevelChoices(name)
        if chapter_idx < self.m_sublevel_choice.GetCount():
            self.m_sublevel_choice.SetSelection(chapter_idx)
            return True
        else:
            return False

    def OnSelectLevel(self, event):
        self._SelectLevel(event.GetSelection())

    def _SelectSublevel(self, idx):
        self.m_sublevel_choice.Select(idx)
        self.__m_current_level = self.m_sublevel_choice.GetClientData(idx)
    def OnSelectSublevel(self, event):
        self._SelectSublevel(event.GetSelection())

    def OnToggleAdvanced(self, event):
        key = event.GetEventObject().GetName()
        (check_box, text_box) = self.__m_devopts_controls[key]
        if text_box:
            text_box.Enabled = check_box.IsChecked()

    def OnSaveSettings(self, event):
        self._WriteConfig()

    def OnLoadSettings(self, event):
        if not self._LoadConfig():
            wx.MessageBox("Could not load config!", "Error loading config", wx.ICON_ERROR)

    def OnReset(self, event):
        config_path = self._GetConfigFilePath()
        if not os.path.exists(config_path):
            return
        res = wx.MessageBox("This will remove the file '%s' from your computer.\n\nDo you wish to continue?" % (config_path, ),
            "Confirmation", wx.ICON_INFORMATION | wx.YES_NO)
        if res != wx.YES:
            return
        try:
            os.unlink(config_path)
        except Exception as e:
            wx.MessageBox("Error while removing '%s': %s" % (config_path, str(e)), "Warning", wx.ICON_ERROR)
        self._ResetControls()

    def OnAbout(self, event):
        info = wx.adv.AboutDialogInfo()
        info.Name = __version__.ProgramName
        info.Version = __version__.Version
        info.Copyright = __version__.Copyright
        info.Description = __version__.Description
        info.WebSite = __version__.ProjectSite
        info.Developers = __version__.Contributers
        info.License = __version__.License
        # Show the wx.AboutBox
        wx.adv.AboutBox(info)


    def _GetAdvancedOptions(self):
        opts = []
        for key, (check_box, text_box) in self.__m_devopts_controls.items():
            if check_box.IsChecked():
                opts.append(key)
                if text_box:
                    opts.append('"%s"' % (text_box.GetValue(), ))
        return opts

    def _GetCommandLineOptions(self):
        options = []
        if self.__m_current_level:
            options.extend([self.__m_current_level, "-NOMAINMENU", ])
        if self.__m_current_outfit:
            options.extend(["-PLAYER", self.__m_current_outfit])
        options.extend(self._GetAdvancedOptions())
        return options

    def _GetConfigFilePath(self):
        exe_path = self._GetTombRaiderExecutable()
        if not exe_path:
            raise Exception("Please set the Tomb Raider Anniversary executable path!");
        anniversary_install_dir = os.path.dirname(exe_path)
        return os.path.join(os.path.splitdrive(anniversary_install_dir)[0] + os.sep, "TRAE", "GAME", "PC", "TRAE.arg")

    def _GetTombRaiderExecutable(self):
        return self.m_exe_picker.GetPath()

    def _ResetControls(self):
        self._SelectLevel(0)
        self.__m_current_outfit = None
        for rb in self.__m_outfit_boxes:
            rb.SetValue(False)
        for key, (cb, tb) in self.__m_devopts_controls.items():
            cb.SetValue(False)
            if tb:
                tb.SetValue("")
                tb.Enable(False)

    def _LoadConfig(self):
        self._ResetControls()

        try:
            config_file_path = self._GetConfigFilePath()
        except Exception as e:
            return False
        if not os.path.exists(config_file_path):
            return True
        try:
            with open(config_file_path, "r") as fh:
                line = fh.readlines()[0]
        except:
            return False

        ok = True
        options = (option for option in line.split(" ") if option)
        for option in options:
            if option in AdvancedOptions:
                try:
                    self.__m_devopts_controls[option][0].SetValue(True)
                    if AdvancedOptions[option][1]:
                        param = next(options)
                        if param.startswith('"'):
                            param = param[1:]
                        if param.endswith('"'):
                            param = param[:-1]
                        if not self.__m_devopts_controls[option][1]:
                            ok = False
                        else:
                            self.__m_devopts_controls[option][1].SetValue(param)
                            self.__m_devopts_controls[option][1].Enable(True)
                except:
                    ok = False
            elif option in OutfitChoices.keys():
                for box_id, outfit_name in self.__m_outfit_to_id_map.items():
                    if option == outfit_name:
                        ctrl = wx.FindWindowById(box_id)
                        if ctrl is None:
                            ok = False
                            break
                        else:
                            ctrl.SetValue(True)
                            break
                else:
                    ok = False
            elif option in ["-NOMAINMENU", "-PLAYER"]:
                continue
            else:
                for name, cp_list in LevelChoices.items():
                    if cp_list is None:
                        continue
                    cp_list = list(item[0] for item in cp_list)
                    try:
                        option_index = cp_list.index(option)
                    except ValueError:
                        continue
                    if not self._SelectLevelByName(name, option_index):
                        ok = False
                    break
                else:
                    ok = False
        return ok

    def _WriteConfig(self):
        command_line_args = self._GetCommandLineOptions()

        config_file_path = self._GetConfigFilePath()
        config_dir = os.path.dirname(config_file_path)
        if not os.path.isdir(config_dir):
            try:
                os.makedirs(config_dir)
            except Exception as e:
                raise Exception("Could not create config directory '%s': %s",
                    (config_dir, str(e)))
        with open(config_file_path, "w+") as config_file:
            config_file.write(" ".join(command_line_args))

    def _LaunchGame(self):
        exe_path = self._GetTombRaiderExecutable()
        if not os.path.isfile(exe_path):
            raise Exception("Tomb Raider Anniversary executable was not found at '%s'!" % (exe_path, ))

        if self.m_chk_steam.GetValue():
            os.startfile('steam://rungameid/8000')
        else:
            subprocess.call(exe_path, cwd=os.path.dirname(exe_path))

    def OnRun(self, event):
        try:
            self._WriteConfig()
            self._LaunchGame()
        except Exception as e:
            wx.MessageBox("%s" % (e, ), "Error launching TR Anniversary", wx.ICON_ERROR)
            traceback.print_exc()


class Application(wx.App):

    def OnInit(self):
        self._m_main_frame = MainFrame()
        self.SetTopWindow(self._m_main_frame)
        self._m_main_frame.Show()
        return True

    def Start(self):
        self.MainLoop()

THE_APP = None
def main():
    THE_APP = Application()
    THE_APP.Start()


if __name__ == "__main__":
    main()