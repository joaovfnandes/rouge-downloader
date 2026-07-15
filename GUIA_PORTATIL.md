# Guia do Rouge Portátil v1.1.0

## Instalação

1. Baixe `Rouge-Windows-x64-v1.1.0.zip` na página Releases do GitHub.
2. Extraia o ZIP inteiro para uma pasta comum, como Documentos.
3. Abra `Rouge.exe`.
4. Mantenha a janela do programa aberta enquanto estiver usando o site.

Não é necessário instalar Python ou Flask. O Rouge utiliza a primeira porta disponível entre `5000` e `5009` e abre o endereço correto automaticamente.

## Onde ficam seus dados

- `nhentai_out/`: galerias e imagens baixadas.
- `tag_history.json`: tags descobertas e frequência de uso.
- `logs/`: registros locais.

Esses dados permanecem no computador e não são enviados ao repositório do projeto.

## Atualizar sem perder a coleção

1. Feche o `Rouge.exe` antigo.
2. Extraia a versão nova em outra pasta.
3. Copie `nhentai_out`, `tag_history.json` e, se desejar, `logs` da pasta antiga para a nova.
4. Abra o novo `Rouge.exe` e confirme sua coleção.
5. Só depois apague a pasta antiga.

## Busca e downloads

- Escreva as tags desejadas no campo de busca.
- Use `-tag:"nome"` para excluir uma tag.
- Escolha quantas galerias baixar e quantas fotos serão baixadas ao mesmo tempo.
- Os controles permitem pausar, continuar, pular a galeria atual e parar.
- Galerias já presentes na coleção não são baixadas novamente.

## Tags descobertas

- A lupa abre o filtro das tags salvas.
- O botão de expansão mostra uma lista maior.
- Clique em uma tag para adicioná-la ou removê-la da busca.
- O número ao lado da tag indica em quantas galerias ela apareceu.

## Sua coleção

Na página **Sua coleção**, o filtro encontra galerias por:

- título;
- código numérico;
- tags descobertas durante o download.

## Layout das imagens recentes

O botão **Layout** oferece três modos:

- **Editorial**: três imagens lado a lado;
- **Mosaico**: uma imagem grande acompanhada de imagens menores;
- **Foco**: mostra somente a imagem mais recente.

O layout escolhido fica salvo no navegador.

## Solução de problemas

- Se o navegador não abrir, tente `http://127.0.0.1:5000` até `http://127.0.0.1:5009`.
- Se o Windows exibir um aviso, confirme que o arquivo foi baixado da Release oficial antes de executar.
- Não abra duas cópias do programa ao mesmo tempo.
- Não mova somente `Rouge.exe`; `_internal` é parte obrigatória do programa.

## Privacidade e responsabilidade

O Rouge funciona localmente e não inclui galerias na distribuição pública. Use o programa somente de acordo com as leis aplicáveis e os termos do serviço acessado.
