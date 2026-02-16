from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from PIL import Image
from pypdf import PdfReader, PdfWriter


def _ensure_unique_path(target_path: Path) -> Path:
    if not target_path.exists():
        return target_path

    stem = target_path.stem
    suffix = target_path.suffix
    parent = target_path.parent

    i = 1
    while True:
        candidate = parent / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def _image_paths_to_pdf(
    image_paths: List[Path],
    output_pdf_path: Path,
    resolution: float = 300.0,
) -> None:
    images: List[Image.Image] = []

    for image_path in image_paths:
        img = Image.open(image_path)
        if img.mode == "RGBA":
            rgb = Image.new("RGB", img.size, (255, 255, 255))
            rgb.paste(img, mask=img.split()[3])
            img = rgb
        elif img.mode != "RGB":
            img = img.convert("RGB")
        images.append(img)

    if not images:
        raise ValueError("No images provided")

    first = images[0]
    rest = images[1:]
    first.save(output_pdf_path, "PDF", resolution=resolution, save_all=True, append_images=rest)


def extend_document(
    base_path: Path,
    base_type: str,
    attachment_image_paths: List[Path],
    output_dir: Path,
    output_filename: str,
    temp_dir: Path,
    rename_base_to_original: bool = True,
) -> Tuple[Path, Optional[Path], int]:
    base_type_norm = base_type.strip().lower()

    if base_type_norm not in {"pdf", "docx"}:
        raise ValueError("base_type must be 'pdf' or 'docx'")

    if not attachment_image_paths:
        raise ValueError("No attachments provided")

    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = _ensure_unique_path(output_dir / output_filename)

    renamed_base_path: Optional[Path] = None

    if rename_base_to_original:
        base_original_candidate = base_path.with_name(f"{base_path.stem}_original{base_path.suffix}")
        renamed_base_path = _ensure_unique_path(base_original_candidate)
        base_path.rename(renamed_base_path)
        base_path = renamed_base_path

    base_pdf_path = base_path
    temp_base_pdf_path: Optional[Path] = None

    if base_type_norm == "docx":
        from docx2pdf import convert

        temp_base_pdf_path = temp_dir / f"{base_path.stem}.pdf"
        temp_base_pdf_path.parent.mkdir(parents=True, exist_ok=True)
        convert(str(base_path), str(temp_base_pdf_path))
        base_pdf_path = temp_base_pdf_path

    attachments_pdf_path = temp_dir / "_attachments.pdf"
    attachments_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    _image_paths_to_pdf(attachment_image_paths, attachments_pdf_path)

    writer = PdfWriter()

    base_reader = PdfReader(str(base_pdf_path))
    for page in base_reader.pages:
        writer.add_page(page)

    attachments_reader = PdfReader(str(attachments_pdf_path))
    for page in attachments_reader.pages:
        writer.add_page(page)

    with output_path.open("wb") as f:
        writer.write(f)

    return output_path, renamed_base_path, len(attachments_reader.pages)
