import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.core.converter import process_images_to_pdf

class TestCoreConverter(unittest.TestCase):

    def setUp(self):
        # Mock callbacks for the converter function
        self.mock_ask_overwrite = MagicMock(return_value="overwrite")
        self.mock_get_new_name = MagicMock(return_value=Path("/mock/path/renamed.pdf"))
        self.mock_update_status = MagicMock()
        self.mock_update_overall_progress = MagicMock()

        # Create a temporary directory for mock file operations
        self.test_dir = Path("./test_output")
        self.test_dir.mkdir(exist_ok=True)

    def tearDown(self):
        # Clean up temporary directory
        for f in self.test_dir.iterdir():
            f.unlink()
        self.test_dir.rmdir()

    @patch('PIL.Image.open')
    @patch('PIL.Image.Image.save')
    def test_process_images_to_pdf_single_pdf_success(self, mock_save, mock_open):
        mock_img_instance = MagicMock()
        mock_img_instance.mode = 'RGB'
        mock_open.return_value = mock_img_instance

        png_paths = [
            "/mock/path/image1.png",
            "/mock/path/image2.png"
        ]
        output_dir = self.test_dir
        output_mode = "single"

        converted, skipped = process_images_to_pdf(
            png_paths=png_paths,
            output_dir=output_dir,
            output_mode=output_mode,
            ask_overwrite_callback=self.mock_ask_overwrite,
            get_new_name_callback=self.mock_get_new_name,
            update_status_callback=self.mock_update_status,
            update_overall_progress_callback=self.mock_update_overall_progress
        )

        self.assertEqual(converted, 2)
        self.assertEqual(skipped, 0)
        self.assertEqual(mock_open.call_count, 2)
        mock_save.assert_called_once_with(
            output_dir / "combined_images.pdf",
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=[mock_img_instance, mock_img_instance] # Need to adjust this for actual mock_img_instance objects
        )
        # Verify status updates
        self.mock_update_status.assert_any_call("/mock/path/image1.png", "✔", "green")
        self.mock_update_status.assert_any_call("/mock/path/image2.png", "✔", "green")

    @patch('PIL.Image.open')
    @patch('PIL.Image.Image.save')
    def test_process_images_to_pdf_separate_pdfs_success(self, mock_save, mock_open):
        mock_img_instance = MagicMock()
        mock_img_instance.mode = 'RGB'
        mock_open.return_value = mock_img_instance

        png_paths = [
            "/mock/path/imageA.png",
            "/mock/path/imageB.png"
        ]
        output_dir = self.test_dir
        output_mode = "separate"

        converted, skipped = process_images_to_pdf(
            png_paths=png_paths,
            output_dir=output_dir,
            output_mode=output_mode,
            ask_overwrite_callback=self.mock_ask_overwrite,
            get_new_name_callback=self.mock_get_new_name,
            update_status_callback=self.mock_update_status,
            update_overall_progress_callback=self.mock_update_overall_progress
        )

        self.assertEqual(converted, 2)
        self.assertEqual(skipped, 0)
        self.assertEqual(mock_open.call_count, 2)
        self.assertEqual(mock_save.call_count, 2)
        mock_save.assert_any_call(output_dir / "imageA.pdf", "PDF", resolution=100.0, quality=100)
        mock_save.assert_any_call(output_dir / "imageB.pdf", "PDF", resolution=100.0, quality=100)
        self.mock_update_status.assert_any_call("/mock/path/imageA.png", "✔", "green")
        self.mock_update_status.assert_any_call("/mock/path/imageB.png", "✔", "green")

    @patch('PIL.Image.open', side_effect=IOError("Mocked IO Error"))
    @patch('PIL.Image.Image.save')
    def test_process_images_to_pdf_separate_pdfs_failure(self, mock_save, mock_open):
        png_paths = [
            "/mock/path/bad_image.png"
        ]
        output_dir = self.test_dir
        output_mode = "separate"

        converted, skipped = process_images_to_pdf(
            png_paths=png_paths,
            output_dir=output_dir,
            output_mode=output_mode,
            ask_overwrite_callback=self.mock_ask_overwrite,
            get_new_name_callback=self.mock_get_new_name,
            update_status_callback=self.mock_update_status,
            update_overall_progress_callback=self.mock_update_overall_progress
        )

        self.assertEqual(converted, 0)
        self.assertEqual(skipped, 1)
        mock_open.assert_called_once()
        mock_save.assert_not_called()
        self.mock_update_status.assert_any_call("/mock/path/bad_image.png", "✖", "red")

    @patch('PIL.Image.open')
    @patch('PIL.Image.Image.save')
    def test_process_images_to_pdf_single_pdf_rgba_conversion(self, mock_save, mock_open):
        mock_img_rgba = MagicMock()
        mock_img_rgba.mode = 'RGBA'
        mock_img_rgba.split.return_value = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        mock_rgb_image = MagicMock()
        mock_rgb_image.mode = 'RGB'

        mock_image_new = MagicMock(return_value=mock_rgb_image)

        with patch('PIL.Image.new', new=mock_image_new):
            mock_open.return_value = mock_img_rgba
            png_paths = ["/mock/path/rgb-image.png"]
            output_dir = self.test_dir
            output_mode = "single"

            converted, skipped = process_images_to_pdf(
                png_paths=png_paths,
                output_dir=output_dir,
                output_mode=output_mode,
                ask_overwrite_callback=self.mock_ask_overwrite,
                get_new_name_callback=self.mock_get_new_name,
                update_status_callback=self.mock_update_status,
                update_overall_progress_callback=self.mock_update_overall_progress
            )

            self.assertEqual(converted, 1)
            self.assertEqual(skipped, 0)
            mock_image_new.assert_called_once_with('RGB', mock_img_rgba.size, (255, 255, 255))
            mock_rgb_image.paste.assert_called_once_with(mock_img_rgba, mask=mock_img_rgba.split()[3])
            mock_save.assert_called_once() # save called on the converted RGB image

if __name__ == '__main__':
    unittest.main()