#!/usr/bin/python
# -*- coding: utf-8 -*-

# INTEL CONFIDENTIAL
# Copyright 2014 Intel Corporation All Rights Reserved.
# The source code contained or described herein and all documents related
# to the source code ("Material") are owned by Intel Corporation or its
# suppliers or licensors. Title to the Material remains with Intel
# Corporation or its suppliers and licensors. The Material may contain
# trade secrets and proprietary and confidential information of Intel
# Corporation and its suppliers and licensors, and is protected by worldwide
# copyright and trade secret laws and treaty provisions. No part of the
# Material may be used, copied, reproduced, modified, published, uploaded,
# posted, transmitted, distributed, or disclosed in any way without
# Intel's prior express written permission.

# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or
# delivery of the Materials, either expressly, by implication, inducement,
# estoppel or otherwise. Any license under such intellectual property rights
# must be express and approved by Intel in writing.

# Unless otherwise agreed by Intel in writing, you may not remove or alter
# this notice or any other notice embedded in Materials by Intel or
# Intel's suppliers or licensors in any way.

######################################
#  Launchpad Blueprint Collector is an app with GUI which collects
#  all valid blueprints from existing project on launchpad via https://api.launchpad.net/devel/
#  Output for this app is the .csv file which is ready to be opened by Excel.
######################################

import csv
import sys
import time
import json
import urllib3
# For InsecureRequestWarning
urllib3.disable_warnings()
import datetime

from PyQt4 import QtGui
from PyQt4 import QtCore

OK = 0
ERROR = 1

OPENSTACK_BP_URL_PREFIX = "https://api.launchpad.net/devel/"
OPENSTACK_BP_URL_SUFFIX = "/valid_specifications?ws.size="


class BPCollector():

    def __init__(self, parent, output_file, project="openstack", extended=False, size=100, with_def_milestone=True):
        self.p = parent
        self.output_file = output_file
        self.project = project
        self.size = size
        self.bp_url = OPENSTACK_BP_URL_PREFIX + str(project) + OPENSTACK_BP_URL_SUFFIX + str(self.size)
        self.file_initialized = False
        self.with_def_milestone = with_def_milestone
        self.ext = extended
        self.allowed_cols = ['web_link', 'name', 'definition_status', 'implementation_status', 'milestone_link',
                             'summary', 'date_started', 'date_created']
        self.delimiter = "\t"

    def collect(self):
        self.p.print("Starting collecting valid blueprints for project: " + str(self.project))

        next_url = self.bp_url
        manager = urllib3.ProxyManager("https://proxy-chain.intel.com:911")
        self.p.setValue(0)
        while True:
            response = manager.request('GET', next_url).data.decode('utf8')
            try:
                content = json.loads(response)
            except:
                self.p.print("Project '" + str(self.project) + "' does not exist!"
                             " Example existing projects: nova, neutron, openstack...")
                return

            with open(self.output_file, "a", encoding='utf-8',  newline='') as bp_file:
                # NOTE: We could try different delimiters here:
                # "delimiter=self.delimiter, quotechar='|', quoting=csv.QUOTE_MINIMAL"
                csv_file = csv.writer(bp_file, dialect="excel")
                if not self.file_initialized:
                    total = float(content.get('total_size', 0))
                    self.p.p_step = float(100.0/total)
                    headers = []
                    if not self.ext:
                        for col in self.allowed_cols:
                            headers.append(str(col))
                    else:
                        for col in content['entries'][0].iterkeys():
                            headers.append(str(col))

                    csv_file.writerow(headers)
                    self.file_initialized = True

                for bp in content['entries']:
                    if not self.ext:
                        self.save_sorted_entry(bp, csv_file)
                    else:
                        self.save_entry(bp, csv_file)

            processed = int(content.get('start', 0)) + min((int(content.get('total_size', 0)) -
                                                            int(content.get('start', 0))), self.size)
            self.p.update_prog(min((int(content.get('total_size', 0)) - int(content.get('start', 0))), self.size))
            self.p.print("Processed " + str(processed) + " of " + str(content.get('total_size', "?")))

            time.sleep(0.05)

            next_url = content.get('next_collection_link', None)
            if not next_url:
                self.p.setValue(100)
                break

        self.p.print("End of process")

    def save_entry(self, bp, file_handler):
        try:
            line = []
            for (col, value) in bp.iteritems():
                if value is None:
                    if col == 'milestone_link' and self.with_def_milestone:
                        raise Exception("Milestone is None")
                    value = "Undefined"
                try:
                    value = str(value)
                except:
                    value = value.encode('utf-8', errors='replace')

                line.append(value)
            file_handler.writerow(line)
        except Exception as ex:
            if str(ex) == "Milestone is None":
                return
            self.p.print("Avoiding line: " + str(ex))

    def save_sorted_entry(self, bp, file_handler):
        try:
            line = []
            for col in self.allowed_cols:

                value = bp.get(col, "There is no such column")
                if value is None:
                    if col == 'milestone_link' and self.with_def_milestone:
                        raise Exception("Milestone is None")
                    value = ""
                try:
                    value = str(value)
                except:
                    value = value.encode('utf-8', errors='replace')

                # NOTE: We could try different delimiters here:
                # "delimiter=self.delimiter, quotechar='|', quoting=csv.QUOTE_MINIMAL"
                line.append(value)
            file_handler.writerow(line)
        except Exception as ex:
            if str(ex) == "Milestone is None":
                return
            self.p.print("Avoiding line: " + str(ex))


