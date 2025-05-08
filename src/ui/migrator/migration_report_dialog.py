"""
Copyright (c) Cutleast
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QListWidget,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.migrator.migration_report import MigrationReport
from core.utilities.exceptions import format_exception


class MigrationReportDialog(QDialog):
    """
    Dialog for displaying a migration report, returned by the migration process.
    """

    __report: MigrationReport

    __vlayout: QVBoxLayout
    __tab_widget: QTabWidget

    class ReportTab(QSplitter):
        """
        Tab for displaying a category of the migration report.
        """

        __errors: dict[str, str]

        __list_widget: QListWidget
        __error_text_box: QPlainTextEdit

        def __init__(self, parent: Optional[QWidget], errors: dict[str, str]) -> None:
            super().__init__(parent)

            self.__errors = errors

            self.__init_ui()
            self.__init_errors()

        def __init_ui(self) -> None:
            self.setOrientation(Qt.Orientation.Horizontal)

            self.__init_list_widget()
            self.__init_error_text_box()

        def __init_list_widget(self) -> None:
            self.__list_widget = QListWidget()
            self.__list_widget.setSelectionMode(
                QListWidget.SelectionMode.SingleSelection
            )
            self.__list_widget.setAlternatingRowColors(True)
            self.__list_widget.currentTextChanged.connect(self.__on_item_select)
            self.addWidget(self.__list_widget)

        def __init_error_text_box(self) -> None:
            self.__error_text_box = QPlainTextEdit()
            self.__error_text_box.setReadOnly(True)
            self.__error_text_box.setObjectName("protocol")
            self.addWidget(self.__error_text_box)

        def __init_errors(self) -> None:
            self.__list_widget.addItems(list(self.__errors.keys()))
            self.__list_widget.setCurrentRow(0)

        def __on_item_select(self, item_text: str) -> None:
            self.__error_text_box.setPlainText(self.__errors[item_text])

    __mods_tab: ReportTab
    __tools_tab: ReportTab
    __other_errors_tab: ReportTab

    def __init__(
        self, report: MigrationReport, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)

        self.__report = report

        self.setWindowTitle(self.tr("Migration Report"))
        self.resize(800, 400)

        self.__init_ui()

        if report.failed_mods:
            self.__tab_widget.setCurrentIndex(0)
        elif report.failed_tools:
            self.__tab_widget.setCurrentIndex(1)
        elif report.other_errors:
            self.__tab_widget.setCurrentIndex(2)

    def __init_ui(self) -> None:
        self.__vlayout = QVBoxLayout()
        self.setLayout(self.__vlayout)

        self.__tab_widget = QTabWidget()
        self.__tab_widget.tabBar().setExpanding(True)
        self.__tab_widget.setObjectName("centered_tab")
        self.__vlayout.addWidget(self.__tab_widget)

        self.__init_mods_tab()
        self.__init_tools_tab()
        self.__init_other_errors_tab()

        ok_button = QPushButton(self.tr("Ok"))
        ok_button.clicked.connect(self.accept)
        self.__vlayout.addWidget(ok_button)

    def __init_mods_tab(self) -> None:
        mods_errors: dict[str, str] = {
            mod.display_name: format_exception(e)
            for mod, e in self.__report.failed_mods.items()
        }

        self.__mods_tab = MigrationReportDialog.ReportTab(self, mods_errors)
        self.__tab_widget.addTab(
            self.__mods_tab, self.tr("Failed Mods") + f" ({len(mods_errors)})"
        )
        self.__tab_widget.setTabEnabled(0, len(mods_errors) > 0)

    def __init_tools_tab(self) -> None:
        tools_errors: dict[str, str] = {
            tool.display_name: format_exception(e)
            for tool, e in self.__report.failed_tools.items()
        }

        self.__tools_tab = MigrationReportDialog.ReportTab(self, tools_errors)
        self.__tab_widget.addTab(
            self.__tools_tab, self.tr("Failed Tools") + f" ({len(tools_errors)})"
        )
        self.__tab_widget.setTabEnabled(1, len(tools_errors) > 0)

    def __init_other_errors_tab(self) -> None:
        other_errors: dict[str, str] = {
            display_name: format_exception(e)
            for display_name, e in self.__report.other_errors.items()
        }

        self.__other_errors_tab = MigrationReportDialog.ReportTab(self, other_errors)
        self.__tab_widget.addTab(
            self.__other_errors_tab, self.tr("Other Errors") + f" ({len(other_errors)})"
        )
        self.__tab_widget.setTabEnabled(2, len(other_errors) > 0)
