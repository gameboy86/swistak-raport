# -*- coding: utf-8 -*-

import wx
import datetime
import hashlib
from os.path import join

from report import CSVReport, HTMLReport, ReportData
from config import SwistakConfig


class SwistakGui(wx.Frame):

    REPORT_TYPE = {'HTML': HTMLReport, 'CSV': CSVReport}

    def __init__(self, parent, id_):
        super(SwistakGui, self).__init__(parent, id_, "Swistak Raport", size=(300, 200))
        self.panel = wx.Panel(self)
        self.create_menu()
        self.config = SwistakConfig()
        self.create_ui()

    def create_menu(self):
        self.CreateStatusBar()
        menubar = wx.MenuBar()
        edit_menu = wx.Menu()
        add = edit_menu.Append(wx.NewId(), 'Dodaj Konto', 'Dodaj nowe konto')
        delete = edit_menu.Append(wx.NewId(), u'Usuń Konto', u'Usuń konto')
        properties = edit_menu.Append(wx.NewId(), u'Ustawienia', u'Ustawienia')
        menubar.Append(edit_menu, 'Edycja')
        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.add_new, add)
        self.Bind(wx.EVT_MENU, self.delete_one, delete)
        self.Bind(wx.EVT_MENU, self.properties, properties)

    def create_ui(self):
        label_one = wx.StaticText(self.panel, wx.ID_ANY, 'Wybierz konto', (20, 20), (100, 20))

        self.account_list_box = wx.ComboBox(self.panel, -1,
                                            self.config.accounts.keys()[0] if self.config.accounts.keys() else '',
                                            (0, 0), (100, -1), self.config.accounts.keys(), wx.CB_READONLY)

        label_two = wx.StaticText(self.panel, wx.ID_ANY, 'Data od')
        self.callendar_input = wx.DatePickerCtrl(self.panel, style=wx.DP_DROPDOWN | wx.DP_SHOWCENTURY, dt=wx.DateTime.Now(),)

        label_tree = wx.StaticText(self.panel, wx.ID_ANY, 'Typ raportu')
        self.textTree = wx.CheckListBox(self.panel, wx.ID_ANY, choices=[a for a in self.REPORT_TYPE])

        self.textTree.Bind(wx.EVT_CHECKLISTBOX, self.__check_if_ok)

        topSizer = wx.BoxSizer(wx.VERTICAL)
        titleSizer = wx.BoxSizer(wx.HORIZONTAL)
        title2Sizer = wx.BoxSizer(wx.HORIZONTAL)
        title3Sizer = wx.BoxSizer(wx.HORIZONTAL)

        titleSizer.Add(label_one, 0, wx.ALL, 5)
        titleSizer.Add(self.account_list_box, 1, wx.ALL, 5)

        title2Sizer.Add(label_two, 0, wx.ALL, 5)
        title2Sizer.Add(self.callendar_input, 1, wx.ALL, 5)

        title3Sizer.Add(label_tree, 0, wx.ALL, 5)
        title3Sizer.Add(self.textTree, 1, wx.ALL, 5)

        topSizer.Add(titleSizer, 0, wx.CENTER)
        topSizer.Add(title2Sizer, 0, wx.CENTER)
        topSizer.Add(title3Sizer, 0, wx.CENTER)

        self.button = wx.Button(self.panel, label='Pobierz')
        self.button.Bind(wx.EVT_BUTTON, self.create_report)
        self.button.Disable()

        topSizer.Add(self.button, 0)
        self.panel.SetSizer(topSizer)
        topSizer.Fit(self)

    def create_report(self, event):
        busyDlg = wx.BusyInfo(u"Proszę czekać... trwa pobieranie danych oraz generowanie raportu")
        from_date = self.wx_date_to_python(self.callendar_input)

        user = self.account_list_box.GetStringSelection()
        selected_reports = self.textTree.GetChecked()

        report = ReportData(user=user, password=self.config.get_account(user))
        report_name = report.get_report_name(from_date)
        try:
            report_data = report.get_data(from_date)
        except Exception as e:
            wx.MessageBox(u'Wystąpił błąd, sprawdz czy dane logowania są porawne albo czy masz dostęp do interntetu\n'
                          u'--------------------------------------------------\n'
                          u'{0}'.format(e),
                          'Error',
                          wx.OK | wx.ICON_INFORMATION)
        else:
            if not report_data:
                return
            for report_type in selected_reports:
                self.__create_report_for_type(report_type, report_name, report_data)
                busyDlg = None

    def add_new(self, event):
        user_name_box = wx.TextEntryDialog(None, "Login ", "Podaj login")
        if user_name_box.ShowModal() == wx.ID_OK:
            password_box = wx.TextEntryDialog(None, "Password ", u"Podaj hasło")
            if password_box.ShowModal() == wx.ID_OK:
                self.config.add_account(user_name_box.GetValue(), hashlib.md5(password_box.GetValue()).hexdigest())
                self.config.write()
                self.__update_account_list_box()
            password_box.Destroy()
        user_name_box.Destroy()

    def delete_one(self, event):
        delete_box = wx.SingleChoiceDialog(None,
                                           u"Zaznacz konto które chcesz usunąć",
                                           "Usuwanie konta",
                                           self.config.accounts.keys())
        if delete_box.ShowModal() == wx.ID_OK:
            self.config.del_account(delete_box.GetStringSelection())
            self.config.write()
            self.__update_account_list_box()
        delete_box.Destroy()

    def properties(self, event):
        dialog = wx.DirDialog(None, "Choose a directory:", style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        dialog.SetPath(self.config.get_report_dir())
        if dialog.ShowModal() == wx.ID_OK:
            self.config.set_report_dir(dialog.GetPath())
            self.config.write()
        dialog.Destroy()

    def __check_if_ok(self, event):
        list_ = event.GetEventObject()
        if list_.GetChecked():
            self.button.Enable()
        else:
            self.button.Disable()

    def __update_account_list_box(self):
        self.account_list_box.Set(self.config.accounts.keys())
        if self.config.accounts.keys():
            self.account_list_box.SetValue(self.config.accounts.keys()[0])

    def __create_report_for_type(self, report_type, report_file_name, report_data):
        selected_report = self.textTree.GetString(report_type)

        self.REPORT_TYPE[selected_report].create_report(
            report_data,
            join(self.config.get_report_dir(), report_file_name))

    @staticmethod
    def wx_date_to_python(calendar_input):
        text_date = calendar_input.GetValue().FormatISODate().split('-')
        return datetime.date(year=int(text_date[0]), month=int(text_date[1]), day=int(text_date[2]))


def create_gui():
    app = wx.App()
    main = SwistakGui(parent=None, id_=-1)
    main.Show()
    app.MainLoop()
