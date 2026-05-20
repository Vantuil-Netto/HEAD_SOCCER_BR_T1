# Head Soccer BR

Um divertido jogo arcade de futebol estilo "Head Soccer" para dois jogadores locais, desenvolvido em Python utilizando a biblioteca **Pygame**.

---

## Requisitos e Instalação de Dependências

Para rodar o jogo, você precisará do **Python 3** instalado em sua máquina e da biblioteca **Pygame**.

### 1. Instalar o Pygame

Abra o seu terminal (Prompt de Comando, PowerShell ou Terminal do Linux/macOS) e execute o comando abaixo para instalar as dependências:

```bash
pip install pygame
```

---

## Como Executar o Jogo

Após instalar o Pygame, navegue até a pasta do projeto no terminal e execute o arquivo principal:

```bash
python head_soccer.py
```

---

## Controles do Jogo

O jogo é jogado inteiramente no teclado por dois jogadores locais.

### Navegação nos Menus
* **Menu Principal / Menu de Pausa:**
  * Use as teclas `W`/`S` ou `Seta Para Cima`/`Seta Para Baixo` para navegar pelas opções.
  * Pressione `Enter` ou clique com o botão esquerdo do mouse sobre o botão para selecionar.
* **Seleção de Personagens:**
  * **Jogador 1:** Use `W`, `A`, `S`, `D` para selecionar o personagem.
  * **Jogador 2:** Use as `Setas do Teclado` para selecionar o personagem.
  * **Iniciar Partida:** Pressione `Enter`.
* **Tela de Fim de Jogo:**
  * Pressione `R` para voltar ao menu principal.

### Controles em Partida
Durante o jogo, os controles para movimentação e chute de cada jogador são:

| Ação | Jogador 1 (Esquerda) | Jogador 2 (Direita) |
| :--- | :---: | :---: |
| **Mover para Esquerda** | `A` | `Seta para Esquerda` |
| **Mover para Direita** | `D` | `Seta para Direita` |
| **Pular** | `W` | `Seta para Cima` |
| **Chutar (Especial)** | `Espaço` | `Enter` |

* **Pausar o jogo:** Pressione a tecla `ESC`.

---

## Regras do Jogo
* Cada partida possui um tempo limite de **60 segundos**.
* O primeiro jogador a marcar **3 gols** vence a partida imediatamente.
* Se o tempo regulamentar terminar empatado, é ativado o **Gol de Ouro (Golden Goal)** com duração de 30 segundos, onde o primeiro que marcar vence o jogo.

---

## Lógica e Funcionamento do Jogo

O código principal do jogo está localizado no arquivo head_soccer.py e baseia-se em uma arquitetura orientada a objetos estruturada em torno de quatro classes principais:[Player], [Ball] [Goal] e o gerenciador principal [Game]

Abaixo estão detalhados os pilares do funcionamento do jogo:

### 1. Máquina de Estados (State Machine)
O fluxo do jogo é controlado por uma máquina de estados simples na classe [Game], chaveando entre os seguintes estados (`self.state`):
* **`SPLASH`**: Tela de abertura animada com efeito de piscar indicando o início.
* **`MENU`**: Menu principal que permite escolher entre iniciar o jogo ou sair.
* **`CHARACTER_SELECT`**: Seleção de personagens para ambos os jogadores.
* **`PLAYING`**: Estado ativo da partida, processando física, entradas do teclado e placar.
* **`PAUSED`**: Jogo pausado, congelando o timer e permitindo retornar, reiniciar ou ir ao menu.
* **`GOAL`**: Estado temporário ativado ao fazer gol, exibindo animação de gol por 2 segundos e reiniciando as posições.
* **`GOLDEN_GOAL`**: Prorrogação ativada em caso de empate, onde o primeiro gol marcado garante a vitória.
* **`END`**: Tela de finalização mostrando o vencedor e permitindo voltar ao menu com a tecla `R`.

### 2. Física de Jogo (Arcade Physics)
* **Gravidade Independente**: A física do jogo simula a aceleração vertical da gravidade. A bola tem uma gravidade menor (`BALL_GRAVITY = 0.24`) permitindo que flutue mais tempo, enquanto os jogadores têm uma gravidade maior (`GRAVITY = 0.45`) para pulos mais rápidos e responsivos.
* **Atrito e Desaceleração**: A velocidade horizontal da bola é atenuada por um atrito constante (`BALL_FRICTION = 0.98`), impedindo que a bola deslize indefinidamente e exigindo constante movimentação dos jogadores.
* **Limitação de Velocidade**: Para manter a jogabilidade arcade sob controle, a bola possui limites estritos de velocidade horizontal (`MAX_BALL_SPEED = 28`) e vertical (`MAX_BALL_VERTICAL_SPEED = 30`).
* **Visual Dinâmico**: A bola rotaciona visualmente de acordo com o sentido e intensidade de sua velocidade horizontal. Além disso, uma sombra de tamanho dinâmico (que encolhe ou expande com base na altura da bola) é desenhada no chão.

### 3. Sistema de Colisões
O jogo detecta e resolve colisões a cada frame:
* **Jogador vs Jogador**: Se ambos os jogadores se tocarem, uma lógica de empurrão (overlap resolution) calcula a distância de sobreposição e afasta ambos os retângulos lateralmente por igual, impedindo que um atravesse o outro.
* **Jogador vs Bola**:
  * **Passivo (Cabeça ou Chuteira parada)**: Quando a bola encosta no corpo ou no pé do jogador, ela sofre um rebote baseado na distância entre os centros dos objetos (colisão circular aproximada), aplicando um empurrão básico.
  * **Ativo (Chute)**: Quando o jogador pressiona o botão de chute (`Espaço`/`Enter`), a chuteira rotaciona rapidamente. Se a chuteira colidir com a bola durante essa animação, a bola é impulsionada com grande velocidade em direção ao campo adversário.
  * **Chute Direcional Inteligente**: Se a bola estiver perto do chão, o chute aplica um impulso com ângulo vertical elevado para encobrir o adversário. Se a bola estiver alta, o impulso vertical é reduzido, chutando a bola mais "rasante".
* **Bola vs Cenário**: A bola rebate elasticamente no chão com um coeficiente de restituição (`BOUNCE = 0.72`), rebate nas paredes laterais e teto, e também colide fisicamente com o travessão horizontal dos gols.

### 4. Reinício e Vantagem no Saque
Após a marcação de um gol (exceto no Gol de Ouro), o jogo reseta as posições. Para manter a partida dinâmica, a bola não reaparece no centro; em vez disso, ela é posicionada no lado do campo do jogador que sofreu o gol, dando a ele a vantagem do primeiro chute (saque).