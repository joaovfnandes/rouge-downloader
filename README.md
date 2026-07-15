# Rouge Downloader

Interface local para pesquisar e baixar galerias do nhentai no Windows, com acompanhamento em tempo real e coleção privada no próprio computador.

> Projeto destinado exclusivamente a maiores de 18 anos. Nenhuma galeria ou imagem de terceiros está incluída neste repositório ou nos arquivos da Release. Use somente de acordo com as leis aplicáveis e os termos do serviço acessado.

## Baixar a versão portátil

Acesse a [Release mais recente](https://github.com/joaovfnandes/rouge-downloader/releases/latest), baixe `Rouge-Windows-x64-v1.0.0.zip`, extraia a pasta inteira e abra `Rouge.exe`.

Não é necessário instalar Python. Mantenha a janela do Rouge aberta enquanto estiver usando o site.

## Recursos

- Downloads paralelos configuráveis.
- Pausar, continuar, parar e pular a galeria atual.
- Imagens aparecem na interface conforme terminam de baixar.
- Proteção contra baixar a mesma galeria duas vezes.
- Histórico local de tags descobertas, com sugestões clicáveis.
- Coleção e leitor locais.
- Interface responsiva em tema Rouge.

## Privacidade

Tudo é armazenado localmente:

- `nhentai_out/`: galerias baixadas.
- `tag_history.json`: histórico das tags descobertas.
- `logs/`: registros locais.

Esses dados são ignorados pelo Git e não fazem parte da versão pública.

## Executar pelo código-fonte

Requer Python 3.12 ou mais recente.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python app.py
```

Depois, abra `http://127.0.0.1:5000`.

No Windows, também é possível abrir `rodar.bat`.

## Criar a pasta portátil

Abra `build_portable.bat`. O resultado será criado em `dist\Rouge`.

## Aviso

Este projeto não é afiliado, patrocinado ou aprovado pelo nhentai. O usuário é responsável pelo conteúdo que decide acessar e armazenar.
