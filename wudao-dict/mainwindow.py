from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import sys
import json
from urllib.error import URLError
import socket

from mainwindow_ui import Ui_MainWindow
from src.GuiDraw import GuiDraw
from src.WudaoClient import WudaoClient
from src.tools import is_alphabet
from src.UserHistory import UserHistory


class MainWindow(QMainWindow):
    ui = None
    mainWindow = None
    client = WudaoClient()
    painter = GuiDraw()
    draw_conf = True
    is_zh = False
    word = ''

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.history_manager = UserHistory()
        self.setup_ui()

    def setup_ui(self):
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # auto complete
        self.auto_com_init()
        self.ui.ol_cb.setChecked(False)
        darkula = QPalette()
        # theme
        darkula.setColor(QPalette.Background, QColor('#300A24'))
        darkula.setColor(QPalette.Base, QColor('#300A24'))
        self.ui.textBrowser.setPalette(darkula)
        # status bar
        self.ui.statusbar.showMessage('@2016 Chestnut Studio')
        # signal slot
        self.ui.lineEdit.returnPressed.connect(self.search_bt_clicked)
        self.ui.search_b.clicked.connect(self.search_bt_clicked)
        self.ui.detail_rb.clicked.connect(self.detail_rb_clicked)
        self.ui.intro_rb.clicked.connect(self.intro_rb_clicked)

    def detail_rb_clicked(self):
        self.draw_conf = True
        self.search_bt_clicked()

    def intro_rb_clicked(self):
        self.draw_conf = False
        self.search_bt_clicked()

    # auto complete
    def auto_com_init(self):
        sl = ['a', 'air', 'airplane']
        com = QCompleter(sl)
        com.setCaseSensitivity(Qt.CaseInsensitive)
        self.ui.lineEdit.setCompleter(com)

    def search_bt_clicked(self):
        self.word = self.ui.lineEdit.text().strip()
        if self.word:
            # if chinese
            if is_alphabet(self.word[0]):
                self.is_zh = False
            else:
                self.is_zh = True
            # query on server
            server_context = self.client.get_word_info(self.word).strip()
            if server_context != 'None':
                wi = json.loads(server_context)
                self.painter.html = ''
                if wi.get('fuzzy'):
                    entry = wi.get('entry')
                    if entry and not self.is_zh:
                        self.history_manager.add_item(entry)
                    self.painter.draw_fuzzy_suggestions(wi, self.draw_conf)
                elif self.is_zh:
                    self.painter.draw_zh_text(wi, self.draw_conf)
                else:
                    self.history_manager.add_item(self.word)
                    self.painter.draw_text(wi, self.draw_conf)
                self.ui.textBrowser.setHtml(self.painter.html)
            else:
                # Online search
                if self.ui.ol_cb.isChecked():
                    # NOTE: For true GUI stability, this network operation 
                    # should run in a separate QThread to avoid blocking the UI.
                    # The following is a simplified improvement focusing on error handling.
                    self.painter.html = ''
                    try:
                        # Provide immediate feedback
                        self.ui.textBrowser.setHtml(self.painter.P_PATTERN % 'Searching online...')
                        QApplication.processEvents() # Update UI immediately

                        from src.WudaoOnline import get_text, get_zh_text
                        # bs4 and lxml should ideally be checked at startup or handled more globally
                        import bs4 
                        import lxml

                        if self.is_zh:
                            word_info = get_zh_text(self.word)
                        else:
                            word_info = get_text(self.word)

                        if not word_info or not word_info.get('paraphrase'): # Check if result is valid
                            html = self.painter.P_W_PATTERN % ('No definition found for: %s online.' % self.word)
                        else:
                            # Only add history/draw if word found
                            if not self.is_zh:
                                self.history_manager.add_word_info(word_info) # Cache result
                                self.painter.draw_text(word_info, self.draw_conf)
                            else:
                                self.painter.draw_zh_text(word_info, self.draw_conf)
                            html = self.painter.html # Use the generated HTML
                        
                        self.ui.textBrowser.setHtml(html)
                        # return # Removed return, html is set below

                    except ImportError:
                        html = self.painter.P_W_PATTERN % 'Error: Dependencies (bs4, lxml) missing for online search.'
                        html += self.painter.P_W_PATTERN % 'Please install using: pip3 install bs4 lxml'
                    except URLError as e:
                        html = self.painter.P_W_PATTERN % f'Network Error: Could not connect ({e}). Please check your internet connection.'
                    except socket.timeout:
                         html = self.painter.P_W_PATTERN % 'Network Error: Connection timed out during online search.'
                    except Exception as e: # Catch unexpected errors
                        html = self.painter.P_W_PATTERN % f'An unexpected error occurred during online search: {e}'
                    
                    self.ui.textBrowser.setHtml(html) # Set HTML regardless of success/failure path above
                    return # Now we can return after setting HTML
                else: # Not searching online
                    # search in online cache first
                    word_info = self.history_manager.get_word_info(self.word)
                    if word_info:
                        self.history_manager.add_item(self.word)
                        self.painter.html = ''
                        if self.is_zh:
                             self.painter.draw_zh_text(word_info, self.draw_conf)
                        else:
                             self.painter.draw_text(word_info, self.draw_conf)
                        html = self.painter.html
                    else:
                        html = self.painter.P_W_PATTERN % ('Error: Word not found locally: ' + self.word)
                        html += self.painter.P_W_PATTERN % 'Tick the "Online" box to search the web.'
                self.ui.textBrowser.setHtml(html)


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
