from PIL import Image
from pathlib import Path
from typing import List, Dict, Tuple

def process_images_to_pdf(
    png_paths: List[str],
    output_dir: Path,
    output_mode: str,
    ask_overwrite_callback,
    get_new_name_callback,
    update_status_callback,
    update_overall_progress_callback
) -> Tuple[int, int]:
    converted_count = 0
    skipped_count = 0
    total_images = len(png_paths)

    if output_mode == "single":
        images_for_single_pdf = []
        for i, png_path in enumerate(png_paths, 1):
            update_overall_progress_callback(f"Processing image {i}/{total_images} for single PDF...", i, total_images)
            update_status_callback(png_path, "(Processing)", "blue")
            try:
                image = Image.open(png_path)
                if image.mode == 'RGBA':
                    rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                    rgb_image.paste(image, mask=image.split()[3])
                    image = rgb_image
                elif image.mode != 'RGB':
                    image = image.convert('RGB')
                images_for_single_pdf.append(image)
                update_status_callback(png_path, "✔", "green")
            except Exception:
                update_status_callback(png_path, "✖", "red")
                skipped_count += 1

        if images_for_single_pdf:
            update_overall_progress_callback("Creating combined PDF...", total_images, total_images)
            first_image = images_for_single_pdf[0]
            other_images = images_for_single_pdf[1:]
            single_pdf_path = output_dir / "combined_images.pdf"
            try:
                # Check if combined PDF already exists
                if single_pdf_path.exists():
                    response = ask_overwrite_callback(str(Path(png_paths[0]).name), single_pdf_path) # Pass first image name for context
                    if response == "skip":
                        skipped_count += 1 # Count the whole combined PDF as skipped
                        return converted_count, skipped_count
                    elif response == "rename":
                        single_pdf_path = get_new_name_callback(single_pdf_path)
                        if single_pdf_path is None:
                            skipped_count += 1
                            return converted_count, skipped_count

                first_image.save(single_pdf_path, "PDF", resolution=100.0, save_all=True, append_images=other_images)
                converted_count += len(images_for_single_pdf) # Count all images as converted if combined successfully
            except Exception:
                skipped_count += len(images_for_single_pdf) # Count all as skipped if combined fails

    else:  # Separate PDFs
        for i, png_path in enumerate(png_paths, 1):
            update_overall_progress_callback(f"Converting {i}/{total_images}...", i, total_images)
            update_status_callback(png_path, "(Converting)", "blue")
            try:
                pdf_path = output_dir / f"{Path(png_path).stem}.pdf"

                if pdf_path.exists():
                    response = ask_overwrite_callback(png_path, pdf_path)
                    if response == "skip":
                        update_status_callback(png_path, "✖", "orange")
                        skipped_count += 1
                        continue
                    elif response == "rename":
                        pdf_path = get_new_name_callback(pdf_path)
                        if pdf_path is None:
                            update_status_callback(png_path, "✖", "orange")
                            skipped_count += 1
                            continue

                image = Image.open(png_path)
                if image.mode == 'RGBA':
                    rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                    rgb_image.paste(image, mask=image.split()[3])
                    image = rgb_image
                elif image.mode != 'RGB':
                    image = image.convert('RGB')

                image.save(pdf_path, 'PDF', resolution=100.0, quality=100)
                converted_count += 1
                update_status_callback(png_path, "✔", "green")

            except Exception:
                update_status_callback(png_path, "✖", "red")
                skipped_count += 1

    return converted_count, skipped_count