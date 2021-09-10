from PyQt5.QtWidgets import QGroupBox, QPushButton, QCheckBox, QLabel, QLineEdit, QGridLayout, QFileDialog, QMessageBox
import logging
import os
import getpass
from ez_ufo_qt.Helpers.stitch_funcs import main_360_mp_depth2

class MultiStitch360Group(QGroupBox):

    def __init__(self):
        super().__init__()

        self.args = {}
        self.e_input = ""
        self.e_output = ""
        self.e_tmpdir = ""
        self.e_ax1 = 0
        self.e_ax2 = 0
        self.e_ax = 0
        self.e_crop = 0
        self.e_manual = False
        self.axis_dict = dict.fromkeys(['z00', 'z01', 'z02', 'z03', 'z04', 'z05',
                                        'z06', 'z07', 'z08', 'z09', 'z010', 'z011'])

        self.setTitle("360 Multi Stitch")
        self.setStyleSheet('QGroupBox {color: red;}')

        self.input_dir_button = QPushButton()
        self.input_dir_button.setText("Select input directory")
        self.input_dir_button.clicked.connect(self.input_button_pressed)

        self.input_dir_entry = QLineEdit()
        self.input_dir_entry.textChanged.connect(self.set_input_entry)

        self.temp_dir_button = QPushButton()
        self.temp_dir_button.setText("Select temporary directory - default value recommended")
        self.temp_dir_button.clicked.connect(self.temp_button_pressed)

        self.temp_dir_entry = QLineEdit()
        self.temp_dir_entry.textChanged.connect(self.set_temp_entry)

        self.output_dir_button = QPushButton()
        self.output_dir_button.setText("Directory to save stitched images")
        self.output_dir_button.clicked.connect(self.output_button_pressed)

        self.output_dir_entry = QLineEdit()
        self.output_dir_entry.textChanged.connect(self.set_output_entry)

        self.crop_checkbox = QCheckBox()
        self.crop_checkbox.setText("Crop all projections to match the width of smallest stitched projection")
        self.crop_checkbox.clicked.connect(self.set_crop_projections_checkbox)

        self.axis_bottom_label = QLabel()
        self.axis_bottom_label.setText("Bottom Axis of Rotation (z00):")

        self.axis_bottom_entry = QLineEdit()
        self.axis_bottom_entry.textChanged.connect(self.set_axis_bottom)

        self.axis_top_label = QLabel()
        self.axis_top_label.setText("Top Axis of Rotation (z0N):")

        self.axis_group = QGroupBox("Enter axis of rotation manually")
        self.axis_group.clicked.connect(self.set_axis_group)

        self.axis_top_entry = QLineEdit()
        self.axis_top_entry.textChanged.connect(self.set_axis_top)

        self.axis_z00_label = QLabel("Axis of Rotation (z00):")
        self.axis_z00_entry = QLineEdit()
        self.axis_z00_entry.textChanged.connect(self.set_z00)

        self.axis_z01_label = QLabel("Axis of Rotation (z01):")
        self.axis_z01_entry = QLineEdit()
        self.axis_z01_entry.textChanged.connect(self.set_z01)

        self.axis_z02_label = QLabel("Axis of Rotation (z02):")
        self.axis_z02_entry = QLineEdit()
        self.axis_z02_entry.textChanged.connect(self.set_z02)

        self.axis_z03_label = QLabel("Axis of Rotation (z03):")
        self.axis_z03_entry = QLineEdit()
        self.axis_z03_entry.textChanged.connect(self.set_z03)

        self.axis_z04_label = QLabel("Axis of Rotation (z04):")
        self.axis_z04_entry = QLineEdit()
        self.axis_z04_entry.textChanged.connect(self.set_z04)

        self.axis_z05_label = QLabel("Axis of Rotation (z05):")
        self.axis_z05_entry = QLineEdit()
        self.axis_z05_entry.textChanged.connect(self.set_z05)

        self.axis_z06_label = QLabel("Axis of Rotation (z06):")
        self.axis_z06_entry = QLineEdit()
        self.axis_z06_entry.textChanged.connect(self.set_z06)

        self.axis_z07_label = QLabel("Axis of Rotation (z07):")
        self.axis_z07_entry = QLineEdit()
        self.axis_z07_entry.textChanged.connect(self.set_z07)

        self.axis_z08_label = QLabel("Axis of Rotation (z08):")
        self.axis_z08_entry = QLineEdit()
        self.axis_z08_entry.textChanged.connect(self.set_z08)

        self.axis_z09_label = QLabel("Axis of Rotation (z09):")
        self.axis_z09_entry = QLineEdit()
        self.axis_z09_entry.textChanged.connect(self.set_z09)

        self.axis_z010_label = QLabel("Axis of Rotation (z010):")
        self.axis_z010_entry = QLineEdit()
        self.axis_z010_entry.textChanged.connect(self.set_z010)

        self.axis_z011_label = QLabel("Axis of Rotation (z011):")
        self.axis_z011_entry = QLineEdit()
        self.axis_z011_entry.textChanged.connect(self.set_z011)

        self.stitch_button = QPushButton()
        self.stitch_button.setText("Stitch")
        self.stitch_button.clicked.connect(self.stitch_button_pressed)
        self.stitch_button.setStyleSheet("color:royalblue;font-weight:bold")

        self.delete_button = QPushButton()
        self.delete_button.setText("Delete output dir")
        self.delete_button.clicked.connect(self.delete_button_pressed)

        self.help_button = QPushButton()
        self.help_button.setText("Help")
        self.help_button.clicked.connect(self.help_button_pressed)

        self.set_layout()

    def set_layout(self):
        layout = QGridLayout()

        layout.addWidget(self.input_dir_button, 0, 0, 1, 4)
        layout.addWidget(self.input_dir_entry, 1, 0, 1, 4)
        layout.addWidget(self.temp_dir_button, 2, 0, 1, 4)
        layout.addWidget(self.temp_dir_entry, 3, 0, 1, 4)
        layout.addWidget(self.output_dir_button, 4, 0, 1, 4)
        layout.addWidget(self.output_dir_entry, 5, 0, 1, 4)
        layout.addWidget(self.crop_checkbox, 6, 0, 1, 4)

        layout.addWidget(self.axis_bottom_label, 7, 0)
        layout.addWidget(self.axis_bottom_entry, 7, 1)
        layout.addWidget(self.axis_top_label, 7, 2)
        layout.addWidget(self.axis_top_entry, 7, 3)

        self.axis_group.setCheckable(True)
        self.axis_group.setChecked(False)
        axis_layout = QGridLayout()

        axis_layout.addWidget(self.axis_z00_label, 0, 0)
        axis_layout.addWidget(self.axis_z00_entry, 0, 1)
        axis_layout.addWidget(self.axis_z06_label, 0, 2)
        axis_layout.addWidget(self.axis_z06_entry, 0, 3)

        axis_layout.addWidget(self.axis_z01_label, 1, 0)
        axis_layout.addWidget(self.axis_z01_entry, 1, 1)
        axis_layout.addWidget(self.axis_z07_label, 1, 2)
        axis_layout.addWidget(self.axis_z07_entry, 1, 3)

        axis_layout.addWidget(self.axis_z02_label, 2, 0)
        axis_layout.addWidget(self.axis_z02_entry, 2, 1)
        axis_layout.addWidget(self.axis_z08_label, 2, 2)
        axis_layout.addWidget(self.axis_z08_entry, 2, 3)

        axis_layout.addWidget(self.axis_z03_label, 3, 0)
        axis_layout.addWidget(self.axis_z03_entry, 3, 1)
        axis_layout.addWidget(self.axis_z09_label, 3, 2)
        axis_layout.addWidget(self.axis_z09_entry, 3, 3)

        axis_layout.addWidget(self.axis_z04_label, 4, 0)
        axis_layout.addWidget(self.axis_z04_entry, 4, 1)
        axis_layout.addWidget(self.axis_z010_label, 4, 2)
        axis_layout.addWidget(self.axis_z010_entry, 4, 3)

        axis_layout.addWidget(self.axis_z05_label, 5, 0)
        axis_layout.addWidget(self.axis_z05_entry, 5, 1)
        axis_layout.addWidget(self.axis_z011_label, 5, 2)
        axis_layout.addWidget(self.axis_z011_entry, 5, 3)
        self.axis_group.setLayout(axis_layout)

        self.axis_group.setTabOrder(self.axis_z00_entry, self.axis_z01_entry)
        self.axis_group.setTabOrder(self.axis_z01_entry, self.axis_z02_entry)
        self.axis_group.setTabOrder(self.axis_z02_entry, self.axis_z03_entry)
        self.axis_group.setTabOrder(self.axis_z03_entry, self.axis_z04_entry)
        self.axis_group.setTabOrder(self.axis_z04_entry, self.axis_z05_entry)
        self.axis_group.setTabOrder(self.axis_z05_entry, self.axis_z06_entry)
        self.axis_group.setTabOrder(self.axis_z06_entry, self.axis_z07_entry)
        self.axis_group.setTabOrder(self.axis_z07_entry, self.axis_z08_entry)
        self.axis_group.setTabOrder(self.axis_z08_entry, self.axis_z09_entry)
        self.axis_group.setTabOrder(self.axis_z09_entry, self.axis_z010_entry)
        self.axis_group.setTabOrder(self.axis_z010_entry, self.axis_z011_entry)

        layout.addWidget(self.axis_group, 8, 0, 1, 4)

        layout.addWidget(self.help_button, 9, 0)
        layout.addWidget(self.delete_button, 9, 1)
        layout.addWidget(self.stitch_button, 9, 2, 1, 2)

        self.setLayout(layout)

    def init_values(self):
        self.input_dir_entry.setText(os.getcwd())
        self.e_input = os.getcwd()
        tmp = os.path.join("/data", "tmp-ezstitch-" + getpass.getuser())
        self.temp_dir_entry.setText(tmp)
        self.e_tmpdir = tmp
        self.output_dir_entry.setText(os.getcwd() + '-stitched')
        self.e_output = os.getcwd() + '-stitched'
        self.crop_checkbox.setChecked(True)
        self.e_crop = True
        self.axis_bottom_entry.setText("245")
        self.e_ax1 = 245
        self.axis_top_entry.setText("245")
        self.e_ax2 = 245
        self.e_ax = self.e_ax1
        self.e_manual = False

    def input_button_pressed(self):
        logging.debug("Input button pressed")
        dir_explore = QFileDialog(self)
        directory = dir_explore.getExistingDirectory()
        self.input_dir_entry.setText(directory)
        self.e_input = directory

    def set_input_entry(self):
        logging.debug("Input directory: " + str(self.input_dir_entry.text()))
        self.e_input = str(self.input_dir_entry.text())

    def temp_button_pressed(self):
        logging.debug("Temp button pressed")
        dir_explore = QFileDialog(self)
        directory = dir_explore.getExistingDirectory()
        self.temp_dir_entry.setText(directory)
        self.e_tmpdir = directory

    def set_temp_entry(self):
        logging.debug("Temp directory: " + str(self.temp_dir_entry.text()))
        self.e_tmpdir = str(self.temp_dir_entry.text())

    def output_button_pressed(self):
        logging.debug("Output button pressed")
        dir_explore = QFileDialog(self)
        directory = dir_explore.getExistingDirectory()
        self.output_dir_entry.setText(directory)
        self.e_output = directory

    def set_output_entry(self):
        logging.debug("Output directory: " + str(self.output_dir_entry.text()))
        self.e_output = str(self.output_dir_entry.text())

    def set_crop_projections_checkbox(self):
        logging.debug("Crop projections: " + str(self.crop_checkbox.isChecked()))
        self.e_crop = bool(self.crop_checkbox.isChecked())

    def set_axis_bottom(self):
        logging.debug("Axis Bottom : " + str(self.axis_bottom_entry.text()))
        self.e_ax1 = int(self.axis_bottom_entry.text())

    def set_axis_top(self):
        logging.debug("Axis Top: " + str(self.axis_top_entry.text()))
        self.e_ax2 = int(self.axis_top_entry.text())

    def set_axis_group(self):
        if self.axis_group.isChecked():
            self.axis_bottom_label.setEnabled(False)
            self.axis_bottom_entry.setEnabled(False)
            self.axis_top_label.setEnabled(False)
            self.axis_top_entry.setEnabled(False)
            self.e_manual = True
            logging.debug("Enter axis of rotation manually: " + str(self.e_manual))
        else:
            self.axis_bottom_label.setEnabled(True)
            self.axis_bottom_entry.setEnabled(True)
            self.axis_top_label.setEnabled(True)
            self.axis_top_entry.setEnabled(True)
            self.e_manual = False
            logging.debug("Enter axis of rotation manually: " + str(self.e_manual))

    def set_z00(self):
        logging.debug("z00 axis: " + str(self.axis_z00_entry.text()))
        self.axis_dict['z00'] = int(self.axis_z00_entry.text())

    def set_z01(self):
        logging.debug("z01 axis: " + str(self.axis_z01_entry.text()))
        self.axis_dict['z01'] = int(self.axis_z01_entry.text())

    def set_z02(self):
        logging.debug("z02 axis: " + str(self.axis_z02_entry.text()))
        self.axis_dict['z02'] = int(self.axis_z02_entry.text())

    def set_z03(self):
        logging.debug("z03 axis: " + str(self.axis_z03_entry.text()))
        self.axis_dict['z03'] = int(self.axis_z03_entry.text())

    def set_z04(self):
        logging.debug("z04 axis: " + str(self.axis_z04_entry.text()))
        self.axis_dict['z04'] = int(self.axis_z04_entry.text())

    def set_z05(self):
        logging.debug("z05 axis: " + str(self.axis_z05_entry.text()))
        self.axis_dict['z05'] = int(self.axis_z05_entry.text())

    def set_z06(self):
        logging.debug("z06 axis: " + str(self.axis_z06_entry.text()))
        self.axis_dict['z06'] = int(self.axis_z06_entry.text())

    def set_z07(self):
        logging.debug("z07 axis: " + str(self.axis_z07_entry.text()))
        self.axis_dict['z07'] = int(self.axis_z07_entry.text())

    def set_z08(self):
        logging.debug("z08 axis: " + str(self.axis_z08_entry.text()))
        self.axis_dict['z08'] = int(self.axis_z08_entry.text())

    def set_z09(self):
        logging.debug("z09 axis: " + str(self.axis_z09_entry.text()))
        self.axis_dict['z09'] = int(self.axis_z09_entry.text())

    def set_z010(self):
        logging.debug("z010 axis: " + str(self.axis_z010_entry.text()))
        self.axis_dict['z010'] = int(self.axis_z010_entry.text())

    def set_z011(self):
        logging.debug("z011 axis: " + str(self.axis_z011_entry.text()))
        self.axis_dict['z011'] = int(self.axis_z011_entry.text())

    def stitch_button_pressed(self):
        logging.debug("Stitch button pressed")
        args = tk_args(self.e_input, self.e_output, self.e_tmpdir,
                       self.e_ax1, self.e_ax2, self.e_ax, self.e_crop, self.e_manual)

        print(self.axis_dict)
        #TODO: pass axis_dict to function and use it to determine axis

        if os.path.exists(self.e_tmpdir):
            os.system('rm -r {}'.format(self.e_tmpdir))

        if os.path.exists(self.e_output):
            raise ValueError('Output directory exists')

        print("")
        print("======= Begin 360 Multi-Stitch =======")
        main_360_mp_depth2(args)
        print("==== Waiting for Next Task ====")

    #TODO Call cleanup function if application is closed

    def delete_button_pressed(self):
        logging.debug("Delete button pressed")
        if os.path.exists(self.e_output):
            os.system('rm -r {}'.format(self.e_output))
            print(" - Directory with reconstructed data was removed")

    def help_button_pressed(self):
        logging.debug("Help button pressed")
        h = "Stitches images horizontally\n"
        h += "Directory structure is, f.i., Input/000, Input/001,...Input/00N\n"
        h += "Each 000, 001, ... 00N directory must have identical subdirectory \"Type\"\n"
        h += "Selected range of images from \"Type\" directory will be stitched vertically\n"
        h += "across all subdirectories in the Input directory"
        h += "to be added as options:\n"
        h += "(1) orthogonal reslicing, (2) interpolation, (3) horizontal stitching"
        QMessageBox.information(self, "Help", h)

class tk_args():
    def __init__(self, e_input, e_output, e_tmpdir, e_ax1, e_ax2, e_ax, e_crop, e_manual):

        self.args={}
        # directories
        self.args['input'] = str(e_input)
        setattr(self, 'input', self.args['input'])
        self.args['output'] = str(e_output)
        setattr(self, 'output', self.args['output'])
        self.args['tmpdir'] = str(e_tmpdir)
        setattr(self, 'tmpdir', self.args['tmpdir'])
        #hor stitch half acq mode
        self.args['ax1'] = int(e_ax1)
        setattr(self, 'ax1', self.args['ax1'])
        self.args['ax2'] = int(e_ax2)
        setattr(self, 'ax2', self.args['ax2'])
        self.args['ax'] = int(e_ax)
        setattr(self, 'ax', self.args['ax'])
        self.args['crop'] = int(e_crop)
        setattr(self, 'crop', self.args['crop'])
        self.args['manual'] = bool(e_manual)
        setattr(self, 'manual', self.args['manual'])
