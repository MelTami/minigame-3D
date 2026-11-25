import moderngl
from PIL import Image

def carregar_textura_srgb(ctx: moderngl.Context, caminho: str, repetir: bool = True) -> moderngl.Texture:
    img = Image.open(caminho).convert("RGBA")
    img = img.transpose(Image.FLIP_TOP_BOTTOM)

    # internal_format=0x8C43 corresponde a GL_SRGB8_ALPHA8 no OpenGL
    tex = ctx.texture(img.size, 4, img.tobytes(), internal_format=0x8C43)
    tex.build_mipmaps()
    tex.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
    tex.repeat_x = repetir
    tex.repeat_y = repetir
    return tex
