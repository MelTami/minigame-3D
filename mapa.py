import glm

class Sentinela:
    def __init__(self, inicio: glm.vec3, fim: glm.vec3, velocidade: float = 2.2):
        self.inicio = glm.vec3(inicio)
        self.fim = glm.vec3(fim)
        self.pos = glm.vec3(inicio)
        self.velocidade = velocidade
        self.indo = True
        self.raio = 0.45

    def atualizar(self, dt: float):
        alvo = self.fim if self.indo else self.inicio
        vetor = alvo - self.pos
        dist = glm.length(vetor)
        if dist < 0.05:
            self.indo = not self.indo
        else:
            direcao = glm.normalize(vetor)
            self.pos += direcao * min(self.velocidade * dt, dist)

class Mapa:
    def __init__(self, tile_size: float = 2.0):
        self.tile_size = tile_size
        self.grid = [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 4, 0, 0, 1, 2, 0, 0, 0, 1],
            [1, 0, 1, 0, 1, 1, 1, 1, 0, 1],
            [1, 0, 1, 0, 0, 0, 0, 0, 0, 1],
            [1, 2, 1, 1, 1, 0, 1, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 1, 2, 0, 1],
            [1, 0, 1, 1, 0, 1, 1, 1, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 0, 3, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ]
        self.paredes = []
        self.chaves = []
        self.pos_saida = glm.vec3(0.0)
        self.pos_inicial_jogador = glm.vec3(2.0, 1.0, 2.0)
        self._construir()

        ts = self.tile_size
        self.sentinelas = [
            Sentinela(glm.vec3(3 * ts, 0.85, 3 * ts), glm.vec3(8 * ts, 0.85, 3 * ts), velocidade=2.4),
            Sentinela(glm.vec3(1 * ts, 0.85, 7 * ts), glm.vec3(7 * ts, 0.85, 7 * ts), velocidade=2.8),
        ]

    def _construir(self):
        half = self.tile_size / 2.0
        for r, row in enumerate(self.grid):
            for c, cell in enumerate(row):
                x = c * self.tile_size
                z = r * self.tile_size
                if cell == 1:
                    self.paredes.append({
                        "min_x": x - half,
                        "max_x": x + half,
                        "min_z": z - half,
                        "max_z": z + half,
                        "centro": glm.vec3(x, 1.25, z)
                    })
                elif cell == 2:
                    self.chaves.append({
                        "pos": glm.vec3(x, 0.9, z),
                        "coletada": False,
                        "raio": 0.35
                    })
                elif cell == 3:
                    self.pos_saida = glm.vec3(x, 0.0, z)
                elif cell == 4:
                    self.pos_inicial_jogador = glm.vec3(x, 1.0, z)

    def colide_esfera_aabb(self, px: float, pz: float, raio: float) -> bool:
        for p in self.paredes:
            closest_x = max(p["min_x"], min(px, p["max_x"]))
            closest_z = max(p["min_z"], min(pz, p["max_z"]))
            dx = px - closest_x
            dz = pz - closest_z
            if (dx * dx + dz * dz) < (raio * raio):
                return True
        return False

    def mover_com_colisao(self, pos_atual: glm.vec3, deslocamento: glm.vec3, raio: float = 0.38) -> glm.vec3:
        nova_pos = glm.vec3(pos_atual)
        if not self.colide_esfera_aabb(nova_pos.x + deslocamento.x, nova_pos.z, raio):
            nova_pos.x += deslocamento.x
        if not self.colide_esfera_aabb(nova_pos.x, nova_pos.z + deslocamento.z, raio):
            nova_pos.z += deslocamento.z
        return nova_pos
