# Alterações no Sistema de Custos

Este repositório contém as alterações necessárias para separar os custos entre materiais e mão de obra no programa de dimensionamento de muros de arrimo.

## Arquivos Modificados

1. `custos.py` - Novo arquivo que contém:
   - Variáveis globais para armazenar os custos
   - Função `inicializar_campos_custo()` para criar os campos na interface
   - Função `editar_custos_popup()` para editar os custos
   - Função `atualizar_info_custos()` para atualizar as informações na interface

2. `temp_dimensionamentos.py` - Versão modificada do arquivo original com:
   - Importação do módulo `custos`
   - Inicialização dos campos de custo na janela principal
   - Atualização da função `calcular()` para usar os custos separados
   - Atualização dos cálculos de custo total para considerar materiais e mão de obra

## Como Aplicar as Alterações

1. Copie o arquivo `custos.py` para o diretório do projeto
2. Compare o arquivo `temp_dimensionamentos.py` com o arquivo original `Dimensionamentos.py`
3. Aplique as alterações necessárias no arquivo original, principalmente:
   - Importação do módulo `custos`
   - Chamada da função `custos.inicializar_campos_custo(root)` na função `criar_janela_principal()`
   - Atualização dos cálculos de custo na função `calcular()`

## Novas Funcionalidades

- Separação dos custos entre materiais e mão de obra
- Interface dedicada para edição dos custos
- Cálculos atualizados considerando os custos separados
- Exibição dos custos totais de materiais e mão de obra

## Observações

- Os valores padrão dos custos podem ser ajustados no arquivo `custos.py`
- A interface de edição de custos é modal, impedindo interação com a janela principal
- Os cálculos são atualizados automaticamente ao modificar os custos 