# Monitor Global de Cibersegurança (automático)

Funciona com GitHub Pages + GitHub Actions: gratuito, sem servidor.

1. Crie um repositório PÚBLICO no GitHub (ex.: cyber-monitor) e envie todos estes arquivos (incluindo a pasta .github).
2. Em Settings > Pages: Source = "Deploy from a branch", Branch = main, pasta / (root).
3. Em Actions, abra "Atualizar noticias" e clique em "Run workflow" para gerar o primeiro noticias.json.
4. Acesse https://SEU-USUARIO.github.io/cyber-monitor/
5. Dali em diante o GitHub atualiza a cada 30 minutos e a página recarrega sozinha a cada 15.

Teste local: `python fetch_news.py` e depois `python -m http.server` e abra http://localhost:8000
Para incluir outros feeds, edite a lista FEEDS em fetch_news.py. Feeds que falharem são ignorados.