class MyThread(QtCore.QThread):
    print_trg = QtCore.pyqtSignal(str)
    pbar_trg = QtCore.pyqtSignal(float)
    stop_coll_trg = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(MyThread, self).__init__(parent)
        self.parent = parent

        # Progress customization.
        self.p_step = 1
        self.p_value = 0

    def setup(self):
        pass

    def print(self, msg):
        self.print_trg.emit(msg)

    def update_prog(self, amount=1):
        self.p_value += amount*self.p_step
        self.pbar_trg.emit(self.p_value)

    # Camel case here to be consistent with PyQt
    def setValue(self, value):
        self.pbar_trg.emit(value)

    def run(self):
        extended = False

        try:
            BPCollector(self, self.parent.output_file, self.parent.project, extended=extended,
                        with_def_milestone=(not self.parent.include_without_milestone.isChecked())).collect()

        except Exception as e:
            import traceback
            self.print(traceback.format_exc())
            self.print("Failed to collect bps " + str(e))

        self.stop_coll_trg.emit()


class MainWindow(QtGui.QDialog):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        QtGui.QMainWindow.__init__(self)
        self.resize(500, 400)
        self.setWindowTitle('Launchpad Blueprint collector. <Saa Team>')

        self.project = "nova"
        self.output_file = ""
        self.generate_output_filename()

        self.pbar = QtGui.QProgressBar(self)
        self.pbar.setValue(0)
        self.log = QtGui.QTextEdit()
        self.log.setReadOnly(True)
        self.chooseFile = QtGui.QPushButton("Choose Custom File Dir", self)
        self.filename = QtGui.QLabel("File output: " + self.output_file)
        self.collect = QtGui.QPushButton("Collect Blueprints", self)
        self.l1 = QtGui.QLabel("Project name (default = nova): ")
        self.include_without_milestone = QtGui.QCheckBox(self)
        self.include_without_milestone.setChecked(False)
        self.include_without_milestone.setText("Include blueprints with undefined milestone")
        self.proj = QtGui.QLineEdit(self)
        self.proj.setText(self.project)
        self.quit = QtGui.QPushButton("Quit", self)

        self.vbmain = QtGui.QVBoxLayout()

        self.hb1 = QtGui.QHBoxLayout()
        self.hb1.addWidget(self.filename)
        self.hb1.addWidget(self.chooseFile)
        self.vbmain.addLayout(self.hb1)

        self.hb2 = QtGui.QHBoxLayout()
        self.hb2.addWidget(self.l1)
        self.hb2.addWidget(self.proj)
        self.vbmain.addLayout(self.hb2)

        self.hb3 = QtGui.QHBoxLayout()
        self.hb3.addWidget(self.include_without_milestone)
        self.hb3.addWidget(self.collect)
        self.vbmain.addLayout(self.hb3)

        self.vbmain.addWidget(self.pbar)
        self.vbmain.addWidget(self.log)
        self.vbmain.addStretch(1)

        self.hbend = QtGui.QHBoxLayout()
        self.hbend.addStretch(1)
        self.hbend.addWidget(self.quit)
        self.vbmain.addLayout(self.hbend)

        self.setLayout(self.vbmain)

        self.proj.textChanged[str].connect(self.on_proj_changed)
        self.connect(self.chooseFile, QtCore.SIGNAL("clicked()"), self.chf_handler)
        self.connect(self.quit, QtCore.SIGNAL("clicked()"), self.quit_handler)
        self.connect(self.collect, QtCore.SIGNAL("clicked()"), self.collect_handler)

        self.thread = None
        self.is_collecting = False

    def generate_output_filename(self):
        d = datetime.datetime.now()
        self.output_file = "collected_bp_" + d.strftime('%Y-%m-%d_%H-%M-%S') + "_.csv"

    def on_proj_changed(self, text):
        if text:
            self.project = text

    def chf_handler(self):
        fname = QtGui.QFileDialog.getSaveFileName(self, "Output file")
        if fname:
            self.output_file = fname
            self.filename.setText("File output: " + self.output_file)

    def stop_if_collecting(self):
        if self.is_collecting:
            self.is_collecting = False
            self.collect.setText("Collect Blueprints")
            return True

        return False

    def collect_handler(self):

        if self.stop_if_collecting(): return

        if self.thread:
            try:
                self.thread.terminate()
            except:
                pass
            self.thread = None

        self.thread = MyThread(self)
        self.thread.print_trg.connect(self.print)
        self.thread.pbar_trg.connect(self.prog_value)
        self.thread.stop_coll_trg.connect(self.stop_if_collecting)
        self.thread.start()
        self.collect.setText("Stop collecting")
        self.is_collecting = True

    def prog_value(self, value):
        self.pbar.setValue(value)

    def print(self, msg):
        self.log.append(msg)

    def quit_handler(self):
        sys.exit()

app = QtGui.QApplication(sys.argv)
main = MainWindow()
main.show()
sys.exit(app.exec_())