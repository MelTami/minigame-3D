import glm


class Sentinela:
    def __init__(self, pos_inicial: glm.vec3, eixo: str, amplitude: float, velocidade: float):
        self.pos_base = glm.vec3(pos_inicial)
        self.pos = glm.vec3(pos_inicial)
        self.eixo = eixo
        self.amplitude = amplitude
        self.velocidade = velocidade
        self.direcao = 1.0
        self.deslocamento = 0.0
        self.raio = 0.45

    def atualizar(self, dt: float):
        self.deslocamento += self.direcao * self.velocidade * dt
        if self.deslocamento > self.amplitude:
            self.deslocamento = self.amplitude
            self.direcao = -1.0
        elif self.deslocamento < -self.amplitude:
            self.deslocamento = -self.amplitude
            self.direcao = 1.0

        self.pos = glm.vec3(self.pos_base)
        if self.eixo == 'x':
            self.pos.x += self.deslocamento
        else:
            self.pos.z += self.deslocamento


class Mapa:
    """
    Representa o labirinto 3D, suas caixas de colisao AABB,
    as chaves coletaveis, as sentinelas e o altar de saida.
    """
    def __init__(self, tile_size: float = 2.0):
        self.tile_size = tile_size
        # 1 = Parede, 0 = Corredor, P = Jogador, K = Chave, E = Saida (.off)
        self.layout = [
            "1111111111",
            "1P001000K1",
            "1010101101",
            "1010001001",
            "1011101011",
            "1K00000001",
            "1110111101",
            "1K001E0001",
            "1111111111",
        ]
        self.paredes = []
        self.chaves = []
        self.sentinelas = []
        self.pos_inicial_jogador = glm.vec3(2.0, 0.5, 2.0)
        self.pos_saida = glm.vec3(10.0, 0.0, 14.0)

        self._construir_mapa()

    def _construir_mapa(self):
        meio = self.tile_size * 0.5
        for linha_idx, linha in enumerate(self.layout):
            for col_idx, celula in enumerate(linha):
                wx = col_idx * self.tile_size
                wz = linha_idx * self.tile_size

                if celula == '1':
                    self.paredes.append({
                        "centro": glm.vec3(wx, 1.25, wz),
                        "min_x": wx - meio,
                        "max_x": wx + meio,
                        "min_y": 0.0,
                        "max_y": 2.5,
                        "min_z": wz - meio,
                        "max_z": wz + meio,
                    })
                elif celula == 'P':
                    self.pos_inicial_jogador = glm.vec3(wx, 0.55, wz)
                elif celula == 'K':
                    self.chaves.append({
                        "pos": glm.vec3(wx, 0.55, wz),
                        "coletada": False,
                        "raio": 0.42
                    })
                elif celula == 'E':
                    self.pos_saida = glm.vec3(wx, 0.0, wz)

        # Sentinelas patrulhando corredores estrategicos
        self.sentinelas.append(Sentinela(glm.vec3(10.0, 0.48, 10.0), eixo='x', amplitude=4.2, velocidade=2.8))
        self.sentinelas.append(Sentinela(glm.vec3(6.0, 0.48, 4.0), eixo='z', amplitude=2.2, velocidade=2.4))

    def colide_esfera_aabb(self, x: float, y: float, z: float, raio: float) -> bool:
        for p in self.paredes:
            cx = max(p["min_x"], min(x, p["max_x"]))
            cy = max(p["min_y"], min(y, p["max_y"]))
            cz = max(p["min_z"], min(z, p["max_z"]))

            dx = x - cx
            dy = y - cy
            dz = z - cz
            if (dx * dx + dy * dy + dz * dz) < (raio * raio):
                return True
        return False

    def mover_com_colisao(self, pos: glm.vec3, deslocamento: glm.vec3, raio: float = 0.38) -> glm.vec3:
        nova_pos = glm.vec3(pos)

        # Testa eixo X em 3D (deslizamento suave ao longo das paredes)
        teste_x = nova_pos.x + deslocamento.x
        if not self.colide_esfera_aabb(teste_x, nova_pos.y, nova_pos.z, raio):
            nova_pos.x = teste_x

        # Testa eixo Z em 3D
        teste_z = nova_pos.z + deslocamento.z
        if not self.colide_esfera_aabb(nova_pos.x, nova_pos.y, teste_z, raio):
            nova_pos.z = teste_z

        return nova_pos
