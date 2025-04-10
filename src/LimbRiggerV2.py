from PySide2.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QSlider, QVBoxLayout, QWidget
from PySide2.QtCore import Qt
from maya.OpenMaya import MVector
import maya.OpenMayaUI as omui
import maya.mel as mel
import shiboken2
import maya.cmds as mc

def GetMayaMainWindow() -> QMainWindow:
    mainWindow = omui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(mainWindow), QMainWindow)

def DeleteWidgetWithName(name):
    for widget in GetMayaMainWindow().findChildren(QWidget, name):
        widget.deleteLater()

class MayaWindow(QWidget):
    def __init__(self):
        super().__init__(parent=GetMayaMainWindow())
        DeleteWidgetWithName(self.GetWidgetUniqueName())
        self.setWindowFlags(Qt.WindowType.Window)
        self.setObjectName(self.GetWidgetUniqueName())

    def GetWidgetUniqueName(self):
        return "lkansdlnwoasjvnsopavjnop"

class LimbRigger:
    def __init__(self):
        self.root = ""
        self.mid = ""
        self.end = ""
        self.controllerSize = 5
        self.controllerColor = [1.0, 1.0, 0.0]

    def FindJointsBasedOnSelection(self):
        try:
            self.root = mc.ls(sl=True, type="joint")[0]
            self.mid = mc.listRelatives(self.root, c=True, type="joint")[0]
            self.end = mc.listRelatives(self.mid, c=True, type="joint")[0]
        except Exception as e:
            raise Exception("Wrong Selection, please select the first joint of the limb!")

    def ApplyColorToController(self, ctrlName):
        shape = mc.listRelatives(ctrlName, shapes=True)[0]
        mc.setAttr(f"{shape}.overrideEnabled", 1)
        mc.setAttr(f"{shape}.overrideRGBColors", 1)
        mc.setAttr(f"{shape}.overrideColorRGB", *self.controllerColor)

    def CreateFKControllerForJoints(self, jntName):
        ctrlName = "ac_l_fk_" + jntName
        ctrlGrpName = ctrlName + "_grp"
        mc.circle(name=ctrlName, radius=self.controllerSize, normal=(1, 0, 0))
        mc.group(ctrlName, n=ctrlGrpName)
        mc.matchTransform(ctrlGrpName, jntName)
        mc.orientConstraint(ctrlName, jntName)
        self.ApplyColorToController(ctrlName)
        return ctrlName, ctrlGrpName

    def CreateBoxController(self, name):
        mel.eval(f"curve -n {name} -d 1 -p 0.5 0.5 0.5 -p 0.5 0.5 -0.5 -p -0.5 0.5 -0.5 -p -0.5 0.5 0.5 -p -0.5 -0.5 0.5 -p 0.5 -0.5 0.5 -p 0.5 -0.5 -0.5 -p -0.5 -0.5 -0.5 -p -0.5 0.5 -0.5 -p 0.5 0.5 -0.5 -p 0.5 -0.5 -0.5 -p 0.5 -0.5 0.5 -p 0.5 0.5 0.5 -p -0.5 0.5 0.5 -p -0.5 -0.5 0.5 -p -0.5 -0.5 -0.5 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15")
        mc.scale(self.controllerSize, self.controllerSize, self.controllerSize, name)
        mc.makeIdentity(name, apply=True)
        grpName = name + "_grp"
        mc.group(name, n=grpName)
        self.ApplyColorToController(name)
        return name, grpName

    def CreatePlusController(self, name):
        mel.eval(f"curve -n {name} -d 1 -p -1 -3 0 -p 1 -3 0 -p 1 -1 0 -p 3 -1 0 -p 3 1 0 -p 1 1 0 -p 1 3 0 -p -1 3 0 -p -1 1 0 -p -3 1 0 -p -3 -1 0 -p -1 -1 0 -p -1 -3 0 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12")
        grpName = name + "_grp"
        mc.group(name, n=grpName)
        self.ApplyColorToController(name)
        return name, grpName

    def GetObjectLocation(self, objectName):
        x, y, z = mc.xform(objectName, q=True, ws=True, t=True)
        return MVector(x, y, z)

    def PrintMVector(self, vector):
        print(f"<{vector.x}, {vector.y}, {vector.z}>")

    def RigLimb(self):
        rootCtrl, rootCtrlGrp = self.CreateFKControllerForJoints(self.root)
        midCtrl, midCtrlGrp = self.CreateFKControllerForJoints(self.mid)
        endCtrl, endtCtrlGrp = self.CreateFKControllerForJoints(self.end)

        mc.parent(midCtrlGrp, rootCtrl)
        mc.parent(endtCtrlGrp, midCtrl)

        ikEndCtrl = "ac_ik_" + self.end
        ikEndCtrl, ikEndCtrlGrp = self.CreateBoxController(ikEndCtrl)
        mc.matchTransform(ikEndCtrlGrp, self.end)
        endOrientConstraint = mc.orientConstraint(ikEndCtrl, self.end)[0]

        rootJntLoc = self.GetObjectLocation(self.root)
        self.PrintMVector(rootJntLoc)

        ikHandleName = "ikHandle_" + self.end
        mc.ikHandle(n=ikHandleName, sol="ikRPsolver", sj=self.root, ee=self.end)

        poleVectorLocationVals = mc.getAttr(ikHandleName + ".poleVector")[0]
        poleVector = MVector(*poleVectorLocationVals)
        poleVector.normal()

        endJntLoc = self.GetObjectLocation(self.end)
        rootToEndVector = endJntLoc - rootJntLoc
        poleVectorCtrlLoc = rootJntLoc + rootToEndVector / 2 + poleVector * rootToEndVector.length()

        poleVectorCtrl = "ac_ik_" + self.mid
        mc.spaceLocator(n=poleVectorCtrl)
        poleVectorCtrlGrp = poleVectorCtrl + "_grp"
        mc.group(poleVectorCtrl, n=poleVectorCtrlGrp)
        mc.setAttr(poleVectorCtrlGrp + ".t", poleVectorCtrlLoc.x, poleVectorCtrlLoc.y, poleVectorCtrlLoc.z, typ="double3")

        mc.poleVectorConstraint(poleVectorCtrl, ikHandleName)

        ikfkBlendCtrl = "ac_ikfk_blend_" + self.root
        ikfkBlendCtrl, ikfkBlendCtrlGrp = self.CreatePlusController(ikfkBlendCtrl)
        mc.setAttr(ikfkBlendCtrl + ".t", rootJntLoc.x * 2, rootJntLoc.y, rootJntLoc.z * 2, typ="double3")

        ikfkBlendAttrName = "ikfkBlend"
        mc.addAttr(ikEndCtrlGrp, ln=ikfkBlendAttrName, min=0, max=1, k=True)
        ikfkBlendAttr = ikfkBlendCtrl + "." + ikfkBlendAttrName

        mc.expression(s=f"{ikHandleName}.ikBlend={ikfkBlendAttr}")
        mc.expression(s=f"{ikEndCtrl}.v={poleVectorCtrlGrp}.v={ikfkBlendAttr}")
        mc.expression(s=f"{rootCtrlGrp}.v=1-{ikfkBlendAttr}")
        mc.expression(s=f"{endOrientConstraint}.{endCtrl}W0 = 1-{ikfkBlendAttr}")
        mc.expression(s=f"{endOrientConstraint}.{ikEndCtrl}W1 = {ikfkBlendAttr}")

        topGrpName = f"{self.root}_rig_grp"
        mc.group([rootCtrlGrp, ikEndCtrlGrp, poleVectorCtrlGrp, ikfkBlendCtrlGrp], n=topGrpName)
        mc.parent(ikHandleName, ikEndCtrl)

