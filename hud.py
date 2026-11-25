import numpy as np
import glm
import moderngl

class PlacarHUD:
    def __init__(self, ctx: moderngl.Context, prog_hud: moderngl.Program):
        self.ctx = ctx
        self.prog = prog_hud

        # Coracao preenchido desenhado com TRIANGLE_FAN (sentido anti-horario para passar no CULL_FACE)
        pontos_coracao = [0.0, 0.0]
        passos = 36
        for i in range(passos + 1):
            t = 2.0 * np.pi * (1.0 - (i / passos))
            x = (16.0 * (np.sin(t) ** 3)) / 16.0
            y = (13.0 * np.cos(t) - 5.0 * np.cos(2.0 * t) - 2.0 * np.cos(3.0 * t) - np.cos(4.0 * t)) / 16.0
            pontos_coracao.extend([x, y])

        v_coracao = np.array(pontos_coracao, dtype='f4')
        self.vbo_coracao = ctx.buffer(v_coracao.tobytes())
        self.vao_coracao = ctx.vertex_array(prog_hud, [(self.vbo_coracao, '2f', 'in_pos')])

        # Chave estilizada (LINES)
        v_chave = np.array([
            -0.3,  0.8,   0.3,  0.8,
             0.3,  0.8,   0.3,  0.2,
             0.3,  0.2,  -0.3,  0.2,
            -0.3,  0.2,  -0.3,  0.8,
             0.0,  0.2,   0.0, -0.9,
             0.0, -0.5,   0.4, -0.5,
             0.0, -0.8,   0.4, -0.8
        ], dtype='f4')
        self.vbo_chave = ctx.buffer(v_chave.tobytes())
        self.vao_chave = ctx.vertex_array(prog_hud, [(self.vbo_chave, '2f', 'in_pos')])

        # Mira central (+) em primeira pessoa (LINES)
        v_mira = np.array([
            -1.0, 0.0,  1.0, 0.0,
             0.0,-1.0,  0.0, 1.0
        ], dtype='f4')
        self.vbo_mira = ctx.buffer(v_mira.tobytes())
        self.vao_mira = ctx.vertex_array(prog_hud, [(self.vbo_mira, '2f', 'in_pos')])

        # Moldura de aviso central (LINE_LOOP)
        v_caixa = np.array([
            -1.0, -1.0,
             1.0, -1.0,
             1.0,  1.0,
            -1.0,  1.0
        ], dtype='f4')
        self.vbo_caixa = ctx.buffer(v_caixa.tobytes())
        self.vao_caixa = ctx.vertex_array(prog_hud, [(self.vbo_caixa, '2f', 'in_pos')])

    def desenhar(self, largura: int, altura: int, vidas: int, chaves_coletadas: int, total_chaves: int, estado_nome: str, primeira_pessoa: bool):
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.disable(moderngl.CULL_FACE)

        ortho = glm.ortho(0.0, float(largura), 0.0, float(altura), -1.0, 1.0)
        self.prog['u_ortho'].write(ortho)

        # 1. Vidas como Coracoes Preenchidos (TRIANGLE_FAN)
        self.prog['u_color'].value = (0.95, 0.15, 0.22)
        for i in range(vidas):
            model = glm.translate(glm.mat4(1.0), glm.vec3(42.0 + i * 44.0, altura - 40.0, 0.0)) * glm.scale(glm.mat4(1.0), glm.vec3(16.0))
            self.prog['u_model'].write(model)
            self.vao_coracao.render(moderngl.TRIANGLE_FAN)

        # 2. Chaves (LINES)
        for i in range(total_chaves):
            model = glm.translate(glm.mat4(1.0), glm.vec3(42.0 + i * 44.0, altura - 88.0, 0.0)) * glm.scale(glm.mat4(1.0), glm.vec3(16.0))
            self.prog['u_model'].write(model)
            self.prog['u_color'].value = (1.0, 0.85, 0.1) if i < chaves_coletadas else (0.35, 0.35, 0.35)
            self.vao_chave.render(moderngl.LINES)

        # 3. Mira central na camera FPS (LINES)
        if estado_nome == "JOGANDO" and primeira_pessoa:
            model = glm.translate(glm.mat4(1.0), glm.vec3(largura * 0.5, altura * 0.5, 0.0)) * glm.scale(glm.mat4(1.0), glm.vec3(8.0))
            self.prog['u_model'].write(model)
            self.prog['u_color'].value = (0.85, 0.9, 0.95)
            self.vao_mira.render(moderngl.LINES)

        # 4. Borda de destaque na tela conforme o estado do jogo (LINE_LOOP)
        if estado_nome != "JOGANDO":
            cores_estado = {
                "INICIO":  (0.2, 0.7, 1.0),
                "PAUSADO": (1.0, 0.8, 0.2),
                "VITORIA": (0.2, 0.95, 0.4),
                "DERROTA": (0.95, 0.2, 0.2),
            }
            self.prog['u_color'].value = cores_estado.get(estado_nome, (1.0, 1.0, 1.0))
            model = glm.translate(glm.mat4(1.0), glm.vec3(largura * 0.5, altura * 0.5, 0.0)) * glm.scale(
                glm.mat4(1.0), glm.vec3(largura * 0.46, altura * 0.44, 1.0)
            )
            self.prog['u_model'].write(model)
            self.vao_caixa.render(moderngl.LINE_LOOP)

        self.ctx.enable(moderngl.CULL_FACE)
        self.ctx.enable(moderngl.DEPTH_TEST)
