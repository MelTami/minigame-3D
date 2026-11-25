import math
import numpy as np
import moderngl
import glm


class PlacarHUD:
    """
    Renderiza o HUD 2D ortogonal na segunda passada:
    - Vidas restantes em formato de coracao preenchido (TRIANGLE_FAN)
    - Chaves coletadas vs. totais (LINES)
    - Mira central em 1a pessoa (LINES)
    - Moldura indicativa de estado (LINE_LOOP)
    """
    def __init__(self, ctx: moderngl.Context, prog_hud: moderngl.Program):
        self.ctx = ctx
        self.prog = prog_hud

        # Coracao preenchido (TRIANGLE_FAN) - desenhado na passada 2D com CULL_FACE desabilitado
        pontos_coracao = [0.0, -0.15]
        passos = 36
        for i in range(passos + 1):
            t = (2.0 * math.pi * i) / passos
            x = 16.0 * (math.sin(t) ** 3)
            y = (
                13.0 * math.cos(t)
                - 5.0 * math.cos(2.0 * t)
                - 2.0 * math.cos(3.0 * t)
                - math.cos(4.0 * t)
            )
            pontos_coracao.extend([x / 17.0, (y + 2.5) / 17.0])

        verts_coracao = np.array(pontos_coracao, dtype='f4')
        self.vbo_coracao = self.ctx.buffer(verts_coracao.tobytes())
        self.vao_coracao = self.ctx.vertex_array(
            self.prog, [(self.vbo_coracao, '2f', 'in_pos')]
        )

        # Icone de chave (LINES)
        verts_chave = np.array([
            # Argola superior
            -0.35, 0.85,   0.35, 0.85,
             0.35, 0.85,   0.35, 0.35,
             0.35, 0.35,  -0.35, 0.35,
            -0.35, 0.35,  -0.35, 0.85,
            # Haste vertical e dentes
             0.00, 0.35,   0.00, -0.90,
             0.00, -0.45,  0.40, -0.45,
             0.00, -0.80,  0.45, -0.80,
        ], dtype='f4')
        self.vbo_chave = self.ctx.buffer(verts_chave.tobytes())
        self.vao_chave = self.ctx.vertex_array(
            self.prog, [(self.vbo_chave, '2f', 'in_pos')]
        )

        # Mira central em 1a pessoa (LINES)
        verts_mira = np.array([
            -1.0,  0.0,   1.0, 0.0,
             0.0, -1.0,   0.0, 1.0,
        ], dtype='f4')
        self.vbo_mira = self.ctx.buffer(verts_mira.tobytes())
        self.vao_mira = self.ctx.vertex_array(
            self.prog, [(self.vbo_mira, '2f', 'in_pos')]
        )

        # Moldura externa de estado (LINE_LOOP)
        verts_caixa = np.array([
            -1.0, -1.0,
             1.0, -1.0,
             1.0,  1.0,
            -1.0,  1.0,
        ], dtype='f4')
        self.vbo_caixa = self.ctx.buffer(verts_caixa.tobytes())
        self.vao_caixa = self.ctx.vertex_array(
            self.prog, [(self.vbo_caixa, '2f', 'in_pos')]
        )

    def _desenhar_item(self, vao, modo, x: float, y: float, sx: float, sy: float, cor: tuple):
        model = glm.translate(glm.mat4(1.0), glm.vec3(x, y, 0.0)) * glm.scale(glm.mat4(1.0), glm.vec3(sx, sy, 1.0))
        self.prog['u_model'].write(model)
        self.prog['u_color'].write(glm.vec3(*cor))
        vao.render(modo)

    def desenhar(
        self,
        largura: int,
        altura: int,
        vidas: int,
        chaves_coletadas: int,
        total_chaves: int,
        estado_nome: str,
        primeira_pessoa: bool,
    ):
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.disable(moderngl.CULL_FACE)

        # Projecao ortografica em pixels: (0, 0) canto inferior esquerdo, (largura, altura) canto superior direito
        ortho = glm.ortho(0.0, float(largura), 0.0, float(altura), -1.0, 1.0)
        self.prog['u_ortho'].write(ortho)

        # 1. Coracoes preenchidos no canto superior esquerdo (TRIANGLE_FAN)
        for i in range(max(0, vidas)):
            px = 42.0 + i * 44.0
            py = altura - 42.0
            self._desenhar_item(
                self.vao_coracao,
                moderngl.TRIANGLE_FAN,
                px,
                py,
                16.0,
                16.0,
                (0.95, 0.18, 0.24),
            )

        # 2. Chaves no canto superior direito (LINES)
        for i in range(total_chaves):
            px = largura - 42.0 - (total_chaves - 1 - i) * 38.0
            py = altura - 42.0
            cor = (1.0, 0.85, 0.20) if i < chaves_coletadas else (0.35, 0.35, 0.40)
            self._desenhar_item(
                self.vao_chave,
                moderngl.LINES,
                px,
                py,
                14.0,
                16.0,
                cor,
            )

        # 3. Mira central apenas em 1a pessoa (LINES)
        if primeira_pessoa and estado_nome == "JOGANDO":
            self._desenhar_item(
                self.vao_mira,
                moderngl.LINES,
                largura * 0.5,
                altura * 0.5,
                10.0,
                10.0,
                (0.90, 0.95, 1.0),
            )

        # 4. Borda colorida conforme o estado da partida (LINE_LOOP)
        cores_estado = {
            "INICIO": (0.25, 0.65, 1.00),
            "PAUSADO": (1.00, 0.82, 0.18),
            "VITORIA": (0.20, 0.92, 0.42),
            "DERROTA": (0.95, 0.22, 0.22),
        }
        if estado_nome in cores_estado:
            self._desenhar_item(
                self.vao_caixa,
                moderngl.LINE_LOOP,
                largura * 0.5,
                altura * 0.5,
                largura * 0.48,
                altura * 0.47,
                cores_estado[estado_nome],
            )

        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.CULL_FACE)
