import sys
from PySide6 import QtCore, QtWidgets, QtGui, Qt3DCore, Qt3DExtras, QtOpenGL
from collections.abc import ItemsView, KeysView, Iterable
import json
from Classes import Room

app = QtWidgets.QApplication(sys.argv)

room = Room(3, 4, 5)
room.set_room_temperature(25)
room.set_wall_uvalues([20, 5, 5, 5, 5, 10])
room.calculate_wall_heat_losses()
room.calculate_room_heat_loss()
print(room.heat_loss)
#room.set_wall_uvalue(2, 20)
room.set_width(10)
print(room.heat_loss)


class GraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setWindowTitle("Test")

        self.scene = QtWidgets.QGraphicsScene()
        self.view = GraphicsView(self.scene)
        self.setCentralWidget(self.view)

        rectangle = QtWidgets.QGraphicsRectItem(QtCore.QRectF(0, 0, 100, 100))
        rectangle.setBrush(QtGui.QColor("red"))
        self.scene.addItem(rectangle)
        rectangle.moveBy(1000, 2000)

        # Top top bar (with generic tabs such as file, edit, view, etc)
        self.menubar = QtWidgets.QMenuBar()
        self.file_menu = self.menubar.addMenu("File")
        self.file_action = self.file_menu.addAction("Open")
        self.file_action.triggered.connect(self.open_model_file)
        self.save_action = self.file_menu.addAction("Save")
        self.save_action.triggered.connect(self.save_model_to_file)
        self.save_as_action = self.file_menu.addAction("Save As...")
        self.save_as_action.triggered.connect(self.save_model_as)
        self.setMenuBar(self.menubar)

        # Secondary bar (functionality to be decided)
        self.toolbar = QtWidgets.QToolBar()
        self.addToolBar(self.toolbar)
        self.toolbar.setMovable(False)
        self.toolbar.addAction("One")
        self.toolbar.addAction("Two")  # TODO Design toolbar for creation of rooms and walls withim rooms

        # Docked sidebar with workspace and properties
        properties = QtWidgets.QPushButton("Hello", self)
        properties2 = QtWidgets.QPushButton("Hello2", self)

        self.properties_table = QtWidgets.QTableWidget()

        # Create tree widget, add functionality for item clicked
        self.tree_widget = QtWidgets.QTreeWidget()
        self.tree_widget.setHeaderLabel("Model")
        self.tree_widget.itemClicked.connect(self.on_tree_item_clicked)  # TODO hide table when item or tree is deselected
        self.tree_widget.itemSelectionChanged.connect(self.on_tree_item_selection_changed)

        #self.populate_tree(room, self.tree_widget)

        # Workflow widget
        self.workflow = QtWidgets.QDockWidget()
        self.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, self.workflow)
        self.dock_widget = QtWidgets.QWidget()
        self.workflow.setWidget(self.dock_widget)
        self.workflow_layout = QtWidgets.QVBoxLayout(self.dock_widget)
        self.workflow_layout.addWidget(self.tree_widget)
        self.workflow_layout.addWidget(self.properties_table)
        self.workflow_layout.addWidget(properties)
        self.workflow_layout.addWidget(properties2)

        self.workflow.setLayout(self.workflow_layout)

        self.workflow.setWindowTitle("Workflow")
        self.workflow.resize(QtCore.QSize(300, 300))
        self.workflow.setMinimumWidth(200)
        self.workflow.setMaximumHeight(1000)

    # File dialog when "File" is clicked
    # Open a model file
    def open_model_file(self):
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open File")
        if file_name:
            self.load_model(file_name)

    # Reads JSON model file and creates Python object from it, populates tree
    def load_model(self, file_name):
        if not file_name.lower().endswith('.vfs'):
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid file format. Please select a .vfs file.")
            return
        try:
            with open(file_name, 'r') as file:
                model = json.load(file)
                room = Room.from_dict(model)
                self.populate_tree(room, self.tree_widget)
                QtWidgets.QMessageBox.information(self, "Open", "File opened successfully")
        except FileNotFoundError:
            QtWidgets.QMessageBox.warning(self, "Error", "File not found.")
        except json.JSONDecodeError:
            QtWidgets.QMessageBox.warning(self, "Error", "The file is not a valid JSON file.")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"An error occurred: {e}")

    def save_model_as(self):
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save File")
        self.save_model_to_file(file_name)

    # Creates model JSON file at given file path
    def save_model_to_file(self, file_name):  # TODO: replace file_name with open file name
        if file_name:
            if not file_name.endswith('.vfs'):
                file_name += '.vfs'
            try:
                with open(file_name, 'w') as file:
                    json.dump(room, file, indent=4, default=lambda o: o.__dict__)
                QtWidgets.QMessageBox.information(self, "Open", "File saved successfully")
            except PermissionError:
                QtWidgets.QMessageBox.warning(self, "Error", "You do not have permission to write to this file.")
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"An error occurred: {e}")

    # Checks if any item in the tree is selected and shows/hides the properties table accordingly
    def on_tree_item_selection_changed(self):
        selected_items = self.tree_widget.selectedItems()
        if selected_items:
            self.properties_table.show()
        else:
            self.properties_table.hide()

    # Set property table data and display it for selected tree item
    def on_tree_item_clicked(self, item, column):
        properties_table = self.create_properties_table(item)
        self.set_table_data(item, properties_table)

    def create_properties_table(self, item):
        object = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        if object is not None:
            properties = object.__dict__.keys()
            properties_list = self.remove_excluded_properties(object, properties)

            properties_widget = QtWidgets.QTableWidget()  # TODO Stylesheet
            properties_widget.setRowCount(len(properties_list))
            properties_widget.setColumnCount(2)
            properties_widget.setShowGrid(False)
            properties_widget.setHorizontalHeaderLabels(["Property", "Value"])
            properties_widget.verticalHeader().setVisible(False)

            # Make first column non-editable as it will contain the property names
            for i in range(len(properties_list)):
                fixed_item = QtWidgets.QTableWidgetItem()  # Create a new item for each row
                fixed_item.setText(properties_list[i])
                fixed_item.setFlags(QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEnabled)  # Make non-editable
                properties_widget.setItem(i, 0, fixed_item)

            # Add items to second column ready for values to be inputted later
            for i in range(len(properties_list)):
                editable_item = QtWidgets.QTableWidgetItem()  # Create a new item for each row of properties
                properties_widget.setItem(i, 1, editable_item)

            properties_widget.resizeColumnsToContents()
            return properties_widget
        return QtWidgets.QWidget()  # Passes empty widget if no includable properties are found

    def remove_excluded_properties(self, object, properties_list):
        exclude_attributes = self.return_excluded_attributes_list(object)

        if isinstance(properties_list, KeysView):
            # Filter out excluded keys and return as a list
            filtered_properties = [key for key in properties_list if key not in exclude_attributes]
        elif isinstance(properties_list, ItemsView):
            # Filter out excluded key-value pairs and return as a dictionary
            filtered_properties = [(key, value) for key, value in properties_list if key not in exclude_attributes]
        else:
            raise TypeError("Expected a dict_keys or dict_items object")

        return filtered_properties

    @staticmethod
    def return_excluded_attributes_list(object):
        # Ensure the object has the method to get the exclude list
        if hasattr(object, 'get_exclude_list'):
            return object.get_exclude_list()
        else:
            return []

    def set_table_data(self, item, table):
        # Get a list of all property names and values from the wall_data object
        # Extract the data object (e.g., Room, Wall) stored in the clicked item
        data_object = item.data(0, QtCore.Qt.ItemDataRole.UserRole)

        if data_object is not None:
            properties = data_object.__dict__.items()
            properties = self.remove_excluded_properties(data_object, properties)  # Returns a list of (key, value) tuples

            # Iterate over the properties and populate the table
            for i, (property_name, property_value) in enumerate(properties):
                # Skip properties that are in the exclude list or are complex class instances
                if not isinstance(property_value, (int, float, str, bool)):
                    continue

                # Ensure the index is within the table's row count
                if i < table.rowCount():
                    # Set the property value in the second column
                    value_item = QtWidgets.QTableWidgetItem(str(property_value))
                    table.setItem(i, 1, value_item)

        # Find the index of the current properties table in the layout
        for i in range(self.workflow_layout.count()):
            widget = self.workflow_layout.itemAt(i).widget()
            if widget == self.properties_table:
                index = i
                break

        # Remove old properties table and insert new at index
        self.workflow_layout.removeWidget(self.properties_table)
        self.properties_table.setParent(None)
        self.workflow_layout.insertWidget(index, table)
        self.properties_table = table

    # Automatically populates tree with an object and any existing sub-objects
    def populate_tree(self, object, parent):
        if self.is_list_of_objects(object):
            for i in range(len(object)):  # Iterates through each individual object in list
                self.add_object_to_tree(object[i], parent)
        else:
            self.add_object_to_tree(object, parent)

    def add_object_to_tree(self, object, parent):
        object_widget = QtWidgets.QTreeWidgetItem(parent)
        object_widget.setText(0, type(object).__name__)
        object_widget.setData(0, QtCore.Qt.ItemDataRole.UserRole, object)
        # Detect whether the object has child objects which need to be displayed in the tree
        child = self.return_displayable_child(object)
        if child is not None:
            self.populate_tree(child, object_widget)

    def return_displayable_child(self, object):
        for i, (key, value) in enumerate(vars(object).items()):
            if self.is_custom_object(getattr(object, key)):
                return value
        return None

    def is_custom_object(self, attribute):
        excluded_types = (int, float, str, bool, list, dict, tuple, set)

        if not isinstance(attribute, excluded_types):
            return True

        if isinstance(attribute, Iterable) and not isinstance(attribute, (str, bytes)):
            return all(self.is_custom_object(item) for item in attribute)

        return False

    def is_list_of_objects(self, attribute):
        if isinstance(attribute, Iterable) and not isinstance(attribute, (str, bytes)):
            return all(self.is_custom_object(item) for item in attribute)
        return False


window = MainWindow(app)
window.show()
app.exec()


