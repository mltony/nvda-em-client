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
import eventHandler
import globalPluginHandler
import gui
import json
import NVDAHelper
from NVDAObjects.behaviors import RowWithFakeNavigation, Dialog, Notification
from NVDAObjects.UIA import UIA
from NVDAObjects.window import winword
import operator
import re
from speech import sayAll
from scriptHandler import script, willSayAllResume
import speech
import struct
import textInfos
import time
import tones
import ui
import UIAHandler
from UIAHandler.utils import createUIAMultiPropertyCondition
import winUser
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



def printTree3(obj, level=10, indent=0):
    result = []
    indentStr = " "*indent
    if obj is None:
        return f"{indentStr}<None>"
    if level < 0:
        return f"{indentStr}..."
    name = obj.name or "<None>"
    if "\n" in name:
        indentStr2 = indentStr + "    "
        name = "\n" + "\n".join(
            [
                indentStr2 + s
                for s in name.split("\n")
            ]
        )
    desc = f"{indentStr}{controlTypes.roleLabels[obj.role]} {name}"
    result.append(desc)
    ni = indent+4
    li = level-1
    child = obj.simpleFirstChild
    while child is not None:
        result.append(printTree3(child, li, ni))
        child = child.simpleNext
    return "\n".join(result)

def getWindow(focus):
    if focus.parent is None:
        raise Exception("Desktop window is focused!")
    while focus.parent.parent is not None:
        focus = focus.parent
    return focus


def     findDocument(window=None):
    if window is None:
        window = api.getForegroundObject()
    document = window.simpleFirstChild.simpleNext
    if document.role != controlTypes.ROLE_DOCUMENT:
        raise Exception(f"Failed to find document. Debug:\n{printTree3(window)}")
    return document

def findSubDocument(window=None):
    document = findDocument(window)
    subdocument = document.simpleLastChild
    if subdocument.role != controlTypes.ROLE_DOCUMENT:
        subdocument = subdocument.simplePrevious
    if subdocument.role != controlTypes.ROLE_DOCUMENT:
        raise Exception(f"Failed to find subdocument. Debug:\n{printTree3(document)}")
    return subdocument

def findTopLevelObject(focus=None, window=None):
    if window is None:
        window = api.getForegroundObject()
    if focus is None:
        focus = api.getFocusObject()
    while focus.parent is not None:
        if focus.simpleParent == window:
            return focus
        focus = focus.simpleParent
    raise Exception("Something went wrong!")

def traverseText(obj):
    child = obj.simpleFirstChild
    if child is None and obj.name is not None and len(obj.name) > 0:
        yield obj.name
    while child is not None:
        for s in traverseText(child):
            yield s
        child = child.simpleNext


def speakObject(document):
    # Try also using:
    # sayAllHandler.readObjects(document)
    generator = traverseText(document)
    def callback():
        try:
            text = generator.__next__()
        except StopIteration:
            return
        speech.speak([text, speech.commands.CallbackCommand(callback)])

    callback()

class AppModule(appModuleHandler.AppModule):
    def chooseNVDAObjectOverlayClasses(self, obj, clsList):
        if obj.role == controlTypes.ROLE_LISTITEM:
            if obj.parent is not None and obj.parent.parent is not None and obj.parent.role == controlTypes.ROLE_TABLE:
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
        ui.message(_("Expanded%d messages") % len(headings))


