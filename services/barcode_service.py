"""
Barcode Generation Service for API
Copied and adapted from MAIN.PY
"""

import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import qrcode
from barcode import Code128
from barcode.writer import ImageWriter
import io
import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
import glob
from typing import List, Optional, Dict, Any, Set
import csv
import random
import aiofiles
import asyncio
from services.archive_manager import ArchiveManager
from models.database import BarcodeRecord


class BarcodeService:
    def __init__(self, output_dir: str = "downloads/barcodes", pdf_dir: str = "downloads/pdfs", logs_dir: str = "logs"):
        self.output_dir = output_dir
        self.pdf_dir = pdf_dir
        self.logs_dir = logs_dir
        self.imei_log_file = os.path.join(self.logs_dir, "imei_log.csv")
        self.archive_manager = ArchiveManager()
        self.create_output_directories()
        
    def create_output_directories(self):
        """Create output directories if they don't exist"""
        for directory in [self.output_dir, self.pdf_dir, self.logs_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)

    def archive_existing_files(self, file_metadata: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Archive existing files to timestamped folders instead of deleting them"""
        print("📦 Archiving existing files...")
        
        # Check if there are any files to archive
        png_files = glob.glob(os.path.join(self.output_dir, "*.png"))
        pdf_files = glob.glob(os.path.join(self.pdf_dir, "*.pdf"))
        
        if not png_files and not pdf_files:
            print("✅ No files to archive - directories are already clean")
            return {
                "session_id": None,
                "archived_files": [],
                "total_files": 0,
                "png_count": 0,
                "pdf_count": 0,
                "total_size": 0
            }
        
        # Archive files using the archive manager
        archive_result = self.archive_manager.archive_files(
            barcode_dir=self.output_dir,
            pdf_dir=self.pdf_dir,
            generation_session=f"cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            file_metadata=file_metadata
        )
        
        print("✨ Archive completed!")
        return archive_result

    # ---------------- IMEI2 utilities -----------------
    def _load_used_imeis(self) -> Set[str]:
        used: Set[str] = set()
        if os.path.exists(self.imei_log_file):
            try:
                with open(self.imei_log_file, "r", newline="") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        val = str(row.get("IMEI2", ""))
                        if val:
                            used.add(val)
            except Exception:
                pass
        return used

    def _append_imei_log(self, imei: str, imei2: str) -> None:
        file_exists = os.path.exists(self.imei_log_file)
        try:
            with open(self.imei_log_file, "a", newline="") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["IMEI", "IMEI2"])  # header
                writer.writerow([imei, imei2])
        except Exception:
            pass

    def generate_unique_imei(self, base_imei: str, used_set: Set[str]) -> str:
        prefix = str(base_imei)[:8]
        while True:
            suffix = str(random.randint(10**6, 10**7 - 1)).zfill(7)
            candidate = prefix + suffix
            if candidate not in used_set:
                used_set.add(candidate)
                return candidate
    
    def extract_color_from_product(self, product_string: str) -> str:
        """Extract color from product string like 'SMART 8 64+3 SHINY GOLD'"""
        if not product_string or product_string == 'nan':
            return 'Unknown Color'
        
        # Split the product string into parts
        parts = str(product_string).strip().split()
        
        if len(parts) < 2:
            return 'Unknown Color'
        
        # Look for the last part that contains a '+' (storage spec like +3, +8, +256)
        # The color should be everything after the storage specification
        color_start_index = 0
        
        for i, part in enumerate(parts):
            if '+' in part and any(char.isdigit() for char in part):
                # Found storage spec, color starts after this
                color_start_index = i + 1
                break
        
        # If we found a storage spec, extract everything after it as color
        if color_start_index > 0 and color_start_index < len(parts):
            color_parts = parts[color_start_index:]
            color = ' '.join(color_parts)
            return color.upper() if color else 'Unknown Color'
        
        # Fallback: if no storage spec found, assume last 1-2 words are color
        if len(parts) >= 2:
            # Try last 2 words first (for colors like "SLEEK BLACK")
            color = ' '.join(parts[-2:])
            return color.upper()
        else:
            return 'Unknown Color'
    
    def generate_qr_code(self, data: str, size: tuple = (100, 100)) -> Image.Image:
        """Generate QR code for given data"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=3,
            border=1,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize(size, Image.Resampling.LANCZOS)
        return qr_img
    
    def generate_code128_barcode(self, data: str, width: int = 200, height: int = 50) -> Image.Image:
        """Generate Code128 barcode for IMEI without text"""
        # Create barcode with writer options to exclude text
        code128 = Code128(data, writer=ImageWriter())
        
        # Generate barcode image in memory with options to remove text and make less bold
        buffer = io.BytesIO()
        options = {
            'write_text': False,  # Don't write text under barcode
            'quiet_zone': 0,      # No quiet zone
            'module_width': 0.15,  # Make bars even thinner (lighter)
            'module_height': 12,  # Adjust height for lighter bars
        }
        code128.write(buffer, options=options)
        buffer.seek(0)
        
        # Open and resize the image
        barcode_img = Image.open(buffer)
        barcode_img = barcode_img.resize((width, height), Image.Resampling.LANCZOS)
        
        return barcode_img
    
    def create_barcode_label(self, imei: str, model: str, color: str, dn: str, 
                           box_id: Optional[str] = None, brand: str = "Infinix", second_label: str = "Box ID") -> Image.Image:
        """Create a clean, perfectly aligned barcode label matching the reference image."""
        
        # Dimensions to match the reference image layout
        label_width = 650
        label_height = 350  # Increased to accommodate all elements without cutoff 
        
        label = Image.new('RGB', (label_width, label_height), 'white')
        draw = ImageDraw.Draw(label)
        
        # Font loading with production-ready fallbacks
        def load_font(font_paths, size):
            """Try multiple font paths and return the first one that works"""
            for font_path in font_paths:
                try:
                    return ImageFont.truetype(font_path, size)
                except (OSError, IOError):
                    continue
            return ImageFont.load_default()
        
        # Define font paths for different environments
        bold_font_paths = [
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",  # Linux production
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux alternative
            "/System/Library/Fonts/Arial Bold.ttf",  # macOS
            "ARIALBD.TTF",  # Local development
        ]
        
        regular_font_paths = [
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",  # Linux production
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux alternative
            "/System/Library/Fonts/Arial.ttf",  # macOS
            "arial.ttf",  # Local development
        ]
        
        # Load fonts with fallbacks
        font_large = load_font(bold_font_paths, 40)
        font_medium = load_font(bold_font_paths, 20)
        font_circle = load_font(bold_font_paths, 40)
        font_regular = load_font(regular_font_paths, 18)

        # --- Top Text (Model and Color) - Match reference layout ---
        x_start = 30
        y_top = 15  # Slightly higher positioning
        
        # Draw model (left side)
        draw.text((x_start, y_top), model, fill='black', font=font_large)
        
        # Draw color (right side, aligned with model)
        color_text = color.upper()
        color_bbox = draw.textbbox((0, 0), color_text, font=font_large)
        color_width = color_bbox[2] - color_bbox[0]
        x_pos_color = label_width - color_width - 60  # Right-aligned
        draw.text((x_pos_color, y_top), color_text, fill='black', font=font_large)

        # --- Barcodes and Text - Match reference positioning exactly ---
        barcode_width = 460
        barcode_height = 60
        
        # 1. First Barcode (IMEI)
        y_pos = 70  # Start position for first barcode
        imei_barcode_img = self.generate_code128_barcode(imei, width=barcode_width, height=barcode_height)
        label.paste(imei_barcode_img, (x_start, y_pos))
        
        # IMEI label directly under barcode - scale to fit barcode width
        y_pos += barcode_height + 8  # Move y_pos below the barcode
        
        # Split text: "IMEI" (bold) and the number (regular)
        imei_label = "IMEI"
        imei_number = imei
        
        # Calculate font size to fit barcode width
        test_font = font_medium
        full_text = f"{imei_label} {imei_number}"
        text_bbox = draw.textbbox((0, 0), full_text, font=test_font)
        text_width = text_bbox[2] - text_bbox[0]
        
        # Scale font size to fit barcode width
        if text_width < barcode_width:
            scale_factor = barcode_width / text_width
            new_font_size = int(16 * scale_factor)
            try:
                # Bold font for "IMEI"
                bold_font = load_font(bold_font_paths, new_font_size)
                # Regular font for the number
                regular_font = load_font(regular_font_paths, new_font_size)
            except:
                bold_font = font_medium
                regular_font = font_regular
        else:
            bold_font = font_medium
            regular_font = font_regular
        
        # Draw the complete IMEI text as one unit and stretch to match barcode width
        full_imei_text = f"{imei_label} {imei_number}"
        
        # Create a temporary image to render the complete text
        temp_img = Image.new('RGBA', (int(barcode_width * 2), 50), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        
        # Render the complete text with mixed formatting
        # First draw "IMEI" in bold
        temp_draw.text((0, 10), imei_label, fill='black', font=bold_font)
        # Then draw the number in regular font after "IMEI"
        imei_bbox = temp_draw.textbbox((0, 10), imei_label, font=bold_font)
        imei_width = imei_bbox[2] - imei_bbox[0]
        number_x = imei_width + 5  # Small space between "IMEI" and number
        temp_draw.text((number_x, 10), imei_number, fill='black', font=regular_font)
        
        # Get the complete text bounds
        full_bbox = temp_draw.textbbox((0, 10), full_imei_text, font=bold_font)
        text_w = full_bbox[2] - full_bbox[0]
        text_h = full_bbox[3] - full_bbox[1]
        
        # Crop to actual text bounds
        cropped = temp_img.crop((0, full_bbox[1], text_w, full_bbox[3]))
        # Stretch to fill barcode width
        stretched_img = cropped.resize((int(barcode_width), text_h), Image.Resampling.LANCZOS)
        label.paste(stretched_img, (int(x_start), int(y_pos)), mask=stretched_img)
        
        # 2. Second Barcode (Box ID or IMEI2)
        if box_id:
            y_pos += 35  # Add vertical space for the next barcode
            box_barcode_img = self.generate_code128_barcode(box_id, width=barcode_width, height=barcode_height)
            label.paste(box_barcode_img, (x_start, y_pos))
            
            # Second label directly under barcode - scale to fit barcode width
            y_pos += barcode_height + 8  # Move y_pos below the barcode
            
            # Split text: second_label (bold) and the number (Arial)
            box_label = second_label
            box_number = box_id
            
            # Calculate font size to fit barcode width
            test_font = font_medium
            full_text = f"{box_label} {box_number}"
            text_bbox = draw.textbbox((0, 0), full_text, font=test_font)
            text_width = text_bbox[2] - text_bbox[0]
            
            # Scale font size to fit barcode width
            if text_width < barcode_width:
                scale_factor = barcode_width / text_width
                new_font_size = int(16 * scale_factor)
                try:
                    # Bold font for "Box ID"
                    bold_font = load_font(bold_font_paths, new_font_size)
                    # Regular Arial for the number
                    number_font = load_font(regular_font_paths, new_font_size)
                except:
                    bold_font = font_medium
                    number_font = font_regular
            else:
                bold_font = font_medium
                number_font = font_medium
            
            # Draw the complete second label text as one unit and stretch to match barcode width
            full_second_text = f"{box_label} {box_number}"
            
            # Create a temporary image to render the complete text
            temp_img = Image.new('RGBA', (int(barcode_width * 2), 50), (0, 0, 0, 0))
            temp_draw = ImageDraw.Draw(temp_img)
            
            # Render the complete text with mixed formatting
            # First draw the label in bold
            temp_draw.text((0, 10), box_label, fill='black', font=bold_font)
            # Then draw the number in regular font after the label
            box_bbox = temp_draw.textbbox((0, 10), box_label, font=bold_font)
            box_width = box_bbox[2] - box_bbox[0]
            number_x = box_width + 5  # Small space between label and number
            temp_draw.text((number_x, 10), box_number, fill='black', font=number_font)
            
            # Get the complete text bounds
            full_bbox = temp_draw.textbbox((0, 10), full_second_text, font=bold_font)
            text_w = full_bbox[2] - full_bbox[0]
            text_h = full_bbox[3] - full_bbox[1]
            
            # Crop to actual text bounds
            cropped = temp_img.crop((0, full_bbox[1], text_w, full_bbox[3]))
            # Stretch to fill barcode width
            stretched_img = cropped.resize((int(barcode_width), text_h), Image.Resampling.LANCZOS)
            label.paste(stretched_img, (int(x_start), int(y_pos)), mask=stretched_img)
            
            # D/N Text - positioned directly below second barcode
            # Match the number font (regular Arial) and size used for IMEI/second number
            y_pos += 30  # Add space below label
            dn_label_text = "D/N:"
            # Use bold for label, same as other labels
            draw.text((x_start, y_pos), dn_label_text, fill='black', font=bold_font)
            # Position the value immediately after label
            dn_label_bbox = draw.textbbox((0, 0), dn_label_text, font=bold_font)
            dn_label_width = dn_label_bbox[2] - dn_label_bbox[0]
            dn_value_x = x_start + dn_label_width + 5
            # Use stretched_number_font if available (computed for second barcode), otherwise fall back to number_font or regular_font
            dn_value_font = 'stretched_number_font' in locals() and stretched_number_font or ('number_font' in locals() and number_font or font_regular)
            draw.text((dn_value_x, y_pos), str(dn), fill='black', font=dn_value_font)

        # --- QR Code and Circled 'A' - Match reference positioning exactly ---
        qr_size = 150
        qr_data = imei  # Only IMEI data in QR code
        qr_code_img = self.generate_qr_code(qr_data, size=(qr_size, qr_size))
        
        # Position QR code on the right side, aligned with first barcode
        qr_x_pos = label_width - qr_size - 0
        qr_y_pos = 65  # Align with first barcode
        label.paste(qr_code_img, (qr_x_pos, qr_y_pos))

        # Circled 'A' - positioned below QR code, aligned with bottom barcode
        circle_diameter = 60
        circle_x_center = 520 + (qr_size / 2) + 15 # Perfectly centered under QR code
        circle_y_center = 280  # Moved down to fit within increased height

        
        # Draw circle outline with precise positioning
        circle_left = circle_x_center - circle_diameter / 2
        circle_top = circle_y_center - circle_diameter / 2
        circle_right = circle_x_center + circle_diameter / 2
        circle_bottom = circle_y_center + circle_diameter / 2
        
        circle_bbox_coords = [circle_left, circle_top, circle_right, circle_bottom]
        draw.ellipse(circle_bbox_coords, outline='black', width=5)
        
        # Center the 'A' perfectly in the circle using textanchor
        a_bbox = draw.textbbox((0, 0), "A", font=font_circle)
        a_width = a_bbox[3] - a_bbox[1]
        a_height = a_bbox[3] - a_bbox[0]
        
        # Calculate exact center position for the 'A' within the circle
        # Account for PIL's text positioning quirks
        a_x = circle_x_center - a_width / 2
        a_y = circle_y_center - a_height / 2 - 3  # Increased adjustment for better centering
        
        # Draw the 'A' at the calculated center position
        draw.text((a_x, a_y), "A", fill='black', font=font_circle)
        
        return label
    
    def _normalize_column_name(self, columns: List[str], possible_names: List[str]) -> Optional[str]:
        """Find the best matching column name from a list of possible names"""
        columns_lower = [col.lower().strip() for col in columns]
        
        for possible_name in possible_names:
            possible_lower = possible_name.lower().strip()
            for i, col_lower in enumerate(columns_lower):
                if possible_lower in col_lower or col_lower in possible_lower:
                    return columns[i]
        
        return None

    async def generate_barcodes_from_data(self, items: List[Dict[str, Any]], auto_generate_second_imei: bool = True) -> List[str]:
        """Generate barcodes from list of data items"""
        # Archive existing files before generating new ones
        archive_result = self.archive_existing_files(file_metadata=items)
        
        # Create a consistent generation session ID
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        generated_files = []
        used_imeis = self._load_used_imeis() if auto_generate_second_imei else set()
        
        # Get column names from first item for flexible mapping
        if items:
            columns = list(items[0].keys())
            print(f"🔍 Available columns: {columns}")
            
            # Map flexible column names - expanded to handle more variations
            imei_col = self._normalize_column_name(columns, [
                'imei', 'imei/sn', 'imei_sn', 'serial', 'serial_number', 'sn', 'serial_no',
                'device_id', 'device_imei', 'phone_imei', 'mobile_imei', 'imei_number'
            ])
            model_col = self._normalize_column_name(columns, [
                'model', 'model_name', 'device_model', 'phone_model', 'mobile_model',
                'device_type', 'product_model', 'model_code'
            ])
            product_col = self._normalize_column_name(columns, [
                'product', 'product_name', 'device', 'device_name', 'phone_name',
                'mobile_name', 'product_description', 'item_name'
            ])
            color_col = self._normalize_column_name(columns, [
                'color', 'colour', 'device_color', 'phone_color', 'mobile_color',
                'color_name', 'finish', 'variant'
            ])
            dn_col = self._normalize_column_name(columns, [
                'dn', 'd/n', 'device_number', 'device_no', 'part_number',
                'part_no', 'sku', 'item_number'
            ])
            box_id_col = self._normalize_column_name(columns, [
                'box_id', 'boxid', 'box_number', 'box_no', 'package_id',
                'package_number', 'carton_id', 'container_id'
            ])
            
            print(f"🎯 Column mapping:")
            print(f"   IMEI: {imei_col}")
            print(f"   Model: {model_col}")
            print(f"   Product: {product_col}")
            print(f"   Color: {color_col}")
            print(f"   D/N: {dn_col}")
            print(f"   Box ID: {box_id_col}")
            
            # If no IMEI column found, try to use the first column or generate IMEIs
            if not imei_col:
                print("⚠️  No IMEI column found. Available columns:")
                for i, col in enumerate(columns):
                    print(f"   {i}: {col}")
                
                # Try to use the first column as IMEI if it looks like a number
                if columns:
                    first_col = columns[0]
                    print(f"🔄 Attempting to use first column '{first_col}' as IMEI...")
                    imei_col = first_col
        
        for index, item in enumerate(items):
            try:
                # Extract data from item using flexible column mapping
                imei = str(item.get(imei_col, '')) if imei_col else str(item.get('imei', ''))
                box_id = str(item.get(box_id_col, '')) if box_id_col and item.get(box_id_col) else str(item.get('box_id', '')) if item.get('box_id') else None
                model = str(item.get(model_col, 'Unknown')) if model_col else str(item.get('model', 'Unknown'))
                
                # Extract color from Product column if available, otherwise use color column
                product_string = str(item.get(product_col, '')) if product_col else str(item.get('product', '')) if item.get('product') else ''
                if product_string and product_string != 'nan':
                    color = self.extract_color_from_product(product_string)
                else:
                    color = str(item.get(color_col, 'Unknown Color')) if color_col else str(item.get('color', 'Unknown Color'))
                
                dn = str(item.get(dn_col, 'M8N7')) if dn_col else str(item.get('dn', 'M8N7'))
                
                # Validate IMEI - use original value as-is without cleaning
                if not imei or imei.lower() in ['nan', 'none', 'null', '']:
                    print(f"Skipping item {index}: No IMEI found (value: '{imei}')")
                    continue
                
                # Use the original IMEI exactly as it appears in Excel - no cleaning
                imei = str(imei).strip()
                
                # Only validate length, don't modify the IMEI
                if len(imei) < 5:  # Reduced minimum length to be more flexible
                    print(f"Skipping item {index}: IMEI too short ({len(imei)} characters): '{imei}'")
                    continue
                
                # Determine second barcode value and label
                second_value = box_id
                second_label = "Box ID"
                if auto_generate_second_imei:
                    # Prefer existing IMEI2 if provided
                    imei2 = str(item.get('imei2', '')) if item.get('imei2') else None
                    if not imei2:
                        imei2 = self.generate_unique_imei(imei, used_imeis)
                    second_value = imei2
                    second_label = "IMEI"

                # Generate barcode label
                label = self.create_barcode_label(
                    imei=imei,
                    box_id=second_value,
                    model=model,
                    color=color,
                    dn=dn,
                    second_label=second_label
                )
                
                # Save the label
                filename = f"barcode_label_{imei}_{index+1}.png"
                filepath = os.path.join(self.output_dir, filename)
                label.save(filepath, 'PNG', dpi=(300, 300))
                
                # Save barcode details immediately to database
                file_size = os.path.getsize(filepath)
                record = BarcodeRecord(
                    filename=filename,
                    file_path=filepath,
                    archive_path=filepath,  # Will be updated when archived
                    file_type="png",
                    file_size=file_size,
                    created_at=datetime.now().isoformat(),
                    archived_at=datetime.now().isoformat(),
                    generation_session=session_id,
                    imei=imei,
                    box_id=second_value,
                    model=model,
                    product=product_string,
                    color=color,
                    dn=dn
                )
                
                record_id = self.archive_manager.db_manager.insert_barcode_record(record)
                print(f"✅ Saved barcode {filename} to database (ID: {record_id})")
                
                generated_files.append(filename)

                # Append to IMEI log if we generated a second IMEI
                if auto_generate_second_imei and second_value:
                    try:
                        self._append_imei_log(imei, second_value)
                    except Exception:
                        pass
                
                print(f"Generated: {filename}")
                
            except Exception as e:
                print(f"Error generating barcode for item {index}: {e}")
        
        return generated_files, session_id
    
    async def generate_barcodes_from_excel(self, file_path: str) -> tuple[List[str], str]:
        """Generate barcodes from Excel file"""
        # Archive existing files before generating new ones
        archive_result = self.archive_existing_files()
        
        # Create a consistent generation session ID
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            
            # Debug: Print column names and first few rows
            print(f"📊 Excel file columns: {list(df.columns)}")
            print(f"📊 Excel file shape: {df.shape}")
            print(f"📊 First 3 rows:")
            print(df.head(3).to_string())
            
            items = df.to_dict('records')
            return await self.generate_barcodes_from_data(items)
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            return [], f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def create_pdf_from_barcodes(self, pdf_filename: Optional[str] = None, 
                               grid_cols: int = 5, grid_rows: int = 12,
                               session_id: str = None) -> Optional[str]:
        """Create a PDF with all generated barcode images arranged in a grid"""
        
        # Set default PDF filename if not provided
        if pdf_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"barcode_collection_{timestamp}.pdf"
        
        # Use provided session_id or create a default one
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        pdf_path = os.path.join(self.pdf_dir, pdf_filename)
        
        # Ensure PDF directory exists
        os.makedirs(self.pdf_dir, exist_ok=True)
        
        # Get all PNG files from the barcode directory
        barcode_files = glob.glob(os.path.join(self.output_dir, "*.png"))
        barcode_files.sort()  # Sort for consistent ordering
        
        print(f"🔍 Looking for PNG files in: {self.output_dir}")
        print(f"🔍 Found {len(barcode_files)} PNG files: {barcode_files}")
        
        if not barcode_files:
            print("❌ No barcode images found to include in PDF")
            return None
        
        print(f"📄 Creating PDF with {len(barcode_files)} barcode images...")
        print(f"📁 PDF will be saved as: {pdf_path}")
        
        # Create PDF canvas
        c = canvas.Canvas(pdf_path, pagesize=A4)
        page_width, page_height = A4
        
        # Calculate grid dimensions
        margin = 20  # Margin from page edges
        available_width = page_width - (2 * margin)
        available_height = page_height - (2 * margin)
        
        # Calculate cell dimensions
        cell_width = available_width / grid_cols
        cell_height = available_height / grid_rows
        
        # Calculate image size (leave some padding in each cell)
        image_padding = 5
        image_width = cell_width - (2 * image_padding)
        image_height = cell_height - (2 * image_padding)
        
        # Process images in batches of grid_cols * grid_rows
        images_per_page = grid_cols * grid_rows
        total_pages = (len(barcode_files) + images_per_page - 1) // images_per_page
        
        for page_num in range(total_pages):
            if page_num > 0:
                c.showPage()  # Start new page
            
            # Calculate which images to include on this page
            start_idx = page_num * images_per_page
            end_idx = min(start_idx + images_per_page, len(barcode_files))
            page_images = barcode_files[start_idx:end_idx]
            
            print(f"📄 Processing page {page_num + 1}/{total_pages} ({len(page_images)} images)")
            
            # Place images in grid
            for i, image_path in enumerate(page_images):
                # Calculate grid position
                row = i // grid_cols
                col = i % grid_cols
                
                # Calculate position on page
                x = margin + (col * cell_width) + image_padding
                y = page_height - margin - ((row + 1) * cell_height) + image_padding
                
                try:
                    # Add image to PDF
                    c.drawImage(ImageReader(image_path), x, y, 
                              width=image_width, height=image_height, 
                              preserveAspectRatio=True, anchor='sw')
                except Exception as e:
                    print(f"⚠️  Warning: Could not add image {os.path.basename(image_path)}: {e}")
        
        # Save the PDF
        c.save()
        
        # Save PDF details immediately to database
        pdf_file_size = os.path.getsize(pdf_path)
        pdf_record = BarcodeRecord(
            filename=pdf_filename,
            file_path=pdf_path,
            archive_path=pdf_path,  # Will be updated when archived
            file_type="pdf",
            file_size=pdf_file_size,
            created_at=datetime.now().isoformat(),
            archived_at=datetime.now().isoformat(),
            generation_session=session_id,
            imei=None,  # PDFs don't have individual IMEI
            box_id=None,
            model=None,
            product=f"Collection of {len(barcode_files)} barcodes",
            color=None,
            dn=None
        )
        
        pdf_record_id = self.archive_manager.db_manager.insert_barcode_record(pdf_record)
        print(f"✅ Saved PDF {pdf_filename} to database (ID: {pdf_record_id})")
        
        print(f"✅ PDF created successfully: {pdf_path}")
        print(f"📊 Total images included: {len(barcode_files)}")
        print(f"📄 Total pages: {total_pages}")
        print(f"📐 Grid layout: {grid_cols} columns × {grid_rows} rows")
        
        return pdf_filename
