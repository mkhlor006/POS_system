# Makhuvele Lorreta
# MKHLOR006
# 16 MARCH 2025

import sqlite3  # Library to interact with SQLite databases
import sys  # For handling system-level operations
from PyQt5.QtWidgets import *  # Import PyQt5 widgets for GUI components
from PyQt5.QtGui import *  # For handling images and fonts
from PyQt5.QtCore import *  # Provides core functionality like timers and events
import datetime  # To handle date and time operations
import os  # To check if the image file exists

class Point(QWidget):  # Main GUI window for the Point of Sale system
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setGeometry(250, 250, 950, 500)  # Set window position and size
        self.setWindowTitle('POINT OF SALES')  # Window title

        # Set background color to gray
        self.setStyleSheet("background-color: gray;")

        # Main layout (Horizontal: Left = Image & Heading, Right = Inputs & Buttons)
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Left panel (Vertical Layout: Heading + Image)
        left_panel = QVBoxLayout()
        main_layout.addLayout(left_panel)

        # Title Label (Heading above the image)
        title_label = QLabel('HARDWARE TUCKSHOP')
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: red;")
        title_label.setAlignment(Qt.AlignCenter)
        left_panel.addWidget(title_label)

        # Image
        image_label = QLabel(self)
        image_path = "Lorettas3.jpg"  # Ensure this file exists in the same directory

        # Check if the image file exists before loading
        if os.path.exists(image_path):  
            pixmap = QPixmap(image_path)
            image_label.setPixmap(pixmap)
            image_label.setScaledContents(True)  # Ensure image fits within label
            image_label.setFixedSize(250, 250)  # Fixed size for better layout
        else:
            image_label.setText("Image not found")  # Display text if image is missing
            image_label.setAlignment(Qt.AlignCenter)

        left_panel.addWidget(image_label)

        # Right panel (Grid layout for input fields & buttons)
        grid = QGridLayout()
        main_layout.addLayout(grid)

        # Quantity Input Field
        quantity_label = QLabel("Enter quantity:")
        self.quantity_edit = QLineEdit()
        grid.addWidget(quantity_label, 0, 0)
        grid.addWidget(self.quantity_edit, 0, 1)

        # Item selection dropdown
        self.combo = QComboBox()
        grid.addWidget(self.combo, 0, 2)

        # Buttons
        self.OK = QPushButton('OK')  # Button to process sale
        grid.addWidget(self.OK, 1, 0)
        self.OK.clicked.connect(self.sale_processing)

        self.report = QPushButton('Report')  # Button to generate sales report
        grid.addWidget(self.report, 1, 1)
        self.report.clicked.connect(self.show_report)

        self.Close = QPushButton('CLOSE')  # Button to close the app
        grid.addWidget(self.Close, 1, 2)
        self.Close.clicked.connect(self.close)

        self.select_items()  # Load items from the database into the dropdown

    def select_items(self):
        connecting_db = sqlite3.connect('Point_Of_Sales.db')  # Connect to the database
        cursor = connecting_db.cursor()
        cursor.execute("SELECT StockCode, NameOfItem FROM Stock")  # Retrieve item details
        items = cursor.fetchall()
        connecting_db.close()  # Close database connection

        self.combo.clear()
        for item in items:
            # Add items to the dropdown (display NameOfItem but store StockCode as data)
            self.combo.addItem(f"{item[1]} (StockCode: {item[0]})", item[0])

    def sale_processing(self):
        code = self.combo.currentData()  # Gets StockCode from the selected item
    
        if code is None:
            QMessageBox.warning(self, "Error", "Please select an item!")
            return
    
        quantity = self.quantity_edit.text()
    
        # Ensure the quantity entered is a positive number
        if not quantity.isdigit() or int(quantity) <= 0:
            QMessageBox.warning(self, "Error", "Please enter a valid positive quantity!")
            return
    
        quantity = int(quantity)  # Convert input to an integer
    
        try:
            connecting_db = sqlite3.connect('Point_Of_Sales.db')  # Connect to database
            cursor = connecting_db.cursor()
    
            # Fetch stock details
            cursor.execute("SELECT QuantityInStock, SalesPrice FROM Stock WHERE StockCode = ?", (code,))
            stocks = cursor.fetchone()
    
            if stocks is None:
                QMessageBox.warning(self, "Error", "Item not found in stock!")
                return
    
            QuantityInStock, SalesPrice = stocks
    
            if QuantityInStock is None or SalesPrice is None:
                QMessageBox.warning(self, "Error", "Invalid stock data. Check database integrity.")
                return
    
            if QuantityInStock < quantity:
                QMessageBox.warning(self, "Error", "Not enough stock available!")
                return

            # Update stock quantity
            cursor.execute("UPDATE Stock SET QuantityInStock = QuantityInStock - ? WHERE StockCode = ?", (quantity, code))
    
            transaction_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Get current timestamp
            cursor.execute("""
                INSERT INTO Sales (StockCode, QuantitySold, DateTime) 
                VALUES (?, ?, ?)
            """, (code, quantity, transaction_time))  # Insert sale record
    
            connecting_db.commit()  # Commit changes to the database
            QMessageBox.information(self, "Success", "Sale recorded successfully!")
    
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {e}")
        finally:
            connecting_db.close()  # Close the database connection
            self.quantity_edit.clear()  # Clear the quantity input field
    
    def show_report(self):
        self.report_window = POS()
        self.report_window.show()

class POS(QWidget):  # Sales Report Window
    def __init__(self):
        super().__init__()
        self.initi()

    def initi(self):
        self.setWindowTitle("Sales Report")
        self.setGeometry(200, 200, 400, 200)

        # Set background color to gray
        self.setStyleSheet("background-color: gray;")

        layout = QVBoxLayout()
    
        connecting_db = sqlite3.connect("Point_Of_Sales.db")
        cursor = connecting_db.cursor()
    
        # Fetch total quantity sold and total sales revenue
        cursor.execute("""
            SELECT SUM(QuantitySold), SUM(QuantitySold * s.SalesPrice) 
            FROM Sales AS sa
            JOIN Stock AS s ON sa.StockCode = s.StockCode
        """)
        report = cursor.fetchone()
        connecting_db.close()
    
        total_items_sold = report[0] if report[0] else 0  # Ensure zero if no sales
        total_sales = report[1] if report[1] else 0.0  
    
        # Report label displaying sales summary
        self.report_label = QLabel(f"Total Items Sold: {total_items_sold}\n"
                                   f"Total Sales Revenue: R{total_sales:.2f}")
        layout.addWidget(self.report_label)
    
        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button)
    
        self.setLayout(layout)

def main():
    app = QApplication(sys.argv)  # Create a PyQt5 application
    my_widget = Point()  # Create the main window
    my_widget.show()  # Show the window
    sys.exit(app.exec_())  # Run the application event loop

main()  # Run the main function