class LimbRiggerWidget(MayaWindow):
    def __init__(self):
        super().__init__()
        self.rigger = LimbRigger()
        self.setWindowTitle("Limb Rigger")

        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)

        toolTipLabel = QLabel("Select the first joint of the limb, and press the auto find button")
        self.masterLayout.addWidget(toolTipLabel)

        self.jntsListLineEdit = QLineEdit()
        self.masterLayout.addWidget(self.jntsListLineEdit)
        self.jntsListLineEdit.setEnabled(False)

        autoFindJntBtn = QPushButton("Auto Find")
        autoFindJntBtn.clicked.connect(self.AutoFindJntBtnClicked)
        self.masterLayout.addWidget(autoFindJntBtn)

        ctrlSizeSlider = QSlider()
        ctrlSizeSlider.setOrientation(Qt.Horizontal)
        ctrlSizeSlider.setRange(1, 30)
        ctrlSizeSlider.setValue(self.rigger.controllerSize)
        self.ctrlSizeLabel = QLabel(f"{self.rigger.controllerSize}")
        ctrlSizeSlider.valueChanged.connect(self.CtrlSizeSliderChanged)

        self.masterLayout.addWidget(ctrlSizeSlider)
        self.masterLayout.addWidget(self.ctrlSizeLabel)

        colorLayout = QHBoxLayout()
        self.rEdit = QLineEdit("1.0")
        self.gEdit = QLineEdit("1.0")
        self.bEdit = QLineEdit("0.0")
        for edit in [self.rEdit, self.gEdit, self.bEdit]:
            edit.setFixedWidth(40)
            colorLayout.addWidget(edit)

        colorBtn = QPushButton("Set Color")
        colorBtn.clicked.connect(self.UpdateColor)
        colorLayout.addWidget(colorBtn)
        self.masterLayout.addLayout(colorLayout)

        rigLimbBtn = QPushButton("Rig Limb")
        rigLimbBtn.clicked.connect(lambda: self.rigger.RigLimb())
        self.masterLayout.addWidget(rigLimbBtn)

    def CtrlSizeSliderChanged(self, newValue):
        self.ctrlSizeLabel.setText(f"{newValue}")
        self.rigger.controllerSize = newValue

    def AutoFindJntBtnClicked(self):
        try:
            self.rigger.FindJointsBasedOnSelection()
            self.jntsListLineEdit.setText(f"{self.rigger.root},{self.rigger.mid},{self.rigger.end}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"{e}")

    def UpdateColor(self):
        try:
            r = float(self.rEdit.text())
            g = float(self.gEdit.text())
            b = float(self.bEdit.text())
            if not all(0.0 <= c <= 1.0 for c in [r, g, b]):
                raise ValueError("RGB values must be between 0 and 1.")
            self.rigger.controllerColor = [r, g, b]
        except Exception as e:
            QMessageBox.critical(self, "Invalid Color", str(e))

limbRiggerWidget = LimbRiggerWidget()
limbRiggerWidget.show()