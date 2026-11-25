"""
================================================================================
ATIVIDADE 05 - JOGO 3D: DUNGEON CRAWLER (LABIRINTO ESCURO)
Disciplina: Computacao Grafica - Prof. Joao Paulo Gois
================================================================================

INSTRUCOES DE EXECUCAO:
1. Certifique-se de ter as bibliotecas instaladas:
   pip install glfw moderngl numpy pyglm pillow
2. Execute o programa a partir da pasta raiz do projeto:
   python main.py

CONTROLES DO TECLADO E DO MOUSE:
- [ENTER / ESPACO / Clique Esq]: Iniciar partida (INICIO) ou Reiniciar (VITORIA/DERROTA)
- [W, A, S, D] ou [Setas]      : Movimentar o jogador pelo labirinto
- [Segurar Botao Dir + Mouse]  : Girar a camera (olhar ao redor)
- [Q / E]                      : Girar a camera suavemente pelo teclado
- [Botao Esq Mouse]            : Ligar / Desligar a lanterna conica (spotlight)
- [C]                          : Alternar camera (3a Pessoa <-> 1a Pessoa)
- [TAB]                        : Alternar Visao Aerea Tatica
- [Scroll Mouse]               : Aproximar / Afastar o zoom (altera o FOV)
- [P]                          : Pausar / Retomar o jogo (sem acumular tempo no dt)
- [R]                          : Reiniciar a partida a qualquer momento
- [V]                          : Ligar / Desligar VSync (observavel no FPS da janela)
- [M]                          : Alternar modo solido / aramado (wireframe)
- [ESC]                        : Fechar o programa
================================================================================
"""

import os
from enum import Enum
import glfw
import moderngl
import glm

from mapa import Mapa
from malha import gerar_cubo, gerar_esfera, gerar_octaedro, carregar_modelo_off
from texturas import carregar_textura_srgb
from hud import PlacarHUD


class EstadoJogo(Enum):
    INICIO = 1
    JOGANDO = 2
    PAUSADO = 3
    VITORIA = 4
    DERROTA = 5


