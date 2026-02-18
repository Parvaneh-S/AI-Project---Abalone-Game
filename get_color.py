import pygame
pygame.init()

try:
    img = pygame.image.load('landing_page_icon.png')

    # Get average color from the corners and edges (likely background)
    width, height = img.get_size()
    colors = []

    # Sample corners and edges
    positions = [
        (0, 0), (width-1, 0), (0, height-1), (width-1, height-1),
        (width//4, 0), (width//2, 0), (3*width//4, 0),
        (width//4, height-1), (width//2, height-1), (3*width//4, height-1),
        (0, height//4), (0, height//2), (0, 3*height//4),
        (width-1, height//4), (width-1, height//2), (width-1, 3*height//4)
    ]

    for x, y in positions:
        try:
            color = img.get_at((x, y))
            colors.append(color[:3])  # RGB only
        except:
            pass

    # Calculate average
    if colors:
        avg_r = sum(c[0] for c in colors) // len(colors)
        avg_g = sum(c[1] for c in colors) // len(colors)
        avg_b = sum(c[2] for c in colors) // len(colors)

        with open('color_output.txt', 'w') as f:
            f.write(f'({avg_r}, {avg_g}, {avg_b})')
        print('Color extracted successfully')

except Exception as e:
    with open('color_output.txt', 'w') as f:
        f.write(f'Error: {e}')

