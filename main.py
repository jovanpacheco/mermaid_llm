from fastapi.responses import HTMLResponse
from urllib.parse import unquote
from fastapi import FastAPI, Request, Form
from openai import OpenAI
import enviroment


app = FastAPI()

@app.get("/textarea", response_class=HTMLResponse)
async def render_mermaid(request: Request):
    # Obtener parámetro 'code' de la URL (GET)
    code = request.query_params.get("code", """
    flowchart TD
    A[Inicio] --> B{¿Usuario autenticado?}
    B -- Sí --> C[Pantalla principal]
    B -- No --> D[Página de login]
    C --> E[Cerrar sesión]
    E --> B
    """)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Editor Mermaid</title>
        <script type="module">
          import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
          mermaid.initialize({{ startOnLoad: true }});
        </script>
        <style>
            body {{ font-family: sans-serif; margin: 20px; }}
            textarea {{ width: 100%; height: 200px; }}
            .mermaid {{ border: 1px solid #ccc; padding: 1rem; margin-top: 2rem; }}
        </style>
    </head>
    <body>
        <h1>Editor de Diagrama Mermaid</h1>
        <form method="get">
            <label for="code">Código Mermaid:</label><br>
            <textarea name="code">{code}</textarea><br><br>
            <button type="submit">Renderizar</button>
        </form>

        <h2>Vista previa:</h2>
        <div class="mermaid">
        {code}
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Generador Mermaid</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js" onload="mermaid.initialize({ startOnLoad: false })"></script>
    <script>
        mermaid.initialize({ startOnLoad: false });

        async function generar(event) {
            event.preventDefault();
            
            const container = document.getElementById("mermaid");
            const input = document.getElementById("prompt").value;
            
            container.innerHTML = 'Cargando'
            const response = await fetch("/generar", {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: new URLSearchParams({ prompt: input })
            });
            const code = await response.text();
            ///container.innerHTML = code;
            let contador = 0
            let idRender = `micounter-${contador}`;
            const { svg } = await mermaid.render(idRender.toString(), code);
            ////alert(svg);
            container.innerHTML = svg;
            contador = contador + 1;

        }
    </script>
</head>
<body>
    <h2>Generador de Diagrama Mermaid</h2>
    <form onsubmit="generar(event)">
        <input type="text" id="prompt" name="prompt" placeholder="Describe tu diagrama" style="width: 60%;">
        <button type="submit">Generar</button>
    </form>
    <div id="mermaid" style="margin-top:20px; border:1px solid #ccc; padding:10px;"></div>
</body>
</html>
"""



@app.get("/llm", response_class=HTMLResponse)
async def index():
    return HTML_TEMPLATE

@app.post("/generar", response_class=HTMLResponse)
async def generar(prompt: str = Form(...)):

    client = OpenAI(
        api_key=enviroment.key
    )
    model = "gpt-4.1-mini-2025-04-14"
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": f"""
                Necesito que me devuelvas un codigo de Mermaid para un diagrama de {prompt}: 
                * Solo devuelve codigo
                * Sin palabras adicionales
                * Antes de responder verifica que la respuesta que estas dando sea solo codigo Mermaid
                """
            },
            {"role": "user", "content": prompt}
        ]
    )
    data_res = completion.choices[0].message.content.replace("```","").replace("mermaid","")
    data_res = data_res.replace("graph TD", "flowchart TD")
    return data_res