# Estudo de viabilidade paramétrico de muros de arrimo utilizando programação em Python

Repositório oficial da ferramenta computacional descrita no artigo de pesquisa sobre análise preliminar de muros de arrimo dos tipos **gravidade** e **flexão** (concreto armado), com interface gráfica, verificações de estabilidade global, pré-dimensionamento estrutural e estimativa comparativa de custos.

**Autores:** Felipe Parellada Nicolodi · Gabriel Felipe Pryjma Cardal Vieira · Daniela Gutstein

**Palavras-chave:** muros de arrimo · Python · muro de gravidade · muro de flexão · orçamento analítico

---

## Resumo

Ferramenta em linguagem **Python** voltada à análise de estabilidade, ao pré-dimensionamento estrutural e à estimativa preliminar de custos de muros de arrimo. A interface gráfica (Tkinter) permite estudos paramétricos com variação de parâmetros geotécnicos, geométricos e de carregamento.

As verificações de estabilidade global contemplam **deslizamento**, **tombamento** e **tensões admissíveis na fundação**, com empuxos fundamentados nas teorias de **Rankine** e **Coulomb** (coeficientes ativo e em repouso conforme a tipologia). O dimensionamento das armaduras dos muros de flexão segue a **NBR 6118** (armadura simples à flexão). A estimativa orçamentária utiliza composições do **SINAPI** (valores editáveis na interface).

A validação foi realizada por comparação com **quatro exemplos analíticos** da literatura (Moliterno, 1980; Marchetti, 2008), com divergências inferiores a **10%** nos parâmetros verificados. Os resultados indicam coerência técnica para estudos paramétricos preliminares de contenções associadas a **barragens, canais hidráulicos e obras de infraestrutura**.

---

## Funcionalidades

| Módulo | Descrição |
|--------|-----------|
| Muro de flexão | Verificação global (FSD, FST, tensões na base), dimensionamento de armadura (CA-50), diagrama de seção com empuxos e cotas, tabela de esforços |
| Muro de gravidade | Dimensionamento iterativo da geometria, verificações de estabilidade e visualização da seção |
| Quantitativos | Concreto estrutural, concreto massa/magro, aço e formas por metro linear de muro |
| Custos (SINAPI) | Estimativa comparativa em R$/m; composições editáveis pelo usuário |
| Estudo paramétrico | Variação de **altura** (com d = H/10), **espessura** do fuste e **ângulo de atrito** φ; otimização da menor base/largura estável em cada ponto |
| Análise de sensibilidade | Varredura de parâmetros individuais com comparação entre tipologias |

### Critérios de estabilidade (carregamento normal)

- **Deslizamento (FSD):** resistência por coesão e atrito, com fatores de segurança parciais (referência Eletrobras, 2003).
- **Tombamento (FST):** relação entre momentos estabilizantes e tombantes em torno do bordo de jusante; exige-se FST ≥ 1,5.
- **Tensões na fundação:** distribuição trapezoidal no contato solo–estrutura; base integralmente comprimida no caso normal.

### Empuxos e tipologias

- **Muro de gravidade:** empuxo em repouso (k₀) ou valor conservador adotado pelo usuário.
- **Muro de flexão:** empuxo ativo (Kₐ), com diagrama triangular de solo e contribuição de sobrecarga quando informada.

### Composições SINAPI de referência (março/2025)

| Item | Código SINAPI |
|------|----------------|
| Concreto usinado fck 25 MPa | 99439 |
| Concreto massa | 94974 |
| Aço CA-50 (cortinas) | 100345 |
| Forma para concreto | 100341 |

Os custos apresentados são **comparativos por metro linear** de muro contínuo, adequados à fase preliminar — não substituem orçamento executivo (mobilização, escavação, ensaios geotécnicos, etc.).

---

## Instalação e execução

**Requisitos:** Python 3.10 ou superior, `matplotlib` e `tkinter` (biblioteca padrão na maioria das instalações do Python no Windows).

```powershell
python -m venv .venv
& .venv\Scripts\python.exe -m pip install --upgrade pip
& .venv\Scripts\python.exe -m pip install -r requirements.txt
& .venv\Scripts\python.exe Dimensionamentos.py
```

## Uso rápido

1. Informe na interface os parâmetros geotécnicos (γ, φ, c, Kₐ/k₀), geometria (H, bases, espessuras) e carregamentos (sobrecarga, pressão admissível).
2. Clique em **Calcular** para atualizar verificações, quantitativos e custos.
3. Use **Exibir Muro de Flexão** ou **Exibir Muro de Gravidade** para os diagramas e relatórios.
4. **Estudo Paramétrico** — compare tipologias variando altura, espessura ou ângulo de atrito; em cada ponto o programa busca a menor base estável dentro dos limites informados.
5. **Análise de Sensibilidade** — avalie a influência de um parâmetro por vez sobre custo e estabilidade.

---

## Estrutura do repositório

| Arquivo | Conteúdo |
|---------|----------|
| `Dimensionamentos.py` | Código-fonte principal (interface, cálculos, gráficos e estudos paramétricos) |
| `requirements.txt` | Dependências Python |
| `LICENSE` | Licença MIT |

---

## Validação

Comparação com quatro exemplos da literatura especializada:

| Exemplo | Tipologia | Parâmetros verificados |
|---------|-----------|------------------------|
| Moliterno (1980) — Ex. 1 | Gravidade | FST, tensão máxima na base |
| Moliterno (1980) — Ex. 2 | Flexão | FSD, peso de aço |
| Marchetti (2008) — Ex. 3 | Gravidade | FST, tensão máxima |
| Marchetti (2008) — Ex. 4 | Flexão | FSD, peso de aço |

As maiores divergências concentram-se no consumo de aço do Exemplo 2 (~9%), associadas ao arredondamento comercial do diâmetro e espaçamento das barras.

---

## Limitações da versão atual

Conforme o escopo do artigo, a ferramenta tem caráter de **pré-dimensionamento e análise preliminar**. Nesta etapa da pesquisa, o foco principal está em casos representativos para validação dos algoritmos e estudos paramétricos comparativos. Não substitui projeto executivo nem análises que exijam modelos avançados de interação solo–estrutura, percolação, ações sísmicas ou verificações completas em estado limite de serviço.

Trabalhos futuros prevêem a expansão para condições de carregamento mais complexas em obras hidráulicas e barragens.

---

## Como citar

> NICOLodi, F. P.; VIEIRA, G. F. P. C.; GUTSTEIN, D. **Estudo de viabilidade paramétrico de muros de arrimo utilizando programação em Python**. *Artigo apresentado no Damsweek* [template R4]. Disponível em: https://github.com/Crocolode/Damsweek-Arrimos

Ajuste venue, ano e páginas conforme a publicação final do congresso.

---

## Referências principais do estudo

- Moliterno, A. (1980). *Caderno de Muros de Arrimo*. São Paulo: Edgard Blücher.
- Marchetti, O. (2008). *Muros de Arrimo*. São Paulo: Blucher.
- Terzaghi, K.; Peck, R. B.; Mesri, G. (1995). *Soil Mechanics in Engineering Practice*. John Wiley & Sons.
- Eletrobras (2003). *Critérios de Projeto Civil de Usinas Hidrelétricas*.
- ABNT NBR 6118 (2026). *Projeto de estruturas de concreto*.
- Caixa Econômica Federal (2024). *Manual Técnico do SINAPI*.

---

## Licença

Este projeto está sob a licença **MIT** — veja o arquivo [LICENSE](LICENSE).
