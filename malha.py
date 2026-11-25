import numpy as np
import glm

def gerar_cubo(uv_scale_xz: float = 1.0, uv_scale_y: float = 1.0) -> np.ndarray:
    faces = [
        ([(-0.5, -0.5,  0.5), ( 0.5, -0.5,  0.5), ( 0.5,  0.5,  0.5), (-0.5,  0.5,  0.5)], (0.0, 0.0, 1.0), (uv_scale_xz, uv_scale_y)),
        ([( 0.5, -0.5, -0.5), (-0.5, -0.5, -0.5), (-0.5,  0.5, -0.5), ( 0.5,  0.5, -0.5)], (0.0, 0.0, -1.0), (uv_scale_xz, uv_scale_y)),
        ([( 0.5, -0.5,  0.5), ( 0.5, -0.5, -0.5), ( 0.5,  0.5, -0.5), ( 0.5,  0.5,  0.5)], (1.0, 0.0, 0.0), (uv_scale_xz, uv_scale_y)),
        ([(-0.5, -0.5, -0.5), (-0.5, -0.5,  0.5), (-0.5,  0.5,  0.5), (-0.5,  0.5, -0.5)], (-1.0, 0.0, 0.0), (uv_scale_xz, uv_scale_y)),
        ([(-0.5,  0.5,  0.5), ( 0.5,  0.5,  0.5), ( 0.5,  0.5, -0.5), (-0.5,  0.5, -0.5)], (0.0, 1.0, 0.0), (uv_scale_xz, uv_scale_xz)),
        ([(-0.5, -0.5, -0.5), ( 0.5, -0.5, -0.5), ( 0.5, -0.5,  0.5), (-0.5, -0.5,  0.5)], (0.0, -1.0, 0.0), (uv_scale_xz, uv_scale_xz)),
    ]

    dados = []
    for verts, normal, (su, sv) in faces:
        uvs = [(0.0, 0.0), (su, 0.0), (su, sv), (0.0, sv)]
        indices = [0, 1, 2, 0, 2, 3]
        for idx in indices:
            vx, vy, vz = verts[idx]
            u, v = uvs[idx]
            dados.extend([vx, vy, vz, normal[0], normal[1], normal[2], u, v])

    return np.array(dados, dtype='f4')

def gerar_esfera(raio: float = 0.5, setores: int = 24, pilhas: int = 16) -> np.ndarray:
    dados = []
    for i in range(pilhas):
        phi0 = np.pi * i / pilhas
        phi1 = np.pi * (i + 1) / pilhas
        for j in range(setores):
            theta0 = 2.0 * np.pi * j / setores
            theta1 = 2.0 * np.pi * (j + 1) / setores

            def ponto(phi, theta):
                x = np.sin(phi) * np.cos(theta)
                y = np.cos(phi)
                z = -np.sin(phi) * np.sin(theta)
                u = theta / (2.0 * np.pi)
                v = 1.0 - (phi / np.pi)
                return (x * raio, y * raio, z * raio, x, y, z, u, v)

            p00 = ponto(phi0, theta0)
            p10 = ponto(phi1, theta0)
            p11 = ponto(phi1, theta1)
            p01 = ponto(phi0, theta1)

            for p in (p00, p10, p11, p00, p11, p01):
                dados.extend(p)

    return np.array(dados, dtype='f4')

def gerar_octaedro(raio: float = 0.4) -> np.ndarray:
    topo = glm.vec3(0.0, raio * 1.4, 0.0)
    base = glm.vec3(0.0, -raio * 1.4, 0.0)
    anel = [
        glm.vec3( raio, 0.0,  0.0),
        glm.vec3( 0.0,  0.0, -raio),
        glm.vec3(-raio, 0.0,  0.0),
        glm.vec3( 0.0,  0.0,  raio),
    ]

    dados = []
    for i in range(4):
        v1 = anel[i]
        v2 = anel[(i + 1) % 4]

        n_sup = glm.normalize(glm.cross(v1 - topo, v2 - topo))
        for v, uv in [(topo, (0.5, 1.0)), (v1, (0.0, 0.0)), (v2, (1.0, 0.0))]:
            dados.extend([v.x, v.y, v.z, n_sup.x, n_sup.y, n_sup.z, uv[0], uv[1]])

        n_inf = glm.normalize(glm.cross(v2 - base, v1 - base))
        for v, uv in [(base, (0.5, 0.0)), (v2, (1.0, 1.0)), (v1, (0.0, 1.0))]:
            dados.extend([v.x, v.y, v.z, n_inf.x, n_inf.y, n_inf.z, uv[0], uv[1]])

    return np.array(dados, dtype='f4')

def carregar_modelo_off(caminho_arquivo: str):
    with open(caminho_arquivo, 'r') as f:
        linhas = [linha.strip() for linha in f if linha.strip() and not linha.strip().startswith('#')]

    if linhas[0] != 'OFF':
        raise ValueError("Arquivo OFF invalido.")

    num_vertices, num_faces, _ = map(int, linhas[1].split())
    vertices_brutos = []
    for i in range(2, 2 + num_vertices):
        x, y, z = map(float, linhas[i].split()[:3])
        vertices_brutos.append(glm.vec3(x, y, z))

    xs = [v.x for v in vertices_brutos]
    ys = [v.y for v in vertices_brutos]
    zs = [v.z for v in vertices_brutos]

    min_v = glm.vec3(min(xs), min(ys), min(zs))
    max_v = glm.vec3(max(xs), max(ys), max(zs))
    centro = (min_v + max_v) * 0.5
    tamanho = max_v - min_v
    maior_dim = max(tamanho.x, tamanho.y, tamanho.z)
    escala = 1.0 / maior_dim if maior_dim > 0 else 1.0

    matriz_enquadramento = glm.scale(glm.mat4(1.0), glm.vec3(escala)) * glm.translate(glm.mat4(1.0), -centro)

    dados = []
    inicio_faces = 2 + num_vertices
    for i in range(inicio_faces, inicio_faces + num_faces):
        partes = list(map(int, linhas[i].split()))
        qtd = partes[0]
        indices = partes[1:1 + qtd]

        for k in range(1, qtd - 1):
            v0 = vertices_brutos[indices[0]]
            v1 = vertices_brutos[indices[k]]
            v2 = vertices_brutos[indices[k + 1]]

            normal = glm.normalize(glm.cross(v1 - v0, v2 - v0))
            for v in (v0, v1, v2):
                rel = v - centro
                u = (glm.atan(-rel.z, rel.x) / (2.0 * glm.pi())) + 0.5
                v_coord = (rel.y - (min_v.y - centro.y)) / (tamanho.y if tamanho.y > 0 else 1.0)
                dados.extend([v.x, v.y, v.z, normal.x, normal.y, normal.z, u, v_coord])

    return np.array(dados, dtype='f4'), matriz_enquadramento
