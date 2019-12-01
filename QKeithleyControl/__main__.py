import sys
from PyQt5.QtWidgets import QApplication
import modules.QKeithleyControl

# Main event loop handler insance
app = QApplication(sys.argv)

# Instantiate the application
window = modules.QKeithleyControl.QKeithleyControl()
window.show()

# Enter event loop
app.exec_()