import unittest
from unittest.mock import patch, MagicMock
import os
from pathlib import Path

# We need to import the class from its new location
from src.gui.app_gui import PNGtoPDFConverter

class TestGUIDialogs(unittest.TestCase):

    def setUp(self):
        # Create a mock root for the PNGtoPDFConverter instance
        self.mock_root = MagicMock()
        self.app = PNGtoPDFConverter(self.mock_root)

    @patch('tkinter.messagebox.askyesnocancel')
    def test_ask_overwrite_yes(self, mock_askyesnocancel):
        mock_askyesnocancel.return_value = True # Simulate 'Yes' (Overwrite)
        png_path = Path("/fake/path/image.png")
        pdf_path = Path("/fake/path/image.pdf")
        result = self.app.ask_overwrite(png_path, pdf_path)
        self.assertEqual(result, "overwrite")
        mock_askyesnocancel.assert_called_once()

    @patch('tkinter.messagebox.askyesnocancel')
    def test_ask_overwrite_no(self, mock_askyesnocancel):
        mock_askyesnocancel.return_value = False # Simulate 'No' (Rename)
        png_path = Path("/fake/path/image.png")
        pdf_path = Path("/fake/path/image.pdf")
        result = self.app.ask_overwrite(png_path, pdf_path)
        self.assertEqual(result, "rename")
        mock_askyesnocancel.assert_called_once()

    @patch('tkinter.messagebox.askyesnocancel')
    def test_ask_overwrite_cancel(self, mock_askyesnocancel):
        mock_askyesnocancel.return_value = None # Simulate 'Cancel' (Skip)
        png_path = Path("/fake/path/image.png")
        pdf_path = Path("/fake/path/image.pdf")
        result = self.app.ask_overwrite(png_path, pdf_path)
        self.assertEqual(result, "skip")
        mock_askyesnocancel.assert_called_once()

    @patch('tkinter.simpledialog.askstring')
    def test_get_new_name_provided(self, mock_askstring):
        mock_askstring.return_value = "new_image_name" # Simulate user providing a new name
        original_path = Path("/fake/path/original.pdf")
        new_path = self.app.get_new_name(original_path)
        self.assertEqual(new_path, Path("/fake/path/new_image_name.pdf"))
        mock_askstring.assert_called_once()

    @patch('tkinter.simpledialog.askstring')
    def test_get_new_name_cancelled(self, mock_askstring):
        mock_askstring.return_value = None # Simulate user cancelling the dialog
        original_path = Path("/fake/path/original.pdf")
        new_path = self.app.get_new_name(original_path)
        self.assertIsNone(new_path)
        mock_askstring.assert_called_once()

if __name__ == '__main__':
    unittest.main()