class DungeonGame:
    def __init__(self):
        if not glfw.init():
            raise RuntimeError("Falha ao inicializar o GLFW.")

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 0)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        self.largura, self.altura = 1100, 760
        self.window = glfw.create_window(
            self.largura,
            self.altura,
            "Dungeon 3D | INICIO [ENTER / Clique: Jogar | C: 3a/1a Pessoa | TAB: Aerea | Scroll: Zoom]",
            None,
            None
        )
        if not self.window:
            glfw.terminate()
            raise RuntimeError("Falha ao criar a janela GLFW.")

        glfw.make_context_current(self.window)
        self.ctx = moderngl.create_context()

        # Requisitos obrigatorios: teste de profundidade e descarte de faces traseiras
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.CULL_FACE)

        # Configuracoes iniciais
        self.estado = EstadoJogo.INICIO
        self.vsync = True
        glfw.swap_interval(1)
        self.modo_camera = 0  # 0 = 3a Pessoa, 1 = 1a Pessoa, 2 = Visao Aerea
        self.wireframe = False
        self.lanterna_ligada = True
        self.fov = 75.0

        # Orientacao da camera (gira apenas ao segurar o botao direito)
        self.yaw = 0.0
        self.pitch = -12.0
        self.sensibilidade = 0.15
        self.girando_camera = False
        self.ultimo_x = self.largura / 2.0
        self.ultimo_y = self.altura / 2.0

        # Registrar callbacks
        glfw.set_framebuffer_size_callback(self.window, self.on_resize)
        glfw.set_key_callback(self.window, self.on_key)
        glfw.set_cursor_pos_callback(self.window, self.on_mouse_move)
        glfw.set_mouse_button_callback(self.window, self.on_mouse_button)
        glfw.set_scroll_callback(self.window, self.on_scroll)

        self._carregar_shaders()
        self._carregar_recursos()
        self.reiniciar_partida()

    def _carregar_shaders(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base_dir, "shaders", "phong.vert"), "r") as f:
            v3d = f.read()
        with open(os.path.join(base_dir, "shaders", "phong.frag"), "r") as f:
            f3d = f.read()
        self.prog_3d = self.ctx.program(vertex_shader=v3d, fragment_shader=f3d)

        with open(os.path.join(base_dir, "shaders", "hud.vert"), "r") as f:
            vhud = f.read()
        with open(os.path.join(base_dir, "shaders", "hud.frag"), "r") as f:
            fhud = f.read()
        self.prog_hud = self.ctx.program(vertex_shader=vhud, fragment_shader=fhud)

    def _carregar_recursos(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))

        dados_parede = gerar_cubo(uv_scale_xz=1.0, uv_scale_y=1.25)
        self.vbo_parede = self.ctx.buffer(dados_parede.tobytes())
        self.vao_parede = self.ctx.vertex_array(self.prog_3d, [(self.vbo_parede, '3f 3f 2f', 'in_pos', 'in_normal', 'in_uv')])

        dados_piso = gerar_cubo(uv_scale_xz=10.0, uv_scale_y=1.0)
        self.vbo_piso = self.ctx.buffer(dados_piso.tobytes())
        self.vao_piso = self.ctx.vertex_array(self.prog_3d, [(self.vbo_piso, '3f 3f 2f', 'in_pos', 'in_normal', 'in_uv')])

        dados_esfera = gerar_esfera(raio=0.45, setores=24, pilhas=16)
        self.vbo_esfera = self.ctx.buffer(dados_esfera.tobytes())
        self.vao_esfera = self.ctx.vertex_array(self.prog_3d, [(self.vbo_esfera, '3f 3f 2f', 'in_pos', 'in_normal', 'in_uv')])

        dados_chave = gerar_octaedro(raio=0.32)
        self.vbo_chave = self.ctx.buffer(dados_chave.tobytes())
        self.vao_chave = self.ctx.vertex_array(self.prog_3d, [(self.vbo_chave, '3f 3f 2f', 'in_pos', 'in_normal', 'in_uv')])

        caminho_off = os.path.join(base_dir, "modelos", "calice.off")
        dados_off, self.matriz_enquadramento_off = carregar_modelo_off(caminho_off)
        self.vbo_off = self.ctx.buffer(dados_off.tobytes())
        self.vao_off = self.ctx.vertex_array(self.prog_3d, [(self.vbo_off, '3f 3f 2f', 'in_pos', 'in_normal', 'in_uv')])

        self.tex_parede = carregar_textura_srgb(self.ctx, os.path.join(base_dir, "texturas", "parede_tijolo.png"), repetir=True)
        self.tex_piso = carregar_textura_srgb(self.ctx, os.path.join(base_dir, "texturas", "chao_pedra.png"), repetir=True)
        self.tex_ouro = carregar_textura_srgb(self.ctx, os.path.join(base_dir, "texturas", "ouro.png"), repetir=True)

        self.hud = PlacarHUD(self.ctx, self.prog_hud)

    def reiniciar_partida(self):
        self.mapa = Mapa(tile_size=2.0)
        self.player_pos = glm.vec3(self.mapa.pos_inicial_jogador)
        self.vidas = 3
        self.chaves_coletadas = 0
        self.total_chaves = len(self.mapa.chaves)
        self.tempo_animacao = 0.0
        self.invulneravel_timer = 0.0
        self.yaw = 0.0
        self.pitch = -12.0
        self.girando_camera = False

    def _iniciar_ou_retomar_jogo(self):
        self.estado = EstadoJogo.JOGANDO
        self.girando_camera = False

    # --- CALLBACKS ---
    def on_resize(self, window, w, h):
        if h == 0:
            return
        self.largura, self.altura = w, h
        self.ctx.viewport = (0, 0, w, h)

    def on_key(self, window, key, scancode, action, mods):
        if action != glfw.PRESS:
            return

        if key == glfw.KEY_ESCAPE:
            glfw.set_window_should_close(self.window, True)

        elif key in (glfw.KEY_ENTER, glfw.KEY_KP_ENTER, glfw.KEY_SPACE):
            if self.estado == EstadoJogo.INICIO:
                self._iniciar_ou_retomar_jogo()
            elif self.estado in (EstadoJogo.VITORIA, EstadoJogo.DERROTA):
                self.reiniciar_partida()
                self._iniciar_ou_retomar_jogo()

        elif key == glfw.KEY_P and self.estado in (EstadoJogo.JOGANDO, EstadoJogo.PAUSADO):
            if self.estado == EstadoJogo.JOGANDO:
                self.estado = EstadoJogo.PAUSADO
                self.girando_camera = False
            else:
                self._iniciar_ou_retomar_jogo()

        elif key == glfw.KEY_R:
            self.reiniciar_partida()
            self._iniciar_ou_retomar_jogo()

        # Tecla C: alterna diretamente entre 3a Pessoa (0) e 1a Pessoa (1)
        elif key == glfw.KEY_C:
            self.modo_camera = 1 if self.modo_camera == 0 else 0

        # Tecla TAB: alterna a Visao Aerea Tatica (2)
        elif key == glfw.KEY_TAB:
            self.modo_camera = 2 if self.modo_camera != 2 else 0

        elif key == glfw.KEY_V:
            self.vsync = not self.vsync
            glfw.swap_interval(1 if self.vsync else 0)

        elif key == glfw.KEY_M:
            self.wireframe = not self.wireframe
            self.ctx.wireframe = self.wireframe

    def on_mouse_move(self, window, xpos, ypos):
        # So gira a camera enquanto o botao direito estiver pressionado
        if not self.girando_camera or self.estado != EstadoJogo.JOGANDO or self.modo_camera == 2:
            self.ultimo_x, self.ultimo_y = xpos, ypos
            return

        dx = (xpos - self.ultimo_x) * self.sensibilidade
        dy = (self.ultimo_y - ypos) * self.sensibilidade
        self.ultimo_x, self.ultimo_y = xpos, ypos

        self.yaw += dx
        self.pitch = max(-45.0, min(45.0, self.pitch + dy))

    def on_mouse_button(self, window, button, action, mods):
        # Botao direito: segura para girar a camera
        if button == glfw.MOUSE_BUTTON_RIGHT:
            if action == glfw.PRESS and self.estado == EstadoJogo.JOGANDO:
                self.girando_camera = True
                self.ultimo_x, self.ultimo_y = glfw.get_cursor_pos(self.window)
            elif action == glfw.RELEASE:
                self.girando_camera = False

        # Botao esquerdo: inicia, reinicia (em VITORIA/DERROTA) ou alterna a lanterna
        elif button == glfw.MOUSE_BUTTON_LEFT and action == glfw.PRESS:
            if self.estado == EstadoJogo.INICIO:
                self._iniciar_ou_retomar_jogo()
            elif self.estado in (EstadoJogo.VITORIA, EstadoJogo.DERROTA):
                self.reiniciar_partida()
                self._iniciar_ou_retomar_jogo()
            elif self.estado == EstadoJogo.JOGANDO:
                self.lanterna_ligada = not self.lanterna_ligada

    def on_scroll(self, window, xoffset, yoffset):
        self.fov = max(45.0, min(90.0, self.fov - yoffset * 4.0))
        if self.modo_camera != 2:
            if yoffset > 0 and self.fov <= 48.0:
                self.modo_camera = 1
            elif yoffset < 0 and self.modo_camera == 1 and self.fov >= 60.0:
                self.modo_camera = 0

    # --- LOGICA E COLISOES ---
    def _obter_direcao_olhar(self) -> glm.vec3:
        fx = glm.cos(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch))
        fy = glm.sin(glm.radians(self.pitch))
        fz = glm.sin(glm.radians(self.yaw)) * glm.cos(glm.radians(self.pitch))
        return glm.normalize(glm.vec3(fx, fy, fz))

    def _atualizar_jogo(self, dt: float):
        self.tempo_animacao += dt
        if self.invulneravel_timer > 0.0:
            self.invulneravel_timer = max(0.0, self.invulneravel_timer - dt)

        # Rotacao suave alternativa pelo teclado (Q e E)
        vel_rotacao = 95.0
        if glfw.get_key(self.window, glfw.KEY_Q) == glfw.PRESS:
            self.yaw -= vel_rotacao * dt
        if glfw.get_key(self.window, glfw.KEY_E) == glfw.PRESS:
            self.yaw += vel_rotacao * dt

        # Movimento continuo via glfw.get_key (WASD ou Setas)
        frente = glm.normalize(glm.vec3(glm.cos(glm.radians(self.yaw)), 0.0, glm.sin(glm.radians(self.yaw))))
        direita = glm.normalize(glm.cross(frente, glm.vec3(0.0, 1.0, 0.0)))

        direcao = glm.vec3(0.0)
        if glfw.get_key(self.window, glfw.KEY_W) == glfw.PRESS or glfw.get_key(self.window, glfw.KEY_UP) == glfw.PRESS:
            direcao += frente
        if glfw.get_key(self.window, glfw.KEY_S) == glfw.PRESS or glfw.get_key(self.window, glfw.KEY_DOWN) == glfw.PRESS:
            direcao -= frente
        if glfw.get_key(self.window, glfw.KEY_D) == glfw.PRESS or glfw.get_key(self.window, glfw.KEY_RIGHT) == glfw.PRESS:
            direcao += direita
        if glfw.get_key(self.window, glfw.KEY_A) == glfw.PRESS or glfw.get_key(self.window, glfw.KEY_LEFT) == glfw.PRESS:
            direcao -= direita

        velocidade = 4.2
        if glm.length(direcao) > 0.0:
            direcao = glm.normalize(direcao)
            self.player_pos = self.mapa.mover_com_colisao(self.player_pos, direcao * velocidade * dt, raio=0.38)

        # Colisao Esfera-Esfera com as Chaves
        raio_jogador = 0.42
        for chave in self.mapa.chaves:
            if not chave["coletada"]:
                dist = glm.distance(glm.vec2(self.player_pos.x, self.player_pos.z), glm.vec2(chave["pos"].x, chave["pos"].z))
                if dist < (raio_jogador + chave["raio"]):
                    chave["coletada"] = True
                    self.chaves_coletadas += 1

        # Atualizar Sentinelas e checar colisao Esfera-Esfera
        for sent in self.mapa.sentinelas:
            sent.atualizar(dt)
            dist = glm.distance(glm.vec2(self.player_pos.x, self.player_pos.z), glm.vec2(sent.pos.x, sent.pos.z))
            if dist < (raio_jogador + sent.raio) and self.invulneravel_timer == 0.0:
                self.vidas -= 1
                self.invulneravel_timer = 1.5
                self.player_pos = glm.vec3(self.mapa.pos_inicial_jogador)
                if self.vidas <= 0:
                    self.estado = EstadoJogo.DERROTA
                    self.girando_camera = False
                    return

        # Checar colisao com o Altar/Calice (.off) da Saida
        dist_saida = glm.distance(glm.vec2(self.player_pos.x, self.player_pos.z), glm.vec2(self.mapa.pos_saida.x, self.mapa.pos_saida.z))
        if dist_saida < 0.85 and self.chaves_coletadas >= self.total_chaves:
            self.estado = EstadoJogo.VITORIA
            self.girando_camera = False

    # --- RENDERIZACAO ---
    def _configurar_iluminacao(self, view_pos: glm.vec3, dir_olhar: glm.vec3):
        self.prog_3d['u_view_pos'].write(view_pos)

        # Luz 0: Tocha pontual que acompanha o jogador
        self.prog_3d['u_lights[0].type'].value = 0
        self.prog_3d['u_lights[0].position'].write(self.player_pos + glm.vec3(0.0, 0.45, 0.0))
        self.prog_3d['u_lights[0].direction'].write(glm.vec3(0.0, -1.0, 0.0))
        self.prog_3d['u_lights[0].color'].write(glm.vec3(1.1, 0.8, 0.48))
        self.prog_3d['u_lights[0].constant'].value = 1.0
        self.prog_3d['u_lights[0].linear'].value = 0.18
        self.prog_3d['u_lights[0].quadratic'].value = 0.09
        self.prog_3d['u_lights[0].cutOff'].value = 0.0
        self.prog_3d['u_lights[0].outerCutOff'].value = 0.0
        self.prog_3d['u_lights[0].enabled'].value = True

        # Luz 1: Lanterna conica (spotlight) controlada pelo clique esquerdo
        self.prog_3d['u_lights[1].type'].value = 1
        self.prog_3d['u_lights[1].position'].write(self.player_pos + glm.vec3(0.0, 0.35, 0.0))
        self.prog_3d['u_lights[1].direction'].write(dir_olhar)
        self.prog_3d['u_lights[1].color'].write(glm.vec3(1.5, 1.5, 1.65))
        self.prog_3d['u_lights[1].constant'].value = 1.0
        self.prog_3d['u_lights[1].linear'].value = 0.08
        self.prog_3d['u_lights[1].quadratic'].value = 0.025
        self.prog_3d['u_lights[1].cutOff'].value = glm.cos(glm.radians(16.0))
        self.prog_3d['u_lights[1].outerCutOff'].value = glm.cos(glm.radians(25.0))
        self.prog_3d['u_lights[1].enabled'].value = self.lanterna_ligada

        # Luz 2: Luz vermelha que se move com a primeira sentinela
        sent_pos = self.mapa.sentinelas[0].pos
        self.prog_3d['u_lights[2].type'].value = 0
        self.prog_3d['u_lights[2].position'].write(sent_pos + glm.vec3(0.0, 0.4, 0.0))
        self.prog_3d['u_lights[2].direction'].write(glm.vec3(0.0, -1.0, 0.0))
        self.prog_3d['u_lights[2].color'].write(glm.vec3(1.1, 0.15, 0.15))
        self.prog_3d['u_lights[2].constant'].value = 1.0
        self.prog_3d['u_lights[2].linear'].value = 0.25
        self.prog_3d['u_lights[2].quadratic'].value = 0.18
        self.prog_3d['u_lights[2].cutOff'].value = 0.0
        self.prog_3d['u_lights[2].outerCutOff'].value = 0.0
        self.prog_3d['u_lights[2].enabled'].value = True

    def _definir_material(self, ka, kd, ks, shininess):
        self.prog_3d['u_material.ka'].write(glm.vec3(*ka))
        self.prog_3d['u_material.kd'].write(glm.vec3(*kd))
        self.prog_3d['u_material.ks'].write(glm.vec3(*ks))
        self.prog_3d['u_material.shininess'].value = float(shininess)

    def _desenhar_objeto(self, vao, model: glm.mat4):
        normal_mat = glm.transpose(glm.inverse(glm.mat3(model)))
        self.prog_3d['u_model'].write(model)
        self.prog_3d['u_normal_matrix'].write(normal_mat)
        vao.render(moderngl.TRIANGLES)

    def _calcular_camera_terceira_pessoa(self, dir_olhar: glm.vec3):
        alvo = self.player_pos + glm.vec3(0.0, 0.35, 0.0)
        dir_horizontal = glm.normalize(glm.vec3(dir_olhar.x, 0.0, dir_olhar.z))

        dist_max = 1.35
        dist_segura = 0.2
        for passo in range(1, 11):
            d = (dist_max * passo) / 10.0
            teste = alvo - dir_horizontal * d
            if not self.mapa.colide_esfera_aabb(teste.x, teste.z, raio=0.25):
                dist_segura = d
            else:
                break

        view_pos = alvo - dir_horizontal * dist_segura + glm.vec3(0.0, 0.55, 0.0)
        ponto_foco = alvo + dir_olhar * 2.5
        return view_pos, glm.lookAt(view_pos, ponto_foco, glm.vec3(0.0, 1.0, 0.0))

    def _renderizar(self):
        self.ctx.clear(0.02, 0.02, 0.03)

        aspecto = self.largura / float(self.altura)
        proj = glm.perspective(glm.radians(self.fov), aspecto, 0.1, 80.0)
        dir_olhar = self._obter_direcao_olhar()

        if self.modo_camera == 2:
            centro_mapa = glm.vec3(9.0, 0.0, 8.0)
            view_pos = glm.vec3(9.0, 21.0, 14.5)
            view = glm.lookAt(view_pos, centro_mapa, glm.vec3(0.0, 1.0, 0.0))
        elif self.modo_camera == 1:
            view_pos = self.player_pos + glm.vec3(0.0, 0.35, 0.0)
            view = glm.lookAt(view_pos, view_pos + dir_olhar, glm.vec3(0.0, 1.0, 0.0))
        else:
            view_pos, view = self._calcular_camera_terceira_pessoa(dir_olhar)

        self.prog_3d['u_view'].write(view)
        self.prog_3d['u_proj'].write(proj)
        self.prog_3d['u_texture'].value = 0
        self._configurar_iluminacao(view_pos, dir_olhar)

        # 1. Piso
        self.tex_piso.use(location=0)
        self._definir_material((0.14, 0.14, 0.16), (0.85, 0.85, 0.85), (0.12, 0.12, 0.12), 8.0)
        model_piso = glm.translate(glm.mat4(1.0), glm.vec3(9.0, -0.05, 8.0)) * glm.scale(glm.mat4(1.0), glm.vec3(20.0, 0.1, 18.0))
        self._desenhar_objeto(self.vao_piso, model_piso)

        # 2. Paredes
        self.tex_parede.use(location=0)
        self._definir_material((0.14, 0.12, 0.12), (0.85, 0.80, 0.80), (0.15, 0.15, 0.15), 12.0)
        for p in self.mapa.paredes:
            model_parede = glm.translate(glm.mat4(1.0), p["centro"]) * glm.scale(glm.mat4(1.0), glm.vec3(2.0, 2.5, 2.0))
            self._desenhar_objeto(self.vao_parede, model_parede)

        # 3. Chaves flutuantes
        self.tex_ouro.use(location=0)
        self._definir_material((0.22, 0.20, 0.08), (0.95, 0.85, 0.45), (0.95, 0.90, 0.60), 64.0)
        for idx, chave in enumerate(self.mapa.chaves):
            if not chave["coletada"]:
                flutuacao = glm.sin(self.tempo_animacao * 3.0 + idx) * 0.12
                m = glm.translate(glm.mat4(1.0), chave["pos"] + glm.vec3(0.0, flutuacao, 0.0))
                m = glm.rotate(m, self.tempo_animacao * 2.2, glm.vec3(0.0, 1.0, 0.0))
                self._desenhar_objeto(self.vao_chave, m)

        # 4. Altar / Calice da Saida (.OFF)
        pulso = 1.0 + 0.08 * glm.sin(self.tempo_animacao * 4.0) if self.chaves_coletadas >= self.total_chaves else 1.0
        m_altar = glm.translate(glm.mat4(1.0), self.mapa.pos_saida + glm.vec3(0.0, 0.75, 0.0))
        m_altar = glm.rotate(m_altar, self.tempo_animacao * 1.2, glm.vec3(0.0, 1.0, 0.0))
        m_altar = glm.scale(m_altar, glm.vec3(1.3 * pulso))
        self._desenhar_objeto(self.vao_off, m_altar * self.matriz_enquadramento_off)

        # 5. Sentinelas Inimigas
        self.tex_parede.use(location=0)
        self._definir_material((0.35, 0.05, 0.05), (0.9, 0.2, 0.2), (0.8, 0.4, 0.4), 32.0)
        for sent in self.mapa.sentinelas:
            m_sent = glm.translate(glm.mat4(1.0), sent.pos)
            m_sent = glm.rotate(m_sent, self.tempo_animacao * 3.0, glm.vec3(0.0, 1.0, 0.0))
            self._desenhar_objeto(self.vao_esfera, m_sent)

        # 6. Avatar do Jogador (visivel em 3a Pessoa e Visao Aerea)
        if self.modo_camera in (0, 2):
            self.tex_ouro.use(location=0)
            self._definir_material((0.25, 0.22, 0.12), (0.95, 0.85, 0.50), (0.9, 0.9, 0.7), 48.0)
            m_player = glm.translate(glm.mat4(1.0), self.player_pos - glm.vec3(0.0, 0.25, 0.0)) * glm.scale(glm.mat4(1.0), glm.vec3(0.72))
            self._desenhar_objeto(self.vao_esfera, m_player)

        # 7. Placar HUD
        self.hud.desenhar(
            self.largura,
            self.altura,
            self.vidas,
            self.chaves_coletadas,
            self.total_chaves,
            self.estado.name,
            self.modo_camera == 1
        )

    def executar(self):
        tempo_anterior = glfw.get_time()
        frames = 0
        tempo_fps = tempo_anterior

        while not glfw.window_should_close(self.window):
            tempo_atual = glfw.get_time()
            dt = tempo_atual - tempo_anterior
            tempo_anterior = tempo_atual

            dt = min(dt, 0.05)

            frames += 1
            if tempo_atual - tempo_fps >= 0.4:
                fps = frames / (tempo_atual - tempo_fps)
                nomes_cam = ["3a Pessoa", "1a Pessoa", "Aerea"]
                aviso_estado = (
                    " [ENTER / Clique: Reiniciar]"
                    if self.estado in (EstadoJogo.VITORIA, EstadoJogo.DERROTA)
                    else (" [ENTER / Clique: Jogar]" if self.estado == EstadoJogo.INICIO else "")
                )
                glfw.set_window_title(
                    self.window,
                    f"Dungeon 3D | {self.estado.name}{aviso_estado} | Cam: {nomes_cam[self.modo_camera]} [C: 3a/1a | TAB: Aerea | Scroll: Zoom] | Chaves: {self.chaves_coletadas}/{self.total_chaves} | FPS: {fps:.0f}"
                )
                frames = 0
                tempo_fps = tempo_atual

            if self.estado == EstadoJogo.JOGANDO:
                self._atualizar_jogo(dt)

            self._renderizar()
            glfw.swap_buffers(self.window)
            glfw.poll_events()

        glfw.terminate()


if __name__ == "__main__":
    DungeonGame().executar()
