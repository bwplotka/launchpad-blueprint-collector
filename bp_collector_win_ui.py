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
######################################

import sys
import json
import urllib3
urllib3.disable_warnings()
# For InsecureRequestWarning
import datetime

from tkinter import Tk, BOTH
from tkinter.ttk import Frame, Button, Style

OK = 0
ERROR = 1

OPENSTACK_BP_URL_PREFIX = "https://api.launchpad.net/devel/"
OPENSTACK_BP_URL_SUFFIX = "/valid_specifications?ws.size="


class BPCollector():

    def __init__(self, output_file, project="openstack", extended=False, size=100, with_def_milestone=True):

        self.output_file = output_file #str(os.path.realpath(__file__) + output_file)
        self.project = project
        self.size = size
        self.bp_url = OPENSTACK_BP_URL_PREFIX + str(project) + OPENSTACK_BP_URL_SUFFIX + str(self.size)
        self.file_initialized = False
        self.with_def_milestone= with_def_milestone
        self.ext = extended
        self.allowed_cols = ['web_link', 'name', 'definition_status', 'implementation_status', 'milestone_link',
                             'summary', 'date_started', 'date_created']

    def collect(self):
        print("Starting collecting valid blueprints for project: " + str(self.project))

        next_url = self.bp_url
        manager = urllib3.ProxyManager("https://proxy-chain.intel.com:911")
        while True:
            content = json.loads(manager.request('GET', next_url).data.decode('utf8'))

            with open(self.output_file, "a") as bp_file:
                if not self.file_initialized:
                    headers = ""
                    if not self.ext:
                        for col in self.allowed_cols:
                            headers += str(col).replace(";", "") + ";"
                    else:
                        for col in content['entries'][0].iterkeys():
                            headers += str(col).replace(";", "") + ";"
                    headers += "\n"
                    bp_file.write(headers)
                    self.file_initialized = True

                for bp in content['entries']:
                    if not self.ext:
                        self.save_sorted_entry(bp, bp_file)
                    else:
                        self.save_entry(bp, bp_file)

            processed = int(content.get('start', 0)) + min((int(content.get('total_size', 0)) - int(content.get('start', 0))), self.size)
            print("Processed " + str(processed) + " of " + str(content.get('total_size', "?")))

            next_url = content.get('next_collection_link', None)
            if not next_url:
                break

        print("End of process")

    def save_entry(self, bp, file_handler):
        try:
            line = ""
            for (col,value) in bp.iteritems():
                if value is None:
                    if col == 'milestone_link' and self.with_def_milestone:
                        raise Exception("Milestone is None")
                    value = ""
                try:
                    value = str(value)
                except:
                    value = value.encode('utf-8', errors='replace')

                line += value.replace(";", "").replace("\n", "|") + ";"
            line += "\n"
            file_handler.write(line)
        except Exception as ex:
            if str(ex) == "Milestone is None":
                return
            print("Avoiding line: " + str(ex))

    def save_sorted_entry(self, bp, file_handler):
        try:
            line = ""
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

                line += value.replace(";", "").replace("\n", "|") + ";"
            line += "\n"
            file_handler.write(line)
        except Exception as ex:
            if str(ex) == "Milestone is None":
                return
            print("Avoiding line: " + str(ex))


class CollectorFrame(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent)

        self.parent = parent

        self.init_UI()
        self.center_window()

    def init_UI(self):

        self.parent.title("Launchpad Blueprint Collector. <SAA Team>")
        self.style = Style()
        self.style.theme_use("default")

        self.pack(fill=BOTH, expand=1)

        quitButton = Button(self, text="Quit",
            command=self.quit)
        quitButton.place(x=50, y=50)

    def center_window(self):
        w = 290
        h = 150

        sw = self.parent.winfo_screenwidth()
        sh = self.parent.winfo_screenheight()

        x = (sw - w)/2
        y = (sh - h)/2
        self.parent.geometry('%dx%d+%d+%d' % (w, h, x, y))



def main():

    root = Tk()
    app = CollectorFrame(root)
    root.mainloop()

    # d = datetime.datetime.now()
    # output_file = None
    # project = "nova"
    # extended = False
    #
    # if not output_file:
    #     output_file = "collected_bp_" + project + "_" + d.strftime('%Y-%m-%d_%H-%M-%S') + "_.csv"
    # try:
    #     BPCollector(output_file, project, extended=extended).collect()
    #
    # except Exception as e:
    #     import traceback
    #     print(traceback.format_exc())
    #     print("Failed to collect bps " + str(e))
    #     return ERROR

    return OK


if __name__ == "__main__":
    sys.exit(main())