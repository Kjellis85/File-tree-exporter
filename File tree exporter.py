import sys
import os
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QGridLayout, QPushButton, QFileDialog, QTreeWidget, QTreeWidgetItem, QWidget, QCheckBox, QMenu, QFileIconProvider
)
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtCore import Qt, QSize, QFileInfo
from qt_material import apply_stylesheet  # Import qt-material for themes
# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
class CustomTreeWidgetItem(QTreeWidgetItem):
    def __lt__(self, other):
        # Check if "self" or "other" are folders
        self_is_folder = self.text(1) == "Folder"
        other_is_folder = other.text(1) == "Folder"
        # Folders should always come before files
        if self_is_folder and not other_is_folder:
            return True
        if not self_is_folder and other_is_folder:
            return False
        # If both are folders or both are files, sort based on the selected column
        column = self.treeWidget().sortColumn()
        # If sorting by "Type" (column 1), only sort files
        if column == 1 and not self_is_folder and not other_is_folder:
            return self.text(column).lower() < other.text(column).lower()
        # For other columns (including "Name"), sort normally
        return self.text(column).lower() < other.text(column).lower()
class FileExplorer(QMainWindow):
    ICON_SIZE = QSize(32, 32)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Structure Explorer")
        self.setGeometry(100, 100, 800, 600)
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        # Grid layout for buttons and checkbox
        self.grid_layout = QGridLayout()
        # Button to select folder
        self.select_folder_button = QPushButton("Select Folder")
        self.select_folder_button.clicked.connect(self.select_folder)
        self.grid_layout.addWidget(self.select_folder_button, 0, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        # Button to export folder structure as an image
        self.export_button = QPushButton("Export as Image")
        self.export_button.clicked.connect(self.export_as_image)
        self.grid_layout.addWidget(self.export_button, 0, 1, alignment=Qt.AlignmentFlag.AlignCenter)
        # Button to toggle all folders expanded or collapsed
        self.toggle_button = QPushButton("Expand/Collapse All Folders")
        self.toggle_button.clicked.connect(self.toggle_all_items)
        self.grid_layout.addWidget(self.toggle_button, 0, 2, alignment=Qt.AlignmentFlag.AlignCenter)
        # Checkbox to toggle file visibility
        self.show_files_checkbox = QCheckBox("Show Files in Addition to Folders")
        self.show_files_checkbox.setChecked(True)
        self.show_files_checkbox.stateChanged.connect(self.update_tree)
        self.grid_layout.addWidget(self.show_files_checkbox, 1, 0, 1, 3, alignment=Qt.AlignmentFlag.AlignCenter)
        # Add the grid layout to the main layout
        self.main_layout.addLayout(self.grid_layout)
        # TreeWidget to display the folder structure
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Name", "Type"])
        self.tree_widget.setIconSize(self.ICON_SIZE)
        self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.open_context_menu)
        self.main_layout.addWidget(self.tree_widget)
        # Enable sorting in QTreeWidget
        self.tree_widget.setSortingEnabled(True)
        # Set default sorting column to "Type" (column 1) and order to ascending
        self.tree_widget.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        # Icon provider for system icons
        self.icon_provider = QFileIconProvider()
        # Variable to hold the selected folder
        self.current_folder = None
        # Adjust button widths
        self.adjust_button_widths()
    def adjust_button_widths(self):
        """Adjusts the minimum width of buttons based on the length of their text."""
        buttons = [self.select_folder_button, self.export_button, self.toggle_button]
        if not buttons:
            return
        max_width = max(self.fontMetrics().horizontalAdvance(button.text()) for button in buttons) + 20  # 10px margin on each side
        for button in buttons:
            button.setMinimumWidth(max_width)
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.current_folder = folder
            self.update_tree()
    def update_tree(self):
        if not self.current_folder:
            return
        self.tree_widget.clear()
        # Create the root node for the selected folder
        root_item = QTreeWidgetItem(self.tree_widget, [os.path.basename(self.current_folder), "Folder"])
        root_item.setIcon(0, self.icon_provider.icon(QFileIconProvider.IconType.Folder))
        # Add subfolders and files
        self.add_items(root_item, self.current_folder)
        # Expand the root node
        root_item.setExpanded(True)
        # Dynamically adjust column width
        self.tree_widget.resizeColumnToContents(0)
        self.tree_widget.setColumnWidth(0, self.tree_widget.columnWidth(0) + 5)
    def add_items(self, parent_item, folder_path):
        """Adds folders and files to the tree."""
        show_files = self.show_files_checkbox.isChecked()
        file_count = 0  # Count the number of files in the folder
        subfolder_count = 0  # Count the number of subfolders in the folder
        # Separate items into folders and files
        folders = []
        files = []
        for item_name in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item_name)
            if os.path.isdir(item_path):
                folders.append(item_name)
            elif os.path.isfile(item_path):
                file_count += 1
                if show_files:
                    files.append(item_name)
        # Sort folders and files alphabetically
        folders.sort()
        files.sort()
        # Add folders first
        for folder_name in folders:
            subfolder_path = os.path.join(folder_path, folder_name)
            folder_item = CustomTreeWidgetItem(parent_item, [folder_name, "Folder"])
            folder_item.setIcon(0, self.icon_provider.icon(QFileIconProvider.IconType.Folder))
            self.add_items(folder_item, subfolder_path)  # Recursively add subfolders
            subfolder_count += 1
        # Add files after folders
        if show_files:
            for file_name in files:
                file_path = os.path.join(folder_path, file_name)
                # Get the file type (e.g., ".txt", ".jpg")
                file_extension = os.path.splitext(file_name)[1] if '.' in file_name else "Unknown"
                file_item = CustomTreeWidgetItem(parent_item, [file_name, file_extension])
                file_info = QFileInfo(file_path)
                file_item.setIcon(0, self.icon_provider.icon(file_info))
        # If the folder has no subfolders, show the number of files
        if subfolder_count == 0 and file_count > 0:
            file_count_text = f"{file_count} files"
            empty_item = CustomTreeWidgetItem(parent_item, [file_count_text, ""])
            empty_item.setForeground(0, Qt.GlobalColor.gray)
        # If the folder is completely empty, show "No files"
        if subfolder_count == 0 and file_count == 0:
            empty_item = CustomTreeWidgetItem(parent_item, ["No files", ""])
            empty_item.setForeground(0, Qt.GlobalColor.gray)
    def toggle_all_items(self):
        """Expands or collapses all folders in the tree."""
        if self.tree_widget.topLevelItemCount() == 0:
            logging.debug("No items in the tree.")
            return
        # Check if the first top-level item is expanded
        first_item = self.tree_widget.topLevelItem(0)
        is_expanded = first_item.isExpanded()
        logging.debug(f"The tree is {'expanded' if is_expanded else 'collapsed'}. Changing to {'collapsed' if is_expanded else 'expanded'}.")
        # Expand or collapse all items
        self.set_all_items_expanded(not is_expanded)
    def set_all_items_expanded(self, expand):
        """Sets all items in the tree to expanded or collapsed."""
        stack = []
        for i in range(self.tree_widget.topLevelItemCount()):
            stack.append(self.tree_widget.topLevelItem(i))
        while stack:
            item = stack.pop()
            if item is None:
                logging.warning("Found an invalid item in the tree.")
                continue
            logging.debug(f"{'Expanding' if expand else 'Collapsing'} item: {item.text(0)}")
            item.setExpanded(expand)
            for i in range(item.childCount()):
                child = item.child(i)
                if child is not None:
                    stack.append(child)
    def open_context_menu(self, position):
        """Opens a context menu to collapse or expand folders."""
        item = self.tree_widget.itemAt(position)
        if item:
            menu = QMenu(self)
            expand_action = menu.addAction("Expand All Subfolders")
            collapse_action = menu.addAction("Collapse All Subfolders")
            action = menu.exec(self.tree_widget.viewport().mapToGlobal(position))
            if action == expand_action:
                self.set_all_items_expanded_under(item, True)
            elif action == collapse_action:
                self.set_all_items_expanded_under(item, False)
    def set_all_items_expanded_under(self, item, expand):
        """Expands or collapses all subfolders under a given node."""
        stack = [item]
        while stack:
            current_item = stack.pop()
            current_item.setExpanded(expand)
            for i in range(current_item.childCount()):
                stack.append(current_item.child(i))
    def export_as_image(self):
        """Exports the entire tree as an image."""
        if self.tree_widget.topLevelItemCount() == 0:
            logging.warning("No items in the tree to export.")
            return
        # Select file path to save the image
        file_path, _ = QFileDialog.getSaveFileName(self, "Save as Image", "", "PNG Images (*.png);;JPEG Images (*.jpg)")
        if not file_path:
            return
        # Calculate total height for the entire tree
        total_height = self.tree_widget.header().height()
        for i in range(self.tree_widget.topLevelItemCount()):
            total_height += self.calculate_visible_item_height(self.tree_widget.topLevelItem(i))
        # Create a pixmap with the correct size
        pixmap = QPixmap(self.tree_widget.width(), total_height)
        pixmap.fill(Qt.GlobalColor.white)
        # Render the tree widget onto the pixmap
        painter = QPainter(pixmap)
        self.tree_widget.render(painter)
        painter.end()
        # Save the pixmap as an image
        if pixmap.save(file_path):
            logging.info(f"Image saved to {file_path}")
        else:
            logging.error("Failed to save the image.")
    def calculate_visible_item_height(self, item):
        """Recursively calculates the height of visible items in the tree."""
        height = self.tree_widget.sizeHintForRow(0)
        if not item.isExpanded():
            return height
        for i in range(item.childCount()):
            height += self.calculate_visible_item_height(item.child(i))
        return height
if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Apply qt-material theme
    apply_stylesheet(app, theme='light_blue_500.xml')  # Choose a theme, e.g., 'light_blue_500.xml'
    window = FileExplorer()
    window.show()
    sys.exit(app.exec())