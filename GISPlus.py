import os.path

from PyQt6 import QtWidgets
from PyQt6 import QtGui
from PyQt6.QtWidgets import QMessageBox, QApplication, QFileDialog, QDialog

import checkLASfunctions
from GISWindow import Ui_MainWindow

import sys

from TableModel import PandasModel
from Preprocessing import preprocessing
import tolas
import DBase


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super(MainWindow, self).__init__(parent=None)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # menubar connections
        self.ui.actionImport_Las.triggered.connect(self.openLAS)
        # menubar shortcuts
        self.ui.actionImport_Las.setShortcut(QtGui.QKeySequence("Ctrl+O"))

        # functional buttons connections
        self.ui.btn_filter.clicked.connect(self.filterDB)
        self.ui.btn_clearfilter.clicked.connect(self.clearFilter)
        self.ui.btn_report.clicked.connect(self.createReport)
        self.ui.btn_reportClear.clicked.connect(self.clearReport)

        # tabs set to 0 index
        self.ui.tabWidgetMain.setCurrentIndex(0)

        # список файлов для импорта
        self.files = []
        self.out_files = []

        # переменные для ошибок
        self.fatal = []
        self.errors_dictionary = {}

        # загрузка базы данных в таблицу
        self.display_DB()

    # выбор LAS для открытия
    def openLAS(self):

        # project_path, file_type = QFileDialog.getOpenFileNames()
        opendlg = QFileDialog(self)
        opendlg.setDirectory('Las')
        opendlg.setFileMode(QFileDialog.FileMode.ExistingFiles)

        if opendlg.exec():
            project_path = opendlg.selectedFiles()

            # список файлов для открытия
            self.files = project_path
            if len(self.files) != 0:

                for item in self.files:

                    # изменение абсолютного пути на относительный
                    item = os.path.relpath(item)

                    # перекодировка файла
                    out_item = tolas.convert_and_filter_file(item)

                    # проверка, что файл можно считать как LAS
                    check, error = tolas.add_las_extension_and_save(out_item)

                    if check:
                        if error is not None:
                            out_item = error

                        # добавление сырого файла в базу данных
                        self.addto_DB(item, 'Сырой')

                        # если удалось, запустить проверку ошибок внутри файла
                        # объединить словари, содержащие ошибки
                        # {название файла: [список ошибок]}
                        check_proc, d = preprocessing(out_item)
                        if check_proc:
                            for key, value in d.items():
                                self.errors_dictionary[key] = value

                        checkLASfunctions.validate_las_file(out_item)

                        # добавить предобработанный файл в базу данных
                        self.addto_DB(out_item, 'Предобработанный')

                    else:
                        # иначе выдать предупреждение
                        msg = QMessageBox(self)
                        msg.setText(item + '\nНевозможно прочитать файл как LAS\n' + error)
                        btn = msg.exec()
                        self.fatal.append(item)
                        self.files.remove(item)

                    self.out_files.append(out_item)

                self.display_DB()


    def addto_DB(self, file_item, ftype):
        self.df = DBase.database(file_item, ftype)

        self.model = PandasModel(self.df)
        self.ui.tableView.setModel(self.model)


    def display_DB(self):
        self.df_out = DBase.display_database()
        self.model = PandasModel(self.df_out)
        self.ui.tableView_2.setModel(self.model)

        # добавление объектов для выбора в combo boxes
        self.ui.cmb_well.clear()
        self.ui.cmb_well.addItem('Любой')
        for item in self.df_out['Номер скважины'].unique():
            self.ui.cmb_well.addItem(item)

        self.ui.cmb_oilfield.clear()
        self.ui.cmb_oilfield.addItem('Любое')
        for item in self.df_out['Название месторождения'].unique():
            self.ui.cmb_oilfield.addItem(item)

        self.ui.cmb_well_logging.clear()
        self.ui.cmb_well_logging.addItem('Любые')
        for item in self.df_out['Методы ГИС'].unique():
            self.ui.cmb_well_logging.addItem(item)

    # фильтрация по выбранным значениям
    def filterDB(self):
        well_logging = self.ui.cmb_well_logging.currentText()
        well = self.ui.cmb_well.currentText()
        oilfield = self.ui.cmb_oilfield.currentText()

        try:
            interval_start = int(self.ui.edit_min.text())
        except ValueError:
            interval_start = self.df_out['Начало интервала'].min()

        try:
            interval_end = int(self.ui.edit_max.text())
        except ValueError:
            interval_end = self.df_out['Конец интервала'].max()

        if well_logging == 'Любые':
            well_logging = self.df_out['Методы ГИС']

        if well == 'Любой':
            well = self.df_out['Номер скважины']

        if oilfield == 'Любое':
            oilfield = self.df_out['Название месторождения']

        self.df_filtered = self.df_out[(self.df_out['Методы ГИС'] == well_logging) &
                                       (self.df_out['Номер скважины'] == well) &
                                       (self.df_out['Название месторождения'] == oilfield) &
                                       (self.df_out['Начало интервала'] >= interval_start) &
                                       (self.df_out['Конец интервала'] <= interval_end)]

        self.newmodel = PandasModel(self.df_filtered)
        self.ui.tableView_2.setModel(self.newmodel)

    def clearFilter(self):
        self.ui.tableView_2.setModel(self.model)

        # добавление объектов для выбора в combo boxes
        self.ui.cmb_well.clear()
        self.ui.cmb_well.addItem('Любой')
        for item in self.df_out['Номер скважины'].unique():
            self.ui.cmb_well.addItem(item)

        self.ui.cmb_oilfield.clear()
        self.ui.cmb_oilfield.addItem('Любое')
        for item in self.df_out['Название месторождения'].unique():
            self.ui.cmb_oilfield.addItem(item)

        self.ui.cmb_well_logging.clear()
        self.ui.cmb_well_logging.addItem('Любые')
        for item in self.df_out['Методы ГИС'].unique():
            self.ui.cmb_well_logging.addItem(item)

        self.ui.edit_min.clear()
        self.ui.edit_max.clear()

    # выывод ошибок в окно программы
    def createReport(self):
        self.ui.listWidget_fatal.clear()
        self.ui.listWidget_nonfatal.clear()

        for item in self.fatal:
            self.ui.listWidget_fatal.addItem(item)

        for k in self.errors_dictionary.keys():
            self.ui.listWidget_nonfatal.addItem(k)
            for val in self.errors_dictionary[k]:
                self.ui.listWidget_nonfatal.addItem(val)

    # очистить список ошибок
    def clearReport(self):
        self.ui.listWidget_fatal.clear()
        self.ui.listWidget_nonfatal.clear()


# launching
app = QApplication(sys.argv)
application = MainWindow()
application.show()
app.setStyle('Fusion')

sys.exit(app.exec())
