from flask import Flask, request, jsonify
import sys, io, traceback
import subprocess
import os
import uuid

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Multi‑Language Code Runner</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/codemirror.min.css"/>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/addon/hint/show-hint.min.css"/>
  <style>
    body { margin:0; display:flex; flex-direction:column; height:100vh; font-family:Arial,sans-serif; }
    header { background:#282c34; color:#61dafb; padding:1rem; text-align:center; }
    #toolbar { display:flex; align-items:center; gap:1rem; padding:0.5rem 1rem; background:#f0f0f0; border-bottom:1px solid #ccc; }
    #editor { flex:1; }
    .CodeMirror { height:100%; font-size:1rem; }
    #controls { padding:1rem; text-align:center; }
    button { padding:0.5rem 1rem; font-size:1rem; background:#61dafb; color:#282c34; border:none; border-radius:4px; cursor:pointer; }
    button:hover { background:#21a1f1; }
    #output { padding:1rem; background:#1e1e1e; color:#d4d4d4; font-family:monospace; height:25vh; overflow:auto; }
  </style>
</head>
<body>
  <header><h1>Code Runner (Python, JS, Ruby, PHP, Lua, Perl, Tcl, Julia, Racket, Scheme)</h1></header>
  <div id="toolbar">
    <label for="lang">Language:</label>
    <select id="lang">
      <option value="python">Python</option>
      <option value="javascript">JavaScript</option>
      <option value="ruby">Ruby</option>
      <option value="php">PHP</option>
      <option value="lua">Lua</option>
      <option value="perl">Perl</option>
      <option value="tcl">Tcl</option>
      <option value="julia">Julia</option>
      <option value="racket">Racket</option>
      <option value="scheme">Scheme</option>
    </select>
    <button id="run-btn">Run ▶️</button>
  </div>
  <div id="editor">
    <textarea id="code">// Select a language and write your code here</textarea>
  </div>
  <div id="output"></div>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/codemirror.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/mode/javascript/javascript.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/mode/ruby/ruby.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/mode/php/php.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/mode/lua/lua.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/mode/perl/perl.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/mode/tcl/tcl.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/mode/julia/julia.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/mode/racket/racket.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/mode/scheme/scheme.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.5/addon/hint/show-hint.min.js"></script>
  <script>
    const editor = CodeMirror.fromTextArea(document.getElementById('code'), {
      mode: 'python',
      lineNumbers: true,
      indentUnit: 4,
      tabSize: 4,
      indentWithTabs: false,
      extraKeys: { 'Tab': cm => cm.replaceSelection('    ', 'end'), 'Ctrl-Space': 'autocomplete' }
    });

    document.getElementById('lang').addEventListener('change', e => {
      const lang = e.target.value;
      editor.setOption('mode', lang);
      editor.setValue(`// ${lang} default code`);
    });

    document.getElementById('run-btn').addEventListener('click', () => {
      const lang = document.getElementById('lang').value;
      const code = editor.getValue();
      const out = document.getElementById('output');
      out.textContent = 'Running…';
      fetch('/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lang, code })
      })
      .then(r => r.json())
      .then(data => out.textContent = data.output)
      .catch(err => out.textContent = 'Error: ' + err);
    });
  </script>
</body>
</html>
"""


@app.route('/', methods=['GET'])
def index():
    return HTML_PAGE


@app.route('/run', methods=['POST'])
def run_code():
    data = request.get_json(force=True)
    lang = data.get('lang')
    code = data.get('code', '')
    buf = io.StringIO()

    if lang == 'python':
        try:
            old_out, old_err = sys.stdout, sys.stderr
            sys.stdout, sys.stderr = buf, buf
            exec(code, {})
        except Exception:
            traceback.print_exc(file=buf)
        finally:
            sys.stdout, sys.stderr = old_out, old_err

    elif lang == 'javascript':
        try:
            proc = subprocess.run(
                ['node', '-e', code],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10
            )
            buf.write(proc.stdout + proc.stderr)
        except Exception as e:
            buf.write(f"Error executing JavaScript: {str(e)}")

    elif lang == 'ruby':
        try:
            proc = subprocess.run(
                ['ruby', '-e', code],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10
            )
            buf.write(proc.stdout + proc.stderr)
        except Exception as e:
            buf.write(f"Error executing Ruby: {str(e)}")

    elif lang == 'php':
        try:
            # Create a temporary PHP file
            temp_file = f"/tmp/php_code_{uuid.uuid4()}.php"
            with open(temp_file, 'w') as f:
                f.write(f"<?php\n{code}\n?>")

            proc = subprocess.run(
                ['php', temp_file],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10
            )
            buf.write(proc.stdout + proc.stderr)

            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception as e:
            buf.write(f"Error executing PHP: {str(e)}")

    elif lang == 'lua':
        try:
            proc = subprocess.run(
                ['lua', '-e', code],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10
            )
            buf.write(proc.stdout + proc.stderr)
        except Exception as e:
            buf.write(f"Error executing Lua: {str(e)}")

    elif lang == 'perl':
        try:
            proc = subprocess.run(
                ['perl', '-e', code],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10
            )
            buf.write(proc.stdout + proc.stderr)
        except Exception as e:
            buf.write(f"Error executing Perl: {str(e)}")

    elif lang == 'tcl':
        try:
            # Create a temporary TCL file
            temp_file = f"/tmp/tcl_code_{uuid.uuid4()}.tcl"
            with open(temp_file, 'w') as f:
                f.write(code)

            proc = subprocess.run(
                ['tclsh', temp_file],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10
            )
            buf.write(proc.stdout + proc.stderr)

            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception as e:
            buf.write(f"Error executing Tcl: {str(e)}")

    elif lang == 'julia':
        try:
            proc = subprocess.run(
                ['julia', '-e', code],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10
            )
            buf.write(proc.stdout + proc.stderr)
        except Exception as e:
            buf.write(f"Error executing Julia: {str(e)}")

    elif lang == 'racket':
        try:
            # Create a temporary Racket file
            temp_file = f"/tmp/racket_code_{uuid.uuid4()}.rkt"
            with open(temp_file, 'w') as f:
                f.write(f"#lang racket\n{code}")

            proc = subprocess.run(
                ['racket', temp_file],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10
            )
            buf.write(proc.stdout + proc.stderr)

            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception as e:
            buf.write(f"Error executing Racket: {str(e)}")

    elif lang == 'scheme':
        try:
            # Create a temporary Scheme file
            temp_file = f"/tmp/scheme_code_{uuid.uuid4()}.scm"
            with open(temp_file, 'w') as f:
                f.write(code)

            proc = subprocess.run(
                ['guile', temp_file],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10
            )
            buf.write(proc.stdout + proc.stderr)

            # Clean up
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception as e:
            buf.write(f"Error executing Scheme: {str(e)}")

    else:
        buf.write(f"Language '{lang}' is not supported.")

    return jsonify({"output": buf.getvalue()})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)