# 🕯️ Dungeon 3D — Labirinto Escuro (Dungeon Crawler)

Jogo 3D em tempo real desenvolvido em **Python** com **OpenGL 4.0 Core Profile** (**ModernGL** e **GLFW**) para a disciplina de **Computação Gráfica** (Prof. João Paulo Gois).

O jogador explora uma masmorra escura iluminada dinamicamente por uma tocha e uma lanterna cônica direcional, precisando coletar **3 chaves douradas**, desviar de **sentinelas inimigas** que patrulham os corredores e alcançar o **cálice sagrado** na saída para vencer.

---

## 🛠️ Tecnologias Utilizadas

* **Python 3.10+**
* **GLFW** — Criação de janela, contexto OpenGL 4.0 Core Profile e gerenciamento de eventos (teclado, mouse e scroll)
* **ModernGL** — Pipeline programável de renderização 3D e 2D ortográfico
* **GLSL (400 Core)** — Shaders de iluminação **Blinn-Phong** multi-fonte com espaço linear/sRGB e shader de HUD 2D
* **PyGLM** — Álgebra linear, matrizes de transformação (`Model`, `View`, `Projection`, `Ortho`) e matriz normal
* **NumPy** — Geração e manipulação de buffers de vértices (VBOs)
* **Pillow (PIL)** — Carregamento de texturas com mipmaps e filtragem trilinear

---

## 📁 Estrutura do Projeto

```text
dungeon_3d/
├── main.py                  # Loop principal, estados do jogo, câmeras, iluminação e entrada
├── mapa.py                  # Matriz do labirinto, AABBs das paredes, sentinelas e colisões
├── malha.py                 # Geradores procedurais (cubo, esfera, octaedro) e leitor .OFF
├── texturas.py              # Carregamento de texturas sRGB com mipmaps
├── hud.py                   # Interface 2D ortográfica (corações, chaves, mira e bordas)
├── shaders/
│   ├── phong.vert           # Vertex shader 3D
│   ├── phong.frag           # Fragment shader 3D (Blinn-Phong com 3 luzes e correção gama)
│   ├── hud.vert             # Vertex shader 2D ortográfico
│   └── hud.frag             # Fragment shader 2D
├── modelos/
│   └── calice.off           # Malha poligonal 3D do cálice da saída
├── texturas/
│   ├── parede_tijolo.png    # Textura difusa das paredes
│   ├── chao_pedra.png       # Textura difusa do piso
│   └── ouro.png             # Textura difusa metálica das chaves e do avatar
└── README.md                # Documentação do projeto
```

---

## 🚀 Como Executar

1. **Instale as dependências:**

   ```bash
   pip install glfw moderngl numpy pyglm pillow
   ```

2. **Execute o jogo a partir da pasta raiz do projeto:**

   ```bash
   python main.py
   ```

---

## 🎮 Controles do Jogo

| Comando / Tecla | Ação |
| :--- | :--- |
| **`ENTER`** / **`ESPAÇO`** / **Clique Esq.** | Iniciar partida (na tela de início) ou reiniciar (após Vitória/Derrota) |
| **`W`**, **`A`**, **`S`**, **`D`** ou **Setas** | Movimentar o jogador pelo labirinto |
| **Segurar Botão Direito + Mouse** | Girar a câmera livremente (olhar ao redor) |
| **`Q`** / **`E`** | Girar a câmera suavemente pelo teclado |
| **Botão Esquerdo do Mouse** | Ligar / desligar a lanterna cônica (*spotlight*) durante o jogo |
| **`C`** | Alternar câmera entre **3ª Pessoa** e **1ª Pessoa** |
| **`TAB`** | Alternar **Visão Aérea Tática** do labirinto |
| **Scroll do Mouse** | Aproximar / afastar o zoom (ajusta o FOV e alterna 1ª/3ª pessoa) |
| **`P`** | Pausar / retomar a partida |
| **`R`** | Reiniciar a partida a qualquer momento |
| **`V`** | Ligar / desligar **VSync** (observável no contador de FPS da janela) |
| **`M`** | Alternar entre renderização sólida e aramada (*wireframe*) |
| **`ESC`** | Fechar o jogo |

---

## ✨ Recursos Implementados

* **Iluminação Blinn-Phong Multi-Fonte:**
  * **Tocha pontual** acoplada ao jogador com atenuação quadrática.
  * **Lanterna cônica (*spotlight*)** direcional com bordas suaves (`cutOff` e `outerCutOff`).
  * **Luz vermelha dinâmica** que acompanha a sentinela nos corredores.
* **Câmeras Dinâmicas:** 3ª Pessoa com prevenção de atravessamento de paredes (*anti-clipping*), 1ª Pessoa com mira central e Visão Aérea Tática.
* **Colisões 3D:** Deslizamento suave **Esfera–AABB** nas paredes e detecção **Esfera–Esfera** para coleta de chaves, dano de sentinelas e conclusão da fase.
* **HUD Ortográfico 2D:** Vidas renderizadas como corações preenchidos (`TRIANGLE_FAN`), ícones de chaves (`LINES`), mira em primeira pessoa (`LINES`) e molduras de estado (`LINE_LOOP`).

---

## 👥 Autores

* **Melissa Tami Vavassori** — RA: `11202231931`