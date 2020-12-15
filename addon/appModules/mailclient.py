# -*- coding: UTF-8 -*-
#A part of em Client addon for NVDA
#Copyright (C) 2020 Tony Malykh
#This file is covered by the GNU General Public License.
#See the file COPYING.txt for more details.

import addonHandler
import api
import appModuleHandler
import bisect
import config
import controlTypes
import ctypes
import globalPluginHandler
import gui
import json
import NVDAHelper
from NVDAObjects.behaviors import RowWithFakeNavigation, Dialog
from NVDAObjects.UIA import UIA
from NVDAObjects.window import winword
import operator
import re
import sayAllHandler
from scriptHandler import script, willSayAllResume
import speech
import struct
import textInfos
import time
import tones
import ui
import UIAHandler
import wx

debug = False
if debug:
    f = open("C:\\Users\\tony\\Dropbox\\1.txt", "w", encoding="utf-8")
def mylog(s):
    if debug:
        print(str(s), file=f)
        f.flush()

def myAssert(condition):
    if not condition:
        raise RuntimeError("Assertion failed")

class AppModule(appModuleHandler.AppModule):
    def chooseNVDAObjectOverlayClasses(self, obj, clsList):
        if obj.role == controlTypes.ROLE_LISTITEM:
            if obj.parent is not None and obj.parent.parent is not None and obj.parent.parent.role == controlTypes.ROLE_TABLE:
                clsList.insert(0, UIAGridRow)
                
    @script(description='Expand all messages in message view', gestures=['kb:NVDA+X'])
    def script_expandMessages(self, gesture):
        focus = api.getFocusObject()
        interceptor = focus.treeInterceptor
        if interceptor is None:
            ui.message(_("Not in message view!"))
            return
        headings = list(interceptor._iterNodesByType("heading2"))
        for heading in headings:
            if heading.obj.IA2Attributes.get('class', "") == "header header_gray":
                heading.obj.doAction()
        ui.message(_("Expanded"))
        ui.message(f"Found {len(headings)} headings")

class UIAGridRow(RowWithFakeNavigation,UIA):
    def _get_name(self):
        return ""
    def _get_value(self):
        result = []
        for child in self.children:
            if child.UIAElement.cachedControlType == UIAHandler.UIA_ImageControlTypeId:
                if child.columnHeaderText == "Read status":
                    if child.name == "False":
                        result.append("Unread")
                    elif child.name == "True":
                        pass
                    else:
                        result.append(child.columnHeaderText + ": " + child.name)
                elif child.name != "False":
                    if child.name == "True":
                        result.append(child.columnHeaderText)
                    else:
                        result.append(child.columnHeaderText + ": " + child.name)
            else:
                result.append(child.name)
        return " ".join(result)
    def _get_previous(self):
        prev = super()._get_previous()
        if prev is not None:
            return prev
        parent = self.parent.previous
        while parent is not None:
            if len(parent.children) > 0:
                return parent.children[-1]
            parent = parent.previous


    def _get_next(self):
        next = super()._get_next()
        if next is not None:
            return next
        parent = self.parent.next
        while parent is not None:
            if len(parent.children) > 0:
                return parent.children[0]
            parent = parent.next
