from PIL import Image, ImageDraw, ImageFont

# Create a blank image with gray background
img = Image.new('RGB', (400, 400), (220, 220, 220))
draw = ImageDraw.Draw(img)

# Draw a border
draw.rectangle([(0, 0), (399, 399)], outline=(180, 180, 180), width=2)

# Add "No Image" text
text = "No Image"
try:
    # Try to use a system font
    font = ImageFont.truetype("arial.ttf", 40)
except:
    # If not available, use default font
    font = ImageFont.load_default()

# Calculate text position to center it
text_width = draw.textlength(text, font=font) if hasattr(draw, 'textlength') else font.getsize(text)[0]
text_position = ((400 - text_width) // 2, 180)

# Draw the text
draw.text(text_position, text, fill=(100, 100, 100), font=font)

# Save the image
img.save("static/img/placeholders/no-image.jpg", "JPEG")
print("Placeholder image created successfully!")