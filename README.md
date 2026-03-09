# ⚡ PowerStudy

Dashboard interativo para rastrear tempo de estudo na faculdade, com sistema de gamificação e recomendações de estudo por IA.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red?logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- 📊 **Dashboard** — KPIs, heatmap de estudos (estilo GitHub), gráficos interativos
- ⏱️ **Timer integrado** — Pomodoro (25/50/90 min) + Cronômetro livre com 🔔 a cada hora
- 📝 **Registro de sessões** — Manual ou via timer, com tópicos e notas
- 📚 **Gerenciamento de matérias** — Por semestre, com cores personalizadas
- 📈 **Analytics** — Evolução temporal, distribuição por matéria, horas por semana
- 📄 **Plano de Aula** — Upload de PDFs, extração de tópicos, checklist de progresso
- 🤖 **Recomendações IA** — Groq (Llama 3) ou Google Gemini analisam seu progresso
- 🏆 **Gamificação** — Pontos, níveis (Calouro → Lenda), badges por matéria, streaks

## 🚀 Como usar

### Localmente

```bash
# Clonar
git clone https://github.com/SEU_USUARIO/PowerStudy.git
cd PowerStudy

# Instalar dependências
pip install -r requirements.txt

# Rodar
streamlit run app.py
```

### Deploy (Streamlit Cloud)

1. Faça push para o GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte seu repositório
4. Selecione `app.py` como arquivo principal
5. Deploy! 🎉

## 🔑 Configurar IA (opcional)

Para recomendações de estudo com IA, obtenha uma API Key gratuita:

- **Groq (Recomendado)**: [console.groq.com](https://console.groq.com) → API Keys → Create
- **Google Gemini**: [aistudio.google.com](https://aistudio.google.com) → Get API Key

Cole a key no sidebar do app (seção 🤖 Configurar IA).

## 🛠️ Tech Stack

| Tecnologia | Uso |
|------------|-----|
| Streamlit | Frontend + Backend |
| SQLite | Banco de dados local |
| Plotly | Gráficos interativos |
| PyMuPDF | Extração de PDF |
| Groq / Gemini | Recomendações IA |

## 📁 Estrutura

```
PowerStudy/
├── app.py                 # App principal
├── requirements.txt       # Dependências
├── database/              # Banco de dados
├── components/            # Páginas da UI
├── services/              # Lógica de negócio
└── assets/                # CSS customizado
```

---

Feito com ❤️ e ⚡ por PowerStudy
