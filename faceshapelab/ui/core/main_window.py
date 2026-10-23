# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MainWindow.ui'
##
## Created by: Qt User Interface Compiler version 6.12.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QDockWidget, QFormLayout, QGridLayout, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMainWindow, QMenu, QMenuBar, QPushButton,
    QScrollArea, QSizePolicy, QSlider, QSpacerItem,
    QStatusBar, QTreeView, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1344, 800)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.panelsLayout = QHBoxLayout(self.centralwidget)
        self.panelsLayout.setObjectName(u"panelsLayout")
        self.leftPanel = QGroupBox(self.centralwidget)
        self.leftPanel.setObjectName(u"leftPanel")
        self.leftPanel.setAcceptDrops(True)
        self.leftPanelLayout = QVBoxLayout(self.leftPanel)
        self.leftPanelLayout.setObjectName(u"leftPanelLayout")
        self.leftImage = QLabel(self.leftPanel)
        self.leftImage.setObjectName(u"leftImage")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.leftImage.sizePolicy().hasHeightForWidth())
        self.leftImage.setSizePolicy(sizePolicy)
        self.leftImage.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.leftPanelLayout.addWidget(self.leftImage)

        self.leftPlaybackLayout = QVBoxLayout()
        self.leftPlaybackLayout.setObjectName(u"leftPlaybackLayout")
        self.leftPlaybackLayout.setContentsMargins(0, 0, 0, 0)
        self.leftTimelineSlider = QSlider(self.leftPanel)
        self.leftTimelineSlider.setObjectName(u"leftTimelineSlider")
        self.leftTimelineSlider.setEnabled(False)
        self.leftTimelineSlider.setMaximum(0)
        self.leftTimelineSlider.setPageStep(2000)
        self.leftTimelineSlider.setOrientation(Qt.Orientation.Horizontal)

        self.leftPlaybackLayout.addWidget(self.leftTimelineSlider)

        self.leftTransportLayout = QHBoxLayout()
        self.leftTransportLayout.setObjectName(u"leftTransportLayout")
        self.leftSkipBackwardButton = QPushButton(self.leftPanel)
        self.leftSkipBackwardButton.setObjectName(u"leftSkipBackwardButton")
        self.leftSkipBackwardButton.setEnabled(False)

        self.leftTransportLayout.addWidget(self.leftSkipBackwardButton)

        self.leftPlayPauseButton = QPushButton(self.leftPanel)
        self.leftPlayPauseButton.setObjectName(u"leftPlayPauseButton")
        self.leftPlayPauseButton.setEnabled(False)

        self.leftTransportLayout.addWidget(self.leftPlayPauseButton)

        self.leftSkipForwardButton = QPushButton(self.leftPanel)
        self.leftSkipForwardButton.setObjectName(u"leftSkipForwardButton")
        self.leftSkipForwardButton.setEnabled(False)

        self.leftTransportLayout.addWidget(self.leftSkipForwardButton)

        self.leftTimeLabel = QLabel(self.leftPanel)
        self.leftTimeLabel.setObjectName(u"leftTimeLabel")
        self.leftTimeLabel.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.leftTransportLayout.addWidget(self.leftTimeLabel)


        self.leftPlaybackLayout.addLayout(self.leftTransportLayout)


        self.leftPanelLayout.addLayout(self.leftPlaybackLayout)

        self.leftPreviewModeComboBox = QComboBox(self.leftPanel)
        self.leftPreviewModeComboBox.addItem("")
        self.leftPreviewModeComboBox.addItem("")
        self.leftPreviewModeComboBox.setObjectName(u"leftPreviewModeComboBox")

        self.leftPanelLayout.addWidget(self.leftPreviewModeComboBox)

        self.leftControls = QGroupBox(self.leftPanel)
        self.leftControls.setObjectName(u"leftControls")
        self.leftControlsGrid = QGridLayout(self.leftControls)
        self.leftControlsGrid.setObjectName(u"leftControlsGrid")
        self.leftDetectFacesButton = QPushButton(self.leftControls)
        self.leftDetectFacesButton.setObjectName(u"leftDetectFacesButton")

        self.leftControlsGrid.addWidget(self.leftDetectFacesButton, 0, 0, 1, 1)

        self.leftDetectLandmarksButton = QPushButton(self.leftControls)
        self.leftDetectLandmarksButton.setObjectName(u"leftDetectLandmarksButton")

        self.leftControlsGrid.addWidget(self.leftDetectLandmarksButton, 0, 1, 1, 1)

        self.leftSaveFaceButton = QPushButton(self.leftControls)
        self.leftSaveFaceButton.setObjectName(u"leftSaveFaceButton")

        self.leftControlsGrid.addWidget(self.leftSaveFaceButton, 1, 0, 1, 1)

        self.leftSaveCroppedFaceButton = QPushButton(self.leftControls)
        self.leftSaveCroppedFaceButton.setObjectName(u"leftSaveCroppedFaceButton")

        self.leftControlsGrid.addWidget(self.leftSaveCroppedFaceButton, 1, 1, 1, 1)

        self.leftSelectedFaceComboBox = QComboBox(self.leftControls)
        self.leftSelectedFaceComboBox.setObjectName(u"leftSelectedFaceComboBox")

        self.leftControlsGrid.addWidget(self.leftSelectedFaceComboBox, 2, 0, 1, 2)


        self.leftPanelLayout.addWidget(self.leftControls)

        self.leftPanelLayout.setStretch(0, 1)

        self.panelsLayout.addWidget(self.leftPanel)

        self.rightPanel = QGroupBox(self.centralwidget)
        self.rightPanel.setObjectName(u"rightPanel")
        self.rightPanel.setAcceptDrops(True)
        self.rightPanelLayout = QVBoxLayout(self.rightPanel)
        self.rightPanelLayout.setObjectName(u"rightPanelLayout")
        self.rightImage = QLabel(self.rightPanel)
        self.rightImage.setObjectName(u"rightImage")
        sizePolicy.setHeightForWidth(self.rightImage.sizePolicy().hasHeightForWidth())
        self.rightImage.setSizePolicy(sizePolicy)
        self.rightImage.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.rightPanelLayout.addWidget(self.rightImage)

        self.rightPlaybackLayout = QVBoxLayout()
        self.rightPlaybackLayout.setObjectName(u"rightPlaybackLayout")
        self.rightPlaybackLayout.setContentsMargins(0, 0, 0, 0)
        self.rightTimelineSlider = QSlider(self.rightPanel)
        self.rightTimelineSlider.setObjectName(u"rightTimelineSlider")
        self.rightTimelineSlider.setEnabled(False)
        self.rightTimelineSlider.setMaximum(0)
        self.rightTimelineSlider.setPageStep(2000)
        self.rightTimelineSlider.setOrientation(Qt.Orientation.Horizontal)

        self.rightPlaybackLayout.addWidget(self.rightTimelineSlider)

        self.rightTransportLayout = QHBoxLayout()
        self.rightTransportLayout.setObjectName(u"rightTransportLayout")
        self.rightSkipBackwardButton = QPushButton(self.rightPanel)
        self.rightSkipBackwardButton.setObjectName(u"rightSkipBackwardButton")
        self.rightSkipBackwardButton.setEnabled(False)

        self.rightTransportLayout.addWidget(self.rightSkipBackwardButton)

        self.rightPlayPauseButton = QPushButton(self.rightPanel)
        self.rightPlayPauseButton.setObjectName(u"rightPlayPauseButton")
        self.rightPlayPauseButton.setEnabled(False)

        self.rightTransportLayout.addWidget(self.rightPlayPauseButton)

        self.rightSkipForwardButton = QPushButton(self.rightPanel)
        self.rightSkipForwardButton.setObjectName(u"rightSkipForwardButton")
        self.rightSkipForwardButton.setEnabled(False)

        self.rightTransportLayout.addWidget(self.rightSkipForwardButton)

        self.rightTimeLabel = QLabel(self.rightPanel)
        self.rightTimeLabel.setObjectName(u"rightTimeLabel")
        self.rightTimeLabel.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.rightTransportLayout.addWidget(self.rightTimeLabel)


        self.rightPlaybackLayout.addLayout(self.rightTransportLayout)


        self.rightPanelLayout.addLayout(self.rightPlaybackLayout)

        self.rightPreviewModeComboBox = QComboBox(self.rightPanel)
        self.rightPreviewModeComboBox.addItem("")
        self.rightPreviewModeComboBox.addItem("")
        self.rightPreviewModeComboBox.setObjectName(u"rightPreviewModeComboBox")

        self.rightPanelLayout.addWidget(self.rightPreviewModeComboBox)

        self.rightControls = QGroupBox(self.rightPanel)
        self.rightControls.setObjectName(u"rightControls")
        self.rightControlsGrid = QGridLayout(self.rightControls)
        self.rightControlsGrid.setObjectName(u"rightControlsGrid")
        self.rightDetectFacesButton = QPushButton(self.rightControls)
        self.rightDetectFacesButton.setObjectName(u"rightDetectFacesButton")

        self.rightControlsGrid.addWidget(self.rightDetectFacesButton, 0, 0, 1, 1)

        self.rightDetectLandmarksButton = QPushButton(self.rightControls)
        self.rightDetectLandmarksButton.setObjectName(u"rightDetectLandmarksButton")

        self.rightControlsGrid.addWidget(self.rightDetectLandmarksButton, 0, 1, 1, 1)

        self.rightSaveFaceButton = QPushButton(self.rightControls)
        self.rightSaveFaceButton.setObjectName(u"rightSaveFaceButton")

        self.rightControlsGrid.addWidget(self.rightSaveFaceButton, 1, 0, 1, 1)

        self.rightSaveCroppedFaceButton = QPushButton(self.rightControls)
        self.rightSaveCroppedFaceButton.setObjectName(u"rightSaveCroppedFaceButton")

        self.rightControlsGrid.addWidget(self.rightSaveCroppedFaceButton, 1, 1, 1, 1)

        self.rightSelectedFaceComboBox = QComboBox(self.rightControls)
        self.rightSelectedFaceComboBox.setObjectName(u"rightSelectedFaceComboBox")

        self.rightControlsGrid.addWidget(self.rightSelectedFaceComboBox, 2, 0, 1, 2)


        self.rightPanelLayout.addWidget(self.rightControls)

        self.rightPanelLayout.setStretch(0, 1)

        self.panelsLayout.addWidget(self.rightPanel)

        self.panelsLayout.setStretch(0, 1)
        self.panelsLayout.setStretch(1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1344, 33))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.filesFoldersDock = QDockWidget(MainWindow)
        self.filesFoldersDock.setObjectName(u"filesFoldersDock")
        self.filesFoldersContents = QWidget()
        self.filesFoldersContents.setObjectName(u"filesFoldersContents")
        self.filesFoldersLayout = QVBoxLayout(self.filesFoldersContents)
        self.filesFoldersLayout.setObjectName(u"filesFoldersLayout")
        self.folderPickerLayout = QHBoxLayout()
        self.folderPickerLayout.setObjectName(u"folderPickerLayout")
        self.folderPath = QLineEdit(self.filesFoldersContents)
        self.folderPath.setObjectName(u"folderPath")
        self.folderPath.setReadOnly(True)

        self.folderPickerLayout.addWidget(self.folderPath)

        self.browseFolderButton = QPushButton(self.filesFoldersContents)
        self.browseFolderButton.setObjectName(u"browseFolderButton")

        self.folderPickerLayout.addWidget(self.browseFolderButton)


        self.filesFoldersLayout.addLayout(self.folderPickerLayout)

        self.filesTree = QTreeView(self.filesFoldersContents)
        self.filesTree.setObjectName(u"filesTree")
        self.filesTree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.filesTree.setDragEnabled(True)
        self.filesTree.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.filesTree.setDefaultDropAction(Qt.DropAction.CopyAction)
        self.filesTree.setUniformRowHeights(True)
        self.filesTree.setSortingEnabled(True)

        self.filesFoldersLayout.addWidget(self.filesTree)

        self.filesFoldersDock.setWidget(self.filesFoldersContents)
        MainWindow.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.filesFoldersDock)
        self.savedFilesDock = QDockWidget(MainWindow)
        self.savedFilesDock.setObjectName(u"savedFilesDock")
        self.savedFilesContents = QWidget()
        self.savedFilesContents.setObjectName(u"savedFilesContents")
        self.savedFilesLayout = QVBoxLayout(self.savedFilesContents)
        self.savedFilesLayout.setObjectName(u"savedFilesLayout")
        self.outputFolderLabel = QLabel(self.savedFilesContents)
        self.outputFolderLabel.setObjectName(u"outputFolderLabel")

        self.savedFilesLayout.addWidget(self.outputFolderLabel)

        self.outputFolderPickerLayout = QHBoxLayout()
        self.outputFolderPickerLayout.setObjectName(u"outputFolderPickerLayout")
        self.outputFolderPath = QLineEdit(self.savedFilesContents)
        self.outputFolderPath.setObjectName(u"outputFolderPath")

        self.outputFolderPickerLayout.addWidget(self.outputFolderPath)

        self.browseOutputFolderButton = QPushButton(self.savedFilesContents)
        self.browseOutputFolderButton.setObjectName(u"browseOutputFolderButton")

        self.outputFolderPickerLayout.addWidget(self.browseOutputFolderButton)


        self.savedFilesLayout.addLayout(self.outputFolderPickerLayout)

        self.refreshOutputsButton = QPushButton(self.savedFilesContents)
        self.refreshOutputsButton.setObjectName(u"refreshOutputsButton")

        self.savedFilesLayout.addWidget(self.refreshOutputsButton)

        self.outputThumbnailsScrollArea = QScrollArea(self.savedFilesContents)
        self.outputThumbnailsScrollArea.setObjectName(u"outputThumbnailsScrollArea")
        self.outputThumbnailsScrollArea.setWidgetResizable(True)
        self.outputThumbnailsContents = QWidget()
        self.outputThumbnailsContents.setObjectName(u"outputThumbnailsContents")
        self.outputThumbnailsContents.setGeometry(QRect(0, 0, 244, 172))
        self.outputThumbnailsGrid = QGridLayout(self.outputThumbnailsContents)
        self.outputThumbnailsGrid.setObjectName(u"outputThumbnailsGrid")
        self.outputThumbnailsScrollArea.setWidget(self.outputThumbnailsContents)

        self.savedFilesLayout.addWidget(self.outputThumbnailsScrollArea)

        self.savedFilesLayout.setStretch(3, 1)
        self.savedFilesDock.setWidget(self.savedFilesContents)
        MainWindow.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.savedFilesDock)
        self.faceSettingsDock = QDockWidget(MainWindow)
        self.faceSettingsDock.setObjectName(u"faceSettingsDock")
        self.faceSettingsContents = QWidget()
        self.faceSettingsContents.setObjectName(u"faceSettingsContents")
        self.faceSettingsLayout = QVBoxLayout(self.faceSettingsContents)
        self.faceSettingsLayout.setObjectName(u"faceSettingsLayout")
        self.detectorsGroup = QGroupBox(self.faceSettingsContents)
        self.detectorsGroup.setObjectName(u"detectorsGroup")
        self.detectorsFormLayout = QFormLayout(self.detectorsGroup)
        self.detectorsFormLayout.setObjectName(u"detectorsFormLayout")
        self.recognitionModelLabel = QLabel(self.detectorsGroup)
        self.recognitionModelLabel.setObjectName(u"recognitionModelLabel")

        self.detectorsFormLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.recognitionModelLabel)

        self.recognitionModelComboBox = QComboBox(self.detectorsGroup)
        self.recognitionModelComboBox.addItem("")
        self.recognitionModelComboBox.addItem("")
        self.recognitionModelComboBox.addItem("")
        self.recognitionModelComboBox.addItem("")
        self.recognitionModelComboBox.setObjectName(u"recognitionModelComboBox")

        self.detectorsFormLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.recognitionModelComboBox)

        self.faceDetectModelLabel = QLabel(self.detectorsGroup)
        self.faceDetectModelLabel.setObjectName(u"faceDetectModelLabel")

        self.detectorsFormLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.faceDetectModelLabel)

        self.faceDetectModelComboBox = QComboBox(self.detectorsGroup)
        self.faceDetectModelComboBox.addItem("")
        self.faceDetectModelComboBox.addItem("")
        self.faceDetectModelComboBox.addItem("")
        self.faceDetectModelComboBox.addItem("")
        self.faceDetectModelComboBox.setObjectName(u"faceDetectModelComboBox")

        self.detectorsFormLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.faceDetectModelComboBox)

        self.detectScoreLabel = QLabel(self.detectorsGroup)
        self.detectScoreLabel.setObjectName(u"detectScoreLabel")

        self.detectorsFormLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.detectScoreLabel)

        self.detectScoreSlider = QSlider(self.detectorsGroup)
        self.detectScoreSlider.setObjectName(u"detectScoreSlider")
        self.detectScoreSlider.setMinimum(1)
        self.detectScoreSlider.setMaximum(100)
        self.detectScoreSlider.setSingleStep(1)
        self.detectScoreSlider.setValue(50)
        self.detectScoreSlider.setOrientation(Qt.Orientation.Horizontal)

        self.detectorsFormLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.detectScoreSlider)

        self.landmarkDetectModelLabel = QLabel(self.detectorsGroup)
        self.landmarkDetectModelLabel.setObjectName(u"landmarkDetectModelLabel")

        self.detectorsFormLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.landmarkDetectModelLabel)

        self.landmarkDetectModelComboBox = QComboBox(self.detectorsGroup)
        self.landmarkDetectModelComboBox.addItem("")
        self.landmarkDetectModelComboBox.addItem("")
        self.landmarkDetectModelComboBox.addItem("")
        self.landmarkDetectModelComboBox.addItem("")
        self.landmarkDetectModelComboBox.addItem("")
        self.landmarkDetectModelComboBox.addItem("")
        self.landmarkDetectModelComboBox.addItem("")
        self.landmarkDetectModelComboBox.addItem("")
        self.landmarkDetectModelComboBox.addItem("")
        self.landmarkDetectModelComboBox.addItem("")
        self.landmarkDetectModelComboBox.addItem("")
        self.landmarkDetectModelComboBox.setObjectName(u"landmarkDetectModelComboBox")

        self.detectorsFormLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.landmarkDetectModelComboBox)

        self.landmarkDetectScoreLabel = QLabel(self.detectorsGroup)
        self.landmarkDetectScoreLabel.setObjectName(u"landmarkDetectScoreLabel")

        self.detectorsFormLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.landmarkDetectScoreLabel)

        self.landmarkDetectScoreSlider = QSlider(self.detectorsGroup)
        self.landmarkDetectScoreSlider.setObjectName(u"landmarkDetectScoreSlider")
        self.landmarkDetectScoreSlider.setMinimum(1)
        self.landmarkDetectScoreSlider.setMaximum(100)
        self.landmarkDetectScoreSlider.setSingleStep(1)
        self.landmarkDetectScoreSlider.setValue(50)
        self.landmarkDetectScoreSlider.setOrientation(Qt.Orientation.Horizontal)

        self.detectorsFormLayout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.landmarkDetectScoreSlider)

        self.showLandmarksCheckBox = QCheckBox(self.detectorsGroup)
        self.showLandmarksCheckBox.setObjectName(u"showLandmarksCheckBox")
        self.showLandmarksCheckBox.setChecked(False)

        self.detectorsFormLayout.setWidget(5, QFormLayout.ItemRole.SpanningRole, self.showLandmarksCheckBox)

        self.showBoundingBoxesCheckBox = QCheckBox(self.detectorsGroup)
        self.showBoundingBoxesCheckBox.setObjectName(u"showBoundingBoxesCheckBox")
        self.showBoundingBoxesCheckBox.setChecked(False)

        self.detectorsFormLayout.setWidget(6, QFormLayout.ItemRole.SpanningRole, self.showBoundingBoxesCheckBox)

        self.compareFacesButton = QPushButton(self.detectorsGroup)
        self.compareFacesButton.setObjectName(u"compareFacesButton")

        self.detectorsFormLayout.setWidget(7, QFormLayout.ItemRole.SpanningRole, self.compareFacesButton)


        self.faceSettingsLayout.addWidget(self.detectorsGroup)

        self.faceSettingsVerticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.faceSettingsLayout.addItem(self.faceSettingsVerticalSpacer)

        self.faceSettingsDock.setWidget(self.faceSettingsContents)
        MainWindow.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.faceSettingsDock)
