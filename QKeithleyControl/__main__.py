import sys
from PyQt5.QtWidgets import QApplication
import modules.QKeithleyControl

# Main event loop handler instance
app = QApplication(sys.argv)

# Instantiate the application
window = modules.QKeithleyControl.QKeithleyControl(app)
window.show()

# Enter event loop
app.exec_()