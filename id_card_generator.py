from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import platform
import os

class IDCardGenerator:
    def __init__(self, data_manager):
        self.data_manager = data_manager

    def generate_id_card(self, name, student_id, course=None):
        """Generate ID card based on Canva design"""
        card_width = 600
        card_height = 350
        
        card = Image.new('RGB', (card_width, card_height), '#1a237e')
        
        for i in range(card_height):
            r = int(26 + (i * 0.1))
            g = int(35 + (i * 0.1))
            b = int(126 + (i * 0.2))
            for x in range(card_width):
                if x < card_width // 2:
                    card.putpixel((x, i), (min(r, 255), min(g, 255), min(b, 255)))
                else:
                    card.putpixel((x, i), (min(r+10, 255), min(g+15, 255), min(b+20, 255)))
        
        draw = ImageDraw.Draw(card)
        
        draw.rectangle([20, 20, card_width-20, card_height-20], fill='white', outline='#ffd700', width=3)
        
        draw.rectangle([30, 30, card_width-30, 80], fill='#1a237e')
        draw.text((card_width//2, 55), "STUDENT ID CARD", fill='#ffd700', anchor="mm", font=self.get_font(24, bold=True))
        
        draw.rectangle([50, 100, 150, 200], fill='#e0e0e0', outline='#1a237e', width=2)
        draw.text((100, 150), "PHOTO", fill='#666', anchor="mm")
        
        draw.text((250, 120), f"Name:", fill='#333', font=self.get_font(14))
        draw.text((250, 120), f"{name}", fill='#1a237e', font=self.get_font(14, bold=True))
        
        draw.text((250, 150), f"ID:", fill='#333', font=self.get_font(14))
        draw.text((250, 150), f"{student_id}", fill='#1a237e', font=self.get_font(14, bold=True))
        
        if course:
            draw.text((250, 180), f"Course:", fill='#333', font=self.get_font(14))
            draw.text((250, 180), f"{course}", fill='#1a237e', font=self.get_font(14, bold=True))
        
        today = datetime.now().strftime("%d/%m/%Y")
        draw.text((250, 230), f"Issued:", fill='#333', font=self.get_font(12))
        draw.text((250, 230), f"{today}", fill='#1a237e', font=self.get_font(12))
        
        draw.line([250, 280, 450, 280], fill='#333', width=2)
        draw.text((350, 290), "Authorized Signature", fill='#666', anchor="mm", font=self.get_font(10))
        
        draw.ellipse([card_width-80, card_height-80, card_width-30, card_height-30], 
                    outline='#ffd700', width=3)
        
        filename = f"ID_Card_{name}_{student_id}.png"
        card.save(filename)
        
        return card, filename

    def get_font(self, size, bold=False):
        """Get font for ID card"""
        try:
            if platform.system() == "Windows":
                font_name = "arialbd.ttf" if bold else "arial.ttf"
                return ImageFont.truetype(font_name, size)
            else:
                if platform.system() == "Darwin":
                    font_paths = [
                        "/System/Library/Fonts/Helvetica.ttc",
                        "/Library/Fonts/Arial.ttf",
                        "/System/Library/Fonts/Supplemental/Arial.ttf"
                    ]
                    for font_path in font_paths:
                        try:
                            return ImageFont.truetype(font_path, size)
                        except:
                            continue
                else:
                    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
                    try:
                        return ImageFont.truetype(font_path, size)
                    except:
                        pass
        except:
            pass
        return ImageFont.load_default()