#if QT_CONFIG(shortcut)
        self.outputFolderLabel.setBuddy(self.outputFolderPath)
        self.recognitionModelLabel.setBuddy(self.recognitionModelComboBox)
        self.faceDetectModelLabel.setBuddy(self.faceDetectModelComboBox)
        self.detectScoreLabel.setBuddy(self.detectScoreSlider)
        self.landmarkDetectModelLabel.setBuddy(self.landmarkDetectModelComboBox)
        self.landmarkDetectScoreLabel.setBuddy(self.landmarkDetectScoreSlider)
#endif // QT_CONFIG(shortcut)

        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(MainWindow)

        self.landmarkDetectModelComboBox.setCurrentIndex(5)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"FaceShapeLab", None))
        self.leftPanel.setTitle(QCoreApplication.translate("MainWindow", u"Media 1", None))
#if QT_CONFIG(accessibility)
        self.leftImage.setAccessibleName(QCoreApplication.translate("MainWindow", u"Media 1 image", None))
#endif // QT_CONFIG(accessibility)
        self.leftImage.setText(QCoreApplication.translate("MainWindow", u"Drop an image or video", None))
#if QT_CONFIG(tooltip)
        self.leftTimelineSlider.setToolTip(QCoreApplication.translate("MainWindow", u"Scrub to a frame", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.leftTimelineSlider.setAccessibleName(QCoreApplication.translate("MainWindow", u"Media 1 timeline", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(tooltip)
        self.leftSkipBackwardButton.setToolTip(QCoreApplication.translate("MainWindow", u"Skip backward 2 seconds", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.leftSkipBackwardButton.setAccessibleName(QCoreApplication.translate("MainWindow", u"Media 1: skip backward 2 seconds", None))
#endif // QT_CONFIG(accessibility)
        self.leftSkipBackwardButton.setText(QCoreApplication.translate("MainWindow", u"-2 s", None))
#if QT_CONFIG(tooltip)
        self.leftPlayPauseButton.setToolTip(QCoreApplication.translate("MainWindow", u"Play or pause", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.leftPlayPauseButton.setAccessibleName(QCoreApplication.translate("MainWindow", u"Media 1: play or pause", None))
#endif // QT_CONFIG(accessibility)
        self.leftPlayPauseButton.setText(QCoreApplication.translate("MainWindow", u"Play", None))
#if QT_CONFIG(tooltip)
        self.leftSkipForwardButton.setToolTip(QCoreApplication.translate("MainWindow", u"Skip forward 2 seconds", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.leftSkipForwardButton.setAccessibleName(QCoreApplication.translate("MainWindow", u"Media 1: skip forward 2 seconds", None))
#endif // QT_CONFIG(accessibility)
        self.leftSkipForwardButton.setText(QCoreApplication.translate("MainWindow", u"+2 s", None))
        self.leftTimeLabel.setText(QCoreApplication.translate("MainWindow", u"00:00 / 00:00", None))
        self.leftPreviewModeComboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"Original", None))
        self.leftPreviewModeComboBox.setItemText(1, QCoreApplication.translate("MainWindow", u"Face", None))

#if QT_CONFIG(accessibility)
        self.leftPreviewModeComboBox.setAccessibleName(QCoreApplication.translate("MainWindow", u"Media 1 preview mode", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(tooltip)
        self.leftPreviewModeComboBox.setToolTip(QCoreApplication.translate("MainWindow", u"Original image with annotations or the selected face aligned and cropped.", None))
#endif // QT_CONFIG(tooltip)
        self.leftControls.setTitle(QCoreApplication.translate("MainWindow", u"Controls", None))
        self.leftDetectFacesButton.setText(QCoreApplication.translate("MainWindow", u"Detect Faces", None))
        self.leftDetectLandmarksButton.setText(QCoreApplication.translate("MainWindow", u"Detect Landmarks", None))
        self.leftSaveFaceButton.setText(QCoreApplication.translate("MainWindow", u"Save Face", None))
        self.leftSaveCroppedFaceButton.setText(QCoreApplication.translate("MainWindow", u"Save Cropped Face", None))
#if QT_CONFIG(accessibility)
        self.leftSelectedFaceComboBox.setAccessibleName(QCoreApplication.translate("MainWindow", u"Selected face", None))
#endif // QT_CONFIG(accessibility)
        self.leftSelectedFaceComboBox.setPlaceholderText(QCoreApplication.translate("MainWindow", u"No detected faces", None))
        self.rightPanel.setTitle(QCoreApplication.translate("MainWindow", u"Media 2", None))
#if QT_CONFIG(accessibility)
        self.rightImage.setAccessibleName(QCoreApplication.translate("MainWindow", u"Media 2 image", None))
#endif // QT_CONFIG(accessibility)
        self.rightImage.setText(QCoreApplication.translate("MainWindow", u"Drop an image or video", None))
#if QT_CONFIG(tooltip)
        self.rightTimelineSlider.setToolTip(QCoreApplication.translate("MainWindow", u"Scrub to a frame", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.rightTimelineSlider.setAccessibleName(QCoreApplication.translate("MainWindow", u"Media 2 timeline", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(tooltip)
        self.rightSkipBackwardButton.setToolTip(QCoreApplication.translate("MainWindow", u"Skip backward 2 seconds", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.rightSkipBackwardButton.setAccessibleName(QCoreApplication.translate("MainWindow", u"Media 2: skip backward 2 seconds", None))
#endif // QT_CONFIG(accessibility)
        self.rightSkipBackwardButton.setText(QCoreApplication.translate("MainWindow", u"-2 s", None))
#if QT_CONFIG(tooltip)
        self.rightPlayPauseButton.setToolTip(QCoreApplication.translate("MainWindow", u"Play or pause", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.rightPlayPauseButton.setAccessibleName(QCoreApplication.translate("MainWindow", u"Media 2: play or pause", None))
#endif // QT_CONFIG(accessibility)
        self.rightPlayPauseButton.setText(QCoreApplication.translate("MainWindow", u"Play", None))
#if QT_CONFIG(tooltip)
        self.rightSkipForwardButton.setToolTip(QCoreApplication.translate("MainWindow", u"Skip forward 2 seconds", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(accessibility)
        self.rightSkipForwardButton.setAccessibleName(QCoreApplication.translate("MainWindow", u"Media 2: skip forward 2 seconds", None))
#endif // QT_CONFIG(accessibility)
        self.rightSkipForwardButton.setText(QCoreApplication.translate("MainWindow", u"+2 s", None))
        self.rightTimeLabel.setText(QCoreApplication.translate("MainWindow", u"00:00 / 00:00", None))
        self.rightPreviewModeComboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"Original", None))
        self.rightPreviewModeComboBox.setItemText(1, QCoreApplication.translate("MainWindow", u"Face", None))

#if QT_CONFIG(accessibility)
        self.rightPreviewModeComboBox.setAccessibleName(QCoreApplication.translate("MainWindow", u"Media 2 preview mode", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(tooltip)
        self.rightPreviewModeComboBox.setToolTip(QCoreApplication.translate("MainWindow", u"Original image with annotations or the selected face aligned and cropped.", None))
#endif // QT_CONFIG(tooltip)
        self.rightControls.setTitle(QCoreApplication.translate("MainWindow", u"Controls", None))
        self.rightDetectFacesButton.setText(QCoreApplication.translate("MainWindow", u"Detect Faces", None))
        self.rightDetectLandmarksButton.setText(QCoreApplication.translate("MainWindow", u"Detect Landmarks", None))
        self.rightSaveFaceButton.setText(QCoreApplication.translate("MainWindow", u"Save Face", None))
        self.rightSaveCroppedFaceButton.setText(QCoreApplication.translate("MainWindow", u"Save Cropped Face", None))
#if QT_CONFIG(accessibility)
        self.rightSelectedFaceComboBox.setAccessibleName(QCoreApplication.translate("MainWindow", u"Selected face", None))
#endif // QT_CONFIG(accessibility)
        self.rightSelectedFaceComboBox.setPlaceholderText(QCoreApplication.translate("MainWindow", u"No detected faces", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"&File", None))
        self.filesFoldersDock.setWindowTitle(QCoreApplication.translate("MainWindow", u"Browse Files", None))
#if QT_CONFIG(accessibility)
        self.folderPath.setAccessibleName(QCoreApplication.translate("MainWindow", u"Selected folder", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(tooltip)
        self.browseFolderButton.setToolTip(QCoreApplication.translate("MainWindow", u"Select a folder", None))
#endif // QT_CONFIG(tooltip)
        self.browseFolderButton.setText(QCoreApplication.translate("MainWindow", u"Browse\u2026", None))
#if QT_CONFIG(accessibility)
        self.filesTree.setAccessibleName(QCoreApplication.translate("MainWindow", u"Files and folders", None))
#endif // QT_CONFIG(accessibility)
        self.savedFilesDock.setWindowTitle(QCoreApplication.translate("MainWindow", u"Saved Files", None))
        self.outputFolderLabel.setText(QCoreApplication.translate("MainWindow", u"Output Folder", None))
#if QT_CONFIG(accessibility)
        self.outputFolderPath.setAccessibleName(QCoreApplication.translate("MainWindow", u"Output Folder", None))
#endif // QT_CONFIG(accessibility)
#if QT_CONFIG(tooltip)
        self.browseOutputFolderButton.setToolTip(QCoreApplication.translate("MainWindow", u"Set output folder", None))
#endif // QT_CONFIG(tooltip)
        self.browseOutputFolderButton.setText(QCoreApplication.translate("MainWindow", u"Browse\u2026", None))
        self.refreshOutputsButton.setText(QCoreApplication.translate("MainWindow", u"Refresh Outputs", None))
#if QT_CONFIG(accessibility)
        self.outputThumbnailsScrollArea.setAccessibleName(QCoreApplication.translate("MainWindow", u"Output thumbnails", None))
#endif // QT_CONFIG(accessibility)
        self.faceSettingsDock.setWindowTitle(QCoreApplication.translate("MainWindow", u"Face Settings", None))
        self.detectorsGroup.setTitle(QCoreApplication.translate("MainWindow", u"Detectors", None))
        self.recognitionModelLabel.setText(QCoreApplication.translate("MainWindow", u"Recognition Model", None))
        self.recognitionModelComboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"Inswapper128ArcFace", None))
        self.recognitionModelComboBox.setItemText(1, QCoreApplication.translate("MainWindow", u"SimSwapArcFace", None))
        self.recognitionModelComboBox.setItemText(2, QCoreApplication.translate("MainWindow", u"GhostArcFace", None))
        self.recognitionModelComboBox.setItemText(3, QCoreApplication.translate("MainWindow", u"CSCSArcFace", None))

#if QT_CONFIG(accessibility)
        self.recognitionModelComboBox.setAccessibleName(QCoreApplication.translate("MainWindow", u"Recognition Model", None))
#endif // QT_CONFIG(accessibility)
        self.faceDetectModelLabel.setText(QCoreApplication.translate("MainWindow", u"Face Detect Model", None))
        self.faceDetectModelComboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"RetinaFace", None))
        self.faceDetectModelComboBox.setItemText(1, QCoreApplication.translate("MainWindow", u"Yolov8", None))
        self.faceDetectModelComboBox.setItemText(2, QCoreApplication.translate("MainWindow", u"SCRFD", None))
        self.faceDetectModelComboBox.setItemText(3, QCoreApplication.translate("MainWindow", u"Yunet", None))

#if QT_CONFIG(accessibility)
        self.faceDetectModelComboBox.setAccessibleName(QCoreApplication.translate("MainWindow", u"Face Detect Model", None))
#endif // QT_CONFIG(accessibility)
        self.detectScoreLabel.setText(QCoreApplication.translate("MainWindow", u"Detect Score", None))
#if QT_CONFIG(accessibility)
        self.detectScoreSlider.setAccessibleName(QCoreApplication.translate("MainWindow", u"Detect Score", None))
#endif // QT_CONFIG(accessibility)
        self.landmarkDetectModelLabel.setText(QCoreApplication.translate("MainWindow", u"Landmark Detect Model", None))
        self.landmarkDetectModelComboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"5", None))
        self.landmarkDetectModelComboBox.setItemText(1, QCoreApplication.translate("MainWindow", u"68", None))
        self.landmarkDetectModelComboBox.setItemText(2, QCoreApplication.translate("MainWindow", u"3d68", None))
        self.landmarkDetectModelComboBox.setItemText(3, QCoreApplication.translate("MainWindow", u"98", None))
        self.landmarkDetectModelComboBox.setItemText(4, QCoreApplication.translate("MainWindow", u"106", None))
        self.landmarkDetectModelComboBox.setItemText(5, QCoreApplication.translate("MainWindow", u"203", None))
        self.landmarkDetectModelComboBox.setItemText(6, QCoreApplication.translate("MainWindow", u"478", None))
        self.landmarkDetectModelComboBox.setItemText(7, QCoreApplication.translate("MainWindow", u"tufa98", None))
        self.landmarkDetectModelComboBox.setItemText(8, QCoreApplication.translate("MainWindow", u"tufa314", None))
        self.landmarkDetectModelComboBox.setItemText(9, QCoreApplication.translate("MainWindow", u"orformer98", None))
        self.landmarkDetectModelComboBox.setItemText(10, QCoreApplication.translate("MainWindow", u"hrffa", None))

#if QT_CONFIG(accessibility)
        self.landmarkDetectModelComboBox.setAccessibleName(QCoreApplication.translate("MainWindow", u"Landmark Detect Model", None))
#endif // QT_CONFIG(accessibility)
        self.landmarkDetectScoreLabel.setText(QCoreApplication.translate("MainWindow", u"Landmark Detect Score", None))
#if QT_CONFIG(accessibility)
        self.landmarkDetectScoreSlider.setAccessibleName(QCoreApplication.translate("MainWindow", u"Landmark Detect Score", None))
#endif // QT_CONFIG(accessibility)
        self.showLandmarksCheckBox.setText(QCoreApplication.translate("MainWindow", u"Show Landmarks", None))
        self.showBoundingBoxesCheckBox.setText(QCoreApplication.translate("MainWindow", u"Show Bounding Boxes", None))
        self.compareFacesButton.setText(QCoreApplication.translate("MainWindow", u"Compare Selected Faces", None))
    # retranslateUi