class UIAGridRow(RowWithFakeNavigation,UIA):
    # Translators: name of the column that denotes read status in the messages table
    readStatus = _("Read status")
    shouldAllowUIAFocusEvent = True
    def _get_name(self):
        return ""

    def getChildren(self, obj=None):
        if obj is None:
            obj = self
        # Collecting all children as a single request in order to make this real fast - code adopted from Outlook appModule
        childrenCacheRequest=UIAHandler.handler.baseCacheRequest.clone()
        childrenCacheRequest.addProperty(UIAHandler.UIA_NamePropertyId)
        childrenCacheRequest.addProperty(UIAHandler.UIA_TableItemColumnHeaderItemsPropertyId)
        childrenCacheRequest.TreeScope=UIAHandler.TreeScope_Children
        # We must filter the children for just text and image elements otherwise getCachedChildren fails completely in conversation view.
        childrenCacheRequest.treeFilter=createUIAMultiPropertyCondition({UIAHandler.UIA_ControlTypePropertyId:[UIAHandler.UIA_TextControlTypeId,UIAHandler.UIA_ImageControlTypeId]})
        cachedChildren=obj.UIAElement.buildUpdatedCache(childrenCacheRequest).getCachedChildren()
        return  cachedChildren
    def _get_value(self):
        result = []
        cachedChildren = self.getChildren()
        for index in range(cachedChildren.length):
            child = cachedChildren.getElement(index)
            name = child.CachedName
            if child.cachedControlType == UIAHandler.UIA_ImageControlTypeId:
                # I adore the beauty of COM interfaces!
                columnHeaderText = child.getCachedPropertyValueEx(UIAHandler.UIA_TableItemColumnHeaderItemsPropertyId,True).QueryInterface(UIAHandler.IUIAutomationElementArray).getElement(0).CurrentName
                if columnHeaderText == self.readStatus:
                    if name == "False":
                        result.append("Unread")
                    elif name == "True":
                        pass
                    else:
                        result.append(columnHeaderText + ": " + name)
                elif name != "False":
                    if name == "True":
                        result.append(columnHeaderText)
                    else:
                        result.append(columnHeaderText + ": " + name)
            else:
                result.append(name)
        return " ".join(result)

        cachedChildren = self.getChildren()
    def findNextUnread(self, direction, errorMsg):
        readStatusIndex = -1
        cachedChildren = self.getChildren()
        for index in range(cachedChildren.length):
            child = cachedChildren.GetElement(index)
            columnHeaderText = child.getCachedPropertyValueEx(UIAHandler.UIA_TableItemColumnHeaderItemsPropertyId,True).QueryInterface(UIAHandler.IUIAutomationElementArray).getElement(0).CurrentName
            if columnHeaderText == self.readStatus:
                readStatusIndex = index
                break
        if readStatusIndex < 0:
            raise Exception("Could not find read status column")
        obj = self
        for i in range(1000):
            obj = obj.next if direction > 0 else obj.previous
            if obj is None:
                ui.message(errorMsg)
                return
            cachedChildren = self.getChildren(obj)
            name = cachedChildren.GetElement(readStatusIndex).CachedName
            if name == "False":
                obj.setFocus()
                return
        raise Exception("Could not find unread email after 1000 iterations!")

    @script(description='Find next unread email', gestures=['kb:N'])
    def script_nextUnread(self, gesture):
        return self.findNextUnread(1, _("No next unread email"))

    @script(description='Find previous unread email', gestures=['kb:P'])
    def script_previousUnread(self, gesture):
        return self.findNextUnread(-1, _("No next previous email"))
    """
    def _get_previous(self):
        prev = super()._get_previous()
        if prev is not None:
            return prev
        parent = self.parent
        counter = 0
        while parent.previous is not None and parent.role == parent.previous.role:
            parent = parent.previous
            if len(parent.children) > 0:
                if counter > 0:
                    # We must have skipped over a collapsed section. Beep to let user know.
                    tones.beep(200, 50)
                return parent.children[-1]
            counter += 1
        return None



    def _get_next(self):
        next = super()._get_next()
        if next is not None:
            return next
        parent = self.parent
        counter = 0
        while parent.next is not None and parent.role == parent.next.role:
            parent = parent.next
            if len(parent.children) > 0:
                if counter > 0:
                    # We must have skipped over a collapsed section. Beep to let user know.
                    tones.beep(200, 50)
                return parent.children[0]
            counter  += 1
        return None
    """
    @script(description='Read current email message.', gestures=['kb:NVDA+DownArrow'])
    def script_readEmail(self, gesture):
        document = findSubDocument()
        speakObject(document)

